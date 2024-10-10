# import json
# from datetime import datetime
#
# from requests import get, post, delete
#
# from data import db_session
# from data.recommendations import Recommendation
# from service.cyber_advent_service import CyberAdventService
# from service.statistics_service import StatisticsService
# from service.user_service import UserService
# from service.admins_service import AdminsService
#
# #
# # def test_api_advice_random():
# #     pass
# #     # print(get('http://localhost:5000/api/jobs/1').json())
# #     # print(get('http://localhost:5000/api/jobs/15').json())
# #     # print(get('http://localhost:5000/api/jobs/q').json())
#
# class Test_api:
#
#     def test_api_advice_today(self):
#         today_day = datetime.now().day
#         db_sess = db_session.create_session()
#         db_recs = db_sess.query(Recommendation).all()
#         db_sess.close()
#         all_recs = []
#         for rec in db_recs:
#             all_recs.append(rec)
#         db_sess.close()
#         recommendations_count = len(all_recs)
#         if today_day > recommendations_count:
#             today_day = 1
#         db_sess = db_session.create_session()
#         db_rec = db_sess.query(Recommendation).filter(Recommendation.id == today_day).first()
#         db_sess.close()
#         dict_rec = {'id': db_rec.id, 'description': db_rec.text}
#         print(dict_rec)
#         #
#         # print(get('http://localhost:5000/api/public/advice/today').json())
#             # print(get('http://localhost:5000/api/jobs/15').json())
#         # print(get('http://localhost:5000/api/jobs/q').json())
#
#
# def main():
#     # test_api_advice_today()
#     db_session.global_init("db/data_base.db")
#     testing = Test_api()
#     testing.test_api_advice_today()
#
# main()
