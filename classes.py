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


class DataBundle:
    """
    Класс для хранения и передачи между функциями данных
    """
    def __init__(self) -> None:
        self.search_city = ''
        self.response_qty = ''
        self.command = ''
        self.min_price = ''
        self.max_price = ''
        self.distance = ''
