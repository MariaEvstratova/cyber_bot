import json
from datetime import datetime

from requests import get, post, delete

from data import db_session
from data.recommendations import Recommendation
from service.cyber_advent_service import CyberAdventService
from service.statistics_service import StatisticsService
from service.statuses_service import StatusRecommendationService
from service.user_service import UserService
from service.admins_service import AdminsService
from web.rest_controller import RestController


class Test_api:

    def test_api_advice_today(self):
        # Сервис для работы с пользователями
        user_service = UserService()
        # Сервис для работы с Cyber-адвентом
        advent_service = CyberAdventService()
        # Инициализируем сервис
        advent_service.init_recommendations()
        # Сервис для работы с администраторами
        admins_service = AdminsService()
        # Сервис для сбора статистики
        statistics_service = StatisticsService(user_service, advent_service)
        # Сервис для работы со статусами рекомендаций
        status_recommendation_service = StatusRecommendationService()

        # Запуск REST-контроллера в фоне
        RestController(5003, "changeit", user_service, advent_service, admins_service,
                       statistics_service,
                       status_recommendation_service).run_background()


        today_day = datetime.now().day
        db_sess = db_session.create_session()
        db_recs = db_sess.query(Recommendation).all()
        db_sess.close()
        all_recs = []
        for rec in db_recs:
            all_recs.append(rec)
        db_sess.close()
        recommendations_count = len(all_recs)
        if today_day > recommendations_count:
            today_day = 1
        db_sess = db_session.create_session()
        db_rec = db_sess.query(Recommendation).filter(Recommendation.id == today_day).first()
        db_sess.close()
        dict_rec_today = {'id': db_rec.id, 'description': db_rec.recommendation}


        today_api = get('http://localhost:5003/api/public/advice/today').json()
        if dict_rec_today == today_api:
            print('OK')
        else:
            print('ERROR')

    def test_api_advice_random(self):
        db_sess = db_session.create_session()
        db_rec = db_sess.query(Recommendation).all()
        count_of_recs = 0
        for rec in db_rec:
            count_of_recs += 1
        db_sess.close()
        random_api_1 = get('http://localhost:5003/api/public/advice/random').json()
        random_api_2 = get('http://localhost:5003/api/public/advice/random').json()
        description = random_api_1["description"]
        recommendation = db_sess.query(Recommendation).filter(Recommendation.recommendation == description).first()
        if len(random_api_1) <= count_of_recs and recommendation and random_api_1 != random_api_2:
            print('OK')
        else:
            print('ERROR')


def main():
    db_session.global_init(db_local_path="../db/data_base.db")
    testing = Test_api()
    testing.test_api_advice_today()
    testing.test_api_advice_random()

main()
