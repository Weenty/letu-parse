import asyncio
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.command import Command
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import requests
import random
import os
import time
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
            print(f'Start browser with proxy {proxy}')
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
        # try:
        return self.get_by(xpath, By.XPATH)
            # return self.browser.find_element(By.XPATH, xpath)
        # except Exception as e:
        #     print(e)
        #     return None
    
    def get_page(self, url):
        self.browser.execute(Command.GET, {'url': url})
        print(f'navigate to {url}')
        self.check_and_switch_city()
    
    def force_click(self, element):
        ActionChains(self.browser).move_to_element(element).click(element).perform()
        self.browser.implicitly_wait(self.delay)
    
    def check_and_switch_city(self):
        city_labeel = self.get_by_class('header-city-selection__label')
        if not city_labeel:
            raise Exception('Не удалось получить город из шапки страницы!')
        city = city_labeel.get_property('textContent').strip()
        if 'Москва' not in city:
            print(f'Установленный город {city}, попытка переключения')
            self.force_click(city_labeel)
            item = self.get_by_xpath("//a[contains(text(), 'Москва')]")
            if item:
                self.force_click(item)
                time.sleep(2)
                print('Успешное переключение')
            else:
                raise Exception('Произошла ошибка при переключении города')
        else:
            print('Город "Моксва", продолжаем работу')
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
        proxy = None
        if len(self.proxy_list) > 0:
            proxy = self.proxy_list.pop(random.randrange(len(self.proxy_list)))
            print(f'Количетсов оставшихся прокси - {len(self.proxy_list)}')
        loop = asyncio.get_event_loop()
        future = await loop.run_in_executor(self.executor, Browser.create, url, proxy)
        browser = await future
        self.browsers.append(browser)
        return browser

    def _format_proxy(self, proxys: bytes, proxy_type) -> list:
        return [proxy_type + proxy_http for proxy_http in proxys.decode("utf-8").split('\n')]
    
    async def initialize_browsers(self):
        if not os.path.exists('./proxy-list.txt'):
            response_http_proxy = requests.get('https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt')
            response_socks5_proxy = requests.get('https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt')
            response_socks4_proxy = requests.get('https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt')
            
            response_http_proxy = self._format_proxy(response_http_proxy.content, 'http://')
            response_socks5_proxy = self._format_proxy(response_socks5_proxy.content, 'socks5://')
            response_socks4_proxy = self._format_proxy(response_socks4_proxy.content, 'socks4://')
            with open('proxy-list.txt', 'w') as file:
                file.write('\n'.join(response_http_proxy + response_socks4_proxy + response_socks5_proxy))
        
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