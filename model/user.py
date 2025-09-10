from model.interests import Interests
from model.sql_handler import SqlHandler
class User:
    """Класс пользователя"""

    __name: str
    __age: int
    __sex: str
    __interests: Interests
    __sex_filtration = {}
    __db_handler: SqlHandler
     
    def __init__(self):

        self.__name: str = None
        self.__age: int = None
        self.__sex: str = None
        self.__interests: Interests = Interests()
        self.__sex_filtration = {"М": False, "Ж": False}
        self.__db_handler = None

    

    def insert_user(self, name: str, age: int):
        """Добавление пользователя"""
        sql = f"INSERT INTO {self.__db_handler.table_name} (name, age) VALUES (?, ?)"
        self.__db_handler.cursor.execute(sql, (name, age))
        self.__db_handler.conn.commit()

    def get_all_users(self):
        """Получение всех пользователей"""
        sql = f"SELECT * FROM {self.__db_handler.table_name}"
        self.__db_handler.cursor.execute(sql)
        return self.__db_handler.cursor.fetchall()

    def update_user_age(self, name: str, new_age: int):
        """Обновление возраста пользователя"""
        sql = f"UPDATE {self.__db_handler.table_name} SET age = ? WHERE name = ?"
        self.__db_handler.cursor.execute(sql, (new_age, name))
        self.__db_handler.conn.commit()

    def delete_user(self, name: str):
        """Удаление пользователя по имени"""
        sql = f"DELETE FROM {self.__db_handler.table_name} WHERE name = ?"
        self.__db_handler.cursor.execute(sql, (name,))
        self.__db_handler.conn.commit()


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

    
     # ---- interests ----
    def get_interests(self) -> Interests:
        """getter for interests"""
        return self.__interests

    def set_interests(self, movie: bool, memes: bool, music: bool):
        """Установка значений интересов"""
        self.__interests.movie = movie
        self.__interests.memes = memes
        self.__interests.music = music

        # just_talking = True, если ни один интерес не выбран
        self.__interests.just_talking = not (movie or memes or music)

    def toggle_interest(self, key: str):
        """Переключить интерес по имени"""
        if hasattr(self.__interests, key):
            current_val = getattr(self.__interests, key)
            setattr(self.__interests, key, not current_val)

            # пересчёт just_talking
            if not (self.__interests.movie or self.__interests.memes or self.__interests.music):
                self.__interests.just_talking = True
            else:
                self.__interests.just_talking = False

    def compare_interests(self, other: "User") -> bool:
        """Сравнивает интересы с другим пользователем"""
        i1 = self.__interests
        i2 = other.get_interests()
        return (
            (i1.movie and i2.movie) or
            (i1.memes and i2.memes) or
            (i1.music and i2.music) or
            (i1.just_talking and i2.just_talking)
        )
    def get_mutual_interests(self, other: "User") -> list[str]:
        """Возвращает список общих интересов с другим пользователем"""
        i1 = self.get_interests()
        i2 = other.get_interests()
        return [k for k in ["movie", "memes", "music", "just_talking"] if getattr(i1, k) and getattr(i2, k)]

    # --- фильтрация по полу ---
    def set_sex_filter(self, sex: str, value: bool):
        """Включает/выключает фильтрацию по полу"""
        if sex not in self.__sex_filtration:
            raise ValueError("Некорректный пол для фильтра")
        self.__sex_filtration[sex] = value

    def get_sex_filters(self) -> dict:
        """Возвращает словарь фильтров по полу"""
        return self.__sex_filtration

    def matches_sex(self, other: "User") -> bool:
        """Проверяет, подходит ли другой пользователь по фильтру пола"""
        # Если фильтры выключены, подходит любой
        if not any(self.__sex_filtration.values()):
            return True
        return self.__sex_filtration.get(other.sex, False)