from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, PasswordField, BooleanField, MultipleFileField
from wtforms.validators import DataRequired, Email



class PostForm(FlaskForm):
    title = StringField("Название: ", validators=[DataRequired()])
    content = TextAreaField("Содержание: ", validators=[DataRequired()])
    upload = MultipleFileField('Изображения добавлены')
    checkbox = BooleanField("Удалить прежние фото к этому посту?")
    submit = SubmitField("Опубликовать")
    

class ComentForm(FlaskForm):
    coment_content = TextAreaField("Добавить комментарий: ", validators=[DataRequired()])
    submit = SubmitField("Опубликовать")

class RegistrForm(FlaskForm):
    user_name = StringField("Ваше имя* ", validators=[DataRequired()])
    email = StringField("Email* ", validators=[Email()])
    psw = PasswordField("Пароль* ", validators=[DataRequired()])
    psw1 = PasswordField("Повторите пароль* ", validators=[DataRequired()])
    submit = SubmitField("Регистрация")

class LoginForm(FlaskForm):
    email = StringField("Email ", validators=[Email()])
    psw = PasswordField("Пароль ", validators=[DataRequired()])
    remember = BooleanField("Запомнить")
    submit = SubmitField("Войти")
