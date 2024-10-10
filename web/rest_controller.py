import json
import threading
import random
import datetime
import jwt as jwt
from flasgger import Swagger

from flask import Flask, request, jsonify, make_response, render_template, flash, redirect
from flask_login import LoginManager

from model.admins import AdminsModel
from service.cyber_advent_service import CyberAdventService
from service.user_service import UserService
from service.admins_service import AdminsService

from forms.admins import RegisterForm, LoginForm

login_manager = LoginManager()

class RestController:

    def __init__(self, port, secret_key, user_service: UserService, advent_service: CyberAdventService, admins_service: AdminsService):
        self.port = port
        self.user_service = user_service
        self.advent_service = advent_service
        self.admins_service = admins_service
        self.web = Flask(__name__)
        self.web.config['JSON_AS_ASCII'] = False
        self.web.config['SECRET_KEY'] = secret_key
        self.setup_swagger()
        self.setup_routes()
        login_manager.init_app(self.web)

    def setup_swagger(self):
        template = {
            "info": {
                "title": "CyberBot API",
                "description": "API для управления CyberBot",
                "version": "1.0"
            },
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
            "definitions": {
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
                },
                "Recommendation": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "description": "Идентификатор рекомендации"},
                        "description": {"type": "string", "description": "Описание рекомендации"},
                    },
                },
                "Error": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "integer", "description": "Ошибка"},
                    },
                }
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

        @self.web.route("/api/v1/users", methods=['GET'])
        def get_users():
            """Получение списка пользователей
                Данное API возвращает список пользователей, использующих CyberBot
                ---
                tags:
                  - Пользователи
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
                            $ref: '#/definitions/User'
            """
            page_num = int(request.args.get("page_num", 0))
            page_size = int(request.args.get("page_size", 25))
            users = self.user_service.get_users(page_num, page_size)
            return json.dumps([user.to_dict() for user in users], ensure_ascii=False)

        @self.web.route("/api/v1/users/<user_id>", methods=['GET'])
        async def get_user(user_id: int):
            """Получение пользователя по идентификатору
                Данное API возвращает пользователя по идентификатору, использующего CyberBot
                ---
                tags:
                  - Пользователи
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
                          $ref: '#/definitions/User'
                  404:
                    description: Пользователь не найден
                    content:
                      application/json:
                        schema:
                          $ref: '#/definitions/Error'
            """
            user = await self.user_service.find_user_by_id(user_id)
            if user:
                return json.dumps(user.to_dict(), ensure_ascii=False)
            else:
                return not_found(f"Пользователь с ID {user_id} не найден")

        @self.web.route("/api/v1/users/<user_id>/recommendations", methods=['GET'])
        async def get_user_recommendations(user_id):
            page_num = int(request.args.get("page_num", 0))
            page_size = int(request.args.get("page_size", 50))
            recommendations = await self.advent_service.get_recommendation_page(user_id, page_num, page_size)
            return json.dumps([rec.to_dict() for rec in recommendations], ensure_ascii=False)

        @self.web.route("/api/public/advice/random", methods=['GET'])
        async def get_user_recommendation_random():
            """Получение случайной рекомендации
                Данное API возвращает случайную рекомендацию кибер-адвента
                ---
                tags:
                  - Рекомендации (публичное API)
                responses:
                  200:
                    description: Рекомендация
                    content:
                      application/json:
                        schema:
                          $ref: '#/definitions/Recommendation'
                  404:
                    description: Рекомендация не найдена
                    content:
                      application/json:
                        schema:
                          $ref: '#/definitions/Error'
            """
            random_num = random.randint(1, 30)
            recommendation = await self.advent_service.get_recommendation_info_by_id(random_num)
            if recommendation:
                return json.dumps(recommendation.to_dict(), ensure_ascii=False)
            else:
                return not_found(f"Рекомендация не найдена")

        @self.web.route("/api/public/advice/today", methods=['GET'])
        async def get_user_recommendation_today():
            """Получение сегодняшней рекомендации
                Данное API возвращает рекомендацию кибер-адвента в соответствии с номером сегодняшнего дня в месяце
                ---
                tags:
                  - Рекомендации (публичное API)
                responses:
                  200:
                    description: Рекомендация
                    content:
                      application/json:
                        schema:
                          $ref: '#/definitions/Recommendation'
                  404:
                    description: Рекомендация не найдена
                    content:
                      application/json:
                        schema:
                          $ref: '#/definitions/Error'
            """
            today_day = datetime.datetime.now().day
            recommendations_count = await self.advent_service.get_recommendation_count()
            if today_day > recommendations_count:
                today_day = 1

            recommendation = await self.advent_service.get_recommendation_info_by_id(today_day)
            if recommendation:
                return json.dumps(recommendation.to_dict(), ensure_ascii=False)
            else:
                return not_found(f"Рекомендация не найдена")


        def not_found(message):
            error = { 'error' : message }
            response = make_response(json.dumps(error, ensure_ascii=False))
            response.status_code = 404
            return response

    def run(self):
        print(f"Web-server starting on port {self.port}")
        self.web.run(host='0.0.0.0', port=self.port)

    def run_background(self):
        threading.Thread(target=self.run, daemon=True).start()
