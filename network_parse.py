from core import Browser
import json
from datetime import datetime
from csv import DictWriter

async def runnner(base_url, file_name):
    result_array = []
    browser = await Browser.create('')
    
    run = True
    page = 1
    while run:
        url = f'{base_url}/page-{page}'
        page += 1
        browser.get_page(url)
        element = browser.get_by_class('products-group-content__info')
        
        if not element:
            raise Exception('Не удалось загрузить страницу')
        
        performance_logs = browser.browser.get_log("performance")
        for performance_log in performance_logs:
            log = json.loads(performance_log["message"])
            if log["message"]["method"] == 'Network.responseReceived':
                if 'https://www.letu.ru/s/api/product/listing/v1/products' in log["message"]["params"]["response"]["url"]:
                    requestId = log["message"]["params"]["requestId"]
                    body = browser.browser.execute_cdp_cmd('Network.getResponseBody', {'requestId': requestId})
                    body = json.loads(body['body'])
                    if len(body['products']) > 0:
                        for product in body['products']:
                            name = product['displayName']
                            price = product['priceWithoutCoupons'] or product['discountedPrice']
                            full_price = product['rawPrice']
                            brand_name = product['brandName']
                            stock = product['isOutOfStock']
                            date = datetime.now()
                            url = f'https://www.letu.ru/product/{product["sefName"]}/{product["repositoryId"]}'
                            result_array.append(
                                {
                                    'name': name,
                                    'brand_name': brand_name,
                                    'url': url,
                                    'price': price,
                                    'full_price': full_price,
                                    'stock': not stock, # наличие 
                                    'date': date
                                }
                            )
                    else:
                        run = False
    
    with open(file_name,'w', encoding='utf-8') as outfile:
        writer = DictWriter(outfile, ('name', 'brand_name', 'url','price', 'full_price', 'stock', 'date'))
        writer.writeheader()
        writer.writerows(result_array)
    print(f'{file_name} saved')