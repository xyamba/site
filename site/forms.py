import re

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField, TextAreaField, DateTimeField
from wtforms.validators import DataRequired, EqualTo, Length, Optional, ValidationError

_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class SimpleEmail:
    """Проверка email без пакета email_validator (часто не ставят на Windows)."""

    def __init__(self, message="Введите корректный email"):
        self.message = message

    def __call__(self, form, field):
        value = (field.data or "").strip()
        if not _EMAIL_RE.match(value):
            raise ValidationError(self.message)


class RegistrationForm(FlaskForm):
    name = StringField('Имя', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[DataRequired(), SimpleEmail()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Роль', choices=[('client', 'Клиент'), ('master', 'Тату-мастер')], validators=[DataRequired()])
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), SimpleEmail()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class SketchFilterForm(FlaskForm):
    style = SelectField('Стиль', choices=[('', 'Любой'), ('традишнл', 'Традишнл'), ('ньюскул', 'Ньюскул'), ('графика', 'Графика'), ('реализм', 'Реализм'), ('дотворк', 'Дотворк'), ('акварель', 'Акварель')], validators=[Optional()])
    color_type = SelectField('Цвет', choices=[('', 'Любой'), ('цветной', 'Цветной'), ('черно-белый', 'Черно-белый')], validators=[Optional()])
    size = SelectField('Размер', choices=[('', 'Любой'), ('небольшой', 'Небольшой'), ('средний', 'Средний'), ('большой', 'Большой')], validators=[Optional()])
    min_price = FloatField('Цена от', validators=[Optional()])
    max_price = FloatField('Цена до', validators=[Optional()])
    master_name = StringField('Имя мастера', validators=[Optional()])
    search = StringField('Поиск', validators=[Optional()])
    submit = SubmitField('Применить фильтр')

class SketchUploadForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired()])
    description = TextAreaField('Описание', validators=[Optional()])
    style = SelectField('Стиль', choices=[('традишнл', 'Традишнл'), ('ньюскул', 'Ньюскул'), ('графика', 'Графика'), ('реализм', 'Реализм'), ('дотворк', 'Дотворк'), ('акварель', 'Акварель')], validators=[DataRequired()])
    color_type = SelectField('Цвет', choices=[('цветной', 'Цветной'), ('черно-белый', 'Черно-белый')], validators=[DataRequired()])
    size = SelectField('Размер', choices=[('небольшой', 'Небольшой'), ('средний', 'Средний'), ('большой', 'Большой')], validators=[DataRequired()])
    price = FloatField('Цена (руб)', validators=[DataRequired()])
    image = FileField('Изображение', validators=[DataRequired(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'])])
    tags = StringField('Теги (через запятую)', validators=[Optional()])
    submit = SubmitField('Загрузить эскиз')

class TimeSlotForm(FlaskForm):
    start_time = DateTimeField('Начало (ГГГГ-ММ-ДД ЧЧ:ММ)', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    end_time = DateTimeField('Конец (ГГГГ-ММ-ДД ЧЧ:ММ)', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    submit = SubmitField('Добавить слот')

class AppointmentForm(FlaskForm):
    master_id = SelectField('Мастер', coerce=int, validators=[DataRequired()])
    slot_id = SelectField('Доступное время', coerce=int, validators=[DataRequired()])
    sketch_id = SelectField('Эскиз (необязательно)', coerce=int, validators=[Optional()])
    comment = TextAreaField('Комментарий')
    submit = SubmitField('Записаться')