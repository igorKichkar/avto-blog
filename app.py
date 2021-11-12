import os
import glob
import shutil

from flask import flash, Flask, make_response, redirect, render_template, request, url_for
from flask_login import current_user, LoginManager, login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from forms import ComentForm, LoginForm, PostForm, RegistrForm
from models import *
from utils import create_random_post, check_user_status

app = Flask(__name__)
app.config['SECRET_KEY'] = '12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///blog.db'
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 32

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return db.session.query(Users).get(user_id)


@app.route('/')
@app.route('/<string:page>')
def main(page=1):
    if request.cookies.get('sort') == 'decrease':
        posts = Post.query.order_by(Post.id.desc()).paginate(int(page), 20)
    else:
        posts = Post.query.paginate(int(page), 20)
    return render_template('main.html',
                           user_status=current_user.status if current_user.is_authenticated else None,
                           posts=posts,
                           autoriz=current_user.is_authenticated,
                           current_user=str(current_user) if current_user.is_authenticated else None,
                           flag='main', )


@app.route('/post/<int:post_id>', methods=['get', 'post'])
def post(post_id):
    viewed_post = Post.query.get(post_id)
    post_dir = 'static/images' + '/' + str(post_id)
    links_img = db.session.query(Link_img).filter(Link_img.post_id == post_id).all()
    count_favorite = len(db.session.query(Favorites).filter(Favorites.post_id == post_id).all())
    user_favorite = db.session.query(Favorites).filter(Favorites.post_id == post_id,
                                                       Favorites.user_email == str(current_user)).all()
    images = []
    if os.path.exists(post_dir):  # получение списка изображений для конкретного поста
        images = os.listdir(post_dir)

    viewed_post.views += 1
    viewed_post.save()

    form = ComentForm()
    if form.validate_on_submit():  # добавление комментария к посту
        try:
            com = Coment(user_name=current_user.user_name,
                         coment_content=request.form['coment_content'],
                         post_id=post_id, )
            com.save()

            viewed_post.views -= 2
            viewed_post.save()
            flash("Комментарий добавлен")
        except Exception:
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
                           user_status=check_user_status(current_user),
                           current_user=str(current_user) if current_user.is_authenticated else None,
                           )


@app.route('/add-post/', methods=['get', 'post'])
@app.route('/add-post/<string:slug>')
def add_post(slug=None):
    form = PostForm()
    if slug == 'random':
        data_post = create_random_post()  # добавление случайной статьи с википедии
        try:
            p = Post(title=data_post[0],
                     content=data_post[1],
                     author=str(current_user), )
            p.save()
            if data_post[2]:
                for i in data_post[2]:
                    l = Link_img(link=i, post_id=Post.query.order_by(Post.id.desc())[0].id)
                    l.save()
            flash("Статья добавлена")
        except Exception:
            db.session.rollback()
            flash("Ошибка добавления")
        return redirect(f'/post/{str(Post.query.order_by(Post.id.desc())[0].id)}')
    else:
        if form.validate_on_submit():  # обавление  поста в БД
            try:
                p = Post(title=request.form['title'],
                         content=request.form['content'],
                         author=str(current_user), )
                p.save()
                flash("Статья добавлена")
            except Exception:
                db.session.rollback()
                flash("Ошибка добавления")
                return redirect(url_for('add_post'))
            else:
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
                           user_status=current_user.status
                           )


@app.route("/edit/<string:post_id>", methods=['get', 'post'])
def edit(post_id):
    post = Post.query.filter(Post.id == post_id).first()
    links_img = db.session.query(Link_img).filter(Link_img.post_id == int(post_id)).all()
    post_dir = '/' + post_id

    form = PostForm()
    form.title.data = post.title
    form.content.data = post.content

    images = []
    if os.path.exists('static/images' + '/' + post_id):  # получение списка изображений для конкретного поста
        images = os.listdir('static/images' + '/' + post_id)

    if form.validate_on_submit():
        try:
            post.title = request.form['title']
            post.content = request.form['content']
            post.save()
            flash("Изменения внесены")
        except:
            db.session.rollback()
            flash("Ошибка добавления")
        else:
            if form.checkbox.data and os.path.exists('static/images' + post_dir):  # удаление прежних изобр.
                del_files = glob.glob('static/images' + post_dir + '/*')  # при редактировании поста
                for f in del_files:
                    os.remove(f)

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
                           user_status=check_user_status(current_user),
                           images=images,
                           links_img=links_img
                           )


@app.route('/delete_post/<int:post_id>')
def delete_post(post_id):
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
    except Exception:
        db.session.rollback()
        flash("Ошибка удаления")
    else:
        if os.path.exists('static/images/' + str(post_id)):  # удаление папки с изоб. к посту
            dir_path = 'static/images/' + str(post_id) + '/'
            try:
                shutil.rmtree(dir_path)
            except OSError as e:
                flash("Ошибка: {} : {}".format(dir_path, e.strerror))

    return redirect(url_for('main'))


@app.route('/delete_coment/<int:coment_id>')
def delete_coment(coment_id):
    row_to_delete = db.session.query(Coment).filter(Coment.id == int(coment_id)).one()
    try:
        db.session.delete(row_to_delete)
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Ошибка удаления")
    return redirect(request.referrer)


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
    viewed_post = Post.query.get(post_id)
    favorite = db.session.query(Favorites).filter(Favorites.post_id == post_id,
                                                  Favorites.user_email == str(current_user)).all()
    if not favorite:  # добавление в избранное если отсуствует, иначе - удаление с избр.
        try:
            f = Favorites(post_id=post_id, user_email=str(current_user))
            f.save()
            viewed_post.views -= 1
            viewed_post.save()
        except Exception:
            db.session.rollback()
            flash("Ошибка")
    else:
        try:
            viewed_post.views += 1
            viewed_post.save()
            db.session.delete(favorite[0])
            db.session.commit()
        except Exception:
            db.session.rollback()

    return redirect(url_for('post', post_id=post_id))


@app.route('/favorites_posts')
@app.route('/favorites_posts/<int:page>')
def favorites_posts(page=1):
    favorites_post_id = db.session.query(Favorites).filter(Favorites.user_email == str(current_user)).all()
    favorites_post_id = [int(i.post_id) for i in favorites_post_id]

    if request.cookies.get('sort') == 'decrease':
        posts = db.session.query(Post)\
            .filter(Post.id.in_(favorites_post_id))\
            .order_by(Post.id.desc()).paginate(page, 20)
    else:
        posts = db.session.query(Post)\
            .filter(Post.id.in_(favorites_post_id))\
            .paginate(page, 20)
    return render_template('main.html',
                           posts=posts,
                           autoriz=current_user.is_authenticated,
                           current_user=str(current_user),
                           user_status=check_user_status(current_user),
                           flag='favorites', )


@app.route("/register/", methods=["POST", "GET"])
def register():
    form = RegistrForm()
    if not form.validate_on_submit():
        return render_template("register.html",
                               form=form,
                               autoriz=current_user.is_authenticated, )

    if request.form['psw'] == request.form['psw1']:  # проверка совпадения паролей при регистрации
        try:
            hash = generate_password_hash(request.form['psw'])
            u = Users(user_name=request.form['user_name'],
                      email=request.form['email'],
                      psw=hash, )
            u.save()
            return redirect(url_for('login'))
        except Exception:
            db.session.rollback()
            flash("Ошибка регистрации")
            return redirect(url_for('register'))
    else:
        flash('Пароли не совпадают')
        return redirect(url_for('register'))


@app.route('/login/', methods=['post', 'get'])
def login():
    if current_user.is_authenticated:  # если пользователь авторизован, переадресация на гл.стр.
        return redirect(url_for('main'))

    form = LoginForm()
    if not form.validate_on_submit():
        return render_template('login.html', form=form)

    user = db.session.query(Users).filter(Users.email == form.email.data).first()
    if user and check_password_hash(user.psw, form.psw.data):
        login_user(user, remember=form.remember.data)
        return redirect(url_for('main'))

    flash("Неправильный email или пароль", 'error')
    return redirect(url_for('login'))


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из профиля")
    return redirect(url_for('login'))


@app.route('/admin-panel/<int:user_id>')
@app.route('/admin-panel/')
def admin_panel(user_id=None):
    if not user_id:
        return render_template('admin_panel.html',
                               users=Users.query.all(),
                               current_user=str(current_user),
                               user_status=check_user_status(current_user),
                               autoriz=current_user.is_authenticated)

    user = db.session.query(Users).filter(Users.id == user_id).first()
    if user.status == 'admin':
        user.status = 'user'
    else:
        user.status = 'admin'

    try:
        user.save()
        flash('Статус изменен')
    except Exception:
        db.session.rollback()
        flash("Ошибка")
    if current_user.id == user_id:
        return redirect(url_for('main'))
    else:
        return redirect(url_for('admin_panel'))


@app.route('/sort/')
@app.route('/sort/<string:slug>')  # сортировка постов для главной стр. и избранного
def sort_posts(slug=None):
    slug_split = slug.split('-') if slug else []
    if len(slug_split) == 2 :
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
        return resp
    else:
        return redirect(url_for('main'))


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
    posts_ids = [i.id for i in posts]
    if request.cookies.get('sort') == 'decrease':
        posts = db.session.query(Post).filter(Post.id.in_(posts_ids)).order_by(Post.id.desc()).paginate(page, 20)
    else:
        posts = db.session.query(Post).filter(Post.id.in_(posts_ids)).paginate(page, 20)

    resp = make_response(render_template('main.html',
                                         posts=posts,
                                         autoriz=current_user.is_authenticated,
                                         current_user=current_user.user_name,
                                         user_status=check_user_status(current_user),
                                         flag='search'))
    resp.set_cookie('serch_prase', req)
    return resp


if __name__ == "__main__":
    app.run(debug=True)
