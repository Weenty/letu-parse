from parse_page import BrowserPool, Browser
from selenium.webdriver.remote.webdriver import WebElement
from selenium.common.exceptions import WebDriverException
import asyncio
from datetime import datetime

BROWSERS = 1

PRICE_CLASS='product-detail-price__base-price'
FULL_PRICE_CLASS='product-detail-price__old--new-price'
NAME_CLASS='product-detail-sku-header-left-block__title'
UNVALIBLE_CLASS='product-detail-offer__unavailable--mt-new-design'

async def execute(executor, loop, func, *arg) -> WebElement:
    return await loop.run_in_executor(executor, func, *arg)

async def parse(pool: BrowserPool, url: str, result: list):
    browser: Browser = await pool.get_browser()
    try:
        strict = {
            'name':       NAME_CLASS,
            'price':      PRICE_CLASS,
            'full_price': FULL_PRICE_CLASS,
            'unvalible':  UNVALIBLE_CLASS
        }
        
        loop = asyncio.get_event_loop()
        await execute(pool.executor, loop, browser.get_page, url)
        for key in strict:
            element = await execute(pool.executor, loop, browser.get_by_class, strict[key])
            if key == 'unvalible':
                if element:
                    strict[key] = True
                else:
                    strict[key] = True
                continue
            
            if element:
                strict[key] = element.get_property('textContent').strip()
                if key == 'name' and ',' in strict[key]:
                    strict[key] = strict[key].split(',')[0]
                
                if (key == 'price' or key=='full_price') and '₽' in strict[key]:
                    strict[key] = strict[key].replace('₽', '').strip()
            else:
                strict[key] = None
                
        strict['date'] = datetime.now()
        strict['url'] = url
        result.append(strict)
        print(f'{url} WAS COMPLITED')
    
    except WebDriverException as e:
        if 'net::ERR_CONNECTION_TIMED_OUT' in e.msg:
            print('Network timeout! Kill browser and try with another proxy...')
            # todo убить браузер и включить снова, но с прокси
        else:
            print(e)
    except Exception as e:
        print(f"Error by url {url}: {e}")
    finally:
        await pool.release_browser(browser)

async def runner(urls):
    result = []
    try:
        pool = BrowserPool(max_browsers=BROWSERS)
        await pool.initialize_browsers()
        tasks = [asyncio.create_task(parse(pool, url, result)) for url in urls]
        await asyncio.gather(*tasks)
    except Exception as e:
        print(e)
    return result
