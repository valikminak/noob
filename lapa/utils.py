import calendar
import os
from datetime import datetime

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

import asyncio
from telethon import TelegramClient

load_dotenv()

api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
channel_id = os.getenv('CHANNEL_ID')


class Button:
    ADD_NEW_POST = '//*[@id="app"]/div[1]/header/nav/a[3]'
    EXP_PERIOD = '//*[@id="make_post_form"]/div[2]/div[1]/button[8]'
    EXP_PERIOD_ONE_DAY = '//*[@id="ModalPostExpiration___BV_modal_body_"]/div[2]/div/button[2]'
    EXP_PERIOD_SAVE = '//*[@id="ModalPostExpiration___BV_modal_footer_"]/button[2]'

    SCHEDULE_POST = '//*[@id="make_post_form"]/div[2]/div[1]/button[9]'
    TIME_BTN = '//*[@id="make_post_form"]/div[3]/div/div[2]/div[2]/div[2]'
    TIME_OK_BTN = '//*[@id="make_post_form"]/div[3]/div/div[2]/div[4]/div[3]/button'
    AM_BTN = '//*[@id="make_post_form"]/div[3]/div/div[2]/div[3]/div/div[3]/div[1]'
    PM_BTN = '//*[@id="make_post_form"]/div[3]/div/div[2]/div[3]/div/div[3]/div[2]'
    DAY_NUMBER_CONTAINER = '//*[@id="make_post_form"]/div[3]/div/div[2]/div[3]/div/div[2]'
    TOGGLE_NEXT_MONTH_BTN = '//*[@id="make_post_form"]/div[3]/div/div[2]/div[3]/div/div[1]/div[3]'

    TEXTAREA = '//*[@id="new_post_text_input"]'
    SCHEDULE_POST_BTN = '//*[@id="content"]/div[1]/div/div/div/div/div[1]/div'


class BrowserManager:
    hours = {
        i: f'//*[@id="make_post_form"]/div[3]/div/div[2]/div[3]/div/div[1]/div[{x if x != 13 else 1}]' for i, x in
        enumerate(range(2, 14), 1)
    }

    def __init__(self, profile):
        self.profile = profile

    def setup_webdriver(self):
        chrome_driver = self.profile.webdriver
        debugger_address = self.profile.selenium
        options = webdriver.ChromeOptions()
        options.add_experimental_option("debuggerAddress", debugger_address)
        options.add_argument("--headless")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-gpu")
        service = webdriver.ChromeService(executable_path=chrome_driver)
        return webdriver.Chrome(service=service, options=options)

    @staticmethod
    def click_element(xpath, driver):
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        ).click()

    @staticmethod
    def click_day_number_div(driver, div):
        driver.execute_script("arguments[0].click();", div)

    def set_expiration_period(self, driver):
        self.click_element(Button.EXP_PERIOD, driver)
        self.click_element(Button.EXP_PERIOD_ONE_DAY, driver)
        self.click_element(Button.EXP_PERIOD_SAVE, driver)
        return True

    def choose_day(self, driver, is_pm, time_number, day_of_month, need_to_change_month):
        self.click_element(Button.SCHEDULE_POST, driver)
        if need_to_change_month:
            self.click_element(Button.TOGGLE_NEXT_MONTH_BTN, driver)

        div_container = driver.find_element(By.XPATH, Button.DAY_NUMBER_CONTAINER)
        for div in div_container.find_elements(By.CLASS_NAME, "vdatetime-calendar__month__day"):
            span = div.find_element(By.TAG_NAME, "span")
            if span:
                child_span = span.find_element(By.TAG_NAME, "span")
                if child_span:
                    if child_span.text == str(day_of_month):
                        self.click_day_number_div(driver, div)
                        break
        self.click_element(Button.TIME_BTN, driver)
        if is_pm:
            self.click_element(Button.PM_BTN, driver)
        else:
            self.click_element(Button.AM_BTN, driver)
        self.click_element(self.hours[time_number], driver)
        self.click_element(Button.TIME_OK_BTN, driver)

        return True

    def add_text(self, driver, text):
        self.click_element(Button.TEXTAREA, driver)
        textarea = driver.find_element(By.XPATH, Button.TEXTAREA)
        actions = ActionChains(driver)
        actions.click(textarea)
        driver.execute_script("""
            arguments[0].value = arguments[1];
            var evt = new Event('input', { 'bubbles': true, 'cancelable': true });
            arguments[0].dispatchEvent(evt);
        """, textarea, text)
        return True

    def upload_image(self, driver):
        self.click_element(Button.TEXTAREA, driver)
        textarea = driver.find_element(By.XPATH, Button.TEXTAREA)
        actions = ActionChains(driver)
        actions.click(textarea)
        actions.key_down(Keys.COMMAND).send_keys('v').key_up(Keys.COMMAND).perform()

    def toggle_next_month(self, driver):
        self.click_element(Button.TOGGLE_NEXT_MONTH_BTN, driver)
        return True

    def schedule_post(self, driver):
        self.click_element(Button.SCHEDULE_POST_BTN, driver)
        return True

    def create_new_post(self, driver):
        self.click_element(Button.ADD_NEW_POST, driver)
        return True

    def make_screenshot(self, driver):
        driver.save_screenshot("screenshot.png")
        return True

    @staticmethod
    def switch_to_the_first_tab(driver):
        # TODO: making browser with more than one tab upwards, need fix
        window_handles = driver.window_handles
        if len(window_handles) > 1:
            for handle in window_handles:
                driver.switch_to.window(handle)
                if "/posts/create" in driver.current_url:
                    break


class TimeHandlerMixin:
    def calculate_time_pm_and_day(self, time, am_pm, day_of_month):
        need_to_change_month = False
        if all([time == 12, am_pm == "PM"]):
            am_pm = "AM"
            day_of_month, need_to_change_month = self.increment_day_of_month(day_of_month)
        elif all([time == 12, am_pm == "AM"]):
            am_pm = "PM"
        return am_pm, day_of_month, need_to_change_month

    def calculate_day_time_pm_plus_12(self, am_pm, day_of_month):
        now = datetime.now()
        _, num_days = calendar.monthrange(now.year, now.month)
        need_to_change_month = False
        am_pm_plus_12 = "PM" if am_pm == "AM" else "AM"
        if am_pm_plus_12 == "AM":
            day_of_month += 1
            if day_of_month > num_days:
                day_of_month = 1
                need_to_change_month = True
        return am_pm_plus_12, day_of_month, need_to_change_month

    def calculate_month_day_pm_time_for_kiev(self, time, am_pm, day_of_month):
        #  +2 hours for Kiev
        plus_12_time = (time + 2) % 12 or 12  # if plus_12_time is 0 then 12
        plus_12_am_pm = am_pm
        need_to_change_month = False
        if time in [10, 11]:
            plus_12_am_pm = "AM" if am_pm == "PM" else "PM"
            if am_pm == "PM":
                day_of_month, need_to_change_month = self.increment_day_of_month(day_of_month)
        return plus_12_time, plus_12_am_pm, day_of_month, need_to_change_month

    def calculate_month_day_pm_time_for_berlin(self, time, am_pm, day_of_month):
        #  +1 hours for Berlin
        plus_12_time = (time + 1) % 12 or 12  # if plus_12_time is 0 then 12
        plus_12_am_pm = am_pm
        need_to_change_month = False
        if time in [11]:
            plus_12_am_pm = "AM" if am_pm == "PM" else "PM"
            if am_pm == "PM":
                day_of_month, need_to_change_month = self.increment_day_of_month(day_of_month)
        return plus_12_time, plus_12_am_pm, day_of_month, need_to_change_month

    def calculate_month_day_pm_time_for_est(self, time, am_pm, day_of_month):
        # -5 hours for EST
        plus_12_time = (time - 5) % 12 or 12
        plus_12_am_pm = am_pm
        need_to_change_month = False
        if time in [1, 2, 3, 4]:
            plus_12_am_pm = "AM" if am_pm == "PM" else "PM"
            if am_pm == "AM":
                day_of_month, need_to_change_month = self.decrement_day_of_month(day_of_month)
        return plus_12_time, plus_12_am_pm, day_of_month, need_to_change_month

    def decrement_day_of_month(self, day_of_month):
        now = datetime.now()
        _, num_days = calendar.monthrange(now.year, now.month)
        day_of_month -= 1
        need_to_change_month = False
        if day_of_month < 1:
            day_of_month = num_days
            need_to_change_month = True
        return day_of_month, need_to_change_month

    def increment_day_of_month(self, day_of_month):
        now = datetime.now()
        _, num_days = calendar.monthrange(now.year, now.month)
        day_of_month += 1
        need_to_change_month = False
        if day_of_month > num_days:
            day_of_month = 1
            need_to_change_month = True
        return day_of_month, need_to_change_month


class TelegramManager:
    def __init__(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.my_client = TelegramClient('anon', api_id, api_hash, loop=loop)

    async def get_messages_async(self):
        messages = await self.my_client.get_messages(channel_id, limit=20)
        dir_name = "./images/"
        post_data = []
        message_ids = []
        for i, message in enumerate(messages):
            if isinstance(message.media, MessageMediaPhoto) or isinstance(message.media, MessageMediaDocument):
                img_name = f"img_{i}.jpg"
                filename = f"{dir_name}{img_name}"
                await self.my_client.download_media(message, filename)
                post_data.append({"image": filename, "text": message.message})
                message_ids.append(message.id)
        return post_data, message_ids

    def fetch_messages(self):
        with self.my_client:
            post_data, message_ids = self.my_client.loop.run_until_complete(self.get_messages_async())
            self.my_client.loop.run_until_complete(self.my_client.delete_messages(channel_id, message_ids))
        return post_data
