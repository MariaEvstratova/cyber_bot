from datetime import datetime


class SentRecommendationModel:
    def __init__(self, rec_id: int, rec_status: str, text: str, send_time: datetime = None, public_status: int = None, header: str = None):
        self.rec_id = rec_id
        self.send_time = send_time
        self.rec_status = rec_status
        self.text = text
        self.public_status = public_status
        self.header = header


    def to_dict(self):
        return {
            'rec_id': self.rec_id,
            'rec_status': self.rec_status,
            'send_time': self.send_time.isoformat(),
            'public_status': self.public_status,
            'header': self.header,
            'text': self.text,
        }
