import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from data.users import User
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .db_session import SqlAlchemyBase


class Status_recommendation(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'Status_recommendations'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    chat_id = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("Users.User_ID")
                                )
    user = orm.relationship('User')
    send_time = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    message_id = sqlalchemy.Column(sqlalchemy.String, nullable=False, default='0')
    rec_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, default='0')
    rec_status = sqlalchemy.Column(sqlalchemy.String, nullable=False, default='0')
