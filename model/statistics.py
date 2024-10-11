class StatisticsModel:

    def __init__(self,
                 users_count: int,
                 completions_count: int = None,
                 subscribers_count: int = None,
                 unsubscribers_count: int = None,
                 sent_recommendations_count: int = None,
                 recommendations_count: int = None,
                 ):
        self.users_count = users_count
        self.completions_count = completions_count
        self.subscribers_count = subscribers_count
        self.unsubscribers_count = unsubscribers_count
        self.sent_recommendations_count = sent_recommendations_count
        self.recommendations_count = recommendations_count

    def to_dict(self):
        return {
            'users_count': self.users_count,
            'completions_count': self.completions_count,
            'subscribers_count': self.subscribers_count,
            'unsubscribers_count': self.unsubscribers_count,
            'sent_recommendations_count': self.sent_recommendations_count,
            'recommendations_count': self.recommendations_count,
        }

