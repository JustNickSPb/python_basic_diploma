## Установка бота
Для начала работы необходимо:
1. Зарегистрировать желаемое имя бота, найдя в телеграмме специального бота для регистрации ботов @BotFather, написав ему "/start" и следуя его дальнейшим указаниям.
2. Выполнить установку необходимых для работы бота пакетов:

        pip install -r requirements.txt

3. Создать файл .env - шаблон в  template.env.txt, в BOT_TOKEN вписать токен, полученный в п.1.

## Запуск бота
Бот запускается командой из корневой папки проекта:

    python main.py

## Использование бота
Для использования бота существует 4 команды:

* [/help](#help)
* [/lowprice](#lowprice)
* [/highprice](#highprice)
* [/bestdeal](#bestdeal)

### help
Команда выводит справочник с кратким описанием доступных команд бота
### lowprice
Команда позволяет осуществить поиск самых дешевых отелей в выбранном городе
### highprice
Команда позволяет осуществить поиск самых дорогих отелей в выбранном городе
### bestdeal
Команда позволяет подобрать отели в заданном ценовом диапазоне, находящиеся не далее заданного расстояния от центра выбранного города