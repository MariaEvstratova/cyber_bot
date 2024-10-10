from datetime import datetime


class SentRecommendationModel:
    def __init__(self, rec_id: int, rec_status: str, text: str, send_time: datetime = None):
        self.rec_id = rec_id
        self.send_time = send_time
        self.rec_status = rec_status
        self.text = text


    def to_dict(self):
        return {
            'rec_id': self.rec_id,
            'rec_status': self.rec_status,
            'send_time': self.send_time.isoformat(),
            'text': self.text,
        }
