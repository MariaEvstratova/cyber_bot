from data.recommendations import Recommendation


class RecommendationModel:
    def __init__(self, num: str, text: str, media: str):
        self.num = num
        self.text = text
        self.media = media

    def to_dict(self):
        return {
            'id': self.num,
            'description': self.text,
        }


def db_recommendation_to_model(db_recommendation: Recommendation) -> RecommendationModel:
    return RecommendationModel(db_recommendation.id, db_recommendation.recommendation, db_recommendation.media)
