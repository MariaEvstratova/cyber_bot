from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class RecsForm(FlaskForm):
    recommendation = TextAreaField("Рекомендация")
    media = TextAreaField("URL медиа контента")
    submit = SubmitField('Применить')