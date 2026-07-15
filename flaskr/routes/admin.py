from flask import Blueprint, jsonify, request, render_template
from ..db import get_db

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin")
def admin_page():
    return render_template("admin/admin.html")

@admin_bp.route("/admin/clubs")
def admin_clubs():
    db = get_db()

    clubs = db.execute("""
        SELECT *
        FROM clubs
        ORDER BY id
    """).fetchall()

    return render_template(
        "admin/clubs.html",
        clubs=clubs
    )

@admin_bp.route("/admin/members")
def member_select():
    db = get_db()

    clubs = db.execute("""
        SELECT *
        FROM clubs
        ORDER BY name
    """).fetchall()

    return render_template(
        "admin/member_select.html",
        clubs=clubs
    )

@admin_bp.route("/admin/members/<int:club_id>")
def members(club_id):
    db = get_db()

    club = db.execute("""
        SELECT *
        FROM clubs
        WHERE id=?
    """, (club_id,)).fetchone()

    members = db.execute("""
        SELECT *
        FROM members
        WHERE club_id=?
        ORDER BY name
    """, (club_id,)).fetchall()

    return render_template(
        "admin/members.html",
        club=club,
        members=members
    )

@admin_bp.route("/admin/keys")
def admin_keys():
    db = get_db()

    keys = db.execute("""
        SELECT
            keys.id,
            keys.key_number,
            keys.available,
            clubs.name AS club_name
        FROM keys
        JOIN clubs
        ON keys.club_id = clubs.id
        ORDER BY keys.id
    """).fetchall()

    clubs = db.execute("""
        SELECT *
        FROM clubs
        ORDER BY name
    """).fetchall()

    return render_template(
        "admin/keys.html",
        keys=keys,
        clubs=clubs
    )

@admin_bp.route("/admin/borrow")
def admin_borrow():
    db = get_db()

    records = db.execute("""
        SELECT
            borrow_records.id,
            borrow_records.student_id,
            borrow_records.student_name,
            borrow_records.key_number,
            borrow_records.borrowed_at,
            borrow_records.returned_at,
            clubs.name AS club_name
        FROM borrow_records
        JOIN clubs
        ON borrow_records.club_id = clubs.id
        ORDER BY borrow_records.borrowed_at DESC
    """).fetchall()

    return render_template(
        "admin/borrow.html",
        records=records
    )

@admin_bp.route("/admin/reports")
def admin_reports():
    return render_template("admin/reports.html")

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

# 貸出履歴一覧
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

# サークル情報更新
@admin_bp.route("/api/admin/clubs/<int:club_id>", methods=["PATCH"])
def update_club(club_id):
    db = get_db()
    data = request.get_json()

    db.execute("""
        UPDATE clubs
        SET
            name=?,
            room_number=?,
            leader_student_id=?,
            status=?,
            category=?
        WHERE id=?
    """, (
        data["name"],
        data["room_number"],
        data["leader_student_id"],
        data["status"],
        data["category"],
        club_id
    ))

    db.commit()

    return jsonify({"message":"club updated"})

# サークル削除
@admin_bp.route("/api/admin/clubs/<int:club_id>", methods=["DELETE"])
def delete_club(club_id):
    db = get_db()

    db.execute("""
        DELETE FROM clubs
        WHERE id = ?
    """, (club_id,))

    db.commit()

    return jsonify({"message": "club deleted"})

# メンバー一覧
@admin_bp.route("/api/admin/members", methods=["GET"])
def get_members():
    db = get_db()

    rows = db.execute("""
        SELECT
            members.id,
            members.student_id,
            members.name,
            members.registered_at,
            clubs.name AS club_name
        FROM members
        JOIN clubs
        ON members.club_id = clubs.id
        ORDER BY members.id
    """).fetchall()

    return jsonify([dict(r) for r in rows])

# メンバー追加
@admin_bp.route("/api/admin/members", methods=["POST"])
def add_member():
    db = get_db()
    data = request.get_json()

    db.execute("""
        INSERT INTO members
        (student_id, name, club_id)
        VALUES (?, ?, ?)
    """, (
        data["student_id"],
        data["name"],
        data["club_id"]
    ))

    db.commit()

    return jsonify({"message": "member added"})

# メンバー更新
@admin_bp.route("/api/admin/members/<int:member_id>", methods=["PATCH"])
def update_member(member_id):
    db = get_db()
    data = request.get_json()

    db.execute("""
        UPDATE members
        SET student_id=?, name=?
        WHERE id=?
    """, (
        data["student_id"],
        data["name"],
        member_id
    ))

    db.commit()

    return jsonify({"message":"member updated"})

# メンバー削除
@admin_bp.route("/api/admin/members/<int:member_id>", methods=["DELETE"])
def delete_member(member_id):
    db = get_db()

    db.execute("""
        DELETE FROM members
        WHERE id = ?
    """, (member_id,))

    db.commit()

    return jsonify({"message": "member deleted"})

# 活動報告一覧
@admin_bp.route("/api/admin/activity-reports", methods=["GET"])
def get_reports():
    db = get_db()

    rows = db.execute("""
        SELECT
            activity_reports.id,
            activity_reports.reporter_name,
            activity_reports.student_id,
            activity_reports.report_date,
            activity_reports.description,
            clubs.name AS club_name
        FROM activity_reports
        JOIN clubs
        ON activity_reports.club_id = clubs.id
        ORDER BY activity_reports.report_date DESC
    """).fetchall()

    return jsonify([dict(r) for r in rows])