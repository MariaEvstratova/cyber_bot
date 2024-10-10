from datetime import datetime

from data.status_recommendation import Status_recommendation


class RecommendationStatusModel:
    def __init__(self, rec_id: int = None, user_id: int = None, send_time: datetime = None,
                 telegram_id: str = None, telegram_message_id: str = None, rec_status: str = None, rec_status_public: int = None):
        self.rec_id = rec_id
        self.user_id = user_id
        self.send_time = send_time
        self.telegram_id = telegram_id
        self.telegram_message_id = telegram_message_id
        self.rec_status = rec_status
        self.rec_status_public = rec_status_public


def db_recommendation_status_to_model(db_recommendation_status: Status_recommendation) -> RecommendationStatusModel:
    return RecommendationStatusModel(db_recommendation_status.rec_id, db_recommendation_status.user_id,
                                     db_recommendation_status.send_time, db_recommendation_status.chat_id,
                                     db_recommendation_status.message_id, db_recommendation_status.rec_status, db_recommendation_status.rec_status_public)
