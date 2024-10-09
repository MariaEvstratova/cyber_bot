from typing import Optional

from sqlalchemy import func, join

from data import db_session
from data.admins import Admins
from model.admins import AdminsModel, db_admin_to_model
from werkzeug.security import generate_password_hash, check_password_hash


class AdminsService:

    # Добавление админа
    def create_admin(self, admins_model: AdminsModel) -> AdminsModel:
        admin = Admins()
        admin.name = admins_model.name
        admin.email = admins_model.email
        admin.hashed_password = admins_model.hashed_password

        db_sess = db_session.create_session()
        db_sess.add(admin)
        db_sess.commit()
        db_sess.close()

        return admins_model

    # Получить пользователя по id
    def find_user_by_id(self, user_id: int) -> Optional[AdminsModel]:
        db_sess = db_session.create_session()
        db_admin = db_sess.query(Admins).filter(Admins.id == user_id).first()
        db_sess.close()
        if db_admin:
            return db_admin_to_model(db_admin)
        return None

    # Получить пользователя по email
    def find_user_by_email(self, email: str) -> Optional[AdminsModel]:
        db_sess = db_session.create_session()
        db_admin = db_sess.query(Admins).filter(Admins.email == email).first()
        db_sess.close()
        if db_admin:
            return db_admin_to_model(db_admin)
        return None

    #Зашифровать пароль
    def set_password(self, password: str):
        hashed_password = generate_password_hash(password)
        return hashed_password
