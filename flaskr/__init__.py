import os

from flask import Flask, render_template, request


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

    # ページの表示
    @app.route('/')
    def hello():
        keys = [
            {'id':24, 'name':"ボードゲーム", 'state':0, 'comment':""},
            {'id':24, 'name':"aaaa", 'state':1, 'comment':""},
            {'id':24, 'name':"ボードゲーム", 'state':0, 'comment':""},
            {'id':24, 'name':"ボードゲーム", 'state':1, 'comment':""},
            {'id':24, 'name':"ボードゲーム", 'state':1, 'comment':""},
            {'id':24, 'name':"ボードゲーム", 'state':0, 'comment':""},
            {'id':24, 'name':"ボードゲーム", 'state':1, 'comment':""},
            {'id':24, 'name':"ボードゲーム", 'state':0, 'comment':""},
            {'id':24, 'name':"ボードゲーム", 'state':1, 'comment':""},
            {'id':24, 'name':"ボードゲーム", 'state':1, 'comment':""},
            {'id':24, 'name':"ボードゲーム", 'state':0, 'comment':""},
            {'id':24, 'name':"ボードゲーム", 'state':0, 'comment':""},
            {'id':24, 'name':"ボードゲーム", 'state':1, 'comment':""}
        ]
        return render_template('index.html', keys=keys)
    
    @app.route('/input')
    def input():
        return render_template('input.html')
    
    @app.route('/id-post', methods=['POST'])
    def sample_form_temp():
        print('POSTデータ受け取ったので処理します')
        id = request.form['student_id'].strip()
        if id[0] == "s":
            id.pop(0)
        if len(id) == 7:
            return f"学籍番号: {id}"
        else:
            return "不正な学籍番号です"

    return app