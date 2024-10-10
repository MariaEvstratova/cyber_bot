from typing import Optional

from data import db_session
from data.admins import Admins
from model.admins import AdminsModel, db_admin_to_model
from werkzeug.security import generate_password_hash, check_password_hash


class AdminsService:

    # Добавление администратора
    def create_admin(self, admins_model: AdminsModel) -> AdminsModel:
        admin = Admins()
        admin.name = admins_model.name
        admin.email = admins_model.email
        admin.hashed_password = self.hash_password(admins_model.password)

        db_sess = db_session.create_session()
        db_sess.add(admin)
        db_sess.commit()
        db_sess.close()

        return admins_model

    # Получить администратора по id
    def find_user_by_id(self, user_id: int) -> Optional[AdminsModel]:
        db_sess = db_session.create_session()
        db_admin = db_sess.query(Admins).filter(Admins.id == user_id).first()
        db_sess.close()
        if db_admin:
            return db_admin_to_model(db_admin)
        return None

    # Получить администратора по email
    def find_user_by_email(self, email: str) -> Optional[AdminsModel]:
        db_sess = db_session.create_session()
        db_admin = db_sess.query(Admins).filter(Admins.email == email).first()
        db_sess.close()
        if db_admin:
            return db_admin_to_model(db_admin)
        return None

    # Верификация пользователя
    def check_user_credentials(self, email: str, password: str) -> bool:
        user = self.find_user_by_email(email)
        if not user:
            return False
        return check_password_hash(user.password, password)

    # Зашифровать пароль
    def hash_password(self, password: str) -> str:
        return generate_password_hash(password)
