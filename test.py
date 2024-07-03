import pandas
xls = pandas.ExcelFile('Задание_для_Разработчика_парсинга.xlsx')
from itertools import groupby

file = xls.parse(1)

# print(file['Конкурент ссылка'])
# file['Цена до скидки'][0] = '123213'
    
from main import runner, asyncio


async def main():
    data_frame_urls = file['Конкурент ссылка']
    urls = list(data_frame_urls)
    urls = [el for el, _ in groupby(urls)]

    file_indexes = file.copy().reset_index()
    dict_urls = dict()
    for index, row in file_indexes.iterrows():
        dict_urls[row['Конкурент ссылка']] = index
    
    result_array = await runner(urls)
    
    for strict in result_array:
        index = dict_urls[strict['url']]
        file['Цена до скидки'][index] = strict['full_price']
        file['Цена со скидкой или по карте лояльности'][index] = strict['price']
        file['Доступен для заказа (есть остаток)'][index] = not strict['unvalible']
        file['Дата'][index] = strict['date']
    
    with pandas.ExcelWriter('output.xlsx') as writer:
        file.to_excel(writer, sheet_name='result')

if __name__ == '__main__':
    asyncio.run(main())