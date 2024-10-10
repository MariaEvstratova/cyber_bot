import json
import threading
import random
import datetime
import model.user
import jwt as jwt
from flasgger import Swagger
import service.user_service
from flask import Flask, request, jsonify, make_response, render_template, flash, redirect
from flask_login import LoginManager

from model.user import UserModel, user_from_dict
from model.admins import AdminsModel
from model.recommendation import RecommendationModel
from service.cyber_advent_service import CyberAdventService
from service.statistics_service import StatisticsService
from service.user_service import UserService
from service.admins_service import AdminsService

from forms.admins import RegisterForm, LoginForm
from forms.recs import RecsForm
from web.statistics_api import StatisticsApi

login_manager = LoginManager()

class RestController:

    def __init__(self,
                 port,
                 secret_key,
                 user_service: UserService,
                 advent_service: CyberAdventService,
                 admins_service: AdminsService,
                 statistics_service: StatisticsService,
                 ):
        self.port = port
        self.user_service = user_service
        self.advent_service = advent_service
        self.admins_service = admins_service
        self.statistics_service = statistics_service
        self.web = Flask(__name__)
        self.web.config['JSON_AS_ASCII'] = False
        self.web.config['SECRET_KEY'] = secret_key
        self.setup_swagger()
        self.setup_routes()
        login_manager.init_app(self.web)

        # Регистрируем дополнительное API для получения статистики
        StatisticsApi(statistics_service).register_api(self.web)

    def setup_swagger(self):
        template = {
            "info": {
                "title": "API \"КиберГигиена\"",
                "description": ('Эта спецификация описывает работу API сервиса "КиберГигиена", который '
                                'предназначен для предоставления пользователям советов по безопасному '
                                'поведению в интернете. Этот API позволяет получать  случайные советы с '
                                'соответствующими рекомендациями.'),
                "license:": {
                    "name": "Apache 2.0",
                    "url": "https://www.apache.org/licenses/LICENSE-2.0.html"
                },
                "version": "1.0.11"
            },
            "tags": [
                {
                    "name": "advice",
                    "description": "Работа с советами по КиберГигиене"
                },
                {
                    "name": "user",
                    "description": "Работа с пользователями бота по КиберГигиене"
                },
                {
                    "name": "auth",
                    "description": "Авторизация"
                }
            ],
            "securityDefinitions": {
                "Bearer": {
                    "type": "apiKey",
                    "name": "Authorization",
                    "in": "header",
                    "description": "Авторизация с помощью Bearer JWT-токена. Укажите: Bearer {token}, где {token} - ваш токен."
                }
            },
            "security": [
                {
                    "Bearer": []
                }
            ]
        }
        config = {
            "openapi": "3.0.3",
            "servers": [
                {
                    "url": f"http://localhost:{self.port}"
                }
            ],
            "components": {
                "schemas": {
                    "User": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer", "description": "Идентификатор пользователя"},
                            "name": { "type": "string", "description": "Имя пользователя" },
                            "sex": {"type": "string", "description": "Пол"},
                            "age_group": {"type": "string", "description": "Возрастная группа"},
                            "registration_day": {"type": "string", "description": "Дата регистрации"},
                            "schedule": {"type": "string", "description": "Режим отправки рекомендаций"},
                            "time": {"type": "string", "description": "Время отправки рекомендации"},
                            "timezone": {"type": "string", "description": "Часовой пояс"},
                            "period": {"type": "string", "description": "Период напоминаний"},
                            "advent_start": {"type": "string", "description": "Дата начала адвента"},
                            "telegram_username": {"type": "string", "description": "Telegram Username"},
                            "telegram_id": {"type": "string", "description": "Telegram Id"},
                        },
                        "example": """
                    {
                        "name": "Иван Петров",
                        "registration_day": "2024-10-10T10:30:00",
                        "age_group": "18-25",
                        "schedule": "Ежедневно",
                        "sex": "Мужской",
                        "telegram_username": "test_user",
                        "telegram_id": "123456780",
                        "time": "10:00",
                        "timezone": "Asia/Novosibirsk",
                        "period": "2",
                        "advent_start": null
                    }"""
                    },
                    "Advice": {
                        "type": "object",
                        "properties": {
                            "id": {
                                "type": "integer",
                                "format": "int64",
                                "title": "Уникальный идентификатор",
                                "example": "5"
                            },
                            "description": {
                                "type": "string",
                                "minLength": "1",
                                "maxLength": "500",
                                "example": ('Вирусы становятся все более опасными и умеют обходить даже самые '
                                            'защищенные информационные системы. В обновленые решения разработчики '
                                            'стараются внедрять инструменты, которые помогут справиться с новыми '
                                            'киберугрозами и обеспечить безопасность в сети. '
                                            '\n'
                                            'Очевидный, но важный совет: загружайте приложения только из '
                                            'официальных источников и покупайте лицензированное ПО. Так вы '
                                            'будете уверены в безопасности своих приобретений.'
                                            '\n'
                                            'Не бойтесь удалить те приложения, которыми не пользуетесь.')
                            },
                        },
                    },
                    "ErrorNotFound": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string", "title": "Краткое описание ошибки", "example": "Запрошенный ресурс не найден." },
                        },
                    },
                    "ErrorBadRequest": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string", "title": "Краткое описание ошибки",
                                      "example": "Переданы неверные данные."},
                        },
                    },
                    "ErrorResponse": {
                        "type": "object",
                        "properties": {
                            "error": {"type": "string", "title": "Краткое описание ошибки", "example": "Внутренняя ошибка сервера. Попробуйте позже." },
                        },
                    },
                },
            },
        }
        Swagger(self.web, config=config, template=template, merge=True)

    def setup_routes(self):
        @login_manager.user_loader
        def load_user(user_id):
            return self.admins_service.find_user_by_id(user_id)

        @self.web.route("/health")
        def health():
            return '{"Up!"}'

        @self.web.route("/")
        def index():
            all_recommendations = self.advent_service.get_all_recommendations()
            return render_template("index.html", recs=all_recommendations)

        # def create_jwt_token(user_id):
        #     payload = {
        #         'sub': user_id,
        #         'iat': datetime.utcnow(),
        #         'exp': datetime.utcnow()
        #     }
        #     token = jwt.encode(payload, self.web.config['JSON_AS_ASCII'], algorithm='HS256')
        #     return token

        @self.web.route('/register', methods=['GET', 'POST'])
        def register():
            form = RegisterForm()
            if form.validate_on_submit():
                if form.password.data != form.password_again.data:
                    return render_template('register.html', title='Регистрация',
                                           form=form,
                                           message="Пароли не совпадают")
                admin = self.admins_service.find_user_by_email(form.email.data)
                if admin:
                    return render_template('register.html', title='Регистрация',
                                           form=form,
                                           message="Такой пользователь уже есть")
                new_admin = AdminsModel(name=form.name.data, email=form.email.data, password=form.password.data)
                self.admins_service.create_admin(new_admin)
                return redirect('/')
            return render_template('register.html', title='Регистрация', form=form)

        @self.web.route('/login', methods=['POST'])
        def login():
            """Авторизация
                Данное API возвращает JWT токен авторизованным пользователям
                ---
                tags:
                  - auth
                parameters:
                  - name: email
                    in: query
                    type: string
                    required: true
                  - name: password
                    in: query
                    type: string
                    required: true
                responses:
                  200:
                    description: JWT-токен
                    content:
                      application/json:
                        schema:
                          type: string
            """
            return "token"

        @self.web.route('/rec', methods=['GET', 'POST'])
        # @self.login_required
        def add_news():
            form = RecsForm()
            if form.validate_on_submit():
                number = len(self.advent_service.get_all_recommendations()) + 1
                new_rec = RecommendationModel(num=number, text=form.recommendation.data, media=form.media.data)
                self.advent_service.create_recommendation(new_rec)
                return redirect('/')
            return render_template('rec.html', title='Добавление рекомендации',
                                   form=form)

        @self.web.route('/rec/<int:id>', methods=['GET', 'POST'])
        # @login_required
        async def edit_news(id):
            form = RecsForm()
            if request.method == "GET":
                rec = await self.advent_service.get_recommendation_info_by_id(id)
                if rec:
                    form.recommendation.data = rec.text
                    form.media.data = rec.media
                else:
                    return not_found(f"Рекомендация с ID {id} не найдена")
            if form.validate_on_submit():
                rec = await self.advent_service.get_recommendation_info_by_id(id)
                if rec:
                    recommendation = RecommendationModel(num=id, text=form.recommendation.data, media=form.media.data)
                    self.advent_service.update_recommendation(recommendation)
                    return redirect('/')
                else:
                    return not_found(f"Рекомендация с ID {id} не найдена")
            return render_template('rec.html',
                                   title='Редактирование рекомендации',
                                   form=form
                                   )

        @self.web.route('/rec_delete/<int:id>', methods=['GET', 'POST'])
        async def news_delete(id):
            rec = await self.advent_service.get_recommendation_info_by_id(id)
            if rec:
                await self.advent_service.delete_recommendation(rec)
                return redirect('/')
            else:
                return not_found(f"Рекомендация с ID {id} не найдена")


        @self.web.route("/api/public/advice/random", methods=['GET'])
        async def get_user_recommendation_random():
            """Возвращает случайную рекомендацию
                Возвращает случайную рекомендацию по безопасному поведению в интернете
                ---
                tags:
                  - advice
                responses:
                  200:
                    description: Успешная операция
                    content:
                      application/json:
                        schema:
                          $ref: '#/components/schemas/Advice'
                  500:
                    description: Внутренняя ошибка сервера
                    content:
                      application/json:
                        schema:
                          $ref: '#/components/schemas/ErrorResponse'
            """
            random_num = random.randint(1, 30)
            recommendation = await self.advent_service.get_recommendation_info_by_id(random_num)
            if recommendation:
                return json.dumps(recommendation.to_dict(), ensure_ascii=False)
            else:
                return internal_error("Не удалось получить рекомендацию")

        @self.web.route("/api/public/advice/today", methods=['GET'])
        async def get_user_recommendation_today():
            """Возвращает рекомендацию дня
                Возвращает рекомендацию дня по безопасному поведению в интернете
                ---
                tags:
                  - advice
                responses:
                  200:
                    description: Успешная операция
                    content:
                      application/json:
                        schema:
                          $ref: '#/components/schemas/Advice'
                  500:
                    description: Внутренняя ошибка сервера
                    content:
                      application/json:
                        schema:
                          $ref: '#/components/schemas/ErrorResponse'
            """
            today_day = datetime.datetime.now().day
            recommendations_count = await self.advent_service.get_recommendation_count()
            if today_day > recommendations_count:
                today_day = 1

            recommendation = await self.advent_service.get_recommendation_info_by_id(today_day)
            if recommendation:
                return json.dumps(recommendation.to_dict(), ensure_ascii=False)
            else:
                return internal_error("Не удалось получить рекомендацию")

        @self.web.route("/api/v1/private/users", methods=['GET'])
        def get_users():
            """Получение списка пользователей
                Данное API возвращает список пользователей, использующих CyberBot
                ---
                tags:
                  - user
                parameters:
                  - name: page_num
                    in: query
                    type: string
                    required: false
                    default: 0
                    example: 0
                  - name: page_size
                    in: query
                    type: string
                    required: false
                    default: 25
                    example: 25
                responses:
                  200:
                    description: Список пользователей
                    content:
                      application/json:
                        schema:
                          type: array
                          items:
                            $ref: '#/components/schemas/User'
            """
            page_num = int(request.args.get("page_num", 0))
            page_size = int(request.args.get("page_size", 25))
            users = self.user_service.get_users(page_num, page_size)
            return json.dumps([user.to_dict() for user in users], ensure_ascii=False)

        @self.web.route("/api/v1/private/users/<user_id>", methods=['GET'])
        async def get_user(user_id: int):
            """Получение пользователя по идентификатору
                Данное API возвращает пользователя по идентификатору, использующего CyberBot
                ---
                tags:
                  - user
                parameters:
                  - name: user_id
                    in: path
                    type: string
                    required: true
                    example: 1
                responses:
                  200:
                    description: Пользователь
                    content:
                      application/json:
                        schema:
                          $ref: '#/components/schemas/User'
                  404:
                    description: Пользователь не найден
                    content:
                      application/json:
                        schema:
                          $ref: '#/components/schemas/ErrorNotFound'
            """
            user = await self.user_service.find_user_by_id(user_id)
            if user:
                return json.dumps(user.to_dict(), ensure_ascii=False)
            else:
                return not_found(f"Пользователь с ID {user_id} не найден")


        @self.web.route("/api/v1/private/users", methods=['POST'])
        async def create_user():
            """Добавление пользователя
                Добавить нового пользователя в чат-бот
                ---
                tags:
                  - user
                requestBody:
                  content:
                    application/json:
                      schema:
                        $ref: '#/components/schemas/User'
                  required: true
                responses:
                  200:
                    description: Пользователь
                    content:
                      application/json:
                        schema:
                          $ref: '#/components/schemas/User'
                  400:
                    description: Переданы неверные данные
                    content:
                      application/json:
                        schema:
                          $ref: '#/components/schemas/ErrorBadRequest'
            """
            user_data = request.get_json()
            if not user_data:
                return bad_request("Не передано содержимое с пользовательскими данными")

            user_model = user_from_dict(user_data)
            if not user_model.name:
                return bad_request("Не передано имя пользователя")

            new_user = self.user_service.create_user(user_model)
            return json.dumps(new_user.to_dict(), ensure_ascii=False)


        @self.web.route("/api/private/users/<user_id>", methods=['PUT'])
        async def update_user(user_id):
            """Обновление пользователя
                Обновить пользователя в чат-боте по ID
                ---
                tags:
                  - user
                parameters:
                  - name: user_id
                    in: path
                    type: string
                    required: true
                    example: 1
                requestBody:
                  content:
                    application/json:
                      schema:
                        $ref: '#/components/schemas/User'
                  required: true
                responses:
                  200:
                    description: Пользователь
                    content:
                      application/json:
                        schema:
                          $ref: '#/components/schemas/User'
                  400:
                    description: Переданы неверные данные
                    content:
                      application/json:
                        schema:
                          $ref: '#/components/schemas/ErrorBadRequest'
                  404:
                    description: Пользователь не найден
                    content:
                      application/json:
                        schema:
                          $ref: '#/components/schemas/ErrorNotFound'
            """
            # Ищем пользователя по идентификатору
            user = await self.user_service.find_user_by_id(user_id)
            if not user:
                return not_found(f"Пользователь с ID {user_id} не найден")

            user_data = request.get_json()
            if not user_data:
                return bad_request("Не передано содержимое с пользовательскими данными")
            user_model = user_from_dict(user_data)
            updated_user = self.user_service.update_user(user_id, user_model)
            return json.dumps(updated_user.to_dict(), ensure_ascii=False)


        @self.web.route("/api/v1/private/users/<user_id>/recommendations", methods=['GET'])
        async def get_user_recommendations(user_id):
            page_num = int(request.args.get("page_num", 0))
            page_size = int(request.args.get("page_size", 50))
            recommendations = await self.advent_service.get_recommendation_page(user_id, page_num, page_size)
            return json.dumps([rec.to_dict() for rec in recommendations], ensure_ascii=False)


        def not_found(message):
            error = { 'error' : message }
            response = make_response(json.dumps(error, ensure_ascii=False))
            response.status_code = 404
            return response

        def bad_request(message):
            error = { 'error' : message }
            response = make_response(json.dumps(error, ensure_ascii=False))
            response.status_code = 400
            return response

        def internal_error(message):
            error = { 'error' : message }
            response = make_response(json.dumps(error, ensure_ascii=False))
            response.status_code = 500
            return response

    def run(self):
        print(f"Web-server starting on port {self.port}")
        self.web.run(host='0.0.0.0', port=self.port)

    def run_background(self):
        threading.Thread(target=self.run, daemon=True).start()