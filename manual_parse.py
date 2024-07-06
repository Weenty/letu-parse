from core import BrowserPool, Browser
from selenium.webdriver.remote.webdriver import WebElement
import asyncio
from datetime import datetime

PRICE_CLASS='product-detail-price__base-price'
FULL_PRICE_CLASS='product-detail-price__old--new-price'
NAME_CLASS='product-detail-sku-header-left-block__title'
UNVALIBLE_XPATH="product-detail-cart__button"

result_array = []

async def execute(executor, loop, func, *arg) -> WebElement:
    return await loop.run_in_executor(executor, func, *arg)

async def parse(pool: BrowserPool, url: str, result_array: list):
    browser: Browser = await pool.get_browser()
    browser_deleted = False
    try:
        strict = {
            'name':       NAME_CLASS,
            'price':      PRICE_CLASS,
            'full_price': FULL_PRICE_CLASS,
            'unvalible':  UNVALIBLE_XPATH
        }
        
        loop = asyncio.get_event_loop()
            
        await execute(pool.executor, loop, browser.get_page, url)
        for key in strict:
            method = browser.get_by_class
            
            element = await execute(pool.executor, loop, method, strict[key])
            
            if key == 'unvalible':
                strict[key] = bool(element)
                continue
            
            if element:
                strict[key] = element.get_property('textContent').strip()
                if key == 'name' and ',' in strict[key]:
                    strict[key] = strict[key].split(',')[0]
                
                if (key == 'price' or key=='full_price') and '₽' in strict[key]:
                    strict[key] = strict[key].replace('₽', '').strip()
            else:
                strict[key] = None
        
        if not strict['price'] and not strict['full_price']:
            raise Exception('Не удалось спарсить')
        
        strict['date'] = datetime.now()
        strict['url'] = url
        result_array.append(strict)
        print(f'PARSED {url}')
    except Exception as e:
        await pool.restart_browser_with_proxy(browser)
        browser_deleted = True
        print(f"Error by url {url}: {e}")
        return url
    finally:
        if not browser_deleted:
            await pool.release_browser(browser)
    return None

async def runner(urls, BROWSERS=1):
    try:
        pool = BrowserPool(max_browsers=BROWSERS)
        await pool.initialize_browsers()
        
        tasks = [asyncio.create_task(parse(pool, url, result_array)) for url in urls]
        # await asyncio.gather(*tasks)
        urls_dict = {task: url for task, url in zip(tasks, urls)}
        while tasks:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                url = urls_dict.pop(task)
                tasks.remove(task)
                result = await task
                if result is not None:
                    new_task = asyncio.create_task(parse(pool, result, result_array))
                    tasks.append(new_task)
                    urls_dict[new_task] = result
    except Exception as e:
        print(e)
    return result_array
