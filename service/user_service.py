from datetime import datetime
from typing import Optional

from data import db_session
from data.users import User
from model.user import UserModel, db_user_to_model


class UserService:

    # Добавление пользователя
    def create_user(self, user_model: UserModel) -> UserModel:
        user = User()
        user.Name = user_model.name
        user.Age_Group = user_model.age_group
        user.Schedule = user_model.schedule
        user.Sex = user_model.sex
        user.UserName = user_model.telegram_username
        user.Chat_Id = user_model.telegram_id
        user.Time = user_model.time
        user.Timezone = user_model.timezone
        user.Period = user_model.period

        db_sess = db_session.create_session()
        db_sess.add(user)
        db_sess.commit()
        user_model.user_id = user.User_ID
        db_sess.close()

        return user_model


    # Обновление пользователя
    def update_user(self, user_id: int, user_model: UserModel) -> UserModel:
        db_sess = db_session.create_session()
        db_user = db_sess.query(User).filter(User.User_ID == user_id).first()
        if user_model.name:
            db_user.Name = user_model.name
        if user_model.age_group:
            db_user.Age_Group = user_model.age_group
        if user_model.schedule:
            db_user.Schedule = user_model.schedule
        if user_model.sex:
            db_user.Sex = user_model.sex
        if user_model.telegram_username:
            db_user.UserName = user_model.telegram_username
        if user_model.telegram_id:
            db_user.Chat_Id = user_model.telegram_id
        if user_model.time:
            db_user.Time = user_model.time
        if user_model.timezone:
            db_user.Timezone = user_model.timezone
        if user_model.period:
            db_user.Period = user_model.period

        db_sess.add(db_user)
        db_sess.commit()
        user_model = db_user_to_model(db_user)
        db_sess.close()

        return user_model


    # Получить пользователя по идентификатору пользователя
    async def find_user_by_id(self, user_id: int) -> Optional[UserModel]:
        db_sess = db_session.create_session()
        db_user = db_sess.query(User).filter(User.User_ID == user_id).first()
        db_sess.close()
        if db_user:
            return db_user_to_model(db_user)
        return None


    # Получить пользователя по его идентификатору в Telegram
    async def find_user_by_telegram_id(self, chat_id: str) -> Optional[UserModel]:
        db_sess = db_session.create_session()
        db_user = db_sess.query(User).filter(User.Chat_Id == str(chat_id)).first()
        db_sess.close()
        if db_user:
            return db_user_to_model(db_user)
        return None


    # Получить список пользователей
    def get_users(self, page_num: int = 0, page_size: int = 25) -> list[UserModel]:
        db_sess = db_session.create_session()
        db_users = (db_sess.query(User)
                    .order_by(User.User_ID.asc())
                    .offset(page_num * page_size)
                    .limit(page_size).all())
        result = list()
        for user in db_users:
            result.append(db_user_to_model(user))
        db_sess.close()
        return result


    # Получить количество пользователей
    def get_users_count(self) -> int:
        db_sess = db_session.create_session()
        users_count = (db_sess.query(User).count())
        db_sess.close()
        return users_count


    # Получить количество пользователей, запустивших адвент
    def get_users_with_advent_count(self) -> int:
        db_sess = db_session.create_session()
        users_count = (db_sess.query(User).filter(User.Advent_Start != None).count())
        db_sess.close()
        return users_count


    # Получить пользователей по списку id
    async def get_users_by_ids(self, user_ids: list[int]) -> list[UserModel]:
        db_sess = db_session.create_session()
        db_users = db_sess.query(User).filter(User.User_ID.in_(user_ids)).all()
        result = list()
        for user in db_users:
            result.append(db_user_to_model(user))
        db_sess.close()
        return result


    # Запуск адвента
    async def start_advent(self, user_id: int):
        db_sess = db_session.create_session()
        db_user = db_sess.query(User).filter(User.User_ID == user_id).first()
        db_sess.close()

        if db_user is None:
            return
        if not (db_user.Advent_Start is None):
            return

        db_user.Advent_Start = datetime.now()
        db_sess = db_session.create_session()
        db_sess.add(db_user)
        db_sess.commit()
        db_sess.close()


    # Получить список пользователей, у которых запущен адвент
    async def get_users_with_advent(self) -> list[UserModel]:
        db_sess = db_session.create_session()
        users = (db_sess.query(User).
                 filter(User.Advent_Start != None).
                 distinct())
        result = list()
        for user in users:
            result.append(db_user_to_model(user))
        db_sess.close()
        return result
