import telebot
from telebot.types import CallbackQuery, Message
import functions
import os
from dotenv import load_dotenv
import re
import classes


load_dotenv()
bot = telebot.TeleBot(os.environ.get('BOT_TOKEN'))
commands = ['/lowprice', '/highprice', '/bestdeal']


@bot.message_handler(content_types=['text'])
def get_text_messages(message: Message) -> None:
    """
    Функция, маршрутизирующая запросы пользователя и выдающая в ответ соответствующее поведение
    :param message Message: контент (в данном случае - текст), получаемый от пользователя
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
        command = message.text
        bot.send_message(message.from_user.id, "В каком городе будем искать?")
        bot.register_next_step_handler(message, set_city, command)
    else:
        bot.send_message(message.from_user.id, "Не могу распознать обращение. \n"
                                               "\"/help\" даст список доступных команд.")


def set_city(message: Message, command: str) -> None:
    """
    Функция, получающая от пользователя в message город и тип поиска,
    и направляющая поток выполнения программы на получение количества результатов
    :param message Message: сообщение, полученное из маршрутизатора
    :param command str: команда для выполнения, полученная из маршрутизатора
    """
    city = message.text
    language = "ru_RU" if re.match(r'[А-Яа-яЁё]+', city) else "en_US"
    os.environ['LANG'] = language
    bot.send_message(message.from_user.id, 'Ищу город в базе...')
    city_found = functions.get_city_id(city)
    if city_found == '404':
        bot.send_message(message.from_user.id, 'Не могу найти такой город.\n'
                                               'Повторите, пожалуйста:')
        bot.register_next_step_handler(message, set_city, command)
    elif isinstance(city_found, list):
        dest_list = telebot.types.InlineKeyboardMarkup()
        for dest_id in city_found:
            i_city = classes.City(dest_id['caption'], dest_id['destinationId'])
            i_city.destination = re.sub(r'<[^<]+?>', '', i_city.destination)
            dest_list.add(telebot.types.InlineKeyboardButton(
                text=i_city.destination, callback_data=i_city.id + ' ' + command))
        bot.send_message(message.from_user.id, 'Уточните, что Вы имели в виду:', reply_markup=dest_list)
    else:
        city = city_found
        bot.send_message(message.from_user.id, 'Сколько вариантов хотите посмотреть?')
        bot.register_next_step_handler(message, set_qty, city, command)


def set_qty(message: Message, city: str, command: str, 
            min_price: str ='', max_price: str ='', distance: str ='100000') -> None:
    """
    Функция, добавляющая в поиск параметр "количество вариантов на показ".
    :param message Message: сообщение, перенаправленное с set_city()
    :param city str: город поиска, заданный в set_city()
    :param command str: команда для поиска, перенаправленная с set_city()
    :param min_price str: минимальная цена для поиска
    :param max_price str: максимальная цена для поиска
    :param distance str: расстояние от центра города. Если не задано, есть дефолтные 100000
    """
    # Если пользователь опечатался в минимальной и максимальной цене, поправим:
    if command == '/bestdeal':
        if int(max_price) < int(min_price):
            max_price, min_price = min_price, max_price


    qty = message.text
    bot.send_message(message.from_user.id, 'Минутку, ищу отели по Вашему запросу...')
    result = functions.get_hotels_by_price(city, qty, command, min_price, max_price, distance)
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
    :param call CallbackQuery: запрос, направленный с кнопки InLine-клавиатуры
    """
    city, command = call.data.split()
    if command == '/bestdeal':
        bot.send_message(call.message.chat.id, 'Введите минимальную суточную стоимость:')
        bot.register_next_step_handler(call.message, set_min_price, city, command)
    else:
        bot.send_message(call.message.chat.id, 'Сколько вариантов хотите посмотреть?')
        bot.register_next_step_handler(call.message, set_qty, city, command)


def set_min_price(message: Message, city: str, command: str) -> None:
    """
    Функция, устанавливающая минимальную цену поиска
    :param message Message: сообщение с минимальной стоимостью для обработки
    :param city str: город поиска
    :param command str: тип поиска
    """
    min_price = message.text
    bot.send_message(message.from_user.id, 'Введите максимальную суточную стоимость:')
    bot.register_next_step_handler(message, set_max_price, city, command, min_price)


def set_max_price(message: Message, city: str, command: str, min_price: str) -> None:
    """
    Функция, устанавливающая максимальную цену поиска
    :param message Message: сообщение с минимальной стоимостью для обработки
    :param city str: город поиска
    :param command str: тип поиска
    :param min_price str: минимальная цена поиска
    """
    max_price = message.text
    bot.send_message(message.from_user.id, 'Насколько далеко от центра города ищем?')
    bot.register_next_step_handler(message, set_distance_from_center, city, command, min_price,
                                    max_price)


def set_distance_from_center(message: Message, city: str, 
                            command: str, min_price: str, 
                            max_price: str) -> None:
    """
    Функция, устанавливающая расстояние от центра города, на котором надо найти отель
    :param message Message: сообщение с минимальной стоимостью для обработки
    :param city str: город поиска
    :param command str: тип поиска
    :param min_price str: минимальная цена поиска
    :param max_price str: максимальная цена поиска
    """
    from_center = message.text
    bot.send_message(message.from_user.id, 'Сколько вариантов хотите посмотреть?')
    bot.register_next_step_handler(message, set_qty, city, command, min_price, max_price, from_center)


bot.polling(none_stop=True, interval=1)
