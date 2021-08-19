class City:
    """ Класс для хранения относящихся к городу переменных """
    def __init__(self, name, city_id) -> None:
        self.__destination = name
        self.__id = city_id
    
    @property
    def destination(self):
        return self.__destination

    @property
    def id(self):
        return self.__id
    
    @destination.setter
    def destination(self, new_name):
        self.__destination = new_name