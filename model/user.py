import sqlite3
from model.interests import Interests
from model.sql_handler import SqlHandler


class User:
    """Класс пользователя"""

    def __init__(self, db_handler: SqlHandler):
        self.__id: int | None = None
        self.__name: str | None = None
        self.__age: int | None = None
        self.__sex: str | None = None
        self.__interests: Interests = Interests()
        self.__sex_filtration: dict[str, bool] = {"М": False, "Ж": False}
        self.__db_handler = db_handler

    # --- свойства ---
    @property
    def id(self) -> int | None:
        return self.__id

    @property
    def name(self) -> str | None:
        return self.__name

    @name.setter
    def name(self, value: str):
        if not isinstance(value, str):
            raise ValueError("Имя должно быть строкой")
        self.__name = value

    @property
    def age(self) -> int | None:
        return self.__age

    @age.setter
    def age(self, value: int):
        if not isinstance(value, int):
            raise ValueError("Возраст должен быть целым числом")
        self.__age = value

    @property
    def sex(self) -> str | None:
        return self.__sex

    @sex.setter
    def sex(self, value: str):
        if value not in ("М", "Ж"):
            raise ValueError("Пол должен быть 'М' или 'Ж'")
        self.__sex = value

    # --- interests ---
    def get_interests(self) -> Interests:
        return self.__interests

    def set_interests(self, movie: bool, memes: bool, music: bool):
        self.__interests.movie = movie
        self.__interests.memes = memes
        self.__interests.music = music
        self.__interests.just_talking = not (movie or memes or music)

    def toggle_interest(self, key: str):
        if hasattr(self.__interests, key):
            current_val = getattr(self.__interests, key)
            setattr(self.__interests, key, not current_val)
            self.__interests.just_talking = not (
                self.__interests.movie or self.__interests.memes or self.__interests.music
            )

    def compare_interests(self, other: "User") -> bool:
        i1, i2 = self.__interests, other.get_interests()
        return (
            (i1.movie and i2.movie)
            or (i1.memes and i2.memes)
            or (i1.music and i2.music)
            or (i1.just_talking and i2.just_talking)
        )

    def get_mutual_interests(self, other: "User") -> list[str]:
        i1, i2 = self.get_interests(), other.get_interests()
        return [k for k in ["movie", "memes", "music", "just_talking"] if getattr(i1, k) and getattr(i2, k)]

    # --- фильтрация по полу ---
    def set_sex_filter(self, sex: str, value: bool):
        if sex not in self.__sex_filtration:
            raise ValueError("Некорректный пол для фильтра")
        self.__sex_filtration[sex] = value

    def get_sex_filters(self) -> dict[str, bool]:
        return self.__sex_filtration

    def matches_sex(self, other: "User") -> bool:
        if not any(self.__sex_filtration.values()):
            return True
        return self.__sex_filtration.get(other.sex, False)

    # --- работа с БД ---
    def save(self):
        """Сохраняет пользователя в БД (новая запись или обновление)"""
        if self.__id is None:  # новый пользователь
            sql = """
            INSERT INTO users (name, age, sex, movie, memes, music, just_talking)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            self.__id = self.__db_handler.execute(
                sql,
                (
                    self.__name,
                    self.__age,
                    self.__sex,
                    self.__interests.movie,
                    self.__interests.memes,
                    self.__interests.music,
                    self.__interests.just_talking
                ),
                commit=True,
                return_lastrowid=True
            )
        else:  # обновление
            sql = """
            UPDATE users
            SET name=?, age=?, sex=?, movie=?, memes=?, music=?, just_talking=?
            WHERE id=?
            """
            self.__db_handler.execute(
                sql,
                (
                    self.__name,
                    self.__age,
                    self.__sex,
                    self.__interests.movie,
                    self.__interests.memes,
                    self.__interests.music,
                    self.__interests.just_talking,
                    self.__id
                ),
                commit=True
            )
        
    def delete(self):
        """Удаляет пользователя из БД"""
        if self.__id is None:
            raise ValueError("Пользователь не сохранён в БД")
        sql = "DELETE FROM users WHERE id = ?"
        self.__db_handler.execute(sql, (self.__id,), commit=True)
        self.__id = None

    def load(self, user_id: int):
        """Загружает пользователя по id"""
        sql = """
            SELECT id, name, age, sex, movie, memes, music, just_talking
            FROM users
            WHERE id = ?
        """
        row = self.__db_handler.execute(sql, (user_id,), fetch=True)
        if row:
            (
                self.__id,
                self.__name,
                self.__age,
                self.__sex,
                movie,
                memes,
                music,
                just_talking,
            ) = row[0]
            self.__interests.movie = bool(movie)
            self.__interests.memes = bool(memes)
            self.__interests.music = bool(music)
            self.__interests.just_talking = bool(just_talking)