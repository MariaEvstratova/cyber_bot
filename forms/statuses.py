import datetime

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, TimeField
from wtforms import BooleanField, SubmitField
from wtforms.validators import DataRequired


class UserForm(FlaskForm):
    id = TextAreaField("Идентификатор пользователя")
    submit = SubmitField('Получить список рекомендаций')

class StatusForm(FlaskForm):
    header = TextAreaField("Заголовок")
    date_posted = DateField('Дата', format='%Y-%m-%d')
    time_posted = TimeField('Время', format='%H:%M')
    public = BooleanField('Опубликовать')
    submit = SubmitField('Применить')