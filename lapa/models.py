import os
import subprocess
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytz
import requests
from django.db import models
from dotenv import load_dotenv

from lapa.utils import BrowserManager, TimeHandlerMixin

load_dotenv()


class ProfileManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(active=True)


class ProfileManagerAll(models.Manager):
    def get_queryset(self):
        return super().get_queryset()


class Profile(models.Model):
    objects = ProfileManager()
    all_objects = ProfileManagerAll()
    username = models.CharField(max_length=100, verbose_name="Username")
    user_id = models.CharField(max_length=100, verbose_name="User ID")
    webdriver = models.CharField(max_length=255, verbose_name="Webdriver", default="", blank=True)
    selenium = models.CharField(max_length=100, verbose_name="Selenium", default="", blank=True)
    timezone = models.CharField(max_length=100, verbose_name="Timezone", default="UTC")
    need_clear_posts_folder = models.BooleanField(default=False, verbose_name="Need clear posts folder")
    active = models.BooleanField(default=True, verbose_name="Active")

    CHROME_URL = os.getenv('CHROME_URL')
    SELERNIUM_URL = "127.0.0.1:{}"
    MAX_RETRIES = 5
    BASE_URL = "http://local.adspower.net:50325/api/v1/browser/start?user_id={user_id}"

    def __str__(self):
        return self.username

    def get_connection_data(self):
        page_url = self.BASE_URL.format(user_id=self.user_id)
        for i in range(self.MAX_RETRIES):
            response = requests.get(page_url).json()
            if response["code"] == 0:
                return response["data"]["webdriver"], response["data"]["ws"]["selenium"]
            elif "Too many request per second" in response["msg"]:
                time.sleep(1)
            else:
                raise Exception(response["msg"])
        raise Exception("Max retries exceeded")

    def update_profile(self, webdriver, selenium):
        self.webdriver = webdriver
        self.selenium = selenium
        self.save(update_fields=["webdriver", "seleneium"])


class Post(models.Model, TimeHandlerMixin):
    text = models.TextField(verbose_name="Text")
    image = models.ImageField(upload_to="images/", verbose_name="Image")
    sent = models.BooleanField(default=False, verbose_name="Sent")
    am_pm = models.CharField(max_length=2, choices=[("AM", "AM"), ("PM", "PM")], default="PM", verbose_name="AM/PM")
    time = models.IntegerField(choices=[(i, i) for i in range(1, 13)], default=1, verbose_name="Time")
    day_of_month = models.IntegerField(choices=[(i, i) for i in range(1, 32)], default=1, verbose_name="Day")
    next_month = models.BooleanField(default=False, verbose_name="Next month")
    is_12_plus = models.BooleanField(default=False, verbose_name="Is 12+")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clipboard_lock = threading.Lock()

    def increase_hour(self):
        Post.objects.filter(pk=self.pk).update(time=models.F("time") + 1)

    def img_to_clipboard(self):
        with self.clipboard_lock:
            try:
                subprocess.run(
                    "osascript -e 'set the clipboard to (read (POSIX file \"" + self.image.path + "\") as JPEG picture)'",
                    shell=True, check=True
                )
            except subprocess.CalledProcessError as e:
                print(e.output)
                raise

    def get_local_time(self, utc_time, timezone):
        utc_time = pytz.timezone('UTC').localize(utc_time)
        local_time = utc_time.astimezone(pytz.timezone(timezone))
        return local_time

    def create_post_for_profile(self, profile: Profile):
        self.browser_manager = BrowserManager(profile)
        driver = self.browser_manager.setup_webdriver()
        self.browser_manager.set_expiration_period(driver)
        day_of_month = self.day_of_month
        is_pm = self.am_pm == "PM"
        time_number = self.time
        next_month = self.next_month
        post_is_first = Post.objects.first() == self
        if not post_is_first:
            if profile.timezone == "Europe/Kiev":
                # + 2 UTC
                time_number, am_pm, day_of_month, next_month = self.calculate_month_day_pm_time_for_kiev(
                    self.time, self.am_pm, self.day_of_month
                )
                is_pm = am_pm == "PM"
            if profile.timezone == "EST":
                # - 5 UTC
                time_number, am_pm, day_of_month, next_month = self.calculate_month_day_pm_time_for_est(
                    self.time, self.am_pm, self.day_of_month
                )
                is_pm = am_pm == "PM"
            if profile.timezone == "Europe/Berlin":
                # + 1 UTC
                time_number, am_pm, day_of_month, next_month = self.calculate_month_day_pm_time_for_berlin(
                    self.time, self.am_pm, self.day_of_month
                )
                is_pm = am_pm == "PM"
            self.browser_manager.choose_day(
                driver, is_pm, time_number, day_of_month, next_month
            )
        self.browser_manager.upload_image(driver)
        self.browser_manager.add_text(driver, self.text)

    def fill(self):
        self.img_to_clipboard()
        profiles = Profile.objects.all()
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(self.create_post_for_profile, x) for x in profiles]
        for future in futures:
            future.result()

    def delete(self, *args, **kwargs):
        if os.path.isfile(self.image.path):
            os.remove(self.image.path)
        super().delete(*args, **kwargs)




