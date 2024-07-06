from manual_parse import runner, asyncio, result_array
import pandas
from itertools import groupby
import signal 
import os

file = None

if os.path.exists('output1.xlsx'):
    xls = pandas.ExcelFile('output1.xlsx')
    file = xls.parse(0)
elif os.path.exists('Задание_для_Разработчика_парсинга.xlsx'):
    xls = pandas.ExcelFile('Задание_для_Разработчика_парсинга.xlsx')
    file = xls.parse(1)
else:
    raise Exception('Не удалось найти файл для начала парсинга!')

def save_results():
    global result_array, file

    file_indexes = file.copy().reset_index()
    dict_urls = dict()
    for index, row in file_indexes.iterrows():
        dict_urls[row['Конкурент ссылка']] = index
    print(result_array)
    for strict in result_array:
        index = dict_urls[strict['url']]
        file.at[index, 'Цена до скидки'] = strict['full_price']
        file.at[index, 'Цена со скидкой или по карте лояльности'] = strict['price']
        file.at[index, 'Доступен для заказа (есть остаток)'] = strict['unvalible']
        file.at[index, 'Дата'] = strict['date']

    with pandas.ExcelWriter('output1.xlsx') as writer:
        file.to_excel(writer, sheet_name='result')

    print("Results saved to output1.xlsx")
    exit()


async def main():
    global result_array

    data_frame = file[file['Цена со скидкой или по карте лояльности'].isnull() & file['Цена до скидки'].isnull()]
    urls = data_frame['Конкурент ссылка']
    urls = list(urls)
    urls = [el for el, _ in groupby(urls)]
    
    await runner(urls, 20)
    save_results()

def signal_handler(signal, frame):
    print("Interrupted! Saving results...")
    save_results()

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Process interrupted")