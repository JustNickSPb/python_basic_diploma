import datetime
import json
import os
from typing import List, Tuple

import requests
from requests import Response

import classes


def get_hotels_by_price(data: classes.DataBundle) -> List[str]:
    """
    Функция возвращает выборку отелей с выбранной сортировкой в выбранном городе
    :param classes.DataBundle data: параметры поиска
    :return List[str] result: результат поиска, возвращающийся в бот
    """
    distance = float(data.distance.replace(',', '.'))
    response = get_data_from_api(data)
    hotels_response = response[0]
    result = response[1]
    miles = response[2]
    hotels = json.loads(hotels_response.text)['data']['body']['searchResults']['results']
    
    for i_hotel in hotels:
        try:
            from_center = i_hotel['landmarks'][0].get('distance',
                            'Нет данных об удаленности от центра...')
            distance_checker = from_center.replace(miles, '')
            distance_checker = distance_checker.replace(',', '.')
            if distance < float(distance_checker):
                continue
            result.append('{hotel}.\n'
                        'Адрес: {address}.\n' 
                        'Расстояние от центра города: {from_center}.\n'
                        'Стоимость номера в сутки: {price}'.format(
                            hotel=i_hotel['name'],
                            address=i_hotel.get('address', {}).get('streetAddress', 
                            'Нет данных об адресе...'),
                            from_center=from_center,
                            price=i_hotel.get('ratePlan', {}).get('price', {}).get('current',
                            'Нет данных о расценках...')
            ))
        except Exception as err:
            result.append('Упс, ошибка. Отошлите, пожалуйста errors.log @Barykinnv')
            with open('errors.log', 'a', encoding='utf-8') as log:
                log.write('{time}: {error}'.format(
                    time=datetime.datetime.now(), error=err))
        
        # Предусматриваем вариант, при котором фильтры слишком строгие:
    if len(result) == 0 or (
        len(result) == 1 and result[0] == 'Не могу показать больше 10 результатов!'
    ):
        result.append('Ничего не нашлось. Попробуйте еще раз с другими параметрами')

    return result


def get_city_id(search_city: str):
    """
    Функция для нахождения id города
    :param str search_city: Название города, полученное от пользователя
    :return: City city: город, если при поиске обнаружен всего один инстанс города,
        List city_id_list: список destinationId, если при поиске обнаружено более одного города,
        str error_code: код ошибки для последующего его перевода во внятное описание ошибки для пользователя
    """
    city_search = 'locations/search'
    city_query = {"query": search_city, 'locale': os.environ.get('LANG')}
    city_response = requests.request(
        "GET", 
        os.environ.get('BASE_URL') + city_search, 
        headers={
            'x-rapidapi-key': os.environ.get('API_KEY'), 
            'x-rapidapi-host': os.environ.get('API_HOST')
        }, 
        params=city_query
        )
    try:
        city_id_list = json.loads(city_response.text)['suggestions'][0]['entities']
        if len(city_id_list) > 1:
            return city_id_list
        else:
            city_id = json.loads(city_response.text)['suggestions'][0]['entities'][0]['destinationId']
            return city_id
    except IndexError:
        error_code = '404'
        return error_code


def get_data_from_api(data: classes.DataBundle) -> Tuple[Response, List[str], str]:
    """
    Подфункция поиска отелей - собственно запрос к API
    :param classes.DataBundle data: блок данных для запроса
    :return: Возвращаем кортеж из:
        ответа API на запрос (распарсим его дальше),
        списка, подготовленного для хранения результатов 
            (если ничего не нашли - там уже будет сообщение об этом),
        региональной меры длины - это понадобится дальше при проверке расстояний до центра
    """
    result = []
    command = data.command
    qty = data.response_qty
    # Понимаем, какую сортировку включать:
    sorting = ''
    if command == '/lowprice':
        sorting = 'PRICE'
    elif command == '/highprice':
        sorting = 'PRICE_HIGHEST_FIRST'
    elif command == '/bestdeal':
        sorting = 'DISTANCE_FROM_LANDMARK'
    
    # Ограничиваем выборку заранее заданным числом:
    if int(qty) > 10:
        qty = '10'
        result.append('Не могу показать больше 10 результатов!')
    
    # Определяем язык и валюту поиска:
    language = os.environ.get('LANG')
    if language == 'ru_RU':
        currency = 'RUB'
        dist_measure = ' км'
    else:
        currency = 'USD'
        dist_measure = ' miles'
    
    # Собственно поиск:
    hotel_search = 'properties/list'
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)

    # Если '/bestdeal' - применяем больше фильтров при поиске:
    if command == '/bestdeal':
        hotel_query = {
            "adults1": "1",
            "pageNumber": "1",
            "destinationId": data.search_city,
            "pageSize": qty,
            "checkOut": tomorrow,
            "checkIn": today,
            "sortOrder": sorting,
            "locale": language,
            "currency": currency,
            'priceMax': data.max_price,
            'priceMin': data.min_price,
            'landmarkIds': 'Центр города'
        }
    else:
        hotel_query = {
            "adults1": "1",
            "pageNumber": "1",
            "destinationId": data.search_city,
            "pageSize": qty,
            "checkOut": tomorrow,
            "checkIn": today,
            "sortOrder": sorting,
            "locale": language,
            "currency": currency
        }
    hotels_response = requests.request(
        "GET", 
        os.environ.get('BASE_URL') + hotel_search, 
        headers={
            'x-rapidapi-key': os.environ.get('API_KEY'), 
            'x-rapidapi-host': os.environ.get('API_HOST')
        },
        params=hotel_query
        )

    return hotels_response, result, dist_measure
