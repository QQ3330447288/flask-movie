from . import admin
from flask import Flask, render_template, redirect, url_for, flash, session, request, stream_with_context, abort
from app.admin.forms import LoginForm, TagForm, PwdForm, AuthForm, RoleForm, AdminForm, MovieForm, PreviewForm
from app.models import Admin, Tag, User, Auth, Role, Comment, Movie, Moviecol, Preview  # 导入要使用人数据模型
from functools import wraps  # 定义访问装饰器
from app import db, app
from werkzeug.utils import secure_filename
import os, datetime, uuid


# 修改文件名称
def change_filename(filename):  # 需要将filename转换为安全的文件爱你名称（filename）有时间前缀字符串拼接的名称
    file_info = os.path.splitext(filename)  # 分割成后缀加前缀
    filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4().hex) + file_info[-1]
    return filename


# 定义访问装饰器
def admin_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):  # 定义装饰器的方法
        if "admin" not in session:
            return redirect(url_for("admin.login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


# 权限访问控制器
def admin_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):  # 定义装饰器的方法
        # if "admin" not in session:
        #     return redirect(url_for("admin.login", next=request.url))
        admin = Admin.query.join(
            Role
        ).filter(
            Role.id == Admin.role_id
        ).first()
        auths = admin.role.auths
        auths = list(map(lambda v: int(v), auths.split(",")))
        auth_list = Auth.query.all()
        urls = [v.url for v in auth_list for val in auths if val == v.id]
        rule = request.url_rule
        if rule not in urls:
            abort(404)
        return f(*args, **kwargs)

    return decorated_function


@admin.route("/admin/")
@admin_login_req
def index():
    return render_template("admin/index.html")


@admin.route("/admin/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data  # 获取表单中的一系列数据
        admin = Admin.query.filter_by(name=data["account"]).first()  # 查询一条时记录
        if not admin.check_pwd(data["pwd"]):
            flash("密码错误！", "err")
            return redirect(url_for("admin.login"))
        session["admin"] = data["account"]
        return redirect(request.args.get("next") or url_for("admin.index"))
    return render_template("admin/login.html", form=form)


@admin.route("/admin/logout/")
@admin_login_req
def logout():
    session.pop("admin", None)
    return redirect(url_for("admin.login"))


# 修改密码
@admin.route("/admin/pwd/", methods=["GET", "POST"])
@admin_login_req
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=session["admin"]).first()
        from werkzeug.security import generate_password_hash
        admin.pwd = generate_password_hash(data["new_pwd"])
        db.session.add(admin)
        db.session.commit()
        flash("修改密码成功,请重新登陆！", "okey")
        redirect(url_for("admin.logout"))  # 使用admin调用logout
    return render_template("admin/pwd.html", form=form)


# 添加标签
@admin.route("/admin/tag/add/", methods=["GET", "POST"])
@admin_login_req
def tag_add():
    form = TagForm()
    if form.validate_on_submit():
        data = form.data  # 使用form.data获取表单数据
        tag = Tag.query.filter_by(name=data["name"]).count()
        if tag == 1:
            flash("标签名称已经存在！", "err")
            return redirect(url_for("admin.tag_add"))
        tag = Tag(
            name=data["name"]
        )
        db.session.add(tag)
        db.session.commit()
        flash("添加标签成功！", "okey")
        redirect(url_for("admin.tag_add"))
    return render_template("admin/tag_add.html", form=form)


# 标签列表
@admin.route("/admin/tag/list/<int:page>", methods=["GET"])
@admin_login_req
def tag_list(page=None):
    if page is None:
        page = 1
    page_data = Tag.query.order_by(
        Tag.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/tag_list.html", page_data=page_data)


# 删除标签
@admin.route("/admin/tag/del/<int:id>", methods=["GET"])
@admin_login_req
def tag_del(id=None):
    tag = Tag.query.filter_by(
        id=id
    ).first_or_404()
    db.session.delete(tag)
    db.session.commit()
    flash("删除列表成功！", "okey")
    return redirect(url_for("admin.tag_list", page=1))


# 编辑标签
@admin.route("/admin/tag/edit/<int:id>", methods=["GET", "POST"])
@admin_login_req
def tag_edit(id=None):
    form = TagForm()
    tag = Tag.query.get_or_404(id)
    if form.validate_on_submit():
        data = form.data  # 使用form.data获取表单数据
        tag_count = Tag.query.filter_by(name=data["name"]).count()
        if tag_count == 1 and tag.name != data["name"]:
            flash("标签名称已经存在！", "err")
            return redirect(url_for("admin.tag_edit", id=id))
        tag.name = data["name"]
        db.session.add(tag)
        db.session.commit()
        flash("修改标签成功！", "ok")
        redirect(url_for("admin.tag_edit", id=id))
    return render_template("admin/tag_edit.html", form=form, tag=tag)


# 添加电影
@admin.route("/admin/movie/add/", methods=["GET", "POST"])
@admin_login_req
def movie_add():
    form = MovieForm()
    if form.validate_on_submit():
        data = form.data
        file_url = secure_filename(form.url.data.filename)  # 获取上传文件的地址
        file_logo = secure_filename(form.logo.data.filename)
        if not os.path.exists(app.config["UP_DIR"]):
            os.makedirs(app.config["UP_DIR"])
            os.chmod(app.config["UP_DIR"], "rw")
        url = change_filename(file_url)
        logo = change_filename(file_logo)
        # 保存文件
        form.url.data.save(app.config["UP_DIR"] + url)
        form.logo.data.save(app.config["UP_DIR"] + logo)
        movie = Movie(
            title=data["title"],
            url=url,
            info=data["info"],
            logo=logo,
            star=int(data["star"]),
            playnum=0,
            commentnum=0,
            tag_id=int(data["tag_id"]),
            area=data["area"],
            release_time=data["release_time"],
            length=data["length"]
        )
        db.session.add(movie)
        db.session.commit()
        flash("添加电影成功！", "ok")
        return redirect(url_for('admin.movie_add'))
    return render_template("admin/movie_add.html", form=form)


# 电影列表
@admin.route("/admin/movie/list/")
@admin_login_req
def movie_list():
    return render_template("admin/movie_list.html")


# 添加电影预告
@admin.route("/admin/preview/add/", methods=["POST", "GET"])
@admin_login_req
def preview_add():
    form = PreviewForm()
    if form.validate_on_submit():
        data = form.data
        file_logo = secure_filename(form.logo.data.filename)
        if not os.path.exists(app.config["PREVIEW_DIR"]):
            os.makedirs(app.config["PREVIEW_DIR"])
            os.chmod(app.config["PREVIEW_DIR"], "rw")
        file = change_filename(file_logo)
        form.logo.data.save(app.config["PREVIEW_DIR"] + file)
        title_count = Preview.query.filter_by(title=data["title"]).count()
        if title_count == 1:
            flash("添加失败，已存在同名的电影预告！", "ok")
            return redirect(url_for('admin.preview_add'))
        preview = Preview(
            title=data["title"],
            logo=file
        )
        db.session.add(preview)
        db.session.commit()
        flash("添加预告成功！", "ok")
        return redirect(url_for('admin.preview_add'))
    return render_template("admin/preview_add.html", form=form)


# 电影预告列表
@admin.route("/admin/preview/list/")
@admin_login_req
def preview_list():
    return render_template("admin/preview_list.html")


# 会员（用户）列表
@admin.route("/admin/user/list/<int:page>", methods=["GET"])
@admin_login_req
def user_list(page=None):
    if page is None:
        page = 1
    page_data = User.query.order_by(
        User.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/user_list.html", page_data=page_data)


# 查看会员信息
@admin.route("/admin/user/view/<int:id>", methods=["GET"])
@admin_login_req
def user_view():
    return render_template("admin/user_view.html")


# 评论列表
@admin.route("/admin/comment/list/<int:page>", methods=["GET"])
@admin_login_req
def comment_list(page=None):
    if page is None:
        page = 1
    page_data = Comment.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Comment.movie_id,
        User.id == Comment.user_id
    ).order_by(
        Comment.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/comment_list.html", page_data=page_data)


# 删除评论
@admin.route("/admin/comment/del/<int:id>", methods=["GET"])
@admin_login_req
def comment_del(id=None):
    comment = Comment.query.filter_by(
        id=id
    ).first_or_404()
    db.session.delete(comment)
    db.session.commit()
    flash("删除评论列表成功！", "ok")
    return redirect(url_for("admin.comment_list", page=1))


# 收藏列表
@admin.route("/admin/moviecol/list/<int:page>")
@admin_login_req
def moviecol_list(page=None):
    if page is None:
        page = 1
    page_data = Moviecol.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Moviecol.movie_id,
        User.id == Moviecol.user_id
    ).order_by(
        Moviecol.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/moviecol_list.html", page_data=page_data)


# 删除电影收藏列表
@admin.route("/admin/moviecol/del/<int:id>", methods=["GET"])
@admin_login_req
def moviecol_del(id=None):
    moviecol = Moviecol.query.filter_by(
        id=id
    ).first_or_404()
    db.session.delete(moviecol)
    db.session.commit()
    flash("删除电影收藏列表成功！", "ok")
    return redirect(url_for("admin.moviecol_list", page=1))


@admin.route("/admin/oplog/list/")
@admin_login_req
def oplog_list():
    return render_template("admin/oplog_list.html")


@admin.route("/admin/adminloginlog/list/")
@admin_login_req
def adminloginlog_list():
    return render_template("admin/adminloginlog_list.html")


@admin.route("/admin/userloginlog/list/")
@admin_login_req
def userloginlog_list():
    return render_template("admin/userloginlog_list.html")


# 添加角色
@admin.route("/admin/role/add/", methods=["GET", "POST"])
@admin_login_req
def role_add():
    form = RoleForm()
    if form.validate_on_submit():
        data = form.data
        # print(data)
        # 打印的是数组{'name': '1', 'auths': [3], 'submit': True, 'csrf_token': 'IjFmMzZlYmJjOGJhNTBiNmUzNzk1ZjEwNjY0ZTVkN2NlZWJlMzJlNGMi.Ds7eOg.mcNHwkpf5GL10_oUJqlGeFCiEyM'}
        role = Role(
            name=data["name"],
            # auths=",".join(data["auths"])  # 用逗号分隔开，拼接成字符串
            auths=",".join(map(lambda v: str(v), data["auths"]))
        )
        db.session.add(role)
        db.session.commit()
        flash("添加角色成功！", "ok")
    return render_template("admin/role_add.html", form=form)


# 角色列表
@admin.route("/admin/role/list/<int:page>", methods=["GET"])
@admin_login_req
def role_list(page=None):
    if page is None:
        page = 1
    page_data = Role.query.order_by(
        Role.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/role_list.html", page_data=page_data)


# 角色删除
@admin.route("/admin/role/del/<int:id>", methods=["GET"])
@admin_login_req
def role_del(id=None):
    role = Role.query.filter_by(
        id=id
    ).first_or_404()
    db.session.delete(role)
    db.session.commit()
    flash("删除角色成功！", "ok")
    return redirect(url_for("admin.role_list", page=1))


# 编辑角色权限
@admin.route("/admin/role/edit/<int:id>", methods=["GET", "POST"])
@admin_login_req
def role_edit(id=None):
    form = RoleForm()
    role = Role.query.get_or_404(id)
    if request.method == "GET":
        auths = role.auths  # 查到auths
        form.auths.data = list(map(lambda v: int(v), auths.split(",")))
        # 逗号分割成列表然后转化为整型再转化为列表
        # print(form.auths.data)
    if form.validate_on_submit():
        data = form.data  # 使用form.data获取表单数据
        role.name = data["name"]
        role.auths = data["auths"]
        db.session.add(role)
        db.session.commit()
        flash("修改角色成功！", "ok")
        redirect(url_for("admin.role_edit", id=id))
    return render_template("admin/role_edit.html", form=form, role=role)


# 权限添加
@admin.route("/admin/auth/add/", methods=["GET", "POST"])
@admin_login_req
def auth_add():
    form = AuthForm()
    if form.validate_on_submit():
        data = form.data
        auth = Auth(
            name=data["name"],
            url=data["url"]
        )
        db.session.add(auth)
        db.session.commit()
        flash("添加权限成功！", "ok")
    return render_template("admin/auth_add.html", form=form)


# 权限列表
@admin.route("/admin/auth/list/<int:page>", methods=["GET"])
@admin_login_req
def auth_list(page=None):
    if page is None:
        page = 1
    page_data = Auth.query.order_by(
        Auth.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/auth_list.html", page_data=page_data)


# 删除权限列表
@admin.route("/admin/auth/del/<int:id>", methods=["GET"])
@admin_login_req
def auth_del(id=None):
    auth = Auth.query.filter_by(
        id=id
    ).first_or_404()
    db.session.delete(auth)
    db.session.commit()
    flash("删除权限成功！", "okey")
    return redirect(url_for("admin.auth_list", page=1))


# 编辑权限
@admin.route("/admin/auth/edit/<int:id>", methods=["GET", "POST"])
@admin_login_req
def auth_edit(id=None):
    form = AuthForm()
    auth = Auth.query.get_or_404(id)
    if form.validate_on_submit():
        data = form.data  # 使用form.data获取表单数据
        auth.name = data["name"]
        auth.url = data["url"]
        db.session.add(auth)
        db.session.commit()
        flash("修改权限成功！", "ok")
        redirect(url_for("admin.auth_edit", id=id))
    return render_template("admin/auth_edit.html", form=form, auth=auth)


# 添加管理员
@admin.route("/admin/add/", methods=["GET", "POST"])
@admin_login_req
def admin_add():
    form = AdminForm()
    from werkzeug.security import generate_password_hash
    if form.validate_on_submit():
        data = form.data
        # 实现数据存库
        admin = Admin(
            name=data["name"],
            pwd=generate_password_hash("pwd"),
            role_id=data["role_id"],
            is_super=1  # 非超级管理员均为1
        )
        db.session.add(admin)
        db.session.commit()
        flash("添加管理员成功！", "ok")
    return render_template("admin/admin_add.html", form=form)


# @admin.route("/admin/list/<int:page>", methods=["GET"])
# @admin_login_req
# def admin_list(page=None):
#     if page is None:
#         page = 1
#     page_data = Admin.query.filter_by(
#     ).paginate(page=page, per_page=10)
#     return render_template("admin/admin_list.html", page_data=page_data)

# 管理员列表
@admin.route("/admin/list/<int:page>", methods=["GET"])
@admin_login_req
def admin_list(page=None):
    if page is None:
        page = 1
    page_data = Admin.query.join(
        Role
    ).filter(
        Role.id == Admin.role_id
    ).filter_by(
    ).paginate(page=page, per_page=10)
    return render_template("admin/admin_list.html", page_data=page_data)
