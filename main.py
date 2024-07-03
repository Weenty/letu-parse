# import asyncio
# from asyncio import Semaphore
# import pandas

# xls = pandas.ExcelFile('Задание_для_Разработчика_парсинга.xlsx')
# xls.parse(1)

from parse_page import BrowserPool, Browser
from selenium.webdriver.remote.webdriver import WebElement
import asyncio

BROWSERS = 2

async def parse(pool: BrowserPool, url: str):
    browser: Browser = await pool.get_browser()
    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(pool.executor, browser.get_page, url)
        element: WebElement = await loop.run_in_executor(pool.executor, browser.get_by_class, "product-detail-sku-header-left-block__title")
        if element:
            print(element.accessible_name)
    finally:
        await pool.release_browser(browser)

async def main():
    pool = BrowserPool(max_browsers=BROWSERS)
    await pool.initialize_browsers()
    
    urls = [
        'https://www.letu.ru/product/vivienne-sabo-paletka-tenei-fleur-du-soleil/104800719/sku/119700898',
        'https://www.letu.ru/product/vivienne-sabo-blesk-dlya-gub-tropique-gloss/128400604/sku/143800833',
        'https://www.letu.ru/product/vivienne-sabo-zhidkie-teni-dlya-vek-perle-de-la-mer-/118800773/sku/134101037'
    ]
    tasks = [asyncio.create_task(parse(pool, url)) for url in urls]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())