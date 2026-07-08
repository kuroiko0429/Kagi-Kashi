from flask import Blueprint, jsonify, request
from db import get_db

admin_bp = Blueprint("admin", __name__)

# 鍵一覧（全鍵＋サークル情報）
@admin_bp.route("/api/admin/keys", methods=["GET"])
def get_keys():
    db = get_db()

    rows = db.execute("""
        SELECT 
            keys.id,
            keys.key_number,
            keys.available,
            clubs.id AS club_id,
            clubs.name AS club_name
        FROM keys
        JOIN clubs ON keys.club_id = clubs.id
        ORDER BY keys.id
    """).fetchall()

    return jsonify([dict(r) for r in rows])

# 鍵追加
@admin_bp.route("/api/admin/keys", methods=["POST"])
def add_key():
    db = get_db()
    data = request.get_json()

    club_id = data["club_id"]
    key_number = data["key_number"]

    db.execute("""
        INSERT INTO keys (club_id, key_number, available)
        VALUES (?, ?, 1)
    """, (club_id, key_number))

    db.commit()
    return jsonify({"message": "key added"})

# 鍵の状態更新（貸出/返却）
@admin_bp.route("/api/admin/keys/<int:key_id>", methods=["PATCH"])
def update_key(key_id):
    db = get_db()
    data = request.get_json()

    available = data["available"]  # 1 or 0

    db.execute("""
        UPDATE keys
        SET available = ?
        WHERE id = ?
    """, (available, key_id))

    db.commit()
    return jsonify({"message": "key updated"})

# サークル一覧（管理者用）
@admin_bp.route("/api/admin/clubs", methods=["GET"])
def get_clubs():
    db = get_db()

    rows = db.execute("""
        SELECT *
        FROM clubs
        ORDER BY id
    """).fetchall()

    return jsonify([dict(r) for r in rows])

# サークル追加
@admin_bp.route("/api/admin/clubs", methods=["POST"])
def add_club():
    db = get_db()
    data = request.get_json()

    db.execute("""
        INSERT INTO clubs (name, room_number, leader_student_id, status, message, icon_color, category)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["name"],
        data["room_number"],
        data.get("leader_student_id"),
        "locked",
        data.get("message", ""),
        data["icon_color"],
        data["category"]
    ))

    db.commit()
    return jsonify({"message": "club added"})

# 部長変更
@admin_bp.route("/api/admin/clubs/<int:club_id>/leader", methods=["PATCH"])
def update_leader(club_id):
    db = get_db()
    data = request.get_json()

    db.execute("""
        UPDATE clubs
        SET leader_student_id = ?
        WHERE id = ?
    """, (data["leader_student_id"], club_id))

    db.commit()
    return jsonify({"message": "leader updated"})

# 貸出履歴一覧（重要）
@admin_bp.route("/api/admin/borrow-records", methods=["GET"])
def get_borrow_records():
    db = get_db()

    rows = db.execute("""
        SELECT 
            borrow_records.id,
            borrow_records.student_id,
            borrow_records.student_name,
            borrow_records.key_number,
            borrow_records.borrowed_at,
            borrow_records.returned_at,
            clubs.name AS club_name
        FROM borrow_records
        JOIN clubs ON borrow_records.club_id = clubs.id
        ORDER BY borrow_records.borrowed_at DESC
    """).fetchall()

    return jsonify([dict(r) for r in rows])

# 返却処理
@admin_bp.route("/api/admin/borrow-records/<int:record_id>/return", methods=["PATCH"])
def return_key(record_id):
    db = get_db()

    # 返却時間を入れる
    db.execute("""
        UPDATE borrow_records
        SET returned_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (record_id,))

    db.commit()
    return jsonify({"message": "returned"}) 