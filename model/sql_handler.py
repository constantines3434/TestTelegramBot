import sqlite3


class SqlHandler:
    """Класс обработки SQL-запросов"""

    # Атрибуты (описание полей)
    db_name: str                 # имя файла базы данных
    conn: sqlite3.Connection     # объект соединения
    cursor: sqlite3.Cursor       # объект курсора
    table_name: str              # имя таблицы
    #fields: dict                 # структура полей таблицы

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
    