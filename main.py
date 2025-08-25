import telebot
import time

#import sys
#sys.path.append("model")

from model.user import User
from model.custom_bot import CustomBot

user = User()
token: str = "8475418659:AAFYV-tcGCHMpEraIhSNIW5yq1K3uZ8uF4w"

bot = CustomBot(token)
bot.user = user

while True:
    try:
        # вызываем polling у приватного бота через геттер
        bot.bot.polling(none_stop=True, interval=0)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(15)
