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

    # Получить описание статуса рекомендации по ID
    async def get_status_recommendation_info_by_id(self, user_id: int, rec_id: int) -> Optional[RecommendationStatusModel]:
        db_sess = db_session.create_session()
        db_stat = db_sess.query(Status_recommendation).filter(Status_recommendation.user_id == user_id, Status_recommendation.rec_id == rec_id).first()
        db_sess.close()
        if db_stat:
            return db_recommendation_status_to_model(db_stat)
        return None

    # Обновление статуса рекомендации
    def update_status_recommendation(self, stat_model: RecommendationStatusModel) -> RecommendationStatusModel:
        db_sess = db_session.create_session()
        db_stat = (db_sess.query(Status_recommendation)
                   .filter(Status_recommendation.user_id == stat_model.user_id, Status_recommendation.rec_id == stat_model.rec_id)
                   .first())
        if db_stat:
            db_stat.rec_id = db_stat.rec_id
            db_stat.user_id = db_stat.user_id
            db_stat.telegram_id = db_stat.telegram_id
            db_stat.telegram_message_id = db_stat.telegram_message_id
            db_stat.rec_status = db_stat.rec_status
            db_stat.send_time = stat_model.send_time
            db_stat.rec_status_public = stat_model.rec_status_public
            db_stat.rec_header = stat_model.rec_header
            db_sess.add(db_stat)
            db_sess.commit()
        db_sess.close()

        return stat_model

    async def delete_status(self, stat_model: RecommendationStatusModel):
        db_sess = db_session.create_session()
        db_rec = db_sess.query(Status_recommendation).filter(Status_recommendation.user_id == stat_model.user_id, Status_recommendation.rec_id == stat_model.rec_id).first()
        db_sess.delete(db_rec)
        db_sess.commit()
        db_sess.close()
        return None