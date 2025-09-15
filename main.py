import time
import sqlite3
import telebot

from model.user import User
from model.custom_bot import CustomBot
from model.sql_handler import SqlHandler

# Работа с SQL

#тест
"""
user = User(db)
user.name = "Максимка"
user.age = 21
user.sex = "М"
user.insert_user_in_database()
db.get_all_users()
user.delete_user()
"""
"""
# Добавляем пользователей
db.insert_user("Алиса", 25)
db.insert_user("Боб", 30)
db.insert_user("Чарли", 28)

print("Все пользователи:")
for user in db.get_all_users():
    print(user)

db.update_user_age("Алиса", 26)
print("\nПосле обновления возраста Алисы:")
for user in db.get_all_users():
    print(user)

db.delete_user("Боб")
print("\nПосле удаления Боба:")
for user in db.get_all_users():
    print(user)
"""

# Работа с ботом
token = "8475418659:AAFYV-tcGCHMpEraIhSNIW5yq1K3uZ8uF4w"

bot = CustomBot(token)
while True:
    try:
        bot.bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(15)
