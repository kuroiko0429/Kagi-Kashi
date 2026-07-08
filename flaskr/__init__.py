import os
from flask import Flask, render_template, request, session
import flaskr.db as db
import datetime
import random

KEYS = [
    {'id':24, 'name':"ボードゲーム", 'state':0, 'comment':""},
    {'id':0, 'name':"aaaa", 'state':1, 'comment':""},
    {'id':1, 'name':"ボードゲーム", 'state':0, 'comment':""},
    {'id':2, 'name':"ボードゲーム", 'state':1, 'comment':""},
    {'id':3, 'name':"ボードゲーム", 'state':1, 'comment':""},
    {'id':4, 'name':"ボードゲーム", 'state':0, 'comment':""},
    {'id':5, 'name':"ボードゲーム", 'state':1, 'comment':""},
    {'id':6, 'name':"ボードゲーム", 'state':0, 'comment':""},
    {'id':7, 'name':"ボードゲーム", 'state':1, 'comment':""},
    {'id':8, 'name':"ボードゲーム", 'state':1, 'comment':""},
    {'id':9, 'name':"ボードゲーム", 'state':0, 'comment':""},
    {'id':10, 'name':"ボードゲーム", 'state':0, 'comment':""},
    {'id':11, 'name':"ボードゲーム", 'state':1, 'comment':""}
]

clab_name = ""
key_id = 0

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
    # メインページ
    @app.route('/')
    def main():
        cur = db.get_db().cursor()
        cur.execute('SELECT * FROM clubs')
        keys = []
        for row in cur.fetchall():
            keys.append({
                "id": row["id"],
                "name": row["name"],
                "state": row["status"]!='locked',
                "comment": row["message"]
            })
        return render_template('index.html', keys=keys)
    # 行選択時
    @app.route("/select_row", methods=["POST"])
    def select_row():
        data = request.get_json()
        session["key_id"] = data["key_id"]
        session["clab_name"] = data["clab_name"]
        print(f"id: {data["key_id"]}, name: {data["clab_name"]}")
        return {"status": "ok"}
    
    # 学生証のタッチ画面
    @app.route('/input')
    def input():
        return render_template('input.html')
    # 学生証をタッチした時
    @app.route('/id-post', methods=['POST'])
    def sample_form_temp():
        # id, clab_id, student_id, student_name, key_num, borrowed_at, returned_at
        # id?, 部活名, 学籍番号, （学生の名前）, 鍵番号, 借りた時間, 返した時間
        print('POSTデータ受け取ったので処理します')
        id = request.form['student_id'].strip()
        if id[0] == "s":
            id.pop(0)

        text = str(
            f"id: {random.randint(-2147483648, 2147483647)}\n"
            f"clab_name: {session["clab_name"]}\n"
            f"student_id: {id}\n"
            f"key_id: {session["key_id"]}\n"
            f"borrowed_at: {datetime.datetime.now()}\n"
            f"returned_at: {1}"
        )
        
        if len(id) == 7:
            print(text)
            return text
        else:
            return "不正な学籍番号です"

    return app