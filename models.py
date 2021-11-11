from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class SaveMixin(object):
    pass

    def save(self):
        db.session.add(self)
        db.session.commit()


class Post(db.Model, SaveMixin):
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text(), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    views = db.Column(db.Integer(), nullable=False, default=0)
    likes = db.Column(db.Integer(), nullable=False, default=0)
    created_on = db.Column(db.DateTime(), default=datetime.utcnow)
    updated_on = db.Column(
        db.DateTime(), default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'{self.id}'


class Coment(db.Model, SaveMixin):
    id = db.Column(db.Integer(), primary_key=True)
    user_name = db.Column(db.String(255), nullable=False)
    coment_content = db.Column(db.String(255))
    created_on = db.Column(db.DateTime(), default=datetime.utcnow)
    post_id = db.Column(db.Integer(), nullable=False)

    def __repr__(self):
        return f'{self.id}'


class Users(db.Model, UserMixin, SaveMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(500), nullable=False)
    email = db.Column(db.String(50), unique=True)
    psw = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='user')
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"{self.email}"


class Favorites(db.Model, SaveMixin):
    id = db.Column(db.Integer(), primary_key=True)
    user_email = db.Column(db.String(255), nullable=False)
    post_id = db.Column(db.Integer(), nullable=False)


class Link_img(db.Model, SaveMixin):
    id = db.Column(db.Integer(), primary_key=True)
    link = db.Column(db.String(255), nullable=False)
    post_id = db.Column(db.Integer(), nullable=False)

    def __repr__(self):
        return f'{self.id}'
