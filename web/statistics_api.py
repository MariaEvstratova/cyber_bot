import json

from flask import Blueprint
from service.statistics_service import StatisticsService


class StatisticsApi:

    def __init__(self, statistics_service: StatisticsService):
        self.statistics_api = Blueprint('statistics_api', __name__)
        self.statistics_service = statistics_service
        self.setup_routes()

    def register_api(self, web):
        web.register_blueprint(self.statistics_api)

    def setup_routes(self):

        @self.statistics_api.route("/api/v1/statistics", methods=['GET'])
        async def get_statistics():
            statistics = await self.statistics_service.get_statistics()
            return json.dumps(statistics.to_dict(), ensure_ascii=False)
