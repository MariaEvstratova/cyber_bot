import os
import logging

from data import db_session
from service.cyber_advent_service import CyberAdventService
from service.statistics_service import StatisticsService
from service.user_service import UserService
from service.admins_service import AdminsService
from service.statuses_service import StatusRecommendationService
from view.telegram_bot import TelegramBot
from web.rest_controller import RestController

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        self.web_port = int(os.environ.get("PORT", 5000))
        self.web_public_url = os.environ.get("PUBLIC_URL", None)
        self.secret_key = os.environ.get("SECRET_KEY", "changeit")
        self.bot_token = os.environ.get('API_BOT_TOKEN', '6522784356:AAHB7lKSBukJDq-Tq3SAB9mxql95Cn9Dutg')
        self.bot_name = os.environ.get('BOT_NAME', 'Cyber_safeness_bot')
        self.database_url = os.environ.get('DB_URL')


def main():
    # Инициализация конфигурации
    config = Config()
    # Инициализация базы данных
    db_session.global_init(config.database_url)

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
    RestController(config.web_port, config.web_public_url, config.secret_key, user_service, advent_service, admins_service, statistics_service,
                   status_recommendation_service).run_background()
    # Запуск telegram бота
    TelegramBot(config.bot_token, config.bot_name, user_service, advent_service).run()


if __name__ == '__main__':
    main()
