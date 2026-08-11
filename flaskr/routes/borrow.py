from flask import Blueprint, request, render_template, session
import datetime
from ..db import get_db

borrow_bp = Blueprint("borrow", __name__, url_prefix="/borrow")


# 学籍番号を比較しやすい形にする
def normalize_student_id(student_id):
    student_id = student_id.strip()

    if student_id[:1].lower() == "s":
        student_id = student_id[1:]

    if student_id[:1].lower() == "a" and student_id[-1:].lower() == "a":
        student_id = student_id[1:-1]

    return student_id


# clubs.status と画面上の状態の対応
STATUS_TO_STATE = {
    "locked": "available",
    "active": "borrowed",
    "temp_locked": "locked",
}


# メインページ
# メインページ
@borrow_bp.route('/')
def main():
    conn = get_db()

    # サークル鍵
    club_rows = conn.execute("""
        SELECT
            clubs.id,
            clubs.name,
            clubs.status,
            clubs.message,
            keys.key_number,
            keys.available
        FROM clubs
        LEFT JOIN keys
        ON keys.club_id = clubs.id
        GROUP BY clubs.id
    """).fetchall()

    # 共用鍵
    common_key_rows = conn.execute("""
        SELECT
            id,
            key_number,
            name,
            available
        FROM common_keys
        ORDER BY id
    """).fetchall()

    # サークル鍵が現在貸出中のサークル
    club_borrowed_ids = {
        row["club_id"]
        for row in conn.execute("""
            SELECT club_id
            FROM borrow_records
            WHERE returned_at IS NULL
        """).fetchall()
    }

    # 共用鍵が現在貸出中の鍵
    common_borrowed_ids = {
        row["common_key_id"]
        for row in conn.execute("""
            SELECT common_key_id
            FROM common_key_borrow_records
            WHERE returned_at IS NULL
        """).fetchall()
    }

    keys = []

    # サークル鍵を一覧に追加
    for row in club_rows:

        # 実際の貸出履歴から判定
        borrowed = row["id"] in club_borrowed_ids

        # 貸出中なら borrowed
        if borrowed:
            state = "borrowed"

        # 貸出中でなく、一時施錠なら locked
        elif row["status"] == "temp_locked":
            state = "locked"

        # それ以外は保管中
        else:
            state = "available"

        keys.append({
            "id": row["id"],
            "name": row["name"],
            "key_number": row["key_number"],
            "state": state,
            "comment": row["message"],
            "borrowed": borrowed,
            "type": "club"
        })

    # 共用鍵を一覧に追加
    for row in common_key_rows:

        # 実際の貸出履歴から判定
        borrowed = row["id"] in common_borrowed_ids

        if borrowed:
            state = "borrowed"
        else:
            state = "available"

        keys.append({
            "id": row["id"],
            "name": row["name"],
            "key_number": row["key_number"],
            "state": state,
            "comment": "共用鍵",
            "borrowed": borrowed,
            "type": "common"
        })

    return render_template(
        'borrow/index.html',
        keys=keys
    )
# 行選択
@borrow_bp.route("/select_row", methods=["POST"])
def select_row():

    data = request.get_json()

    key_type = data["type"]

    if key_type == "club":

        session["club_id"] = data["id"]
        session["borrow_type"] = "club"

        print(
            f"サークル鍵選択: club_id={data['id']}"
        )

    elif key_type == "common":

        session["common_key_id"] = data["id"]
        session["borrow_type"] = "common"

        print(
            f"共用鍵選択: common_key_id={data['id']}"
        )

    return {"status": "ok"}


# 共用鍵使用サークル選択画面
@borrow_bp.route("/select_club")
def select_club():

    conn = get_db()

    clubs = conn.execute("""
        SELECT
            id,
            name
        FROM clubs
        ORDER BY name
    """).fetchall()

    return render_template(
        "borrow/select_club.html",
        clubs=clubs
    )


# 共用鍵使用サークル選択
@borrow_bp.route("/select_common_club", methods=["POST"])
def select_common_club():

    data = request.get_json()

    session["club_id"] = data["club_id"]

    print(
        f"共用鍵使用サークル選択: club_id={data['club_id']}"
    )

    return {
        "status": "ok"
    }


# 学生証入力画面
@borrow_bp.route('/input')
def input():
    return render_template(
        'borrow/input.html'
    )


# 学生証をタッチしたとき
@borrow_bp.route('/id-post', methods=['POST'])
def send_borrow_data():

    print("POSTデータ受け取ったので処理します")

    student_id = normalize_student_id(
        request.form['student_id']
    )

    borrow_type = session.get("borrow_type")

    club_id = session.get("club_id")

    if not club_id:
        return render_template(
            'borrow/result.html',
            message="サークルが選択されていません。"
        )

    conn = get_db()

    # 共通処理：メンバー確認
    member = conn.execute("""
        SELECT
            student_id,
            name
        FROM members
        WHERE club_id = ?
    """, (club_id,)).fetchall()

    member_data = None

    for m in member:

        if normalize_student_id(
            m["student_id"]
        ) == student_id:

            member_data = m
            break

    if member_data is None:

        return render_template(
            'borrow/result.html',
            message="この部活のメンバーではありません。"
        )

    # 学籍番号チェック
    if len(student_id) != 7:

        return render_template(
            'borrow/result.html',
            message="不正な学籍番号です。"
        )

    student_name = member_data["name"]

    # サークル鍵の場合
    if borrow_type == "club":

        key = conn.execute("""
            SELECT
                id,
                key_number,
                available
            FROM keys
            WHERE club_id = ?
        """, (club_id,)).fetchone()

        if not key:

            return render_template(
                'borrow/result.html',
                message="このサークルの鍵が見つかりません。"
            )

        if key["available"] == 0:

            return render_template(
                'borrow/result.html',
                message="この鍵は現在貸出中です。"
            )

        # 貸出履歴
        conn.execute("""
            INSERT INTO borrow_records
            (
                club_id,
                student_id,
                student_name,
                key_number,
                borrowed_at
            )
            VALUES
            (?, ?, ?, ?, datetime('now', 'localtime'))
        """, (
            club_id,
            student_id,
            student_name,
            key["key_number"]
        ))

        # 鍵を貸出中にする
        conn.execute("""
            UPDATE keys
            SET available = 0
            WHERE id = ?
        """, (key["id"],))

        # サークルをactiveにする
        conn.execute("""
            UPDATE clubs
            SET status = 'active',
                message = ''
            WHERE id = ?
        """, (club_id,))

        conn.commit()

        return render_template(
            'borrow/result.html',
            message="借りる処理が完了しました。"
        )

    # 共用鍵の場合
    elif borrow_type == "common":

        common_key_id = session.get(
            "common_key_id"
        )

        if not common_key_id:

            return render_template(
                'borrow/result.html',
                message="共用鍵が選択されていません。"
            )

        common_key = conn.execute("""
            SELECT
                id,
                key_number,
                name,
                available
            FROM common_keys
            WHERE id = ?
        """, (
            common_key_id,
        )).fetchone()

        if not common_key:

            return render_template(
                'borrow/result.html',
                message="共用鍵が見つかりません。"
            )

        # 共用鍵が貸出中か確認
        if common_key["available"] == 0:

            return render_template(
                'borrow/result.html',
                message="この共用鍵は現在貸出中です。"
            )

        # 共用鍵の貸出履歴を登録
        conn.execute("""
            INSERT INTO common_key_borrow_records
            (
                common_key_id,
                club_id,
                student_id,
                borrowed_at
            )
            VALUES
            (?, ?, ?, datetime('now', 'localtime'))
        """, (
            common_key_id,
            club_id,
            student_id
        ))

        # 共用鍵を貸出中にする
        conn.execute("""
            UPDATE common_keys
            SET available = 0
            WHERE id = ?
        """, (
            common_key_id,
        ))

        # サークルを活動中にする
        conn.execute("""
            UPDATE clubs
            SET status = 'active',
                message = ''
            WHERE id = ?
        """, (
            club_id,
        ))

        conn.commit()

        return render_template(
            'borrow/result.html',
            message=f"{common_key['name']}の貸出が完了しました。"
        )


@borrow_bp.route("/return_row", methods=["POST"])
def return_row():
    data = request.get_json()

    selected_id = data["id"]
    key_type = data.get("type")

    conn = get_db()

    # サークル鍵の返却
    if key_type == "club":

        club_id = selected_id

        active_borrow = conn.execute("""
            SELECT *
            FROM borrow_records
            WHERE club_id = ?
            AND returned_at IS NULL
        """, (
            club_id,
        )).fetchone()

        if not active_borrow:

            return {
                "status": "error",
                "message": "サークル鍵の貸出中の記録が見つかりません"
            }, 404

        # サークル鍵を返却済みにする
        conn.execute("""
            UPDATE borrow_records
            SET returned_at = datetime('now', 'localtime')
            WHERE id = ?
        """, (
            active_borrow["id"],
        ))

        # サークル鍵を保管中にする
        conn.execute("""
            UPDATE keys
            SET available = 1
            WHERE club_id = ?
            AND key_number = ?
        """, (
            club_id,
            active_borrow["key_number"]
        ))

    # 共用鍵の返却
    elif key_type == "common":

        # selected_id は共用鍵のID
        common_key_id = selected_id

        common_borrow = conn.execute("""
            SELECT *
            FROM common_key_borrow_records
            WHERE common_key_id = ?
            AND returned_at IS NULL
        """, (
            common_key_id,
        )).fetchone()

        if not common_borrow:

            return {
                "status": "error",
                "message": "共用鍵の貸出中の記録が見つかりません"
            }, 404

        # 共用鍵を返却済みにする
        conn.execute("""
            UPDATE common_key_borrow_records
            SET returned_at = datetime('now', 'localtime')
            WHERE id = ?
        """, (
            common_borrow["id"],
        ))

        # 共用鍵を保管中にする
        conn.execute("""
            UPDATE common_keys
            SET available = 1
            WHERE id = ?
        """, (
            common_key_id,
        ))

        # 貸出記録から使用していたサークルを取得
        club_id = common_borrow["club_id"]

    else:

        return {
            "status": "error",
            "message": "返却する鍵の種類が正しくありません"
        }, 400

    # サークル鍵・共用鍵の貸出状況を確認
    club_borrow = conn.execute("""
        SELECT id
        FROM borrow_records
        WHERE club_id = ?
        AND returned_at IS NULL
    """, (
        club_id,
    )).fetchone()

    common_borrow = conn.execute("""
        SELECT id
        FROM common_key_borrow_records
        WHERE club_id = ?
        AND returned_at IS NULL
    """, (
        club_id,
    )).fetchone()

    # どちらか一方でも貸出中なら活動中
    if club_borrow or common_borrow:

        conn.execute("""
            UPDATE clubs
            SET status = 'active',
                message = ''
            WHERE id = ?
        """, (
            club_id,
        ))

    # 両方とも返却済みなら保管中
    else:

        conn.execute("""
            UPDATE clubs
            SET status = 'locked',
                message = ''
            WHERE id = ?
        """, (
            club_id,
        ))

    conn.commit()

    return {
        "status": "ok"
    }
