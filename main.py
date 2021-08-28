import os
import re

from dotenv import load_dotenv
import telebot
from telebot.types import CallbackQuery, Message

import classes
import functions


load_dotenv()
bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))
commands = ['/lowprice', '/highprice', '/bestdeal']
data = classes.DataBundle()


@bot.message_handler(content_types=['text'])
def get_text_messages(message: Message, data: classes.DataBundle) -> None:
    """
    Функция, маршрутизирующая запросы пользователя и выдающая в ответ соответствующее поведение
    :param Message message: контент (в данном случае - текст), получаемый от пользователя
    :param classes.DataBundle data: блок данных, который мы начинаем перегонять между функциями
    :return: возврата в традиционном понимании нет, функция сразу диктует боту поведение
    """
    if message.text in ["Привет", '/hello-world', '/start']:
        bot.send_message(message.from_user.id, "Приветствую!\n"
                                               '"/help" покажет справку,\n'
                                               '"/lowprice" найдет самые дешевые отели города,\n'
                                               '"/highprice" покажет самые дорогие отели города,\n'
                                               '"/bestdeal" найдет отели по диапазону цен и удаленности от центра')
    elif message.text == "/help":
        bot.send_message(message.from_user.id, "На данный момент доступны команды:\n"
                                               "\"Привет\": я еще раз с Вами поздороваюсь :)\n"
                                               '"/lowprice": запрос самых дешевых отелей в городе;\n'
                                               '"/highprice": запрос самых дорогих отелей в городе;\n'
                                               '"/bestdeal": фильтр отелей по цене и удаленности от центра города.')
    elif message.text in commands:
        data.command = message.text
        bot.send_message(message.from_user.id, "В каком городе будем искать?")
        bot.register_next_step_handler(message, set_city, data.command)
    else:
        bot.send_message(message.from_user.id, "Не могу распознать обращение. \n"
                                               "\"/help\" даст список доступных команд.")


def set_city(message: Message, data: classes.DataBundle) -> None:
    """
    Функция, получающая от пользователя в message город и тип поиска,
    и направляющая поток выполнения программы на получение количества результатов
    :param Message message: сообщение, полученное из маршрутизатора
    :param classes.DataBundle data: блок данных, в котором получаем все, помимо сообщения
    """
    data.search_city = message.text
    language = "ru_RU" if re.match(r'[А-Яа-яЁё]+', data.search_city) else "en_US"
    os.environ['LANG'] = language
    bot.send_message(message.from_user.id, 'Ищу город в базе...')
    city_found = functions.get_city_id(data.search_city)
    if city_found == '404':
        bot.send_message(message.from_user.id, 'Не могу найти такой город.\n'
                                               'Повторите, пожалуйста:')
        bot.register_next_step_handler(message, set_city, data.command)
    elif isinstance(city_found, list):
        dest_list = telebot.types.InlineKeyboardMarkup()
        for dest_id in city_found:
            i_city = classes.City(dest_id['caption'], dest_id['destinationId'])
            i_city.destination = re.sub(r'<[^<]+?>', '', i_city.destination)
            dest_list.add(telebot.types.InlineKeyboardButton(
                text=i_city.destination, callback_data=i_city.id + ' ' + data.command))
        bot.send_message(message.from_user.id, 'Уточните, что Вы имели в виду:', reply_markup=dest_list)
    else:
        data.search_city = city_found
        bot.send_message(message.from_user.id, 'Сколько вариантов хотите посмотреть?')
        bot.register_next_step_handler(message, set_qty, data)


def set_qty(message: Message, search_data: classes.DataBundle) -> None:
    """
    Функция, добавляющая в поиск параметр "количество вариантов на показ".
    :param Message message: сообщение, перенаправленное с set_city()
    :param classes.DataBundle search_data: параметры поиска, переданные в блоке данных
    """
    if not search_data.distance:
        search_data.distance = '10000'
    # Если пользователь опечатался в минимальной и максимальной цене, поправим:
    if search_data.command == '/bestdeal':
        if int(search_data.max_price) < int(search_data.min_price):
            search_data.max_price, search_data.min_price = search_data.min_price, search_data.max_price

    search_data.response_qty = message.text
    bot.send_message(message.from_user.id, 'Минутку, ищу отели по Вашему запросу...')
    result = functions.get_hotels_by_price(search_data)
    for each in result:
        bot.send_message(message.from_user.id, each)


# Обработчик нажатий на кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call: CallbackQuery) -> None:
    """
    Функция, получающая данные о нажатой кнопке при уточнении города,
    и направляющая дальнейший поток выполнения программы в зависимости от команды:
    при "/bestdeal" - на поток набора параметров для запроса по "/bestdeal";
    при остальных командах - сразу на установку количества вариантов
    :param CallbackQuery call: запрос, направленный с кнопки InLine-клавиатуры
    """
    data.city, data.command = call.data.split()
    if data.command == '/bestdeal':
        bot.send_message(call.message.chat.id, 'Введите минимальную суточную стоимость:')
        bot.register_next_step_handler(call.message, set_min_price, data)
    else:
        bot.send_message(call.message.chat.id, 'Сколько вариантов хотите посмотреть?')
        bot.register_next_step_handler(call.message, set_qty, data)


def set_min_price(message: Message) -> None:
    """
    Функция, устанавливающая минимальную цену поиска
    :param Message message: сообщение с минимальной стоимостью для обработки
    """
    data.min_price = message.text
    bot.send_message(message.from_user.id, 'Введите максимальную суточную стоимость:')
    bot.register_next_step_handler(message, set_max_price, data)


def set_max_price(message: Message) -> None:
    """
    Функция, устанавливающая максимальную цену поиска
    :param Message message: сообщение с минимальной стоимостью для обработки
    """
    data.max_price = message.text
    bot.send_message(message.from_user.id, 'Насколько далеко от центра города ищем?')
    bot.register_next_step_handler(message, set_distance_from_center, data)


def set_distance_from_center(message: Message) -> None:
    """
    Функция, устанавливающая расстояние от центра города, на котором надо найти отель
    :param Message message: сообщение с минимальной стоимостью для обработки
    """
    data.distance = message.text
    bot.send_message(message.from_user.id, 'Сколько вариантов хотите посмотреть?')
    bot.register_next_step_handler(message, set_qty, data)


bot.polling(none_stop=True, interval=1)
