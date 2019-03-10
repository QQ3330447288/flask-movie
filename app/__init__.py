from flask import Flask, render_template  # render_template主要是返回404页面
from flask_sqlalchemy import SQLAlchemy
import pymysql, os

# 用PyMySQL代替MySQLdb
app = Flask(__name__)
# app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+pymysql://root:123456@123.206.74.24:3306/movie'
app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+pymysql://root:nxl123@localhost:3306/movie'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config["SECRET_KEY"] = '0160a068dba74c5aa21f5b93cc6b95c5'
# app.config["FC_DIR"] = 'os.path.join(os.path.abspath(os.path.dirname(__file__)), "static/uploads/users/")'
# 定义一个文件上传保存路径
app.config["UP_DIR"] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static/uploads/")
app.config["FC_DIR"] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static/uploads/users/")
app.config["PREVIEW_DIR"] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static/uploads/preview_logo/")
app.debug = True
db = SQLAlchemy(app)

from app.home import home as home_blueprint
from app.admin import admin as admin_blueprint

app.register_blueprint(home_blueprint)
app.register_blueprint(admin_blueprint)


@app.errorhandler(404)
def page_not_found(error):
    return render_template("home/404.html"), 404
