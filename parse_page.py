import asyncio
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.command import Command
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
class Browser:
    @classmethod
    async def create(cls, url):
        self = cls()
        chrome_options = Options()
        # chrome_options.add_argument('--headless')
        self.browser = webdriver.Chrome(options=chrome_options)
        self.delay = 10
        self.is_available = True
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

    async def get_by_id(self, id):
        return await self.get_by(self.browser, id, By.ID)
    
    async def get_by_text(self, text):
        return await self.get_by(self.browser, text, By.LINK_TEXT)
    
    def get_page(self, url):
        self.browser.execute(Command.GET, {'url': url})

    def close(self):
        self.browser.quit()

class BrowserPool:
    def __init__(self, max_browsers):
        self.max_browsers = max_browsers
        self.executor = ThreadPoolExecutor(max_workers=max_browsers)
        self.semaphore = asyncio.Semaphore(max_browsers)
        self.browsers = []

    async def create_browser(self, url):
        loop = asyncio.get_event_loop()
        future = await loop.run_in_executor(self.executor, Browser.create, url)
        browser = await future
        self.browsers.append(browser)
        return browser

    async def initialize_browsers(self):
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