import os
import glob
import shutil
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from forms import PostForm, ComentForm, RegistrForm, LoginForm
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


app = Flask(__name__)
app.config['SECRET_KEY'] = '12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 32

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(Users).get(user_id)


db = SQLAlchemy(app)


class Post(db.Model):
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


class Coment(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_name = db.Column(db.String(255), nullable=False)
    coment_content = db.Column(db.String(255))
    created_on = db.Column(db.DateTime(), default=datetime.utcnow)
    post_id = db.Column(db.Integer(), nullable=False)

    def __repr__(self):
        return f'{self.id}'


class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    user_name1 = db.Column(db.String(500), nullable=False)
    email = db.Column(db.String(50), unique=True)
    psw = db.Column(db.String(500), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"{self.email}"

class Favorites(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_email = db.Column(db.String(255), nullable=False)
    post_id = db.Column(db.Integer(), nullable=False)

    def __repr__(self):
        return f'{self.id}'


@app.route('/')
@app.route('/<int:post_id>', methods=['get', 'post'])
def main(post_id=None):
    if not post_id:
        return render_template('main.html', 
                                posts=Post.query.all(), 
                                autoriz=current_user.is_authenticated,
                                current_user = str(current_user),)
    else:
        post_dir = 'static/images'+ '/' + str(post_id)
        count_favorite = len(db.session.query(Favorites).filter(Favorites.post_id==post_id).all())
        user_favorite = db.session.query(Favorites).filter(Favorites.post_id==post_id,
                        Favorites.user_email==str(current_user)).all()
        if (os.path.exists(post_dir)):  # получение списка изображений для конкретного поста
            images = os.listdir(post_dir)
        else:
            images = []               
        try:                                        # увеличение счетчика просмотров
            viwe = Post.query.get(post_id)
            viwe.views = viwe.views + 1
            db.session.add(viwe)
            db.session.commit()
        except:
            db.session.rollback()
            flash("Ошибка добавления")

        form = ComentForm()
        if form.validate_on_submit():               # добавление комментария к посту
            try:
                com = Coment(user_name=current_user.user_name1,
                             coment_content=request.form['coment_content'],
                             post_id=post_id, )
                viwe = Post.query.get(post_id)
                viwe.views -= 2 
                db.session.add(viwe)
                db.session.add(com)
                db.session.commit()
            except:
                db.session.rollback()
                flash("Ошибка добавления")
            return redirect(f'/{post_id}')
        return render_template('post.html',
                               post=Post.query.filter(Post.id == post_id).first(),
                               post_id=post_id,
                               coments=Coment.query.filter(Coment.post_id == post_id).all(),
                               form=form,
                               directory=str(post_id),
                               images=images,
                               autoriz=current_user.is_authenticated,
                               count_favorite=count_favorite,
                               user_favorite=user_favorite,
                               current_user = str(current_user),)


@app.route('/favorites_posts')
def favorites_posts():
    posts =[]
    favorites_post_id = db.session.query(Favorites).filter(Favorites.user_email==str(current_user)).all()
    favorites_post_id = [i.post_id for i in favorites_post_id]
    for i in favorites_post_id:
        posts.append(Post.query.get(i))
    return render_template('main.html', 
                            posts=posts, 
                            autoriz=current_user.is_authenticated,
                            current_user = str(current_user),)

@app.route('/add-post/', methods=['get', 'post'])
def add_post():
    flag = False
    form = PostForm()
    if form.validate_on_submit():     # Добавление  поста в БД
        try:
            p = Post(title=request.form['title'],
                     content=request.form['content'],
                     author=str(current_user), )
            db.session.add(p)
            db.session.commit()
            flag = True
            flash("Статья добавлена")
        except:
            db.session.rollback()
            flash("Ошибка добавления")
            return redirect(url_for('add_post'))
        if flag:        # если данные в БД добавились, создаются каталоги и в них грузятся изображения для постов
            files = request.files.getlist('upload')
            if files[0]:
                post_dir = '/' + str(Post.query.order_by(Post.id.desc())[0])
                app.config['UPLOAD_PATH'] = 'static/images' + post_dir
                os.mkdir('static/images' + post_dir)
                for file in files:
                        filename = file.filename
                        file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
        return redirect(f'/{str(p.id)}')
    return render_template('add_post.html',
                           form=form,
                           edit_post=False,
                           autoriz=current_user.is_authenticated, )

@app.route("/edit/<string:post_id>", methods=['get', 'post'])
def edit(post_id):
    flag = False
    post_dir = '/' + str(Post.query.filter(Post.id == post_id).first().id)
    form = PostForm()
    form.title.data = Post.query.filter(Post.id == post_id).first().title
    form.content.data = Post.query.filter(Post.id == post_id).first().content
    if form.validate_on_submit():
        try:
            post = Post.query.get(post_id)
            post.title = request.form['title']
            post.content = request.form['content'] 
            db.session.add(post)
            db.session.commit()
            flag = True
            flash("Изменения внесены")
        except:
            db.session.rollback()
            flash("Ошибка добавления")
        if form.checkbox.data and os.path.exists('static/images' + post_dir):       # удаление прежних изобр. 
                    del_files = glob.glob('static/images' + post_dir + '/*')        # при редактировании поста
                    for f in del_files:
                        print(f)
                        os.remove(f)
        if flag:        # если пост обновился, создаются каталоги (если их нет) и в них грузятся изображения для постов
            files = request.files.getlist('upload')
            if files[0]:
                app.config['UPLOAD_PATH'] = 'static/images' + post_dir
                if not (os.path.exists('static/images' + post_dir)):
                    os.mkdir('static/images' + post_dir) 
                for file in files:
                    filename = file.filename
                    file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
        return redirect(f'/{post_id}')
    return render_template('add_post.html',
                           form=form,
                           post_id=str(post_id),
                           edit_post=True,
                           coments=Coment.query.filter(Coment.post_id == post_id).all(),
                           autoriz=current_user.is_authenticated, )


@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    flag = False
    favorit = db.session.query(Favorites).filter(Favorites.post_id==post_id).all()
    row_to_delete = db.session.query(Post).filter(Post.id==int(post_id)).one()
    coment_rows_delete = db.session.query(Coment).filter(Coment.post_id==post_id).all()
    try:
        for i in coment_rows_delete:
            db.session.delete(i)
        for i in favorit:
            db.session.delete(i)
        db.session.delete(row_to_delete)
        db.session.commit()
        flag = True
    except:
        db.session.rollback()
        flash("Ошибка удаления")
    if flag and (os.path.exists('static/images/' + str(post_id))): # удаление папки с изоб. к посту
        dir_path = 'static/images/' + str(post_id) + '/'
        try:
            shutil.rmtree(dir_path)
        except OSError as e:
            flash("Ошибка: {} : {}".format(dir_path, e.strerror))
    return redirect(url_for('main'))

@app.route('/delete_coment/<int:coment_id>')
def delete_coment(coment_id):
    edit_post = db.session.query(Coment).filter(Coment.id==int(coment_id)).one().post_id
    row_to_delete = db.session.query(Coment).filter(Coment.id==int(coment_id)).one()
    try:
        db.session.delete(row_to_delete)
        db.session.commit()
    except:
        db.session.rollback()
        flash("Ошибка удаления")
    return redirect(url_for('edit', post_id = edit_post))


@app.route('/favorites/<int:post_id>')
def favorites(post_id):
    favorit = db.session.query(Favorites).filter(Favorites.post_id==post_id,
                                                 Favorites.user_email==str(current_user)).all()
    if not favorit: # добавление в избранное если отсуствует, иначе - удаление с избр.
        try:
            f = Favorites(post_id=post_id, user_email=str(current_user))
            viwe = Post.query.get(post_id)
            viwe.views = viwe.views - 1
            db.session.add(viwe)
            db.session.add(f)
            db.session.commit()
        except:
            db.session.rollback()
            flash("Ошибка")
    else:
        try:
            viwe = Post.query.get(post_id)
            viwe.views = viwe.views - 1
            db.session.add(viwe)
            db.session.delete(favorit[0])
            db.session.commit()
        except:
            db.session.rollback()
    return redirect(url_for('main', post_id = post_id))



@app.route("/register/", methods=("POST", "GET"))
def register():
    form = RegistrForm()
    if form.validate_on_submit(): 
        if request.form['psw'] == request.form['psw1']: # проверка совпадения паролей при регистрации
            try:
                hash = generate_password_hash(request.form['psw']) 
                u = Users(user_name1=request.form['user_name1'],
                          email=request.form['email'],
                          psw=hash, )
                db.session.add(u)
                db.session.commit()
                return redirect(url_for('login'))
            except:
                db.session.rollback()
                flash("Ошибка регистрации")
                return redirect(url_for('register'))
        else:
            flash('Пароли не совпадают')
            return redirect(url_for('register'))
    return render_template("register.html",
                           form=form,
                           autoriz=current_user.is_authenticated, )


@app.route('/login/', methods=['post', 'get']) 
def login():
    if current_user.is_authenticated:      # если пользователь авторизован, переадресация на гл.стр.
	    return redirect(url_for('main'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(Users).filter(Users.email == form.email.data).first()
        if user and check_password_hash(user.psw, form.psw.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('main'))

        flash("Неправильный email или пароль", 'error')
        return redirect(url_for('login'))
    return render_template('login.html', form=form)


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из профиля")
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.run(debug=True)
