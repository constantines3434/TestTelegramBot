import sqlite3


class SqlHandler:
    """Класс обработки SQL-запросов"""

    # Атрибуты (описание полей)
    db_name: str                 # имя файла базы данных
    conn: sqlite3.Connection     # объект соединения
    cursor: sqlite3.Cursor       # объект курсора
    
    def __init__(self, db_name: str):
        """Конструктор класса"""
        self.db_name = db_name
        self.conn = None
        self.cursor = None

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
        fields: dict = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL",
            "age": "INTEGER",
            "sex": "TEXT",
            # булевы колонки для интересов
            "movie": "BOOLEAN DEFAULT 0",
            "memes": "BOOLEAN DEFAULT 0",
            "music": "BOOLEAN DEFAULT 0",
            "just_talking": "BOOLEAN DEFAULT 0"
        }
        
        fields_str = ", ".join(
            f"{name} {dtype}" for name, dtype in fields.items()
        )
        query = f"CREATE TABLE IF NOT EXISTS users ({fields_str})"
        self.cursor.execute(query)
        self.conn.commit()
    
    def get_all_users(self):
        """Получение всех пользователей"""
        sql = "SELECT * FROM users"
        self.cursor.execute(sql)
        return self.cursor.fetchall()
    
    def delete_user(self, id: int):
        """Удаление пользователя по имени"""
        sql = "DELETE FROM users WHERE id = ?"
        self.cursor.execute(sql, (id))
        self.conn.commit()