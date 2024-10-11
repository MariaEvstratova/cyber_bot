from datetime import datetime

from data import db_session
from service.cyber_advent_service import CyberAdventService
from service.statistics_service import StatisticsService
from service.statuses_service import StatusRecommendationService
from service.user_service import UserService
from service.admins_service import AdminsService
from web.rest_controller import RestController

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

@pytest.fixture
def client():
    db_session.global_init(db_local_path="../db/data_base.db")
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
    app = RestController(5000, None, "changeit", user_service, advent_service, admins_service,
                   statistics_service,
                   status_recommendation_service)

    # Тестовый клиент для WEB API
    with app.web.test_client() as client:
        yield client

def test_random_advice(client):
    response = client.get('/api/public/advice/random')
    assert response.status_code == 200
    assert response.json.get("id") is not None
    assert response.json.get("description") is not None

def test_today_advice(client):
    response = client.get('/api/public/advice/today')
    current_day = datetime.now().day
    assert response.status_code == 200
    assert response.json.get("id") == current_day
    assert response.json.get("description") is not None

