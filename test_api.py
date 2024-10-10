import json
from datetime import datetime

from requests import get, post, delete

from data import db_session
from data.recommendations import Recommendation
from service.cyber_advent_service import CyberAdventService
from service.statistics_service import StatisticsService
from service.user_service import UserService
from service.admins_service import AdminsService


class Test_api:

    def test_api_advice_today(self):
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
        dict_rec_today = {'id': db_rec.id, 'description': db_rec.text}
        today_api = get('http://localhost:5000/api/public/advice/today').json()
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
        random_api_1 = get('http://localhost:5000/api/public/advice/random').json()
        random_api_2 = get('http://localhost:5000/api/public/advice/random').json()
        recommendation = db_sess.query(Recommendation).filter(Recommendation.recommendation == random_api_1.description).first()
        if random_api_1 <= count_of_recs and recommendation and random_api_1 != random_api_2:
            print('OK')
        else:
            print('ERROR')


def main():
    db_session.global_init("db/data_base.db")
    testing = Test_api()
    testing.test_api_advice_today()
    testing.test_api_advice_random()

main()
