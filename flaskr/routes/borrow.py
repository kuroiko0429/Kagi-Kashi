from flask import Blueprint, request, render_template, session
import random
import datetime
from ..db import get_db

borrow_bp = Blueprint("borrow", __name__, url_prefix="/borrow")

# 先頭の"s"/"S"を取り除いて学籍番号を比較できる形にする
def normalize_student_id(student_id):
    student_id = student_id.strip()
    if student_id[:1].lower() == "s":
        student_id = student_id[1:]
    return student_id

# clubs.status(locked/active/temp_locked) と一覧の状態表示(available/borrowed/locked)の対応
STATUS_TO_STATE = {
    "locked": "available",
    "active": "borrowed",
    "temp_locked": "locked",
}

# メインページ
@borrow_bp.route('/')
def main():
    conn = get_db()
    rows = conn.execute("""
        SELECT clubs.id, clubs.name, clubs.status, clubs.message, keys.key_number
        FROM clubs
        LEFT JOIN keys ON keys.club_id = clubs.id
        GROUP BY clubs.id
    """).fetchall()
    active_club_ids = {
        row["club_id"] for row in
        conn.execute("SELECT club_id FROM borrow_records WHERE returned_at IS NULL")
    }
    keys = []
    for row in rows:
        keys.append({
            "id": row["id"],
            "name": row["name"],
            "key_number": row["key_number"],
            "state": STATUS_TO_STATE.get(row["status"], "available"),
            "comment": row["message"],
            "borrowed": row["id"] in active_club_ids
        })
    return render_template('borrow/index.html', keys=keys)

# 行選択時
@borrow_bp.route("/select_row", methods=["POST"])
def select_row():
    data = request.get_json()
    session["id"] = data["key_id"]
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
    id = normalize_student_id(request.form['student_id'])

    club_id = session["id"]

    text = str(
        f"id: {random.randint(-2147483648, 2147483647)}\n"
        f"clab_name: {session["clab_name"]}\n"
        f"student_id: {id}\n"
        f"key_id: {club_id}\n"
        f"borrowed_at: {datetime.datetime.now()}\n"
        f"returned_at: {1}"
    )

    # 部活のメンバーでなければ借りられないようにする
    club_members = get_db().execute(
        "SELECT student_id FROM members WHERE club_id = ?",
        (club_id,)
    ).fetchall()
    if not any(normalize_student_id(member["student_id"]) == id for member in club_members):
        return render_template('borrow/result.html', message="この部活のメンバーではありません。")

    if len(id) == 7:
        print(text)
        conn = get_db()
        key_row = conn.execute(
            "SELECT key_number FROM keys WHERE club_id = ?",
            (club_id,)
        ).fetchone()

        conn.execute(
            "INSERT INTO borrow_records (club_id, student_id, student_name, key_number, borrowed_at) VALUES (?, ?, ?, ?, datetime('now', 'localtime'))",
            (club_id, id, id, key_row["key_number"])
        )
        conn.execute("""
                UPDATE keys
                SET available = ?
                WHERE club_id = ? AND key_number = ?
            """, (0, club_id, key_row["key_number"]))
        conn.execute(
            "UPDATE clubs SET status = 'active', message = '' WHERE id = ?",
            (club_id,)
        )
        conn.commit()
        return render_template('borrow/result.html', message="借りる処理が完了しました。")
    else:
        return render_template('borrow/result.html', message="不正な学籍番号です。")

# 貸出中のサークルを選んで返却
@borrow_bp.route("/return_row", methods=["POST"])
def return_row():
    data = request.get_json()
    club_id = data["club_id"]
    conn = get_db()

    active_borrow = conn.execute(
        "SELECT * FROM borrow_records WHERE club_id = ? AND returned_at IS NULL",
        (club_id,)
    ).fetchone()

    if not active_borrow:
        return {"status": "error", "message": "貸出中の記録が見つかりません"}, 404

    conn.execute(
        "UPDATE borrow_records SET returned_at = datetime('now', 'localtime') WHERE id = ?",
        (active_borrow["id"],)
    )
    conn.execute(
        "UPDATE clubs SET status = 'locked', message = '' WHERE id = ?",
        (club_id,)
    )
    conn.execute(
        "UPDATE keys SET available = 1 WHERE club_id = ? AND key_number = ?",
        (club_id, active_borrow["key_number"])
    )
    conn.commit()
    return {"status": "ok"}
