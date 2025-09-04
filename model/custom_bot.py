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
   
    def __init__(self, token: str):
        self.__bot = TeleBot(token)
        self.register_handlers() 
    
    def register_handlers(self):
        """Регистрируем все обработчики"""
        self.__bot.message_handler(commands=['start'])(self.start)
        self.__bot.message_handler(commands=['help'])(self.help)
        self.__bot.message_handler(commands=['filters'])(self.filter)
        self.__bot.message_handler(func=self.is_reply_button)(self.handle_reply_buttons)
        self.__bot.callback_query_handler(func=lambda call: call.data == "interest_done")(self.handle_interest_inline_callback)
        self.__bot.callback_query_handler(func=lambda call: call.data == "sex_done")(self.handle_sex_inline_callback)
        self.__bot.callback_query_handler(func=lambda call: call.data == "m_sex")(self.handle_sex_inline_callback)
        self.__bot.callback_query_handler(func=lambda call: call.data == "f_sex")(self.handle_sex_inline_callback)
        self.__bot.message_handler(content_types=['text'])(self.handle_other_text)
    
    @property
    def bot(self) -> TeleBot:
        """getter bot"""
        return self.__bot

    def start(self, message: Message):
        """Обработка команды /start"""
        # Проверяем, есть ли пользователь уже
        user = self.__users.get(message.chat.id)
        if not user:
            user = User()
            self.__users[message.chat.id] = user

        self.__bot.send_message(message.chat.id, "Как тебя зовут?")
        self.__bot.register_next_step_handler(message, self.user_registration, step="name")
    
    def help(self, message: Message):
        """Помощь пользователю"""
        self.__bot.send_message(message.chat.id, "Тут будет текст помощи пользователю")

    def filter(self, message: Message):
        """фильтры при поиске собеседника (интересы, пол, возраст[число..число])"""
        self.__bot.send_message(message.chat.id, "Тут будет текст фильтрации")
        self.get_user_interest(message)

    def user_registration(self, message: Message, step="name"):
        """Главный метод регистрации"""
        if step == "name":
            self.get_user_name(message)
        elif step == "age":
            self.get_user_age(message)
        elif step == "sex":
            self.choice_user_sex(message)
        elif step == "interest":
            self.get_user_interest(message) 
        
        """ после выбора пола
        self.show_main_menu(message.chat.id)
        self.__bot.send_message(message.chat.id, "Выберите интересы.")
            #self.__bot.register_next_step_handler(message, self.user_registration, step="interest")
            self.get_user_interest(message)"""

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
        self.choice_user_sex(message)
        
    #выбор пола пользователя
    def choice_user_sex(self, message: Message):
        """Отправка inline-кнопок для выбора пола"""
        user = self.__users.get(message.chat.id)
        selected_sex = user.sex if user else None
        menu = self.create_sex_menu(selected_sex)
        self.__bot.send_message(
            message.chat.id,
            "Выбери свой пол:",
            reply_markup=menu
        )
        

    def create_sex_menu(self, selected_sex: str = None):  
        """Создание кнопок выбора пола с выделением выбранного"""
        markup = InlineKeyboardMarkup()
        
        text_m = "М ✅" if selected_sex == "М" else "М"
        text_f = "Ж ✅" if selected_sex == "Ж" else "Ж"

        btn1 = InlineKeyboardButton(text_m, callback_data="m_sex")
        btn2 = InlineKeyboardButton(text_f, callback_data="f_sex")
        
        markup.add(btn1, btn2)
        markup.add(InlineKeyboardButton("Готово", callback_data="sex_done"))        
        return markup

    def handle_sex_inline_callback(self, call):
        """Обработчик inline-кнопок выбора пола"""
        
        user_id = call.message.chat.id
        user = self.__users.get(user_id)
        self.__bot.answer_callback_query(call.id, "Попал в handle_sex_inline_callback")
        if not user:
            return
        
        # Обработка выбора пола
        updated = False
        if call.data == "m_sex":            
            if user.sex != "М":
                user.sex = "М"
                updated = True
            self.__bot.answer_callback_query(call.id, "Вы выбрали: Мужской")

        elif call.data == "f_sex":
            if user.sex != "Ж":
                user.sex = "Ж"
                updated = True
            self.__bot.answer_callback_query(call.id, "Вы выбрали: Женский")

        elif call.data == "sex_done":
            if not user.sex:
                self.__bot.answer_callback_query(call.id, "Выберите пол перед подтверждением!")
                return
            self.__bot.send_message(user_id, f"Пол выбран: {user.sex}. Продолжаем регистрацию...")
            self.user_registration(call.message, step="interest")

        # Обновляем клавиатуру только если был выбран другой пол
        if updated:
            try:
                self.__bot.edit_message_reply_markup(
                    chat_id=user_id,
                    message_id=call.message.message_id,
                    reply_markup=self.create_sex_menu(selected_sex=user.sex)
                )
            except apihelper.ApiTelegramException as e:
                if "message is not modified" not in str(e):
                    raise
   
    #интересы
    def get_user_interest(self, message: Message):
        """создание интересов """
        """menu = self.create_interest_menu()
        self.__bot.send_message(
            message.chat.id,
            "Выбери свои интересы (можно несколько):",
            reply_markup=menu
        )"""
    def create_interest_menu(self):  
        """Создание кнопок интересов"""
        """markup = InlineKeyboardMarkup()
        for key, selected in self.__interests.items():
            text = f"✅ {key}" if selected else key
            markup.add(InlineKeyboardButton(text, callback_data=key))
        markup.add(InlineKeyboardButton("Готово", callback_data="interest_done"))
        return markup"""
    
    def handle_interest_inline_callback(self, call):
        """Обработчик inline кнопки выбора интересов"""
        """user_id = call.message.chat.id
        user = self.__users.get(user_id)
        if not user:
            return  # пользователь не найден

        if call.data == "interest_done":
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
            except apihelper.ApiTelegramException as e:
                if "message is not modified" not in str(e):
                    raise"""

    
            
    #фильтр выбора пола собеседника
    def choice_filter_user_sex(self, message: Message):
        """Обработчик выбора пола """
        menu = self.create_sex_menu()
        self.__bot.send_message(
            message.chat.id,
            "Выберите пол собеседника :",
            reply_markup=menu
        )

    def create_filter_sex_menu(self):  
        """Создание кнопок интересов"""
        markup = InlineKeyboardMarkup()
        btn1 = InlineKeyboardButton("М", callback_data="m_sex")
        btn2 = InlineKeyboardButton("Ж", callback_data="f_sex")
        markup.add(btn1, btn2)
        markup.add(InlineKeyboardButton("Готово", callback_data="sex_done"))        
        return markup
    
    def handle_filter_sex_inline_callback(self, call):
        """Обработчик inline кнопки выбора интересов"""
        """ser_id = call.message.chat.id
        user = self.__users.get(user_id)
        if not user:
            return  # пользователь не найден

        if call.data == "sex_done":
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
            except apihelper.ApiTelegramException as e:
                if "message is not modified" not in str(e):
                    raise"""

        
    def show_main_menu(self, chat_id: int):
        """Показать главное меню с кнопками"""
        """markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(
            KeyboardButton("Начать диалог"),
            KeyboardButton("Выход")
        )"""
    
        
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

            self.__bot.send_message(user_id, f"Диалог c {user.name if user else 'Неизвестный'} завершён!")
    
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
            #interests1 = self.__selected_interests.get(user_id, {})
            #interests2 = self.__selected_interests.get(partner_id, {})
            #mutual_interests = [k for k in interests1 if interests1.get(k) and interests2.get(k)]

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