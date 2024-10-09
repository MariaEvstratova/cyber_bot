import json
import threading
import random
import datetime

from flask import Flask, request, jsonify, make_response, render_template

from service.cyber_advent_service import CyberAdventService
from service.user_service import UserService

class RestController:

    def __init__(self, port, user_service: UserService, advent_service: CyberAdventService):
        self.port = port
        self.user_service = user_service
        self.advent_service = advent_service
        self.web = Flask(__name__)
        self.web.config['JSON_AS_ASCII'] = False
        self.setup_routes()


    def setup_routes(self):
        @self.web.route("/health")
        def health():
            return '{"Up!"}'

        @self.web.route("/")
        def index():
            return render_template("index.html")

        @self.web.route("/api/v1/users", methods=['GET'])
        def get_users():
            page_num = int(request.args.get("page_num", 0))
            page_size = int(request.args.get("page_size", 25))
            users = self.user_service.get_users(page_num, page_size)
            return json.dumps([user.to_dict() for user in users], ensure_ascii=False)

        @self.web.route("/api/v1/users/<user_id>", methods=['GET'])
        async def get_user(user_id: int):
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
            random_num = random.randint(1, 30)
            recommendation = await self.advent_service.get_recommendation_info_by_id(random_num)
            if recommendation:
                return json.dumps(recommendation.to_dict(), ensure_ascii=False)
            else:
                return not_found(f"Рекомендация не найдена")

        @self.web.route("/api/public/advice/today", methods=['GET'])
        async def get_user_recommendation_today():
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
