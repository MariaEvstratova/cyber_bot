# from datetime import datetime
#
# from requests import get, post, delete
#
# from service.cyber_advent_service import CyberAdventService
# from service.statistics_service import StatisticsService
# from service.user_service import UserService
# from service.admins_service import AdminsService
#
#
# def test_api_advice_random():
#      print(get('http://localhost:5000/api/jobs/1').json())
#      print(get('http://localhost:5000/api/jobs/15').json())
#      print(get('http://localhost:5000/api/jobs/q').json())
#
#
# def test_api_advice_today(advent_service):
#     today_day = datetime.datetime.now().day
#     recommendations_count = await advent_service.get_recommendation_count()
#     if today_day > recommendations_count:
#         today_day = 1
#
#     print(get('http://localhost:5000/api/public/advice/today').json())
#     print(get('http://localhost:5000/api/jobs/15').json())
#     print(get('http://localhost:5000/api/jobs/q').json())
#
#
# def test_api_advice_random():
#     print(get('http://localhost:5000/api/jobs/1').json())
#     print(get('http://localhost:5000/api/jobs/15').json())
#     print(get('http://localhost:5000/api/jobs/q').json())
# # print(post('http://localhost:8080/api/news',
# #            json={'title': 'Заголовок'}).json())
# #
# # print(post('http://localhost:8080/api/news',
# #            json={'title': 'Заголовок',
# #                  'content': 'Текст новости',
# #                  'user_id': 1,
# #                  'is_private': False}).json())
# # print(delete('http://localhost:8080/api/news/6').json())
#
#
#
#
# # # print(get('http://localhost:8080/api/v2/news').json())
# # print(delete('http://localhost:8080/api/v2/news/14').json())
# # print(post('http://localhost:8080/api/v2/news',
# #            json={'title': 'Заголовок',
# #                  'content': 'Текст этой новости',
# #                  'user_id': 1,
# #                  'is_private': False}).json())
# def main():
#     user_service = UserService
#     advent_service = CyberAdventService
#     admins_service = AdminsService
#     statistics_service = StatisticsService
#     test_api_advice_today()
#     test_api_advice_today(advent_service)
