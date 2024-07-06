import asyncio
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.command import Command
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import requests
import random
import os
class Browser:
    @classmethod
    async def create(cls, url, proxy=None):
        self = cls()
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_argument("--output=/dev/null")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-crash-reporter")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-in-process-stack-traces")
        if proxy:
            chrome_options.add_argument(f"--proxy-server={proxy}")
        self.browser = webdriver.Chrome(options=chrome_options)
        self.delay = 10
        self.is_available = True
        self.proxy = proxy
        self.discard = False
        self.dev_tools = None
        # self.delay_counter = 10
        self.url = url
        return self
    
    def get_by(self, indetificator, locator):
        try:
            return WebDriverWait(self.browser, self.delay).until(EC.presence_of_element_located((locator, indetificator)))
        except TimeoutException:
            print(f"Timeout for {locator} {indetificator}")
        except Exception as e:
            print(e)
        return None
    
    def get_by_class(self, class_name):
        return self.get_by(class_name, By.CLASS_NAME)

    def get_by_id(self, id):
        return self.get_by(id, By.ID)
    
    def get_by_xpath(self, xpath):
        try:
            return self.browser.find_element(By.XPATH, xpath)
        except Exception as e:
            print(e)
            return None
    
    def get_page(self, url):
        self.browser.execute(Command.GET, {'url': url})
        print(f'navigate to {url}')
    
    def close(self):
        self.browser.quit()

class BrowserPool:
    def __init__(self, max_browsers):
        self.max_browsers = max_browsers
        self.executor = ThreadPoolExecutor(max_workers=max_browsers)
        self.semaphore = asyncio.Semaphore(max_browsers)
        self.browsers = []
        self.proxy_list = []
    async def create_browser(self, url):
        if len(self.proxy_list) > 0:
            proxy = random.choice(self.proxy_list)
        loop = asyncio.get_event_loop()
        future = await loop.run_in_executor(self.executor, Browser.create, url, proxy)
        browser = await future
        self.browsers.append(browser)
        return browser

    async def initialize_browsers(self):
        if not os.path.exists('./proxy-list.txt'):
            response = requests.get('https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt')
            with open('proxy-list.txt', 'wb') as file:
                file.write(response.content)
        
        with open('proxy-list.txt', 'r') as file:
            self.proxy_list = (file.read()).split('\n')
        
        await asyncio.gather(*[self.create_browser('https://google.com') for _ in range(self.max_browsers)])
    
    async def get_browser(self):
        async with self.semaphore:
            while True:
                for browser in self.browsers:
                    if browser.is_available:
                        browser.is_available = False
                        return browser
                await asyncio.sleep(0.1)

    async def release_browser(self, browser):
        browser.is_available = True
        print(f"browser release")

    def close_all_browsers(self):
        for browser in self.browsers:
            browser.close()

    def __del__(self):
        self.close_all_browsers()
    
    async def restart_browser_with_proxy(self, browser):
        browser.discard = True
        for index, item_browser in enumerate(self.browsers):
            if item_browser.discard:
                del self.browsers[index]
        browser.close()
        print(f"browser сlosed")
        new_browser = await self.create_browser('https://google.com')
        print('browser restarted')