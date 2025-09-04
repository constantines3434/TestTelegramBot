from telebot import TeleBot, apihelper
from telebot.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from model.user import User


class CustomBot:
    """Бот для поиска собеседника с учетом интересов и пола"""

    __bot: TeleBot
    __users = {}  # {chat_id: User}
    __waiting_users = []  # список chat_id пользователей, которые ищут собеседника
    __active_chats = {}  # {chat_id: partner_chat_id}

    def __init__(self, token: str):
        self.__bot = TeleBot(token)
        self.register_handlers()

    def register_handlers(self):
        self.__bot.message_handler(commands=["start"])(self.start)
        self.__bot.message_handler(commands=["help"])(self.help)
        self.__bot.message_handler(commands=["filters"])(self.filter)
        self.__bot.message_handler(func=self.is_reply_button)(self.handle_reply_buttons)
        self.__bot.callback_query_handler(
            func=lambda c: c.data.startswith("interest_") or c.data == "interest_done"
        )(self.handle_interest_inline_callback)
        self.__bot.callback_query_handler(
            func=lambda c: c.data in ["user_m_sex", "user_f_sex", "user_sex_done"]
        )(self.handle_user_sex_inline_callback)
        self.__bot.callback_query_handler(
            func=lambda c: c.data
            in ["partner_m_sex", "partner_f_sex", "partner_sex_done"]
        )(self.handle_partner_sex_inline_callback)
        self.__bot.message_handler(content_types=["text"])(self.handle_other_text)

    @property
    def bot(self) -> TeleBot:
        return self.__bot

    # ------------------ Регистрация ------------------
    def start(self, message: Message):
        user = self.__users.get(message.chat.id)
        if not user:
            user = User()
            self.__users[message.chat.id] = user
        self.__bot.send_message(message.chat.id, "Как тебя зовут?")
        self.__bot.register_next_step_handler(
            message, self.user_registration, step="name"
        )

    def user_registration(self, message: Message, step="name"):
        user = self.__users.get(message.chat.id)
        if not user:
            user = User()
            self.__users[message.chat.id] = user

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
        self.__bot.send_message(message.chat.id, "Тут будет текст помощи пользователю")

    def filter(self, message: Message):
        self.__bot.send_message(message.chat.id, "Фильтры поиска собеседника:")
        self.get_user_interest(message)

    # ------------------ Пол ------------------
    def choice_user_sex(self, message: Message):
        user = self.__users.get(message.chat.id)
        menu = self.create_user_sex_menu(user.sex if user else None)
        self.__bot.send_message(
            message.chat.id, "Выберите свой пол:", reply_markup=menu
        )

    def create_user_sex_menu(self, selected_sex: str = None):
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
        user = self.__users.get(message.chat.id)
        menu = self.create_partner_sex_menu(user.get_sex_filters() if user else None)
        self.__bot.send_message(
            message.chat.id, "Выберите пол собеседника:", reply_markup=menu
        )

    def create_partner_sex_menu(self, sex_filters: dict = None):
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
        menu = self.create_interest_menu(message.chat.id)
        self.__bot.send_message(
            message.chat.id, "Выберите свои интересы:", reply_markup=menu
        )

    def create_interest_menu(self, chat_id: int):
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

    # ------------------ Главное меню ------------------
    def show_main_menu(self, chat_id: int):
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("Начать диалог"), KeyboardButton("Выход"))
        self.__bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

    def is_reply_button(self, msg: Message) -> bool:
        return msg.text in ["Начать диалог", "Выход"]

    def handle_reply_buttons(self, message: Message):
        user_id = message.chat.id
        if message.text == "Начать диалог":
            self.__bot.send_message(user_id, "Поиск пользователя...")
            self.search_user(user_id)
        elif message.text == "Выход":
            self.end_chat(user_id)

    def handle_other_text(self, message: Message):
        chat_id = message.chat.id
        if chat_id in self.__active_chats:
            partner_id = self.__active_chats[chat_id]
            self.__bot.send_message(
                partner_id, f"Сообщение от собеседника: {message.text}"
            )
        else:
            self.__bot.send_message(
                chat_id, "Для продолжения выберите /start или кнопки"
            )

    # ------------------ Поиск собеседника ------------------
    def get_sex_emoji(self, user: User) -> str:
        if user.sex:
            return "👨" if user.sex.lower() == "м" else "👩"
        return ""

    def search_user(self, user_id: int):
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
