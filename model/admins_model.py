from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Admins(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    jwt_token = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f'<User {self.username}>'