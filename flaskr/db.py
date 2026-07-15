import sqlite3
import click
from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

        # テーブルが存在しない場合は自動的に初期化する
        cursor = g.db.cursor()
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='clubs'")
            if not cursor.fetchone():
                init_db()
        except sqlite3.Error:
            pass

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    # スキーマの実行
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

    # シードデータの挿入
    # 1. サークル (Clubs)
    clubs_data = [
        # 既存サークル
        ("囲碁・将棋・ボードゲーム部", "401", "2023101", "locked", "本日は17:00から活動予定です。", "#10b981", "cultural"),
        ("Computer Operating Club(COC)", "402", "2023102", "active", "", "#4f46e5", "cultural"),
        ("写真サークル", "102", "2023103", "locked", "", "#ec4899", "association"),
        ("軽音楽部", "204", "2023104", "temp_locked", "機材搬入のため15分ほど施錠します。すぐ戻ります！", "#8b5cf6", "cultural"),
        ("総合創作サークル(SSS)", "105", "2023105", "locked", "", "#f97316", "cultural"),

        # 体育系
        ("バスケットボール部", "111", "2023201", "locked", "", "#f97316", "sports"),
        ("硬式野球部", "112", "2023202", "locked", "", "#3b82f6", "sports"),
        ("バドミントン部", "113", "2023203", "locked", "", "#10b981", "sports"),
        ("卓球部", "114", "2023204", "locked", "", "#ef4444", "sports"),
        ("軟式野球部", "115", "2023205", "locked", "", "#6366f1", "sports"),

        # 文化系
        ("アートクラブ", "211", "2023301", "locked", "", "#f43f5e", "cultural"),
        ("映像研究部", "212", "2023302", "locked", "", "#06b6d4", "cultural"),
        ("DTMサークル Sound Terminal", "213", "2023303", "locked", "", "#84cc16", "cultural"),
        ("eスポーツサークル", "214", "2023304", "locked", "", "#a855f7", "cultural"),
        ("宇宙開発研究会", "215", "2023305", "locked", "", "#1e1b4b", "cultural"),

        # 同好会
        ("Yosakoiソーランサークル", "311", "2023401", "locked", "", "#e11d48", "association"),
        ("ESS(English Speaking Society)", "312", "2023402", "locked", "", "#2563eb", "association"),
        ("TRPG同好会", "313", "2023403", "locked", "", "#16a34a", "association"),
        ("ゲーム開発同好会", "329", "2023404", "locked", "", "#4f46e5", "association"),
        ("ダンスサークル", "331", "2023405", "locked", "", "#e11d48", "association")
    ]
    for name, room, leader, status, msg, color, cat in clubs_data:
        db.execute(
            "INSERT INTO clubs (name, room_number, leader_student_id, status, message, icon_color, category) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, room, leader, status, msg, color, cat)
        )

    # 2. サークルメンバー (Members)
    # 各サークルIDは1から5
    # 退部ロック検証用に登録日時をシード値として設定（佐藤太陽は60日前[解除可]、鈴木美咲は5日前[ロック中]）
    members_data = [
        # ボードゲームサークル (ID: 1)
        ("2023001", "佐藤 太陽", 1, "datetime('now', '-60 days', 'localtime')"),
        ("2023002", "鈴木 美咲", 1, "datetime('now', '-5 days', 'localtime')"),
        # コンピュータ研究会 (ID: 2)
        ("2023003", "高橋 蓮", 2, "datetime('now', '-45 days', 'localtime')"),
        ("2023004", "田中 葵", 2, "datetime('now', '-10 days', 'localtime')"),
        # 写真部 (ID: 3)
        ("2023005", "渡辺 陸", 3, "datetime('now', '-40 days', 'localtime')"),
        ("S2023006", "伊藤 結衣", 3, "datetime('now', '-12 days', 'localtime')"),
        # 軽音楽部 (ID: 4)
        ("2023007", "中村 陽翔", 4, "datetime('now', '-50 days', 'localtime')"),
        ("2023008", "小林 凛", 4, "datetime('now', '-2 days', 'localtime')"),
        # アニメーション研究会 (ID: 5)
        ("2023009", "加藤 颯太", 5, "datetime('now', '-35 days', 'localtime')"),
        ("2023010", "吉田 杏", 5, "datetime('now', '-8 days', 'localtime')"),
    ]
    for student_id, name, club_id, reg_expr in members_data:
        db.execute(
            f"INSERT INTO members (student_id, name, club_id, registered_at) VALUES (?, ?, ?, {reg_expr})",
            (student_id, name, club_id)
        )

    # 3. 貸出中のレコード設定 (コンピュータ研究会は現在活動中(active)なので貸出履歴を挿入)
    db.execute(
        "INSERT INTO borrow_records (club_id, student_id, student_name, key_number, borrowed_at) VALUES (?, ?, ?, ?, datetime('now', '-2 hours'))",
        (2, "2023003", "高橋 蓮", "K-402")
    )
    
    # 4. 貸出中のレコード設定 (軽音楽部は現在一時施錠中(temp_locked)なので貸出履歴を挿入)
    db.execute(
        "INSERT INTO borrow_records (club_id, student_id, student_name, key_number, borrowed_at) VALUES (?, ?, ?, ?, datetime('now', '-4 hours'))",
        (4, "2023007", "中村 陽翔", "K-204")
    )

    # 5. 活動報告書 (Activity Reports) の初期データ
    reports_data = [
        (1, "佐藤 太陽", "2023001", "2026-05-20", "新入生歓迎ゲーム会を実施しました。カタンとカルカソンヌをプレイし、大いに盛り上がりました。"),
        (2, "高橋 蓮", "2023003", "2026-05-22", "Webアプリ制作の勉強会を行いました。FlaskとTailwindを用いたモバイル画面設計について議論しました。"),
        (3, "渡辺 陸", "2023005", "2026-05-18", "学内ポートレート撮影会を開催しました。構図とライティングについての基礎講座も行いました。"),
    ]
    for club_id, reporter_name, student_id, report_date, desc in reports_data:
        db.execute(
            "INSERT INTO activity_reports (club_id, reporter_name, student_id, report_date, description) VALUES (?, ?, ?, ?, ?)",
            (club_id, reporter_name, student_id, report_date, desc)
        )
    # 6. 鍵データ（Keys）
    keys_data = [
        (1, "K-401", 1),
        (2, "K-402", 1),
        (3, "K-102", 1),
        (4, "K-204", 0),
        (5, "K-105", 1),

        (6, "K-111", 1),
        (7, "K-112", 1),
        (8, "K-113", 1),
        (9, "K-114", 1),
        (10, "K-115", 1),

        (11, "K-211", 1),
        (12, "K-212", 1),
        (13, "K-213", 1),
        (14, "K-214", 1),
        (15, "K-215", 1),

        (16, "K-311", 1),
        (17, "K-312", 1),
        (18, "K-313", 1),
        (19, "K-329", 1),
        (20, "K-331", 1)
    ]

    for club_id, key_number, available in keys_data:
        db.execute(
            "INSERT INTO keys (club_id, key_number, available) VALUES (?, ?, ?)",
            (club_id, key_number, available)
        )

    db.commit()


@click.command('init-db')
def init_db_command():
    """既存のデータをクリアし、新規テーブルを作成します。"""
    init_db()
    click.echo('データベースを初期化しました。初期シードデータを投入しました。')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
