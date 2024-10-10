from typing import Optional

from sqlalchemy import func, join

from data import db_session
from data.recommendations import Recommendation
from data.status_recommendation import Status_recommendation
from model.recommendation import RecommendationModel, db_recommendation_to_model
from model.sent_recommendation import SentRecommendationModel
from model.status_recommendation import db_recommendation_status_to_model, RecommendationStatusModel
from service.user_service import UserService
from service.cyber_advent_service import CyberAdventService

REC_STATUS_INIT, REC_STATUS_DONE, REC_STATUS_SKIP = '0', '1', '2'


class StatusRecommendationService:

    async def get_text_of_all_statuses_recommendations(self):
        db_sess = db_session.create_session()
        db_stats = db_sess.query(Status_recommendation).all()
        db_sess.close()
        all_recs_statuses = []
        for stat in db_stats:
            id = stat.rec_id
            advent_service = CyberAdventService()
            rec = await advent_service.get_recommendation_info_by_id(id)
            all_recs_statuses.append(rec.text)

        return all_recs_statuses

    async def get_all_statuses_recommendations(self):
        db_sess = db_session.create_session()
        db_stats = db_sess.query(Status_recommendation).all()
        db_sess.close()
        return db_stats
