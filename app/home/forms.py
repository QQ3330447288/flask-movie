# coding:utf8
from flask_wtf import FlaskForm  # FlaskForm是表单的基类
from wtforms import StringField, PasswordField, SubmitField, FileField, TextAreaField
from wtforms.validators import DataRequired, ValidationError, EqualTo, Email, Regexp
from app.models import User


class RegistForm(FlaskForm):
    '''user注册表单'''
    name = StringField(
        label="昵称",
        validators=[
            DataRequired("请输入昵称！")
        ],
        description="昵称",
        render_kw={
            "class": "form-control input",
            "placeholder": "请输入昵称！",
        }
    )
    email = StringField(
        label='邮箱',
        validators=[
            DataRequired("请输入邮箱！"),
            Email("邮箱格式不正确！")
        ],
        description="昵称",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入邮箱！",
        }
    )
    phone = StringField(
        label='手机号',
        validators=[
            DataRequired("请输入手机号！"),
            Regexp('1[34578]\\d{9}', message='手机号格式不正确！')
        ],
        description="手机号",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入手机号！",
        }
    )
    pwd = PasswordField(
        label="密码",
        validators=[
            DataRequired("请输入密码！")
        ],
        description="密码",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入密码！"
        }
    )
    repwd = PasswordField(
        label="确认密码",
        validators=[
            DataRequired("请输入确认密码！"),
            EqualTo('pwd', message='两次密码不一致')
        ],
        description="确认密码",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入确认密码！",
        }
    )

    submit = SubmitField(
        '注册',
        render_kw={
            "class": "btn btn-log btn-success btn-block"
        }
    )

    def validate_name(self, field):
        name = field.data
        user = User.query.filter_by(name=name).count()
        if user == 1:
            raise ValidationError('昵称已经存在！')

    def validate_phone(self, field):
        name = field.data
        user = User.query.filter_by(name=name).count()
        if user == 1:
            raise ValidationError('该手机号已被注册！')

    def validate_email(self, field):
        name = field.data
        user = User.query.filter_by(name=name).count()
        if user == 1:
            raise ValidationError('该邮箱已被注册！')


class LoginForm(FlaskForm):
    '''user注册表单'''
    name = StringField(
        label="昵称",
        validators=[
            DataRequired("请输入昵称！")
        ],
        description="昵称",
        render_kw={
            "class": "form-control input",
            "placeholder": "请输入昵称！",
        }
    )
    pwd = PasswordField(
        label="密码",
        validators=[
            DataRequired("请输入密码！")
        ],
        description="密码",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入密码！"
        }
    )
    submit = SubmitField(
        '登陆',
        render_kw={
            "class": "btn btn-log btn-success btn-block"
        }
    )


class UserDetailForm(FlaskForm):
    name = StringField(
        label="昵称",
        validators=[
            DataRequired("请输入昵称！")
        ],
        description="昵称",
        render_kw={
            "class": "form-control input",
            "placeholder": "请输入昵称！",
        }
    )
    email = StringField(
        label='邮箱',
        validators=[
            DataRequired("请输入邮箱！"),
            Email("邮箱格式不正确！")
        ],
        description="昵称",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入邮箱！",
        }
    )
    phone = StringField(
        label='手机号',
        validators=[
            DataRequired("请输入手机号！"),
            Regexp('1[34578]\\d{9}', message='手机号格式不正确！')
        ],
        description="手机号",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入手机号！",
        }
    )

    face = FileField(
        label='头像',
        validators=[
            DataRequired("请上传头像！")
        ],
        description="头像"
    )
    info = TextAreaField(
        label="简介",
        validators=[
            DataRequired("请输入简介！")
        ],
        description="简介",
        render_kw={
            "class": "form-control",
            "rows": 10
        }
    )
    submit = SubmitField(
        '保存修改',
        render_kw={
            "class": "btn btn-success"
        }
    )


class PwdForm(FlaskForm):
    old_pwd = PasswordField(
        label="旧密码",
        validators=[
            DataRequired("请输入旧密码！")
        ],
        description="密码",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入旧密码！",
            "id": "input_pwd"
        }
    )
    new_pwd = PasswordField(
        label="新密码",
        validators=[
            DataRequired("请输入新密码！")
        ],
        description="新密码",
        render_kw={
            "class": "form-control",
            "placeholder": "请输入新密码！",
            "id": "input_newpwd"
        }
    )
    submit = SubmitField(
        '修改',
        render_kw={
            "class": "btn btn-primary"
        }
    )

    def validate_old_pwd(self, field):
        from flask import session
        pwd = field.data
        name = session["user"]  # 获取用户名
        user = User.query.filter_by(
            name=name
        ).first()
        if not user.check_pwd(pwd):
            raise ValidationError("旧密码错误！")


class CommentForm(FlaskForm):
    content = TextAreaField(
        label="内容",
        validators=[
            DataRequired("请输入评论内容！")
        ],
        description="内容",
        render_kw={
            "id": "input_content"
        }
    )
    submit = SubmitField(
        '提交评论',
        render_kw={
            "class": "btn btn-success",
            "id": "btn-sub"
        }
    )
