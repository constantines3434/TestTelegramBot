import sqlite3


class SqlHandler:
    """Класс обработки SQL-запросов"""

    # Атрибуты (описание полей)
    db_name: str                 # имя файла базы данных
    conn: sqlite3.Connection     # объект соединения
    cursor: sqlite3.Cursor       # объект курсора
    table_name: str              # имя таблицы
    fields: dict                 # структура полей таблицы

    def __init__(self, db_name: str):
        """Конструктор класса"""
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.table_name = "users"
        self.fields = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL",
            "age": "INTEGER"
        }

    def connect(self):
        """Подключение к базе данных"""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()

    def close(self):
        """Закрытие соединения"""
        if self.conn:
            self.conn.close()

    def create_user_table(self):
        """Создание таблицы пользователей"""
        fields_str = ", ".join(
            f"{name} {dtype}" for name, dtype in self.fields.items()
        )
        query = f"CREATE TABLE IF NOT EXISTS {self.table_name} ({fields_str})"
        self.cursor.execute(query)
        self.conn.commit()

    def insert_user(self, name: str, age: int):
        """Добавление пользователя"""
        sql = f"INSERT INTO {self.table_name} (name, age) VALUES (?, ?)"
        self.cursor.execute(sql, (name, age))
        self.conn.commit()

    def get_all_users(self):
        """Получение всех пользователей"""
        sql = f"SELECT * FROM {self.table_name}"
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def update_user_age(self, name: str, new_age: int):
        """Обновление возраста пользователя"""
        sql = f"UPDATE {self.table_name} SET age = ? WHERE name = ?"
        self.cursor.execute(sql, (new_age, name))
        self.conn.commit()

    def delete_user(self, name: str):
        """Удаление пользователя по имени"""
        sql = f"DELETE FROM {self.table_name} WHERE name = ?"
        self.cursor.execute(sql, (name,))
        self.conn.commit()
