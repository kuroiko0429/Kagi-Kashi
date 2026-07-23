from flask import Blueprint, request, render_template, session, redirect, url_for
import random
import datetime
from ..db import get_db

borrow_bp = Blueprint("borrow", __name__, url_prefix="/borrow")

# メインページ
@borrow_bp.route('/')
def main():
    rows = get_db().execute("""
        SELECT
            keys.id,
            keys.key_number,
            keys.available,
            clubs.id AS club_id,
            clubs.name AS club_name,
            clubs.message AS club_message
        FROM keys
        JOIN clubs ON keys.club_id = clubs.id
        ORDER BY keys.id
    """).fetchall()
    keys = []
    for key in rows:
        print(key.keys())
        keys.append({
            "id": key["key_number"],
            "name": key["club_name"],
            "status": key["available"],
            "comment": key["club_message"]
        })
    return render_template('borrow/index.html', keys=keys)

# 行選択時
@borrow_bp.route("/select_row", methods=["POST"])
def select_row():
    data = request.get_json()
    session["key_id"] = data["key_id"]
    session["clab_name"] = data["clab_name"]
    print(f"id: {data["key_id"]}, name: {data["clab_name"]}")
    return {"status": "ok"}

# 学生証のタッチ画面
@borrow_bp.route('/input')
def input():
    return render_template('borrow/input.html')

# 学生証をタッチした時
@borrow_bp.route('/id-post', methods=['POST'])
def send_borrow_data():
    # id, clab_id, student_id, student_name, key_num, borrowed_at, returned_at
    # id?, 部活名, 学籍番号, （学生の名前）, 鍵番号, 借りた時間, 返した時間
    print('POSTデータ受け取ったので処理します')
    id = request.form['student_id'].strip()
    if id[0] == "s":
        id = id[1:]

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
        conn = get_db()
        conn.execute(
            "INSERT INTO borrow_records (club_id, student_id, student_name, key_number, borrowed_at) VALUES (?, ?, ?, ?, datetime('now', 'localtime'))",
            (2, id, id, session["key_id"])
        )
        conn.execute(
            "UPDATE clubs SET status = 'active', message = '' WHERE id = ?",
            (session["key_id"],)
        )
        conn.execute("""
                UPDATE keys
                SET available = ?
                WHERE id = ?
            """, (0, session["key_id"]))
        conn.commit()
        return redirect(url_for('borrow.main'))
    else:
        pass