import calendar
import os
from concurrent.futures import ThreadPoolExecutor

from PIL import Image
from django import forms
from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from requests import Response

from lapa.models import Profile, Post

import pyautogui
from datetime import datetime, timedelta

from lapa.utils import TelegramManager, TimeHandlerMixin, BrowserManager


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("username", "user_id", "webdriver", "selenium")

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    actions = ["update_connection"]

    @admin.action(description="Update connection")
    def update_connection(self, request, queryset):
        bulk = []
        for x in queryset:
            wd, sel = x.get_connection_data()
            x.webdriver = wd
            x.selenium = sel
            bulk.append(x)
        Profile.objects.bulk_update(bulk, ['webdriver', 'selenium'])


@admin.register(Post)
class PostAdmin(admin.ModelAdmin, TimeHandlerMixin):
    list_display = (
        "_image", "next_month", "_text", "is_12_plus", "sent", "time", "day_of_month", "am_pm", "_fill_post")
    change_list_template = "admin/lapa/post_change_list.html"
    actions = ["_delete_selected"]

    class Meta:
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # return qs.order_by("pk")
        return qs.filter(sent=False).order_by("pk")

    def has_delete_permission(self, request, obj=None):
        return False

    @staticmethod
    def _delete_selected(modeladmin, request, queryset):
        queryset.delete()

    _delete_selected.short_description = "Delete"

    def _text(self, obj):
        post_text = obj.text[:70] + "..." if len(obj.text) > 70 else obj.text
        return mark_safe(f'<p>{post_text}</p>')

    @staticmethod
    def _image(obj):
        return mark_safe(f'<img src="{obj.image.url}" width="100" height="100">')

    @staticmethod
    def _fill_post(obj):
        url = reverse('admin:posts_fill_post')
        return mark_safe(
            f'<button type="button" data-id="{obj.pk}" class="fill-post btn" data-url="{url}" class="fill-post">FILL</button>')

    def make_screenshot(self):
        screenshot = pyautogui.screenshot(region=(0, 90, 1490, 600))
        dir_screenshot = "./screenshots/"
        done_screenshot_count = len(os.listdir("./now/"))
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        screenshot.save(f"{dir_screenshot}{done_screenshot_count}_{timestamp}.png")
        return True

    @staticmethod
    def clear_img_directory():
        img_folder = "images"
        for filename in os.listdir(img_folder):
            file_path = os.path.join(img_folder, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)

    def fetch_posts(self, request):
        # move screenshots to now folder
        self.move_screenshots()
        # delete all the posts and its images
        Post.objects.all().delete()
        self.clear_img_directory()
        # fetch new posts
        manager = TelegramManager()
        post_data = manager.fetch_messages()
        bulk_posts = []
        utc_time = datetime.utcnow()
        utc_time = utc_time + timedelta(minutes=10)  # add 10 minutes to utc_time
        utc_time_now = int(utc_time.strftime("%I"))
        am_pm = utc_time.strftime("%p")
        day_of_month = utc_time.day
        post_time = None
        need_to_change_month = False
        for i, data in enumerate(post_data):
            if i == 0:
                post_time = utc_time_now
            else:
                post_time += 1
                if post_time == 13:
                    post_time = 1
                am_pm, day_of_month, need_to_change_month = self.calculate_time_pm_and_day(
                    post_time, am_pm, day_of_month
                )
            bulk_posts.append(
                Post(
                    image=data["image"],
                    text=data["text"],
                    time=post_time,
                    am_pm=am_pm,
                    day_of_month=day_of_month,
                    next_month=need_to_change_month
                )
            )
        Post.objects.bulk_create(bulk_posts)
        self.create_posts_plus_12()
        return redirect(request.META.get('HTTP_REFERER'))

    def create_posts_plus_12(self):
        now = datetime.now()
        year, month = now.year, now.month
        _, num_days = calendar.monthrange(year, month)

        posts = Post.objects.all()
        bulk = []
        for post in posts:
            day_of_month = post.day_of_month
            am_pm_plus_12, day_of_month, new_need_to_change_month = self.calculate_day_time_pm_plus_12(
                post.am_pm, day_of_month
            )
            duplicate_post = Post(
                image=post.image,
                text=post.text,
                time=post.time,
                am_pm=am_pm_plus_12,
                day_of_month=day_of_month,
                next_month=new_need_to_change_month,
                is_12_plus=True
            )
            bulk.append(duplicate_post)
        Post.objects.bulk_create(bulk)

    def fill_post(self, request):
        if request.method == "POST":
            pk = request.POST.get("id")
            post = Post.objects.get(pk=pk)
            post.fill()
            post.sent = True
            post.save(update_fields=["sent"])
        return HttpResponse()

    def get_browser_manager_and_driver(self, profile: Profile):
        browser_manager = BrowserManager(profile)
        driver = browser_manager.setup_webdriver()
        return browser_manager, driver

    def schedule_post_for_profile(self, profile: Profile):
        browser_manager, driver = self.get_browser_manager_and_driver(profile)
        browser_manager.schedule_post(driver)

    def schedule_post(self, request):
        if request.method == "POST":
            profiles = Profile.objects.all()
            with ThreadPoolExecutor(max_workers=len(profiles)) as executor:
                futures = [executor.submit(self.schedule_post_for_profile, x) for x in profiles]
            for future in futures:
                future.result()
        self.make_screenshot()
        return HttpResponse()

    def click_plus_btn(self, profile: Profile):
        browser_manager, driver = self.get_browser_manager_and_driver(profile)
        browser_manager.create_new_post(driver)

    def create_new_post(self, request):
        if request.method == "POST":
            profiles = Profile.objects.all()
            with ThreadPoolExecutor(max_workers=len(profiles)) as executor:
                futures = [executor.submit(self.click_plus_btn, x) for x in profiles]
            for future in futures:
                future.result()
        return HttpResponse()

    def move_screenshots(self):
        dir_screenshot = "./screenshots/"
        dir_screenshot_now = "./now/"
        for filename in os.listdir(dir_screenshot):
            file_path = os.path.join(dir_screenshot, filename)
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.rename(file_path, f"{dir_screenshot_now}{filename}")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('fetch_posts/', self.admin_site.admin_view(self.fetch_posts), name="posts_fetch_posts"),
            path('fill_post/', self.admin_site.admin_view(self.fill_post), name="posts_fill_post"),
            path('schedule_post/', self.admin_site.admin_view(self.schedule_post), name="posts_schedule_post"),
            path('create_new_post/', self.admin_site.admin_view(self.create_new_post), name="posts_create_new_post"),
        ]
        return custom_urls + urls
