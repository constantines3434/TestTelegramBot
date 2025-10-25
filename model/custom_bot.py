from telebot import TeleBot, apihelper
from telebot.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from telebot.formatting import hbold, hcite, escape_html
from model.user import User
from model.sql_handler import SqlHandler

class CustomBot:
    """Бот для поиска собеседника с учетом интересов и пола"""

    __bot: TeleBot = None
    __users = {}          # {chat_id: User}
    __waiting_users = []  # список chat_id пользователей, которые ищут собеседника
    __active_chats = {}   # {chat_id: partner_chat_id}
    __db_handler: SqlHandler = None

    def __init__(self, token: str):
        """Конструктор класса"""
        # Инициализация БД
        self.__db_handler = SqlHandler("my_database.db")
        self.__db_handler.connect()
        self.__db_handler.create_user_table()
        self.__db_handler.close()

        # Инициализация бота
        self.__bot = TeleBot(token)
        self.register_handlers()
        print("✅ Бот инициализирован и готов к работе!")

    # -------------------------------------------------------------
    #                     Превью и запуск
    # -------------------------------------------------------------

    def preview_message(self, message: Message) -> None:
        """Превью для пользователя"""
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🚀 Начать", callback_data="start"))

        caption = (
            "👋 Хеллоу!\n\n"
            "Я бот Кости!\n"
            "В этом тестовом боте можно анонимно общаться с челиками и чувылдами 🤙😎🤙\n\n"
            "Выбери действие ниже 👇"
        )

        try:
            with open("src/preview.jpeg", "rb") as photo:
                self.__bot.send_photo(message.chat.id, photo, caption=caption, reply_markup=markup)
        except FileNotFoundError:
            # если картинка не найдена, просто отправляем текст
            self.__bot.send_message(message.chat.id, caption, reply_markup=markup)

    def handle_start_button(self, call):
        """Обработка нажатия кнопки '🚀 Начать'"""
        chat_id = call.message.chat.id
        self.__bot.answer_callback_query(call.id)
        self.start(call.message)

    # -------------------------------------------------------------
    #                      Регистрация
    # -------------------------------------------------------------

    def start(self, message: Message):
        """Начало регистрации"""
        user = self.__users.get(message.chat.id)
        if not user:
            user = User(self.__db_handler, message.chat.id)
            self.__users[message.chat.id] = user

        self.__bot.send_message(message.chat.id, "Как тебя зовут?")
        self.__bot.register_next_step_handler(message, self.user_registration, step="name")

    # -------------------------------------------------------------
    #                   Регистрация обработчиков
    # -------------------------------------------------------------

    def register_handlers(self):
        """Регистрация всех обработчиков"""
        # Команды
        self.__bot.message_handler(commands=["start"])(self.preview_message)
        self.__bot.message_handler(commands=["help"])(self.help)
        self.__bot.message_handler(commands=["filters"])(self.filter)

        # Callback при нажатии "🚀 Начать"
        self.__bot.callback_query_handler(func=lambda c: c.data == "start")(self.handle_start_button)

        # Остальные типы сообщений
        self.__bot.message_handler(content_types=["sticker"])(self.sticker_handler)
        self.__bot.message_handler(content_types=["voice"])(self.voice_message_handler)
        self.__bot.message_handler(content_types=["audio"])(self.audio_message_handler)
        self.__bot.message_handler(content_types=["video"])(self.video_message_handler)
        self.__bot.message_handler(content_types=["video_note"])(self.video_note_message_handler)
        self.__bot.message_handler(content_types=["document"])(self.document_message_handler)
        self.__bot.message_handler(content_types=["photo"])(self.photo_message_handler)

        # Inline кнопки
        self.__bot.message_handler(func=self.is_reply_button)(self.handle_reply_buttons)
        self.__bot.callback_query_handler(
            func=lambda c: c.data.startswith("interest_") or c.data == "interest_done"
        )(self.handle_interest_inline_callback)
        self.__bot.callback_query_handler(
            func=lambda c: c.data in ["user_m_sex", "user_f_sex", "user_sex_done"]
        )(self.handle_user_sex_inline_callback)
        self.__bot.callback_query_handler(
            func=lambda c: c.data in ["partner_m_sex", "partner_f_sex", "partner_sex_done"]
        )(self.handle_partner_sex_inline_callback)
        self.__bot.message_handler(content_types=["text"])(self.handle_other_text)
        self.__bot.callback_query_handler(
            func=lambda c: c.data in ["confirm_user_data", "edit_user_data"]
        )(self.handle_confirm_user_data_for_db)

    # -------------------------------------------------------------
    #                       Вспомогательные
    # -------------------------------------------------------------

    @property
    def bot(self) -> TeleBot:
        """Геттер бота"""
        return self.__bot

    def user_registration(self, message: Message, step="name"):
        """Регистрация пользователя"""
        user = self.__users.get(message.chat.id)
        
        if step == "name":
            user.name = message.text.strip()
            self.__bot.send_message(
                message.chat.id, f"Приятно познакомиться, {user.name}!"
            )
            self.__bot.send_message(message.chat.id, "Введите свой возраст:")
            self.__bot.register_next_step_handler(
                message, self.user_registration, step="age"
            )
        elif step == "age":
            try:
                user.age = int(message.text.strip())
            except ValueError:
                self.__bot.send_message(
                    message.chat.id, "Возраст должен быть целым числом. Попробуйте ещё раз."
                )
                self.__bot.register_next_step_handler(
                    message, self.user_registration, step="age"
                )
                return
            self.choice_user_sex(message)

        elif step == "interest":
            self.get_user_interest(message)

    def help(self, message: Message):
        """Обработчик помощи пользователю"""
        self.__bot.send_message(message.chat.id, "Тут будет текст помощи пользователю")

    def filter(self, message: Message):
        """Фильтрация по интересам"""
        self.__bot.send_message(message.chat.id, "Фильтры поиска собеседника:")
        self.get_user_interest(message)

    # ------------------ Пол ------------------
    def choice_user_sex(self, message: Message):
        """Выбор пола пользователя"""
        user = self.__users.get(message.chat.id)
        menu = self.create_user_sex_menu(user.sex if user else None)
        self.__bot.send_message(
            message.chat.id, "Выберите свой пол:", reply_markup=menu
        )
    def create_user_sex_menu(self, selected_sex: str = None):
        """Создание кнопок выбора пола пользователя"""
        markup = InlineKeyboardMarkup()
        text_m = "М ✅" if selected_sex == "М" else "М"
        text_f = "Ж ✅" if selected_sex == "Ж" else "Ж"
        markup.add(
            InlineKeyboardButton(text_m, callback_data="user_m_sex"),
            InlineKeyboardButton(text_f, callback_data="user_f_sex"),
        )
        markup.add(InlineKeyboardButton("Готово", callback_data="user_sex_done"))
        return markup

    def handle_user_sex_inline_callback(self, call):
        """Оброботчик выбора пола пользователя кнопкаами"""
        user_id = call.message.chat.id
        user = self.__users.get(user_id)
        if not user:
            return

        updated = False
        if call.data == "user_m_sex":
            if user.sex != "М":
                user.sex = "М"
                updated = True
            self.__bot.answer_callback_query(call.id, "Вы выбрали: Мужской")

        elif call.data == "user_f_sex":
            if user.sex != "Ж":
                user.sex = "Ж"
                updated = True
            self.__bot.answer_callback_query(call.id, "Вы выбрали: Женский")

        elif call.data == "user_sex_done":
            if not user.sex:
                self.__bot.answer_callback_query(
                    call.id, "Выберите пол перед подтверждением!"
                )
                return
            self.__bot.send_message(
                user_id, f"Ваш пол: {user.sex}"
            )
            self.choice_partner_sex(call.message)
            
        if updated:
            try:
                self.__bot.edit_message_reply_markup(
                    chat_id=user_id,
                    message_id=call.message.message_id,
                    reply_markup=self.create_user_sex_menu(user.sex),
                )
                
            except apihelper.ApiTelegramException as e:
                if "message is not modified" not in str(e):
                    raise
        # ------------------ Фильтрация по полу собеседника ------------------

    def choice_partner_sex(self, message: Message):
        """Выбор пола собеседника"""
        user = self.__users.get(message.chat.id)
        menu = self.create_partner_sex_menu(user.get_sex_filters() if user else None)
        self.__bot.send_message(
            message.chat.id, "Выберите пол собеседника:", reply_markup=menu
        )

    def create_partner_sex_menu(self, sex_filters: dict = None):
        """Создание меню выбора пола собеседника"""
        markup = InlineKeyboardMarkup()
        if not sex_filters:
            sex_filters = {"М": False, "Ж": False}

        text_m = "М ✅" if sex_filters.get("М") else "М"
        text_f = "Ж ✅" if sex_filters.get("Ж") else "Ж"

        markup.add(
            InlineKeyboardButton(text_m, callback_data="partner_m_sex"),
            InlineKeyboardButton(text_f, callback_data="partner_f_sex"),
        )
        markup.add(InlineKeyboardButton("Готово", callback_data="partner_sex_done"))
        return markup

    def handle_partner_sex_inline_callback(self, call):
        """Обработчик выбора пола собеседника кнопками"""
        user_id = call.message.chat.id
        user = self.__users.get(user_id)
        if not user:
            return

        updated = False
        if call.data == "partner_m_sex":
            current = user.get_sex_filters().get("М", False)
            user.set_sex_filter("М", not current)
            updated = True
            self.__bot.answer_callback_query(
                call.id, f"Фильтр по мужчинам: {'вкл' if not current else 'выкл'}"
            )
        elif call.data == "partner_f_sex":
            current = user.get_sex_filters().get("Ж", False)
            user.set_sex_filter("Ж", not current)
            updated = True
            self.__bot.answer_callback_query(
                call.id, f"Фильтр по женщинам: {'вкл' if not current else 'выкл'}"
            )
        elif call.data == "partner_sex_done":
            filters = user.get_sex_filters()
            selected = [sex for sex, v in filters.items() if v]
            if not selected:
                text = "Фильтр не выбран — будут все."
            else:
                text = f"Вы выбрали поиск только по: {', '.join(selected)}. Продолжаем регистрацию..."
                self.__bot.send_message(user_id, text)
                self.user_registration(call.message, step="interest")
            return
        if updated:
            try:
                self.__bot.edit_message_reply_markup(
                    chat_id=user_id,
                    message_id=call.message.message_id,
                    reply_markup=self.create_partner_sex_menu(user.get_sex_filters()),
                )
                #self.choice_user_sex(call.message)
            except apihelper.ApiTelegramException as e:
                if "message is not modified" not in str(e):
                    raise

    # ------------------ Интересы ------------------
    def get_user_interest(self, message: Message):
        """Получение интересов пользователя выбором кнопок"""
        menu = self.create_interest_menu(message.chat.id)
        self.__bot.send_message(
            message.chat.id, "Выберите свои интересы:", reply_markup=menu
        )

    def create_interest_menu(self, chat_id: int):
        """Создание кнопок интересов"""
        user = self.__users.get(chat_id)
        markup = InlineKeyboardMarkup()
        if user:
            interests = user.get_interests().__dict__
            for key, val in interests.items():
                if key != "just_talking":
                    text = f"✅ {key}" if val else key
                    markup.add(
                        InlineKeyboardButton(text, callback_data=f"interest_{key}")
                    )
            markup.add(InlineKeyboardButton("Готово", callback_data="interest_done"))
        return markup

    def handle_interest_inline_callback(self, call):
        """Обработчик кнопок интересов"""
        user_id = call.message.chat.id
        user = self.__users.get(user_id)
        if not user:
            return

        if call.data == "interest_done":
            selected = [
                k
                for k, v in user.get_interests().__dict__.items()
                if v and k != "just_talking"
            ]
            try:
                self.__bot.edit_message_text(
                    chat_id=user_id,
                    message_id=call.message.message_id,
                    text=f"Вы выбрали: {', '.join(selected) if selected else 'ничего'}",
                )
                self.confirm_user_data_for_db_menu(call.message)
               
            except apihelper.ApiTelegramException as e:
                if "message is not modified" not in str(e):
                    raise

        elif call.data.startswith("interest_"):
            key = call.data.replace("interest_", "")
            user.toggle_interest(key)
            try:
                self.__bot.edit_message_reply_markup(
                    chat_id=user_id,
                    message_id=call.message.message_id,
                    reply_markup=self.create_interest_menu(user_id),
                )
            except apihelper.ApiTelegramException as e:
                if "message is not modified" not in str(e):
                    raise
            
    # ------------------ Подтверждение данных пользователя для бд ------------------        
    def confirm_user_data_for_db_menu(self, message: Message):
        """Подтверждение данных пользователя для отправки в бд"""
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("Да", callback_data="confirm_user_data"),
            InlineKeyboardButton("Нет. Заполнить профиль заново", callback_data="edit_user_data"),
        )
        self.__bot.send_message(
            message.chat.id, "Данные для профиля введены корректно?", reply_markup=markup)
        
    def handle_confirm_user_data_for_db(self, call):
        """Обработчик выбора пола пользователя кнопкаами"""
        user_id = call.message.chat.id
        user = self.__users.get(user_id)
        if not user:
            return
        
        if call.data == "edit_user_data":
            self.__bot.answer_callback_query(call.id, "Вы выбрали: Заполнить профиль заново")

        elif call.data == "confirm_user_data":
            if not user.sex:
                self.__bot.answer_callback_query(
                    call.id, "Подтвердите данные!"
                )
                return
            self.__bot.send_message(
                user_id, "Данные отправлены в бд")
            self.save_user_data(call.message)
            self.show_main_menu(call.message.chat.id)
                
    #методы обработки бд
    def save_user_data(self, message: Message):
        """Сохранение данных пользователя в бд"""
        user_id = message.chat.id
        user = self.__users.get(user_id)
        if not user:
            return
        
        #db_handler = SqlHandler("my_database.db")
        #db_handler.connect()
        #сейчас тут
        #сохранение данных пользовател    
        user.save()
        #user.insert_user_in_database(db_handler)  # сохраняем пользователя
        self.__bot.send_message(user_id, "Тестовое сохранение пользователя в бд")
        #db_handler.close()
            
    # ------------------ Главное меню ------------------
    def show_main_menu(self, chat_id: int):
        """Отображение меню"""
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("Начать диалог"), KeyboardButton("Выход"))
        self.__bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

    def is_reply_button(self, msg: Message) -> bool:
        """Проверка на reply кнопку"""
        return msg.text in ["Начать диалог", "Выход"]

    def handle_reply_buttons(self, message: Message):
        """обработка reply кнопок"""
        user_id = message.chat.id
        if message.text == "Начать диалог":
            self.__bot.send_message(user_id, "Поиск пользователя...")
            self.search_user(user_id)
        elif message.text == "Выход":
            self.end_chat(user_id)

    def handle_other_text(self, message: Message):
        """Обработка текста с цитатой ответа и названием (бот или партнёр)."""
        chat_id = message.chat.id

        if chat_id not in self.__active_chats:
            self.__bot.send_message(chat_id, "Для продолжения выберите /start или кнопки")
            return

        partner_id = self.__active_chats[chat_id]

        if message.reply_to_message:
            original = message.reply_to_message
            quote_text = original.text or "<медиа>"
            formatted_quote = hcite(quote_text, escape=True)

            # Определяем, кто пишет сообщение (текущий пользователь)
            sender = self.__users.get(chat_id)
            sender_name = sender.name if sender is not None else "Собеседник"
            title = hbold(escape_html(sender_name), escape=True)

            user_text = escape_html(message.text)
            response = "\n".join([title, formatted_quote, user_text])
            self.__bot.send_message(partner_id, response, parse_mode='HTML')

        else:
            self.__bot.send_message(partner_id, escape_html(message.text), parse_mode='HTML')

    def sticker_handler(self, message: Message):
        """Обработчик стикеров"""
        partner_id = self.__active_chats.get(message.chat.id)
        if partner_id:
            sticker_id = message.sticker.file_id
            self.__bot.send_sticker(partner_id, sticker_id)
        else:
            self.__bot.send_message(message.chat.id, "Стикеры обрабатываются только в переписке")
            
    def voice_message_handler(self, message: Message):
        """Обработчик голосовых сообщений"""
        partner_id = self.__active_chats.get(message.chat.id)
        if partner_id:
            voice_message_id = message.voice.file_id
            self.__bot.send_voice(partner_id, voice_message_id)
        else:
            self.__bot.send_message(message.chat.id, "Голосовые сообщения обрабатываются только в переписке")
    
    def audio_message_handler(self, message: Message):
        """Обработчик аудиофайлов"""
        partner_id = self.__active_chats.get(message.chat.id)
        if partner_id:
            audio_message_id = message.audio.file_id
            self.__bot.send_audio(partner_id, audio_message_id)
        else:
            self.__bot.send_message(message.chat.id, "Аудиофайлы сообщения обрабатываются только в переписке")
    
    def video_message_handler(self, message: Message):
        """Обработчик видео"""
        partner_id = self.__active_chats.get(message.chat.id)
        if partner_id:
            video_message_id = message.video.file_id
            self.__bot.send_video(partner_id, video_message_id)
        else:
            self.__bot.send_message(message.chat.id, "Видео обрабатываются только в переписке")        

    def video_note_message_handler(self, message: Message):
        """Обработчик видео сообщений"""
        partner_id = self.__active_chats.get(message.chat.id)
        if partner_id:
            video_note_message_id = message.video_note.file_id
            self.__bot.send_video_note(partner_id, video_note_message_id)
        else:
            self.__bot.send_message(message.chat.id, "Видеосообщения обрабатываются только в переписке")
    
    def document_message_handler(self, message: Message):
        """Обработчик документов в сообщениях"""
        partner_id = self.__active_chats.get(message.chat.id)
        if partner_id:
            document_message_id = message.document.file_id
            self.__bot.send_document(partner_id, document_message_id)
        else:
            self.__bot.send_message(message.chat.id, "Документы обрабатываются только в переписке")
    
    def photo_message_handler(self, message: Message):
        """Обработчик фото в сообщениях"""
        partner_id = self.__active_chats.get(message.chat.id)
        if partner_id:
            # Получаем ID самой качественной фотографии
            photo_message_id = message.photo[-1].file_id
            # Получаем текст, прикреплённый к фотографии
            caption = message.caption
            # Отправляем фотографию с текстом собеседнику
            self.__bot.send_photo(partner_id, photo_message_id, caption=caption)
        else:
            self.__bot.send_message(message.chat.id, "Фотографии обрабатываются только в переписке")

    def get_sex_emoji(self, user: User) -> str:
        """Получение эмодзи пола"""
        if user.sex:
            return "👨" if user.sex.lower() == "м" else "👩"
        return ""

    
    def search_user(self, user_id: int):
        """поиск собеседника"""
        user = self.__users.get(user_id)
        if not user:
            return

        partner_id = None
        for uid in self.__waiting_users:
            candidate = self.__users.get(uid)
            if not candidate:
                continue

            # 🔹 проверка фильтрации по полу
            if not user.matches_sex(candidate):
                continue
            if not candidate.matches_sex(user):
                continue

            # 🔹 проверка интересов
            if not user.compare_interests(candidate):
                continue

            partner_id = uid
            break

        if partner_id:
            self.__waiting_users.remove(partner_id)
            self.__active_chats[user_id] = partner_id
            self.__active_chats[partner_id] = user_id

            user2 = self.__users.get(partner_id)
            emoji1, emoji2 = self.get_sex_emoji(user), self.get_sex_emoji(user2)
            mutual_interests = user.get_mutual_interests(user2)

             # Пол, который ищет каждый
            user_filters = [sex for sex, v in user.get_sex_filters().items() if v]
            user2_filters = [sex for sex, v in user2.get_sex_filters().items() if v]

            self.__bot.send_message(
                user_id,
                f"✅ Собеседник найден!\nИмя: {user2.name}\n{emoji2}, Возраст: {user2.age}\n"
                f"Взаимные интересы: {', '.join(mutual_interests) if mutual_interests else 'нет'}\n"
                f"Ищет: {', '.join(user2_filters) if user2_filters else 'все'}\nМожете начать чат.",
            )
            self.__bot.send_message(
                partner_id,
                f"✅ Собеседник найден!\nИмя: {user.name}\n{emoji1}, Возраст: {user.age}\n"
                f"Взаимные интересы: {', '.join(mutual_interests) if mutual_interests else 'нет'}\n"
                f"Ищет: {', '.join(user_filters) if user_filters else 'все'}\nМожете начать чат.",
            )
        else:
            if user_id not in self.__waiting_users:
                self.__waiting_users.append(user_id)
            self.__bot.send_message(user_id, "🔎 Ждём подключения собеседника...")


    def end_chat(self, user_id: int):
        """Обработчик завершения чата"""
        if user_id in self.__active_chats:
            partner_id = self.__active_chats.pop(user_id)
            if partner_id in self.__active_chats:
                self.__active_chats.pop(partner_id)

            user = self.__users.get(user_id)
            partner = self.__users.get(partner_id)
            if partner:
                self.__bot.send_message(
                    partner_id,
                    f"❌ Собеседник {user.name if user else 'Неизвестный'} завершил диалог.",
                )
            self.__bot.send_message(
                user_id, f"Диалог с {partner.name if partner else 'Неизвестный'} завершён!"
            )
        else:
            self.__bot.send_message(user_id, "❌ Вы не находитесь в диалоге.")
