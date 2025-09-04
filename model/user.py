from model.interests import Interests
class User:
    """Класс пользователя"""

    __name: str
    __age: int
    __sex: str = None
    __interest: Interests = Interests()
     
    __interests = {"movie": False, "memes": False, "music": False}
    __selected_interests = {}
    __sex_filters = {"М": False, "Ж": False}
    __selected_sex_filters = {}
    
    def __init__(self):
        pass

    @property
    def name(self) -> str:
        """Получение значения свойства __name"""
        return self.__name

    @name.setter
    def name(self, value: str):
        """Установка значения свойства __name"""
        if not isinstance(value, str):
            raise ValueError("Имя должно быть строкой")
        self.__name = value

    @property
    def age(self) -> int:
        """Получение значения свойства __age"""
        return self.__age

    @age.setter
    def age(self, value: int):
        """Установка значения свойства __age"""
        if not isinstance(value, int):
            raise ValueError("Возраст должен быть целым числом")
        self.__age = value

    @property
    def sex(self) -> str:
        """Получение значения свойства __sex"""
        return self.__sex

    @sex.setter
    def sex(self, value: str):
        """Установка значения свойства __sex"""
        if not isinstance(value, str):
            raise ValueError("Пол должен быть строкой")
        self.__sex = value

    
    def get_interest(self) -> str:
        """Получение значения свойства __interest"""
        return self.__interest

    def set_interest(self, movie: bool, memes: bool, music: bool):
        """Установка значения свойства __interests"""
        self.__interest.movie = movie
        self.__interest.memes = memes
        self.__interest.music = music
        if((self.__interest.movie is False) 
           and (self.__interest.memes is False)
           and (self.__interest.music is False)):
            self.__interest.just_talking = True
        else:
            self.__interest.just_talking = False

    def compare_interests(self, other: "User") -> bool:
        """Сравнивает интересы с другим пользователем"""
        i1 = self.get_interest()  # self.__interest
        i2 = other.get_interest()  # other.__interest
        return (
            (i1.movie and i2.movie) or
            (i1.memes and i2.memes) or
            (i1.music and i2.music)
        )