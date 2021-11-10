import os
import glob
from datetime import datetime
import shutil

from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from forms import PostForm, ComentForm, RegistrForm, LoginForm
from create_random_post import create_random_post

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
    user_name = db.Column(db.String(500), nullable=False)
    email = db.Column(db.String(50), unique=True)
    psw = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='user')
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"{self.email}"


class Favorites(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    user_email = db.Column(db.String(255), nullable=False)
    post_id = db.Column(db.Integer(), nullable=False)


class Link_img(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    link = db.Column(db.String(255), nullable=False)
    post_id = db.Column(db.Integer(), nullable=False)

    def __repr__(self):
        return f'{self.id}'


def check_user_status():
    return str(current_user.status) if current_user.is_authenticated else None

def add_db(*args):
    for i in args:
        db.session.add(i)   
    db.session.commit()
            


@app.route('/')
@app.route('/<string:page>')
def main(page=1):
    if request.cookies.get('sort') == 'decrease':
        posts = Post.query.order_by(Post.id.desc()).paginate(int(page), 20)
    else:
        posts = Post.query.paginate(int(page), 20)
    return render_template('main.html',
                           user_status=str(current_user.status) if current_user.is_authenticated else None,
                           posts=posts,
                           autoriz=current_user.is_authenticated,
                           current_user=str(current_user),
                           flag='main', )


@app.route('/post/<int:post_id>', methods=['get', 'post'])
def post(post_id):
    post_dir = 'static/images' + '/' + str(post_id)
    links_img = db.session.query(Link_img).filter(Link_img.post_id == post_id).all()
    count_favorite = len(db.session.query(Favorites).filter(Favorites.post_id == post_id).all())
    user_favorite = db.session.query(Favorites).filter(Favorites.post_id == post_id,
                                                       Favorites.user_email == str(current_user)).all()
    images = []
    if (os.path.exists(post_dir)):  # получение списка изображений для конкретного поста
        images = os.listdir(post_dir)   
    try:  # увеличение счетчика просмотров
        viwe = Post.query.get(post_id)
        viwe.views = viwe.views + 1
        add_db(viwe)
    except:
        db.session.rollback()
        flash("Ошибка добавления")

    form = ComentForm()
    if form.validate_on_submit():  # добавление комментария к посту
        try:
            com = Coment(user_name=current_user.user_name,
                         coment_content=request.form['coment_content'],
                         post_id=post_id, )
            viwe = Post.query.get(post_id)
            viwe.views -= 2
            add_db(viwe, com)
            flash("Комментарий добавлен")
        except:
            db.session.rollback()
            flash("Ошибка добавления")
        return redirect(f'/post/{post_id}')
    return render_template('post.html',
                           post=Post.query.filter(Post.id == post_id).first(),
                           coments=Coment.query.filter(Coment.post_id == post_id).all(),
                           form=form,
                           images=images,
                           links_img=links_img,
                           autoriz=current_user.is_authenticated,
                           count_favorite=count_favorite,
                           user_favorite=user_favorite,
                           user_status=check_user_status(),
                           current_user=str(current_user), )


@app.route('/add-post/', methods=['get', 'post'])
@app.route('/add-post/<string:slug>')
def add_post(slug=None):
    flag = False
    form = PostForm()
    if slug == 'random':
        data_post = create_random_post()  # добавление случайной статьи с википедии
        try:
            p = Post(title=data_post[0],
                     content=data_post[1],
                     author=str(current_user), )
            db.session.add(p)
            db.session.commit()
            if data_post[2]:
                for i in data_post[2]:
                    l = Link_img(link=i,
                                 post_id=Post.query.order_by(Post.id.desc())[0].id)
                    db.session.add(l)
                    db.session.commit()
            flash("Статья добавлена")
        except:
            db.session.rollback()
            flash("Ошибка добавления")
        return redirect(f'/post/{str(Post.query.order_by(Post.id.desc())[0].id)}')
    else:
        if form.validate_on_submit():  # обавление  поста в БД
            try:
                p = Post(title=request.form['title'],
                         content=request.form['content'],
                         author=str(current_user), )
                db.session.add(p)
                db.session.commit()
                flash("Статья добавлена")
            except:
                db.session.rollback()
                flash("Ошибка добавления")
                return redirect(url_for('add_post'))
            else:
                 flag = True
        if flag:  # если данные в БД добавились, создаются каталоги и в них грузятся изображения для постов
            files = request.files.getlist('upload')
            if files[0]:
                post_dir = '/' + str(Post.query.order_by(Post.id.desc())[0])
                app.config['UPLOAD_PATH'] = 'static/images' + post_dir
                os.mkdir('static/images' + post_dir)
                for file in files:
                    filename = file.filename
                    file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
            return redirect(f'/post/{str(Post.query.order_by(Post.id.desc())[0].id)}')
    return render_template('add_post.html',
                           form=form,
                           edit_post=False,
                           autoriz=current_user.is_authenticated,
                           user_status=str(current_user.status), )


@app.route("/edit/<string:post_id>", methods=['get', 'post'])
def edit(post_id):
    flag = False
    post = Post.query.filter(Post.id == post_id).first()
    links_img = db.session.query(Link_img).filter(Link_img.post_id == int(post_id)).all()
    post_dir = '/' + post_id
    form = PostForm()
    form.title.data = post.title
    form.content.data = post.content
    images = []
    if (os.path.exists('static/images' + '/' + post_id)):  # получение списка изображений для конкретного поста
        images = os.listdir('static/images' + '/' + post_id)    
    if form.validate_on_submit():
        try:
            post.title = request.form['title']
            post.content = request.form['content']
            add_db(post)
            flash("Изменения внесены")
        except:
            db.session.rollback()
            flash("Ошибка добавления")
        else:
            flag = True
        if form.checkbox.data and os.path.exists('static/images' + post_dir):  # удаление прежних изобр.
            del_files = glob.glob('static/images' + post_dir + '/*')  # при редактировании поста
            for f in del_files:
                os.remove(f)
        if flag:  # если пост обновился, создаются каталоги (если их нет) и в них грузятся изображения для постов
            files = request.files.getlist('upload')
            if files[0]:
                app.config['UPLOAD_PATH'] = 'static/images' + post_dir
                if not (os.path.exists('static/images' + post_dir)):
                    os.mkdir('static/images' + post_dir)
                for file in files:
                    filename = file.filename
                    file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
        return redirect(f'/post/{post_id}')
    return render_template('add_post.html',
                           form=form,
                           post_id=post_id,
                           edit_post=True,
                           coments=Coment.query.filter(Coment.post_id == post_id).all(),
                           autoriz=current_user.is_authenticated,
                           user_status=check_user_status(),
                           images=images,
                           links_img=links_img, )


@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
    flag = False
    favorit = db.session.query(Favorites).filter(Favorites.post_id == post_id).all()
    row_to_delete = db.session.query(Post).filter(Post.id == int(post_id)).one()
    coment_rows_delete = db.session.query(Coment).filter(Coment.post_id == post_id).all()
    links_img = db.session.query(Link_img).filter(Link_img.post_id == post_id).all()
    try:
        for i in coment_rows_delete:
            db.session.delete(i)
        for i in favorit:
            db.session.delete(i)
        for i in links_img:
            db.session.delete(i)
        db.session.delete(row_to_delete)
        db.session.commit()
    except:
        db.session.rollback()
        flash("Ошибка удаления")
    else:
        flag = True
    if flag and (os.path.exists('static/images/' + str(post_id))):  # удаление папки с изоб. к посту
        dir_path = 'static/images/' + str(post_id) + '/'
        try:
            shutil.rmtree(dir_path)
        except OSError as e:
            flash("Ошибка: {} : {}".format(dir_path, e.strerror))
    return redirect(url_for('main'))


@app.route('/delete_coment/<int:coment_id>')
def delete_coment(coment_id):
    edit_post = db.session.query(Coment).filter(Coment.id == int(coment_id)).one().post_id
    row_to_delete = db.session.query(Coment).filter(Coment.id == int(coment_id)).one()
    try:
        db.session.delete(row_to_delete)
        db.session.commit()
    except:
        db.session.rollback()
        flash("Ошибка удаления")
    return redirect(url_for('edit', post_id=edit_post))


@app.route('/delete_img/<path:img>')  # удаление конкретного изображения при редактировании поста
def delete_img(img):
    path = img.split('/')
    if len(path) == 3 and path[2] == 'link':  # удаление ссылки на изображение
        row_to_delete = db.session.query(Link_img).filter(Link_img.id == int(path[1])).one()
        try:
            db.session.delete(row_to_delete)
            db.session.commit()
        except:
            db.session.rollback()
            flash("Ошибка удаления")
    else:  # удаление статического изображения
        del_file = 'static/images' + '/' + path[0] + '/' + path[1]
        os.remove(del_file)

    return redirect(url_for('edit', post_id=path[0]))


@app.route('/favorites/<int:post_id>')
def favorites(post_id):
    favorit = db.session.query(Favorites).filter(Favorites.post_id == post_id,
                                                 Favorites.user_email == str(current_user)).all()
    if not favorit:  # добавление в избранное если отсуствует, иначе - удаление с избр.
        try:
            f = Favorites(post_id=post_id, user_email=str(current_user))
            viwe = Post.query.get(post_id)
            viwe.views = viwe.views - 1
            add_db(viwe, f)
        except:
            db.session.rollback()
            flash("Ошибка")
    else:
        try:
            viwe = Post.query.get(post_id)
            viwe.views = viwe.views - 1
            db.session.delete(favorit[0])
            add_db(viwe)
        except:
            db.session.rollback()
    return redirect(url_for('post', post_id=post_id))


@app.route('/favorites_posts')
@app.route('/favorites_posts/<int:page>')
def favorites_posts(page=1):
    favorites_post_id = db.session.query(Favorites).filter(Favorites.user_email == str(current_user)).all()
    favorites_post_id = [int(i.post_id) for i in favorites_post_id]

    if request.cookies.get('sort') == 'decrease' or not request.cookies.get('sort'):
        posts = db.session.query(Post).filter(Post.id.in_(favorites_post_id)).order_by(Post.id.desc()).paginate(page,
                                                                                                                20)
    else:
        posts = db.session.query(Post).filter(Post.id.in_(favorites_post_id)).paginate(page, 20)
    return render_template('main.html',
                           posts=posts,
                           autoriz=current_user.is_authenticated,
                           current_user=str(current_user),
                           user_status=check_user_status(),
                           flag='favorites', )


@app.route("/register/", methods=["POST", "GET"])
def register():
    form = RegistrForm()
    if form.validate_on_submit():
        if request.form['psw'] == request.form['psw1']:  # проверка совпадения паролей при регистрации
            try:
                hash = generate_password_hash(request.form['psw'])
                u = Users(user_name=request.form['user_name'],
                          email=request.form['email'],
                          psw=hash, )
                add_db(u)
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
    if current_user.is_authenticated:  # если пользователь авторизован, переадресация на гл.стр.
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


@app.route('/admin-panel/<int:user_id>')
@app.route('/admin-panel/')
def admin_panel(user_id=None):
    if user_id:
        user = db.session.query(Users).filter(Users.id == user_id).first()
        print(user.status)
        if user.status == 'admin':
            user.status = 'user'
        else:
            user.status = 'admin'
        try:
            add_db(user)
            flash('Статус изменен')
        except:
            db.session.rollback()
            flash("Ошибка")
        if current_user.id == user_id:
            return redirect(url_for('main'))
        else:
            return redirect(url_for('admin_panel'))
    else:
        return render_template('admin_panel.html',
                               users=Users.query.all(),
                               current_user=str(current_user),
                               user_status=check_user_status(),
                               autoriz=current_user.is_authenticated, )


@app.route('/sort/<string:slug>')  # сортировка постов для главной стр. и избранного
def sort_posts(slug=None):
    if slug:
        slug_split = slug.split('-')
        if slug_split[1] == 'main':
            resp = make_response(redirect(url_for('main')))
        elif slug_split[1] == 'favorites':
            resp = make_response(redirect(url_for('favorites_posts')))
        elif slug_split[1] == 'search':
            resp = make_response(redirect(url_for('find_phrase')))

        if slug_split[0] == 'increase':
            resp.set_cookie('sort', 'increase')
        elif slug_split[0] == 'decrease':
            resp.set_cookie('sort', 'decrease')
        else:
            return redirect(url_for('main'))
        return resp


@app.route('/search')
@app.route('/search/<int:page>')
def find_phrase(page=1):  # большая часть кода необходима для работы пагинации и сортировки
    posts = []
    if request.args.get("search_prase"):
        req = request.args.get("search_prase")
    else:
        req = request.cookies.get('serch_prase')
    for i in db.session.query(Post).all():
        if req.lower() in i.title.lower() or req.lower() in i.content.lower():
            posts.append(i)
    post_id = [i.id for i in posts]
    if request.cookies.get('sort') == 'decrease' or not request.cookies.get('sort'):
        posts = db.session.query(Post).filter(Post.id.in_(post_id)).order_by(Post.id.desc()).paginate(page, 20)
    else:
        posts = db.session.query(Post).filter(Post.id.in_(post_id)).paginate(page, 20)

    resp = make_response(render_template('main.html',
                                         posts=posts,
                                         autoriz=current_user.is_authenticated,
                                         current_user=str(current_user),
                                         user_status=check_user_status(),
                                         flag='search', ))
    resp.set_cookie('serch_prase', req)
    return resp


if __name__ == "__main__":
    app.run(debug=True)
