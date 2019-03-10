from . import home
from flask import Flask, render_template, redirect, url_for, flash, session, request
from app.home.forms import RegistForm, LoginForm, UserDetailForm, PwdForm, CommentForm
from app.models import User, Userlog, Comment, Movie, Preview, Tag
from werkzeug.security import generate_password_hash
import uuid
from app import db, app
from functools import wraps
from werkzeug.utils import secure_filename  # 文件上传
import os, datetime


# 修改文件名称
def change_filename(filename):  # 需要将filename转换为安全的文件爱你名称（filename）有时间前缀字符串拼接的名称
    file_info = os.path.splitext(filename)  # 分割成后缀加前缀
    filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4().hex) + file_info[-1]
    return filename


# 定义访问装饰器
def user_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):  # 定义装饰器的方法
        if "user" not in session:
            return redirect(url_for("home.login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


@home.route("/login/", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        user = User.query.filter_by(name=data["name"]).first()
        if not user.check_pwd(data["pwd"]):
            flash("密码错误！", "err")
            return redirect(url_for("home.login"))
        session["user"] = user.name
        session["user_id"] = user.id
        userlog = Userlog(
            user_id=user.id,
            ip=request.remote_addr
        )
        db.session.add(userlog)
        db.session.commit()
        return redirect(url_for("home.user"))
    return render_template("home/login.html", form=form)


@home.route("/logout/")
def logout():
    session.pop("user", None)
    session.pop("user", None)
    return redirect(url_for("home.login"))


# 会员注册
@home.route("/register/", methods=['GET', 'POST'])
def register():
    form = RegistForm()
    if form.validate_on_submit():
        data = form.data
        user = User(
            name=data["name"],
            email=data["email"],
            phone=data["phone"],
            pwd=generate_password_hash(data["pwd"]),
            uuid=uuid.uuid4().hex
        )
        print(user)
        db.session.add(user)
        db.session.commit()
        flash("注册成功", "ok")
    return render_template("home/register.html", form=form)


# 修改会员资料
@home.route("/user/", methods=["GET", "POST"])
@user_login_req
def user():
    form = UserDetailForm()
    user = User.query.get(int(session["user_id"]))
    form.face.validators = []  # 第一次上传头像可以用来空
    # print(user.name)
    if request.method == "GET":
        print(user.name)
        form.name.data = user.name
        form.email.data = user.email
        form.phone.data = user.phone
        form.info.data = user.info
    if form.validate_on_submit():
        data = form.data
        file_face = secure_filename(form.face.data.filename)
        if not os.path.exists(app.config["FC_DIR"]):
            os.makedirs(app.config["FC_DIR"])
            os.chmod(app.config["FC_DIR"], "rw")
        user.face = change_filename(file_face)
        form.face.data.save(app.config["FC_DIR"] + user.face)
        name_count = User.query.filter_by(name=data["name"]).count()
        if name_count == 1 and data["name"] != user.name:
            flash("昵称已经存在！", "ok")
            return redirect(url_for("home.user"))
        email_count = User.query.filter_by(email=data["email"]).count()
        if email_count == 1 and data["email"] != user.email:
            flash("邮箱已经存在！", "ok")
            return redirect(url_for("home.user"))
        phone_count = User.query.filter_by(phone=data["phone"]).count()
        if phone_count == 1 and data["phone"] != user.phone:
            flash("手机号码已经存在！", "ok")
            return redirect(url_for("home.user"))
        user.name = data["name"]
        user.email = data["email"]
        user.phone = data["phone"]
        user.info = data["info"]
        db.session.add(user)
        db.session.commit()
        flash("修改成功", "ok")
        return redirect(url_for("home.user"))
    return render_template("home/user.html", form=form, user=user)


# 修改密码
@home.route("/pwd/", methods=["GET", "POST"])
@user_login_req
def pwd():
    form = PwdForm()
    data = form.data
    if form.validate_on_submit():
        user = User.query.filter_by(name=session["user"]).first()
        user.pwd = generate_password_hash(data["new_pwd"])
        db.session.add(user)
        db.session.commit()
        flash("密码修改成功,请重新登陆！", "ok")
        return redirect(url_for('home.logout'))
    return render_template("home/pwd.html", form=form)


# 评论列表
@home.route("/comments/<int:page>", methods=["GET"])
@user_login_req
def per_comments_list(page=None):
    if page is None:
        page = 1
    page_data = Comment.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Comment.movie_id,
        User.id == session["user_id"]
    ).order_by(
        Comment.addtime.desc()
    ).paginate(page=page, per_page=5)
    return render_template("home/comments.html", page_data=page_data)


# 登陆日志
@home.route("/loginlog/<int:page>", methods=["GET"])
@user_login_req
def loginlog(page=None):
    if page is None:
        page = 1
    page_data = Userlog.query.order_by(
        Userlog.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("home/loginlog.html", page_data=page_data)


@home.route("/moviecol/")
@user_login_req
def moviecol():
    return render_template("home/moviecol.html")


@home.route("/")
def index():
    return render_template("home/index.html")


# 上映预告
@home.route("/animation/")
def animation():
    data = Preview.query.all()
    return render_template("home/animation.html", data=data)


@home.route("/search/<int:page>/")
def search(page=None):
    if page is None:
        page = 1
    key = request.args.get("key", "")
    movie_count = Movie.query.filter(
        Movie.title.ilike('%' + key + '%')
    ).count()
    page_data = Movie.query.filter(
        # user_id=int(session["user_id"])
        Movie.title.ilike('%' + key + '%')
    ).order_by(
        Movie.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("home/search.html", page=page, key=key, page_data=page_data, movie_count=movie_count)


@home.route("/play/<int:id>/", methods=["GET", "POST"])
def play(id=None):
    movie = Movie.query.join(Tag).filter(
        Tag.id == Movie.tag_id,
        Movie.id == int(id)
    ).first_or_404()  # 只需要一条
    movie.playnum = movie.playnum + 1
    form = CommentForm()
    if "user" in session and form.validate_on_submit():
        data = form.data
        comment = Comment(
            content=data["content"],
            movie_id=movie.id,
            user_id=session["user_id"]
        )
        db.session.add(comment)
        db.session.commit()
        movie.commentnum = movie.commentnum + 1
        flash("添加评论成功！", "ok")
        return redirect(url_for('home.play', id=movie.id))
    db.session.add(movie)
    db.session.commit()
    return render_template("home/play.html", movie=movie, form=form)
