import os
from flask import Flask, render_template, request, session
import flaskr.db as db
import datetime
import random
from .routes.admin import admin_bp
from .routes.mobile import mobile_bp
from .routes.borrow import borrow_bp
from . import db

def create_app(test_config=None):
    # appの作成と設定
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    # テスト中か
    if test_config is None:
        # 設定用ファイルがあればそれを読み込む
        app.config.from_pyfile('config.py', silent=True)
    else:
        # テスト中ならテスト用設定を読み込む
        app.config.from_mapping(test_config)

    # インスタンスフォルダの生成
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)    #DBの初期化

    app.register_blueprint(admin_bp)    #管理者側のBlueprint登録
    app.register_blueprint(mobile_bp)   #スマホ版(kagi-kashi-ex)のBlueprint登録
    app.register_blueprint(borrow_bp)   #本体のBlueprint登録

    return app