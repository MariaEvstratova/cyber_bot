from datetime import datetime, timedelta, time
from typing import Optional

import pytz
import telegram
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler, \
    CallbackQueryHandler, ContextTypes
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, Update

from model.status_recommendation import RecommendationStatusModel
from model.user import UserModel
from service.cyber_advent_service import CyberAdventService, REC_STATUS_INIT, REC_STATUS_DONE, REC_STATUS_SKIP
from service.user_service import UserService
from service.utils import get_timezone_by_utc_offset

(GREETING_STATE, REGISTRATION_STATE, NAME_STATE, SCHEDULE_STATE, SEX_STATE,
 AGE_STATE, TIME_STATE, TIMEZONE_STATE, PERIOD_STATE) = range(9)

PROFILE_SHOW_STATE, PROFILE_EDIT_STATE, PROFILE_EDIT_FIELD_STATE, PROFILE_EDIT_APPLY_STATE = range(4)
ADVENT_TIMER_STATE, ADVENT_WORK_STATE = range(2)
RESULTS_SHOW, RESULTS_REC_NUM, RESULTS_CHANGE = range(3)

BUTTON_REC_DONE, BUTTON_REC_SKIP, BUTTON_REC_REPORT, BUTTON_REC_SHARE, BUTTON_RUN_TEST = ("button_rec_done",
                                                                                          "button_rec_skip",
                                                                                          "button_rec_report",
                                                                                          "button_rec_share",
                                                                                          "button_run_test")

class TelegramBot:

    def __init__(self, bot_token: str, bot_name: str, user_service: UserService, advent_service: CyberAdventService):
        self.bot_token = bot_token
        self.bot_name = bot_name
        self.bot = telegram.Bot(token=self.bot_token)
        self.bot_url = f'https://t.me/{self.bot_name}'
        self.user_service = user_service
        self.advent_service = advent_service

    async def help_message(self, update, context):
        user = await self.user_service.find_user_by_telegram_id(update.message.chat.id)
        if user is None:
            advent_start = None
        else:
            advent_start = user.advent_start

        """Отправляет сообщение когда получена команда /help"""
        await update.message.reply_text("Этот чат-бот предназначен для повышения уровня знаний цифровой гигиены и помощи "
                                        "в усилении безопасности существующих аккаунтов и чувствительных данных.\n\n"
                                        "Доступные команды:\n\n"
                                        "/start - регистрация;\n"
                                        "/stop - остановка бота;\n"
                                        "/menu - основное меню;\n"
                                        "/help - показать справку.\n\n"
                                        "После регистрации вам будет доступно меню, благодаря которому вы можете общаться "
                                        "с ботом. Чтобы изменить данные, заданные по регистрации, можно перейти по кнопке "
                                        "Мой профиль и далее в *Редактировать данные* и поменять нужный параметр.\n\n"
                                        "Чтобы запустить рассылку рекомендаций, нужно нажать на кнопку *Запустить новогодний"
                                        " адвент* по цифровой гигиене. После нажатия вам будут подаваться рекомендации в "
                                        "зависимости от выбранного графика(ежедневно, рабочие, выходные дни).\n\n"
                                        "Вам следует выполнять наши рекомендации и отмечать это в боте (по кнопке *выполнить* "
                                        "или *отложить*). Также вы можете посмотреть выданные рекомендации по кнопке "
                                        "Рекомендации и изменить статус их выполнения в *Результаты выполнения*.\n\n"
                                        "Кнопка *Пригласить друзей* поможет вам сделать ваших друзей более грамотными в "
                                        "цифровой среде и поделиться с ними ссылкой на нашего бота. Чтобы проверить свои "
                                        "знания, можно пройти тест по кнопке *Пройти тест по цифровой гигиене*.",
                                        reply_markup=self.build_main_menu(advent_start), parse_mode='markdown')


    async def stop(self, update, context):
        await update.message.reply_text("Всего доброго!", reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END


    def build_job_rec_name(self, user_id: str) -> str:
        return f"rec_{user_id}"


    def build_job_not_name(self, user_id: str) -> str:
        return f"not_{user_id}"


    async def skip_rec(self, context, user_id, rec_id):
        user = await self.user_service.find_user_by_id(user_id)
        if user is None:
            return

        rec = await self.advent_service.find_status_rec_by_id(user.user_id, rec_id)
        if rec is None:
            return
        elif rec.rec_status != REC_STATUS_INIT:
            return

        # Удаляем сообщение с рекомендацией из чата
        if rec.telegram_message_id != "":
            await context.bot.delete_message(chat_id=user.telegram_id, message_id=rec.telegram_message_id)

        # Откладываем рекомендацию
        await self.advent_service.skip_rec(user.user_id, rec.rec_id)


    async def start(self, update, context):
        chat_id = str(update.message.chat.id)
        user = await self.user_service.find_user_by_telegram_id(chat_id)
        if user is None:
            reply_keyboard = [['Запустить']]
            markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
            await self.bot.send_photo(chat_id=chat_id,
                                 photo='https://img.freepik.com/free-vector/flat-background-for-safer-internet-day_23-2151127509.jpg?w=2000&t=st=1717694697~exp=1717695297~hmac=edd5b2ffe89d8b2901334e3df3190bffc0ed426ca69706be691a573487acdd33',
                                 caption="Добрый день. Данный бот поможет вам за N дней усилить защиту ваших аккаунтов, данных,"
                                         " а также обучит основам обеспечения цифровой гигиены. 🤖 Вам достаточно ежедневно"
                                         " выполнять по одной рекомендации.",
                                 reply_markup=markup)
            return GREETING_STATE
        else:
            await self.bot.send_photo(chat_id=chat_id,
                                 photo='https://img.freepik.com/free-vector/technical-support-service-site_80328-68.jpg?t=st=1717695596~exp=1717699196~hmac=419f0dc67a3bb3e7fecfe47e9e64615daaee5692bdb3c828e3c2dae5265d1376&w=2000',
                                 caption=f"Добрый день, {user.name}, давно не виделись! Воспользуйтесь меню.",
                                 reply_markup=self.build_main_menu(user.advent_start))
            return ConversationHandler.END


    async def greeting(self, update, context):
        message_text = update.message.text
        if message_text == 'Запустить':
            reply_keyboard = [['Давайте поскорее начнём!']]
            markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text("Вы сделали уверенный шаг на пути обеспечения безопасности ваших данных. "
                                            "Пожалуйста, ответьте на несколько вопросов, и мы начнем.", reply_markup=markup)
            return REGISTRATION_STATE
        else:
            reply_keyboard = [['Запустить']]
            markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text(f"Неизвестная команда [{message_text}], попробуйте еще раз",
                                            reply_markup=markup)
            return GREETING_STATE


    async def registration(self, update, context):
        message_text = update.message.text
        if message_text == 'Давайте поскорее начнём!' or message_text == 'Редактировать данные':
            await update.message.reply_text("Как к вам обращаться?")
            return NAME_STATE
        else:
            reply_keyboard = [['Давайте поскорее начнём!']]
            markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text(f"Неизвестная команда [{message_text}], попробуйте еще раз",
                                            reply_markup=markup)
            return REGISTRATION_STATE


    async def name(self, update, context):
        name_value = update.message.text
        if any(ch.isdigit() for ch in name_value):
            await update.message.reply_text("🫣 Не похоже на [имя/фамилию]. Попробуйте еще раз")
            return NAME_STATE
        else:
            context.user_data['name'] = name_value
            reply_keyboard = [['Ежедневно'], ['Рабочие дни', 'Выходные дни']]
            markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text("Сформируйте удобный для вас график получения"
                                            " рекомендаций и уведомлений. Какой график для вас удобен?",
                                            reply_markup=markup)
            return SCHEDULE_STATE


    async def schedule(self, update, context):
        days_value = update.message.text
        if days_value == "Ежедневно" or days_value == "Рабочие дни" or days_value == "Выходные дни":
            context.user_data['days'] = days_value
            await update.message.reply_text(
                "⌚ Укажите время в формате ЧЧ:ММ, в которое вы хотите получать рекомендации, например, 16:30")
            return TIME_STATE
        else:
            await update.message.reply_text("Неизвестное значение, выберите график из предложенных вариантов")
            return SCHEDULE_STATE


    async def time_schedule(self, update, context):
        time_value = update.message.text
        try:
            # Проверка на валидность введенного времени
            _ = datetime.strptime(time_value, "%H:%M")
            context.user_data['time'] = time_value
            await update.message.reply_text("Укажите интервал, в который вам будут присылаться напоминания "
                                            "о прохождении рекомендаций в днях. Например: каждые 2 дня.")
            return PERIOD_STATE
        except ValueError:
            await update.message.reply_text("Неверный формат 😝, попробуйте ещё раз указать время в формате HH:MM, например, 17:35")
            return TIME_STATE


    async def period(self, update, context):
        period_value = update.message.text
        if period_value.isdigit():
            if 1 <= int(period_value) <= 30:
                context.user_data['period'] = str(period_value)
                await update.message.reply_text("Укажите разницу по времени вашего региона относительно UTC "
                                                "(в часах, начиная с + или -). "
                                                "Например, для Новосибирска: +7, для Москвы: +3")
                return TIMEZONE_STATE
            else:
                await update.message.reply_text("😝 Число должно быть в диапазоне от 0 до 30, попробуйте ещё раз")
                return PERIOD_STATE
        else:
            await update.message.reply_text("Значение, которое вы ввели не является числом 😜, попробуйте ещё раз")
            return PERIOD_STATE


    async def timezone_schedule(self, update, context):
        if update.message.text[0] != "+" and update.message.text[0] != "-":
            await update.message.reply_text("Разница во времени с UTC должна начинаться либо с +, либо с -. Попробуйте еще раз.")
            return TIMEZONE_STATE

        if update.message.text[1:].isdigit():
            utc_offset_value = update.message.text.replace("+", "")
            utc_offset_hours = timedelta(hours=int(utc_offset_value))
            user_timezone = await get_timezone_by_utc_offset(utc_offset_hours)
            if user_timezone == "":
                await update.message.reply_text(f"Не удалось определить часовой пояс по UTC{update.message.text}, "
                                                f"попробуйте еще раз ввести разницу по часам с UTC.")
                return TIMEZONE_STATE
            else:
                context.user_data['timezone'] = user_timezone

                reply_keyboard = [['Мужской', 'Женский'], ['Пропустить']]
                markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
                await update.message.reply_text("Укажите пол", reply_markup=markup)
                return SEX_STATE
        else:
            await update.message.reply_text("Значение, которое вы ввели не является числом 😜, попробуйте ещё раз")
            return TIMEZONE_STATE


    async def sex(self, update, context):
        sex_value = update.message.text
        if sex_value == "Мужской" or sex_value == "Женский" or sex_value == "Пропустить":
            context.user_data['sex'] = sex_value
            reply_keyboard = [['до 18'], ['от 18 до 25'], ['от 26 до 30', 'от 31 до 35'],
                              ['от 36 до 40', 'от 41 до 45'], ['от 46 до 55', 'старше 55']]
            markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text("Укажите возраст.", reply_markup=markup)
            return AGE_STATE
        else:
            await update.message.reply_text("Неизвестное значение, выберите пол из предложенных вариантов")
            return SEX_STATE


    async def age(self, update, context):
        age_value = update.message.text
        if len(age_value.split()) != 2:
            age = age_value.split()
            context.user_data['age'] = f"{age[1]}-{age[3]}"
        else:
            age = age_value.split()
            if age[1] == '18':
                context.user_data['age'] = "0-18"
            else:
                context.user_data['age'] = "55-100"

        self.create_profile(update, context)

        await update.message.reply_text("Меню", reply_markup=self.build_main_menu())
        return ConversationHandler.END


    def create_profile(self, update, context):
        user = UserModel()
        user.name = context.user_data['name']
        user.age_group = context.user_data['age']
        user.schedule = context.user_data['days']
        user.sex = context.user_data['sex']
        user.telegram_username = str(update.message.from_user.username)
        user.telegram_id = str(update.message.chat.id)
        user.time = context.user_data['time']
        user.timezone = context.user_data['timezone']
        user.period = str(context.user_data['period'])
        self.user_service.create_user(user)


    def build_main_menu(self, advent_start: Optional[datetime] = None) -> ReplyKeyboardMarkup:
        reply_keyboard = [['Мой профиль', 'Рекомендации']]
        if advent_start is None:
            # Кнопку запуска адвента показываем только, если пользователь не запустил ранее адвент
            reply_keyboard.append(['Запустить новогодний адвент по цифровой гигиене'])

        reply_keyboard.extend([
            ['Результаты выполнения'],
            ['Пройти тест по цифровой гигиене'],
            ['Пригласить друзей', 'Помощь']])

        return ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)


    async def show_main_menu(self, update, context):
        user = await self.user_service.find_user_by_telegram_id(update.message.chat.id)
        if user is None:
            await update.message.reply_text("Для отображения основного меню необходимо предварительно "
                                            "зарегистрироваться, воспользуйтесь командой /start",
                                            reply_markup=ReplyKeyboardRemove())
            return

        await update.message.reply_text("Меню", reply_markup=self.build_main_menu(user.advent_start))
        return ConversationHandler.END


    async def show_profile(self, update, context):
        reply_keyboard = [['Редактировать данные'], ['Меню']]
        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)

        user = await self.user_service.find_user_by_telegram_id(update.message.chat.id)
        reply_text = ("Профиль 🔽 \n"
                      f"💠 Имя - {user.name} \n"
                      f"💠 График - {user.schedule} \n"
                      f"💠 Возраст - {user.age_group} лет \n"
                      f"💠 Время выдачи рекомендаций - {user.time} \n")
        if user.sex != 'Пропустить':
            reply_text = reply_text + f"💠 Пол - {user.sex}"

        await update.message.reply_text(reply_text, reply_markup=markup)
        return PROFILE_EDIT_STATE


    async def edit_profile(self, update, context):
        user = await self.user_service.find_user_by_telegram_id(update.message.chat.id)
        if user is None:
            return PROFILE_EDIT_STATE

        sent_recs = await self.advent_service.sent_recommendation_count(user.user_id)
        if sent_recs == 0:
            reply_keyboard = [['Имя', 'Возраст', 'Пол', 'График', 'Время'], ["Период напоминаний", 'Назад']]
        else:
            reply_keyboard = [['Имя', 'Возраст', 'Пол', "Период напоминаний"], ['Назад']]
        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)

        await update.message.reply_text("Что отредактировать?", reply_markup=markup)
        return PROFILE_EDIT_FIELD_STATE


    async def edit_profile_request(self, update, context):
        message_text = update.message.text
        context.user_data["edit_profile_request"] = message_text
        if message_text == "Имя":
            await update.message.reply_text("Введите новое имя")
        elif message_text == "Возраст":
            reply_keyboard = [['до 18'], ['от 18 до 25'], ['от 26 до 30', 'от 31 до 35'],
                              ['от 36 до 40', 'от 41 до 45'], ['от 46 до 55', 'старше 55']]
            markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text("Введите новый возраст", reply_markup=markup)
        elif message_text == "Пол":
            reply_keyboard = [['Мужской', 'Женский'], ['Пропустить']]
            markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text("Укажите новый пол", reply_markup=markup)
        elif message_text == "График":
            reply_keyboard = [['Ежедневно'], ['Рабочие', 'Выходные дни']]
            markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text("Сформируйте удобный для вас график получения"
                                            " рекомендаций и уведомлений. Какой график для вас удобен?",
                                            reply_markup=markup)
        elif message_text == "График":
            reply_keyboard = [['Ежедневно'], ['Рабочие', 'Выходные дни']]
            markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
            await update.message.reply_text("Сформируйте удобный для вас график получения"
                                            " рекомендаций и уведомлений. Какой график для вас удобен?",
                                            reply_markup=markup)
        elif message_text == "Время":
            await update.message.reply_text(
                "Укажите время в часах(от 0 до 23), в которое вы хотите получать рекомендации ⌚")
        elif message_text == "Период напоминаний":
            await update.message.reply_text("Укажите интервал, в который вам будут присылаться напоминания "
                                            "о прохождении рекомендаций в днях. Например: каждые 2 дня.")
        return PROFILE_EDIT_APPLY_STATE


    async def edit_profile_apply(self, update, context):
        message_text = update.message.text
        request_type = context.user_data["edit_profile_request"]

        if request_type == "Имя":
            if any(ch.isdigit() for ch in message_text):
                await update.message.reply_text("🫣 Не похоже на [имя/фамилию]. Попробуйте еще раз")
                return PROFILE_EDIT_APPLY_STATE
            context.user_data['name'] = message_text
        elif request_type == "Возраст":
            age_value = update.message.text
            if len(age_value.split()) != 2:
                age = age_value.split()
                context.user_data['age'] = f"{age[1]}-{age[3]}"
            else:
                age = age_value.split()
                if age[1] == '18':
                    context.user_data['age'] = "0-18"
                else:
                    context.user_data['age'] = "55-100"
        elif request_type == "Пол":
            if message_text == "Мужской" or message_text == "Женский" or message_text == "Пропустить":
                context.user_data['sex'] = message_text
            else:
                await update.message.reply_text("Выберите один из доступных вариантов")
                return PROFILE_EDIT_APPLY_STATE
        elif request_type == "График":
            if message_text == "Ежедневно" or message_text == "Рабочие" or message_text == "Выходные дни":
                context.user_data['days'] = message_text
            else:
                await update.message.reply_text("Выберите один из доступных вариантов")
                return PROFILE_EDIT_APPLY_STATE
        elif request_type == "Время":
            if message_text.isdigit():
                if 0 <= int(message_text) <= 23:
                    context.user_data['time'] = f'{message_text}:00'
                else:
                    await update.message.reply_text("В сутках только 24 часа 😝, попробуйте ещё раз")
                    return PROFILE_EDIT_APPLY_STATE
            else:
                await update.message.reply_text("Значение, которое вы ввели не является числом 😜, попробуйте ещё раз")
                return PROFILE_EDIT_APPLY_STATE
        elif request_type == "Период напоминаний":
            if message_text.isdigit():
                if 1 <= int(message_text) <= 30:
                    context.user_data['period'] = str(message_text)
                else:
                    await update.message.reply_text("Вы выбрали слишком большой или маленький период. Попробуйте ещё раз.")
                    return PROFILE_EDIT_APPLY_STATE
            else:
                await update.message.reply_text("Значение, которое вы ввели не является числом 😜, попробуйте ещё раз")
                return PROFILE_EDIT_APPLY_STATE

        user = await self.user_service.find_user_by_telegram_id(update.message.chat.id)

        user.Name = context.user_data.get('name', user.name)
        user.Age_Group = context.user_data.get('age', user.age_group)
        user.Schedule = context.user_data.get('days', user.schedule)
        user.Sex = context.user_data.get('sex', user.sex)
        user.Time = context.user_data.get('time', user.time)
        user.Period = context.user_data.get('period', user.period)

        self.user_service.update_user(user.user_id, user)

        reply_keyboard = [['Показать профиль', 'Меню']]
        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)

        await update.message.reply_text("Изменения профиля успешно применены!", reply_markup=markup)
        return PROFILE_SHOW_STATE

    async def send_recommendation_job(self, context):
        is_all_sent = await self.send_recommendation(context, context.job.chat_id)
        if is_all_sent:
            context.job.schedule_removal()


    # Отправка пользователю очередной рекомендации
    async def send_recommendation(self, context, chat_id) -> bool:
        # Выполняем поиск пользователя по идентификатору чата
        user = await self.user_service.find_user_by_telegram_id(chat_id)
        # Если пользователь не найден, то адвент прекращается - выход
        if user is None:
            await context.bot.send_message(chat_id=chat_id,
                                           text='Такой пользователь не найден, воспользуйтесь командой /start')
            return True

        # Определяем количество рекомендаций, которые в принципе нужно было отправить
        recommendations_count = await self.advent_service.get_recommendation_count()

        # Получаем все ранее отправленные рекомендации этому пользователю
        sent_recommendations = await self.advent_service.get_sended_recommendations(user.user_id)

        # Если ранее уже отправлялись рекомендации, то определяем последнюю отправленную, иначе используем первую
        if len(sent_recommendations) != 0:
            last_rec = sent_recommendations[-1]
            new_req_id = last_rec.rec_id + 1
        else:
            last_rec = None
            new_req_id = 1

        # Если все рекомендации уже были отправлены ранее, то завершаем адвент - выход
        if new_req_id > recommendations_count:
            await context.bot.send_message(chat_id=user.telegram_id, text=f'Вы получили все рекомендации!',
                                           reply_markup=self.build_main_menu(user.advent_start))
            return True

        # Получаем текст очередной рекомендации и отправляем ее пользователю
        rec_new = await self.advent_service.get_recommendation_info_by_id(new_req_id)
        if rec_new is None:
            return False

        keyboard = [
            [
                InlineKeyboardButton("Выполнить", callback_data=f"{BUTTON_REC_DONE}:{new_req_id}"),
                InlineKeyboardButton("Отложить", callback_data=f"{BUTTON_REC_SKIP}:{new_req_id}"),
            ]
        ]
        markup = InlineKeyboardMarkup(keyboard)

        # Отправляем рекомендацию
        message = await context.bot.send_message(chat_id=user.telegram_id,
                                                 text=f'{user.name}, '
                                                      f'рекомендация № {new_req_id}: '
                                                      f'{rec_new.text}!',
                                                 reply_markup=markup)

        # Сохраняем отправленную рекомендацию в базу
        stat_rec = RecommendationStatusModel()
        stat_rec.telegram_id = user.telegram_id
        stat_rec.user_id = user.user_id
        stat_rec.send_time = datetime.now()
        stat_rec.telegram_message_id = message.message_id
        stat_rec.rec_id = new_req_id
        stat_rec.rec_status = REC_STATUS_INIT
        await self.advent_service.add_recommendation(stat_rec)

        # Если отправленная рекомендация не первая
        if last_rec:
            # Если рекомендация была проигнорирована пользователем, то откладываем ее
            if last_rec.rec_status == REC_STATUS_INIT:
                await self.skip_rec(context, user.user_id, last_rec.rec_id)

        return False

    async def send_notification_job(self, context: ContextTypes.DEFAULT_TYPE):
        user = await self.user_service.find_user_by_telegram_id(context.job.chat_id)
        if user is None:
            await context.bot.send_message(chat_id=context.job.chat_id,
                                           text='Такой пользователь не найден, воспользуйтесь командой /start')
            context.job.schedule_removal()
            return

        # Если адвент выполнен, то прекращаем отправку уведомлений
        if await self.advent_service.is_advent_completed(user.user_id):
            context.job.schedule_removal()
            return

        skipped_recommendations = await self.advent_service.get_skipped_recommendations(user.user_id)

        if len(skipped_recommendations) == 0:
            return

        result = ''
        for rec in skipped_recommendations:
            rec_info = await self.advent_service.get_recommendation_info_by_id(rec.rec_id)
            if rec_info is None:
                continue
            result += f'День {rec.rec_id}. {rec_info.text}\n'

        result = f'Не выполнено {len(skipped_recommendations)} рекомендаций:\n' + result
        keyboard = [[InlineKeyboardButton("Сообщить о выполнении", callback_data=f"{BUTTON_REC_REPORT}")]]
        markup = InlineKeyboardMarkup(keyboard)

        # Отправляем уведомление
        await context.bot.send_message(chat_id=user.telegram_id, text=result, reply_markup=markup)


    async def done_recommendation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        chat_id = query.message.chat_id
        del_idx = query.data.find(":") + 1
        rec_id = int(query.data[del_idx:])

        user = await self.user_service.find_user_by_telegram_id(chat_id)
        if user is None:
            return

        # Отмечаем рекомендацию как выполненную
        await self.advent_service.done_rec(user.user_id, rec_id)

        await query.delete_message()
        await context.bot.send_message(chat_id=chat_id, text=f"Выполнена рекомендация №: {rec_id}")


    async def skip_recommendation(self, update, context):
        query = update.callback_query
        await query.answer()

        chat_id = query.message.chat_id
        del_idx = query.data.find(":") + 1
        rec_id = int(query.data[del_idx:])

        user = await self.user_service.find_user_by_telegram_id(chat_id)
        if user is None:
            return

        await self.skip_rec(context, user.user_id, rec_id)
        await context.bot.send_message(chat_id=user.telegram_id, text=f"Отложена рекомендация №: {rec_id}")


    async def run_recommendation_job(self, context, chat_id):
        user = await self.user_service.find_user_by_telegram_id(chat_id)
        if user is None:
            return

        user_tz = pytz.timezone(user.timezone)
        user_time = datetime.strptime(user.time, '%H:%M')

        # Запуск рекомендаций только если не все рекомендации были отправлены
        if not await self.advent_service.is_all_recommendation_sent(user.user_id):
            sent_time = time(user_time.hour, user_time.minute, 00, tzinfo=user_tz)
            sent_days = (0, 1, 2, 3, 4, 5, 6)
            if user.schedule == "Рабочие дни":
                sent_days = (0, 1, 2, 3, 4)
            elif user.schedule == 'Выходные дни':
                sent_days = (5, 6)

            # Ежедневный запуск задачи
            context.job_queue.run_daily(self.send_recommendation_job, name=self.build_job_rec_name(user.telegram_id),
                                        time=sent_time, days=sent_days, data=user.name, chat_id=user.telegram_id)

        # Запуск напоминаний только если не завершен адвент
        if not await self.advent_service.is_advent_completed(user.user_id):
            # Напоминание отправляем после отправки рекомендации на 30 мин позже
            sent_datetime = (user_tz.localize(
                datetime.combine(datetime.today(), time(user_time.hour, user_time.minute, 00)), is_dst=None) +
                             timedelta(minutes=30))

            # Запускаем задачу с отправкой напоминаний с пользовательским интервалом
            context.job_queue.run_repeating(self.send_notification_job, name=self.build_job_not_name(user.telegram_id),
                                            first=sent_datetime, interval=timedelta(days=int(user.period)),
                                            data=user.name, chat_id=user.telegram_id)

        # TODO: Для тестирования
        # context.job_queue.run_repeating(send_recommendation_job, 5, name=build_job_rec_name(user.Chat_Id), data=user.Name, chat_id=user.Chat_Id)
        # context.job_queue.run_repeating(send_notification_job, 10, name=build_job_not_name(user.Chat_Id), data=user.Name, chat_id=user.Chat_Id)


    async def start_advent(self, update, context):
        chat_id = update.message.chat_id
        user = await self.user_service.find_user_by_telegram_id(chat_id)
        if user is None:
            await context.bot.send_message(chat_id=chat_id, text='Такой пользователь не найден, '
                                                                 'воспользуйтесь командой /start')
            return

        if not (user.advent_start is None):
            await context.bot.send_message(chat_id=chat_id, text='Новогодний адвент уже был запущен ранее!',
                                           reply_markup=self.build_main_menu(user.advent_start))
            return

        await self.user_service.start_advent(user.user_id)

        await context.bot.send_message(chat_id=chat_id, text='Новогодний адвент запущен',
                                       reply_markup=self.build_main_menu(datetime.now()))

        # Отправляем первую рекомендацию сразу же после запуска адвента
        await self.send_recommendation(context, chat_id)
        # Запускаем задание для отправки будущих рекомендаций
        await self.run_recommendation_job(context, chat_id)


    async def resume_sending(self, context):
        users_ids = {}

        # Определяем пользователей, у которых запущен адвент, но еще не было отправлено ни одно рекомендации
        users_with_advent = await self.user_service.get_users_with_advent()
        for user in users_with_advent:
            users_ids[user.user_id] = user.user_id

        # Определяем пользователей, которым были отправлены рекомендации, но еще не все
        active_users = await self.advent_service.get_active_users_ids()
        for user_id in active_users:
            users_ids[user_id] = user_id

        users = await self.user_service.get_users_by_ids(list(users_ids.keys()))
        for user in users:
            await self.run_recommendation_job(context, user.telegram_id)


    async def share(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.message.chat.id)

        user = await self.user_service.find_user_by_telegram_id(chat_id)
        if user is None:
            await context.bot.send_message(chat_id=chat_id, text='Такой пользователь не найден, адвент будет остановлен!')
            context.job.schedule_removal()
            return

        keyboard = [
            [
                InlineKeyboardButton("Поделиться", url=f'https://t.me/share/url?url={self.bot_url}')
            ]
        ]
        markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(chat_id=chat_id,
                                       text=f"Поделитесь нашим ботом со своими друзьями, чтобы и они "
                                            f"были грамотными в цифровой среде!",
                                       reply_markup=markup)
        await self.show_main_menu(update, context)


    async def show_recommendation(self, update, context):
        chat_id = update.message.chat_id
        user = await self.user_service.find_user_by_telegram_id(chat_id)
        if user is None:
            return

        list_rec = await self.advent_service.get_last_sended_recommendations(user.user_id, 3)
        if len(list_rec) == 0:
            await context.bot.send_message(chat_id=user.telegram_id,
                                           text='Список рекомендаций пуст. Убедитесь, что вы запустили "Новогодний адвент"',
                                           reply_markup=self.build_main_menu(user.advent_start))
            return

        result = ''
        for idx, rec in enumerate(list_rec):
            rec_info = await self.advent_service.get_recommendation_info_by_id(rec.rec_id)
            if rec_info is None:
                continue
            if idx == 0:
                today = " Сегодня." if rec.send_time.date() == datetime.today().date() else ""
                result += f'*День {rec.rec_id}.{today}* {rec_info.text}\n'
            else:
                result += f'*День {rec.rec_id}.* {rec_info.text}\n'

        await context.bot.send_message(chat_id=user.telegram_id, text=f'Список трех последних рекомендаций:\n\n{result}',
                                       reply_markup=self.build_main_menu(user.advent_start),
                                       parse_mode='markdown')


    async def test_knowledge(self, update, context):
        user = await self.user_service.find_user_by_telegram_id(update.message.chat_id)
        if user is None:
            return

        if await self.advent_service.is_advent_completed(user.user_id):
            keyboard = [[InlineKeyboardButton("Пройти тест", callback_data=f"{BUTTON_RUN_TEST}")]]
            markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                'Поздравляем, вы выполнили все рекомендации! '
                'Хотите пройти проверку знаний и получить звание Джедая ордена Цифровой гигиены и '
                'возможность скачать стикерпак от Киберпротекта? '
                'Тогда попробуйте пройти тест!',
                reply_markup=markup)
            await self.show_main_menu(update, context)
        else:
            await update.message.reply_text(
                'Пройти тест можно будет только после выполнения всех рекомендаций адвента',
                reply_markup=self.build_main_menu(user.advent_start))


    async def forma_yandex(self, update, context):
        query = update.callback_query
        await query.answer()

        chat_id = query.message.chat_id
        user = await self.user_service.find_user_by_telegram_id(chat_id)
        if user is None:
            return

        await context.bot.send_message(chat_id=user.telegram_id, text='https://forms.yandex.ru/u/6663258b5056903972729751/',
                                       reply_markup=self.build_main_menu(user.advent_start))


    # Получить страницу с отправленными рекомендациями
    async def get_recommendation_page(self, user_id: int, page_num: int, page_size: int) -> str:
        # Получаем страницу отправленных рекомендаций пользователю
        sent_recommendations = await self.advent_service.get_recommendation_page(user_id, page_num, page_size)
        result = ''
        for rec in sent_recommendations:
            if rec.rec_status == REC_STATUS_DONE:
                visualize = '🟢'
            elif rec.rec_status == REC_STATUS_SKIP:
                visualize = '🔴'
            else:
                visualize = '⚪️'
            result += f'{visualize} № {rec.rec_id}: {rec.text}\n'
        return result


    async def show_result_query(self, update, context):
        query = update.callback_query
        await query.answer()
        return await self.show_results(update, context)


    async def show_results(self, update, context):
        if not (update.callback_query is None):
            query = update.callback_query
            await query.answer()
            chat_id = query.message.chat_id
        else:
            chat_id = update.message.chat_id

        user = await self.user_service.find_user_by_telegram_id(chat_id)
        if user is None:
            await context.bot.send_message(chat_id=chat_id, text='Пользователь не найден, воспользуйтесь командой /start')
            return

        # Определяем количество отправленных рекомендаций
        rec_count = await self.advent_service.sent_recommendation_count(user.user_id)
        if rec_count == 0:
            await context.bot.send_message(chat_id=user.telegram_id, text='Еще ни одной рекомендации не было отправлено',
                                           reply_markup=self.build_main_menu(user.advent_start))
            return

        page_size = 5
        page_num = 0
        page_count = rec_count // page_size
        if rec_count % page_size > 0:
            page_count += 1

        if page_count > 1:
            reply_keyboard = [['Показать далее...', 'Изменить статус выполнения', 'Меню']]
        else:
            reply_keyboard = [['Изменить статус выполнения', 'Меню']]

        result = await self.get_recommendation_page(user.user_id, page_num, page_size)
        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        await context.bot.send_message(chat_id=user.telegram_id, text=f'Результат выполнения:\n\n{result}\n\n'
                                                                  f'Страница {page_num+1} из {page_count}',
                                       parse_mode='HTML', reply_markup=markup)

        context.user_data['page_size'] = page_size
        context.user_data['page_count'] = page_count
        context.user_data['page_num'] = page_num
        return RESULTS_SHOW


    async def show_result_next(self, update, context):
        user = await self.user_service.find_user_by_telegram_id(update.message.chat_id)
        if user is None:
            return

        page_size = context.user_data['page_size']
        page_count = context.user_data['page_count']
        page_num = context.user_data['page_num'] + 1

        if page_num < (page_count - 1):
            reply_keyboard = [['Показать далее...', 'Изменить статус выполнения', 'Меню']]
        else:
            reply_keyboard = [['Изменить статус выполнения', 'Меню']]

        result = await self.get_recommendation_page(user.user_id, page_num, page_size)
        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
        await context.bot.send_message(chat_id=user.telegram_id, text=f'Результат выполнения:\n\n{result}\n\n'
                                                                  f'Страница {page_num+1} из {page_count}',
                                       parse_mode='HTML', reply_markup=markup)

        context.user_data['page_num'] = page_num
        return RESULTS_SHOW


    async def change_results(self, update, context):
        user = await self.user_service.find_user_by_telegram_id(update.message.chat_id)
        if user is None:
            return

        page_count = context.user_data['page_count']
        page_num = context.user_data['page_num'] + 1

        if page_num < (page_count - 1):
            reply_keyboard = [['Показать далее...', 'Изменить статус выполнения', 'Меню']]
        else:
            reply_keyboard = [['Изменить статус выполнения', 'Меню']]
        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)

        await context.bot.send_message(chat_id=user.telegram_id,
                                       text='Введите номер рекомендации, статус которой Вы хотели бы изменить',
                                       reply_markup=markup)
        return RESULTS_REC_NUM


    async def change_status_results(self, update, context):
        user = await self.user_service.find_user_by_telegram_id(update.message.chat_id)
        if user is None:
            return

        page_count = context.user_data['page_count']
        page_num = context.user_data['page_num'] + 1

        if page_num < (page_count - 1):
            reply_keyboard = [['Показать далее...', 'Изменить статус выполнения', 'Меню']]
        else:
            reply_keyboard = [['Изменить статус выполнения', 'Меню']]
        markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)

        rec_id = update.message.text
        if not rec_id.isdigit():
            await context.bot.send_message(chat_id=user.telegram_id, text="Введите номер рекомендации",
                                           reply_markup=markup)
            return RESULTS_REC_NUM

        rec_info = await self.advent_service.get_recommendation_info_by_id(update.message.text)
        if rec_info is None:
            await context.bot.send_message(chat_id=user.telegram_id,
                                           text="Рекомендации с таким номером не найдена, попробуйте еще раз",
                                           reply_markup=markup)
            return RESULTS_REC_NUM

        keyboard = [
            [InlineKeyboardButton("Отметить как выполненное", callback_data=f"{BUTTON_REC_DONE}:{rec_id}")],
            [InlineKeyboardButton("Отложить выполнение", callback_data=f"{BUTTON_REC_SKIP}:{rec_id}")]
        ]
        inline_markup = InlineKeyboardMarkup(keyboard)
        rec = f'№ {rec_id}: {rec_info.text}\n'
        await context.bot.send_message(chat_id=user.telegram_id, text=rec, reply_markup=inline_markup)
        return RESULTS_SHOW


    async def handle_everything_else(self, update, context):
        user = await self.user_service.find_user_by_telegram_id(update.message.chat_id)
        if user is None:
            await context.bot.send_message(chat_id=update.message.chat_id,
                                           text="🤖 Ой, возможно мы еще не знакомы с вами, попробуйте выполнить команду /start")
            return

        await update.message.reply_text("🤖 Что-то я вас не понял, воспользуйтесь главным меню",
                                        reply_markup=self.build_main_menu(user.advent_start))
        return ConversationHandler.END

    def run(self):
        application = Application.builder().token(self.bot_token).build()

        # Возобновление отправки рекомендаций после рестарта
        application.job_queue.run_once(self.resume_sending, 1)

        application.add_handler(CommandHandler("stop", self.stop))
        application.add_handler(CommandHandler("help", self.help_message))
        application.add_handler(CommandHandler("menu", self.show_main_menu))

        condition = (filters.TEXT | filters.PHOTO) & ~filters.COMMAND

        # Сценарий регистрации нового пользователя или приветствия существующего пользователя
        start_handler = ConversationHandler(
            entry_points=[CommandHandler("start", self.start)],
            states={
                GREETING_STATE: [MessageHandler(condition, self.greeting)],
                REGISTRATION_STATE: [MessageHandler(condition, self.registration)],
                NAME_STATE: [MessageHandler(condition, self.name)],
                SCHEDULE_STATE: [MessageHandler(condition, self.schedule)],
                TIME_STATE: [MessageHandler(condition, self.time_schedule)],
                TIMEZONE_STATE: [MessageHandler(condition, self.timezone_schedule)],
                SEX_STATE: [MessageHandler(condition, self.sex)],
                AGE_STATE: [MessageHandler(condition, self.age)],
                PERIOD_STATE: [MessageHandler(condition, self.period)],
            },
            fallbacks=[
                CommandHandler('stop', self.stop),
            ]
        )
        application.add_handler(start_handler)

        # Сценарий обработки кнопки "Мой профиль"
        profile_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Text(["Мой профиль"]), self.show_profile)],
            states={
                PROFILE_SHOW_STATE: [
                    MessageHandler(filters.Text(["Показать профиль"]), self.show_profile)
                ],
                PROFILE_EDIT_STATE: [
                    MessageHandler(filters.Text(["Редактировать данные"]), self.edit_profile)
                ],
                PROFILE_EDIT_FIELD_STATE: [
                    MessageHandler(filters.Text(["Имя", "Возраст", "Пол", "График", "Время", "Период напоминаний"]),
                                   self.edit_profile_request),
                    MessageHandler(filters.Text(["Назад"]), self.show_profile)
                ],
                PROFILE_EDIT_APPLY_STATE: [
                    MessageHandler(condition, self.edit_profile_apply)
                ],
            },
            fallbacks=[
                MessageHandler(filters.Text(["Меню"]), self.show_main_menu),
                MessageHandler(filters.ALL, self.handle_everything_else)
            ]
        )

        application.add_handler(profile_handler)
        application.add_handler(
            MessageHandler(filters.Text(["Запустить новогодний адвент по цифровой гигиене"]), self.start_advent))
        application.add_handler(MessageHandler(filters.Text(["Рекомендации"]), self.show_recommendation))
        application.add_handler(MessageHandler(filters.Text(["Пройти тест по цифровой гигиене"]), self.test_knowledge))
        application.add_handler(MessageHandler(filters.Text(["Пригласить друзей"]), self.share))
        application.add_handler(MessageHandler(filters.Text(["Помощь"]), self.help_message))

        # Обработка кнопки "Результаты выполнения"
        results_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Text(["Результаты выполнения"]), self.show_results),
                CallbackQueryHandler(self.show_result_query, pattern=f"^{BUTTON_REC_REPORT}")
            ],
            states={
                RESULTS_SHOW: [
                    MessageHandler(filters.Text(["Показать далее..."]), self.show_result_next),
                    MessageHandler(filters.Text(["Изменить статус выполнения"]), self.change_results)
                ],
                RESULTS_REC_NUM: [
                    MessageHandler(condition, self.change_status_results)
                ],
                RESULTS_CHANGE: [
                    MessageHandler(filters.Text(["Назад"]), self.show_results)
                ],
            },
            fallbacks=[
                MessageHandler(filters.Text(["Меню"]), self.show_main_menu),
                MessageHandler(filters.ALL, self.handle_everything_else)
            ],
        )
        application.add_handler(results_handler)

        application.add_handler(CallbackQueryHandler(self.done_recommendation, pattern=f"^{BUTTON_REC_DONE}:\\d+$"))
        application.add_handler(CallbackQueryHandler(self.skip_recommendation, pattern=f"^{BUTTON_REC_SKIP}:\\d+$"))
        application.add_handler(CallbackQueryHandler(self.forma_yandex, pattern=f"^{BUTTON_RUN_TEST}$"))
        application.add_handler(
            CallbackQueryHandler(results_handler.entry_points[0].callback, pattern=f"^{BUTTON_REC_REPORT}"))

        application.add_handler(MessageHandler(filters.ALL, self.handle_everything_else))
        application.run_polling()

