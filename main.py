import time
import sqlite3
import telebot

from model.user import User
from model.custom_bot import CustomBot
from model.sql_handler import SqlHandler

# Работа с ботом
token = "8475418659:AAFYV-tcGCHMpEraIhSNIW5yq1K3uZ8uF4w"
bot = CustomBot(token)
while True:
    try:
        bot.bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(15)

