import datetime
import sqlalchemy
from flask_login import UserMixin
# from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .db_session import SqlAlchemyBase


class Recommendation(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'Recommendations'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    recommendation = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    media = sqlalchemy.Column(sqlalchemy.String, nullable=True)