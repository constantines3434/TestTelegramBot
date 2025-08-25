from telebot import TeleBot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from user import User


class CustomBot:
    """description of class CustomBot"""

    __bot: TeleBot
    users = {}             # {chat_id: User} — словарь всех пользователей
    waiting_users = []      # пользователи, которые ищут собеседника
    active_chats = {}       # словарь {id_пользователя: id_собеседника}

    def __init__(self, token: str):
        self.__bot = TeleBot(token)
        self.register_handlers() 
    
    def register_handlers(self):
        """Регистрируем все обработчики"""
        self.__bot.message_handler(commands=['start'])(self.start)
        self.__bot.message_handler(func=self.is_reply_button)(self.handle_reply_buttons)
        self.__bot.callback_query_handler(func=lambda call: True)(self.handle_callback)
        self.__bot.message_handler(content_types=['text'])(self.handle_other_text)
    
    @property
    def bot(self) -> TeleBot:
        return self.__bot

    def start(self, message: Message):
        """Обработка команды /start"""
        user = User()
        self.users[message.chat.id] = user
        self.__bot.send_message(message.chat.id, "Как тебя зовут?")
        self.__bot.register_next_step_handler(message, self.user_registration, step="name")

    def user_registration(self, message: Message, step="name"):
        """Главный метод регистрации"""
        if step == "name":
            self.get_user_name(message)
        elif step == "age":
            self.get_user_age(message)
        elif step == "sex":
            self.get_user_sex(message)    

    def get_user_name(self, message: Message):
        """Получение имени пользователя"""
        user = self.users.get(message.chat.id)
        if not user:
            user = User()
            self.users[message.chat.id] = user

        user.name = message.text.strip()
        self.__bot.send_message(message.chat.id, f"Приятно познакомиться, {user.name}!")
        # следующий шаг -> возраст
        self.__bot.send_message(message.chat.id, "Введи свой возраст")
        self.__bot.register_next_step_handler(message, self.user_registration, step="age")

    def get_user_age(self, message: Message):
        """Получение возраста пользователя"""
      
        user = self.users.get(message.chat.id)
        if not user:
            return

        try:
            user.age = int(message.text.strip())
        except ValueError:
            self.__bot.send_message(message.chat.id, "Возраст должен быть числом. Попробуй ещё раз.")
            self.__bot.register_next_step_handler(message, self.user_registration, step="age")
            return

        self.__bot.send_message(message.chat.id, f"Ваш возраст: {user.age}!")

        # следующий шаг -> пол
        self.__bot.send_message(message.chat.id, "Введи свой пол: М или Ж (позже сделаю кнопками)")
        self.__bot.register_next_step_handler(message, self.user_registration, step="sex")
        
    def get_user_sex(self, message: Message):
        """Получение пола пользователя"""
        user = self.users.get(message.chat.id)
        if not user:
            return
        try:
            sex: str
            sex = str(message.text.strip())
        except ValueError:
            self.__bot.send_message(message.chat.id, "Пол должен быть строкой. Попробуй ещё раз.")
            self.__bot.register_next_step_handler(message, self.user_registration, step="sex")
            return
        if(((sex == "М") or (sex == "Ж"))):
            #обработка
            user.sex = sex
            self.__bot.send_message(message.chat.id, f"Ваш пол: {user.sex}!")
            #отображение кнопок
            self.show_main_menu(message.chat.id)
            self.__bot.send_message(message.chat.id, "Можете использовать кнопки.")
        else:
            #сделать в цикле
            self.__bot.send_message(message.chat.id, "Пол должен быть М или Ж. Попробуй ещё раз.")
        
    def show_main_menu(self, chat_id: int):
        """Показать главное меню с кнопками"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            KeyboardButton("Начать диалог"),
            KeyboardButton("Выход")
        )
        #self.__bot.send_message(chat_id, "Что дальше?", reply_markup=markup)
        
    def handle_other_text(self, message: Message):
        """Обработчик непредусмотренных сообщений"""
        chat_id = message.chat.id
        if chat_id in self.active_chats:  
            partner_id = self.active_chats[chat_id]
            self.__bot.send_message(partner_id, f"Сообщение от собеседника: {message.text}")
        else:
            self.__bot.send_message(chat_id, "Для продолжения выбери /start или кнопки")

    def handle_callback(self, call):
        """обработчик inline кнопки"""
        if call.data == "continue":
            self.__bot.send_message(call.message.chat.id, "Вы выбрали продолжить")
        elif call.data == "exit":
            self.__bot.send_message(call.message.chat.id, "До встречи!")

    def is_reply_button(self, msg: Message) -> bool:
        """провека текста кнопки"""
        return msg.text in ["Начать диалог", "Выход"]

    def handle_reply_buttons(self, message: Message):
        """Обработчик reply кнопок"""
        user_id = message.chat.id

        if message.text == "Начать диалог":
            self.__bot.send_message(user_id, "Поиск пользователя...")
            self.search_user(user_id)

        elif message.text == "Выход":
            if user_id in self.active_chats:
                partner_id = self.active_chats.pop(user_id)  # убираем себя из active_chats
                if partner_id in self.active_chats:
                    self.active_chats.pop(partner_id)

                # достаём User-объекты из словаря
                user = self.users.get(user_id)
                partner = self.users.get(partner_id)

                # уведомляем собеседника
                if partner:
                    self.__bot.send_message(
                        partner_id,
                        f"❌ Собеседник {user.name if user else 'Неизвестный'} завершил диалог."
                    )
            else:
                self.__bot.send_message(user_id, "❌ Вы не находитесь в диалоге.")

            self.__bot.send_message(user_id, "До встречи!")
    
    def get_sex_emoji(self, user: User) -> str:
        """Получени эмодзи пола"""
        if hasattr(user, "sex"):
            if user.sex.lower() == "м":
                return "👨"
            elif user.sex.lower() == "ж":
                return "👩"
        return ""  # если пол не указан
    
    def search_user(self, user_id: int):
        """Метод поиска собеседника"""
        if self.waiting_users:
            partner_id = self.waiting_users.pop(0)

            self.active_chats[user_id] = partner_id
            self.active_chats[partner_id] = user_id

            user1 = self.users.get(user_id)
            user2 = self.users.get(partner_id)

            emoji1 = self.get_sex_emoji(user1)
            emoji2 = self.get_sex_emoji(user2)

            self.__bot.send_message(
                user_id,
                f"✅ Собеседник найден!\nИмя: {user2.name}\n{emoji2}, Возраст: {user2.age}\nМожете начать чат."
            )
            self.__bot.send_message(
                partner_id,
                f"✅ Собеседник найден!\nИмя: {user1.name}\n{emoji1}, Возраст: {user1.age}\nМожете начать чат."
            )
        else:
            self.waiting_users.append(user_id)
            self.__bot.send_message(user_id, "🔎 Ждём подключения собеседника...")
