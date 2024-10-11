from model.statistics import StatisticsModel
from service.cyber_advent_service import CyberAdventService
from service.user_service import UserService


class StatisticsService:

    def __init__(self, user_service: UserService, advent_service: CyberAdventService):
        self.user_service = user_service
        self.advent_service = advent_service

    # Получение статистики
    async def get_statistics(self) -> StatisticsModel:
        # Количество участников
        users_count = self.user_service.get_users_count()

        # Количество участников, завершивших адвент
        completions_count = await self.advent_service.get_users_count_with_advent_completed()

        # Количество подписавшихся, т.е. начавших адвент
        subscribers_count = self.user_service.get_users_with_advent_count()

        # Количество отписавшихся, т.е. прекративших адвент (TODO: не знаем таких)
        unsubscribers_count = 0

        # Общее количество отправленных рекомендаций
        sent_recommendations_count = await self.advent_service.sent_all_recommendation_count()

        # Общее количество рекомендаций
        recommendations_count = await self.advent_service.get_recommendation_count()

        return StatisticsModel(
            users_count=users_count,
            completions_count=completions_count,
            subscribers_count=subscribers_count,
            unsubscribers_count=unsubscribers_count,
            sent_recommendations_count=sent_recommendations_count,
            recommendations_count=recommendations_count
        )
