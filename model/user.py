from datetime import datetime
from data.users import User

class UserModel:

    def __init__(self, user_id: int = None, name: str = None, registration_day: datetime = None,
                 age_group: str = None, schedule: str = None, sex: str = None, telegram_username: str = None,
                 telegram_id: str = None, time: str = None, timezone: str = None, period: str = None,
                 advent_start: datetime = None):
        self.user_id = user_id
        self.name = name
        self.registration_day = registration_day
        self.age_group = age_group
        self.schedule = schedule
        self.sex = sex
        self.telegram_username = telegram_username
        self.telegram_id = telegram_id
        self.time = time
        self.timezone = timezone
        self.period = period
        self.advent_start = advent_start


    def to_dict(self):
        return {
            'id': self.user_id,
            'name': self.name,
            'registration_day': self.registration_day.isoformat() if self.registration_day else None,
            'age_group': self.age_group,
            'schedule': self.schedule,
            'sex': self.sex,
            'telegram_username': '*****',
            'telegram_id': '*****',
            'time': self.time,
            'timezone': self.timezone,
            'period': self.period,
            'advent_start': self.advent_start.isoformat() if self.advent_start else None,
        }


def user_from_dict(user_data):
    return UserModel(
        name=user_data.get('name', None),
        age_group=user_data.get('age_group', None),
        registration_day=datetime.fromisoformat(user_data['registration_day']) if user_data.get('registration_day', None) else None,
        schedule=user_data.get('schedule', None),
        sex=user_data.get('sex', None),
        time=user_data.get('time', None),
        timezone=user_data.get('timezone', None),
        period=user_data.get('period', None),
        advent_start=datetime.fromisoformat(user_data['advent_start']) if user_data.get('advent_start', None) else None,
        telegram_username=user_data.get('telegram_username', None),
        telegram_id=user_data.get('telegram_id', None),
    )


def db_user_to_model(db_user: User) -> UserModel:
    return UserModel(db_user.User_ID, db_user.Name, db_user.Registration_Day, db_user.Age_Group,
                     db_user.Schedule, db_user.Sex, db_user.UserName, db_user.Chat_Id,
                     db_user.Time, db_user.Timezone, db_user.Period, db_user.Advent_Start)
