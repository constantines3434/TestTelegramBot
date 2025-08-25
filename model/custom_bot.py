from telebot import TeleBot, apihelper
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from model.user import User


class CustomBot:
    """description of class CustomBot"""

    __bot: TeleBot
    __users = {}             # {chat_id: User} — словарь всех пользователей
    __waiting_users = []      # пользователи, которые ищут собеседника
    __active_chats = {}       # словарь {id_пользователя: id_собеседника}
    # состояние кнопок интересов
    __interests = {"movie": False, "memes": False, "music": False}
    __selected_interests = {}

    def __init__(self, token: str):
        self.__bot = TeleBot(token)
        self.register_handlers() 
    
    def register_handlers(self):
        """Регистрируем все обработчики"""
        self.__bot.message_handler(commands=['start'])(self.start)
        self.__bot.message_handler(func=self.is_reply_button)(self.handle_reply_buttons)
        self.__bot.callback_query_handler(func=lambda call: True)(self.handle_inline_callback)
        self.__bot.message_handler(content_types=['text'])(self.handle_other_text)
    
    @property
    def bot(self) -> TeleBot:
        """getter bot"""
        return self.__bot

    def start(self, message: Message):
        """Обработка команды /start"""
        user = User()
        self.__users[message.chat.id] = user
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
        elif step == "interest":
            self.get_user_interest(message) 

    def get_user_name(self, message: Message):
        """Получение имени пользователя"""
        user = self.__users.get(message.chat.id)
        if not user:
            user = User()
            self.__users[message.chat.id] = user

        user.name = message.text.strip()
        self.__bot.send_message(message.chat.id, f"Приятно познакомиться, {user.name}!")
        # следующий шаг -> возраст
        self.__bot.send_message(message.chat.id, "Введи свой возраст")
        self.__bot.register_next_step_handler(message, self.user_registration, step="age")

    def get_user_age(self, message: Message):
        """Получение возраста пользователя"""
        user = self.__users.get(message.chat.id)
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
        user = self.__users.get(message.chat.id)
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
            #отображение кнопок
            self.show_main_menu(message.chat.id)
            self.__bot.send_message(message.chat.id, "Выберите интересы.")
            #self.__bot.register_next_step_handler(message, self.user_registration, step="interest")
            self.get_user_interest(message)
        else:
            #сделать в цикле
            self.__bot.send_message(message.chat.id, "Пол должен быть М или Ж. Попробуй ещё раз.")
            self.__bot.register_next_step_handler(message, self.user_registration, step="sex")

    def get_user_interest(self, message: Message):
        """создание интересов """
        menu = self.create_interest_menu()
        self.__bot.send_message(
            message.chat.id,
            "Выбери свои интересы (можно несколько):",
            reply_markup=menu
        )
    def create_interest_menu(self):  
        """Создание кнопок интересов"""
        markup = InlineKeyboardMarkup()
        for key, selected in self.__interests.items():
            text = f"✅ {key}" if selected else key
            markup.add(InlineKeyboardButton(text, callback_data=key))
        markup.add(InlineKeyboardButton("Готово", callback_data="done"))
        return markup
    
    def handle_inline_callback(self, call):
        """Обработчик inline кнопки выбора интересов"""
        user_id = call.message.chat.id
        user = self.__users.get(user_id)
        if not user:
            return  # пользователь не найден

        if call.data == "done":
            # сохраняем выбранные интересы текущего пользователя
            self.__selected_interests[user_id] = self.__interests.copy()

            # Берём значения по ключам
            movie_val = self.__interests.get("movie", False)
            memes_val = self.__interests.get("memes", False)
            music_val = self.__interests.get("music", False)

            # Вызываем сеттер напрямую с тремя аргументами
            user.set_interest(movie_val, memes_val, music_val)

            # Отправляем итоговое сообщение
            try:
                self.__bot.edit_message_text(
                    chat_id=user_id,
                    message_id=call.message.message_id,
                    text=f"Вы выбрали: {', '.join([k for k, v in self.__interests.items() if v]) or 'ничего'}"
                )
            except apihelper.ApiTelegramException as e:
                if "message is not modified" not in str(e):
                    raise

        elif call.data in self.__interests:
            # Переключаем состояние выбранной кнопки
            self.__interests[call.data] = not self.__interests[call.data]

            # Обновляем клавиатуру с защитой от "message is not modified"
            try:
                self.__bot.edit_message_reply_markup(
                    chat_id=user_id,
                    message_id=call.message.message_id,
                    reply_markup=self.create_interest_menu()
                )
            except apihelper.ApiTelegramException as e:  # <--- здесь
                if "message is not modified" not in str(e):
                    raise



    def show_main_menu(self, chat_id: int):
        """Показать главное меню с кнопками"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            KeyboardButton("Начать диалог"),
            KeyboardButton("Выход")
        )
    
        
    def handle_other_text(self, message: Message):
        """Обработчик непредусмотренных сообщений"""
        chat_id = message.chat.id
        if chat_id in self.__active_chats:  
            partner_id = self.__active_chats[chat_id]
            self.__bot.send_message(partner_id, f"Сообщение от собеседника: {message.text}")
        else:
            self.__bot.send_message(chat_id, "Для продолжения выбери /start или кнопки")

    
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
            if user_id in self.__active_chats:
                partner_id = self.__active_chats.pop(user_id)  # убираем себя из active_chats
                if partner_id in self.__active_chats:
                    self.__active_chats.pop(partner_id)

                # достаём User-объекты из словаря
                user = self.__users.get(user_id)
                partner = self.__users.get(partner_id)

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
        """Метод поиска собеседника с совпадением интересов"""
        user = self.__users.get(user_id)
        if not user:
            return

        partner_id = None
        for uid in self.__waiting_users:
            candidate = self.__users.get(uid)
            if candidate and user.compare_interests(candidate):
                partner_id = uid
                break

        if partner_id:
            self.__waiting_users.remove(partner_id)
            self.__active_chats[user_id] = partner_id
            self.__active_chats[partner_id] = user_id

            user1 = user
            user2 = self.__users.get(partner_id)

            emoji1 = self.get_sex_emoji(user1)
            emoji2 = self.get_sex_emoji(user2)

            # взаимные интересы
            interests1 = self.__selected_interests.get(user_id, {})
            interests2 = self.__selected_interests.get(partner_id, {})
            mutual_interests = [k for k in interests1 if interests1.get(k) and interests2.get(k)]

            self.__bot.send_message(
                user_id,
                f"✅ Собеседник найден!\nИмя: {user2.name}\n{emoji2}, Возраст: {user2.age}\n"
                f"Взаимные интересы: {', '.join(mutual_interests) if mutual_interests else 'нет'}\nМожете начать чат."
            )
            self.__bot.send_message(
                partner_id,
                f"✅ Собеседник найден!\nИмя: {user1.name}\n{emoji1}, Возраст: {user1.age}\n"
                f"Взаимные интересы: {', '.join(mutual_interests) if mutual_interests else 'нет'}\nМожете начать чат."
            )
        else:
            self.__waiting_users.append(user_id)
            self.__bot.send_message(user_id, "🔎 Ждём подключения собеседника...")