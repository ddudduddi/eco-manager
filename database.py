import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "eco.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS platforms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS eco (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eco_number TEXT UNIQUE NOT NULL,
            platforms TEXT NOT NULL DEFAULT '[]',
            change_category TEXT NOT NULL DEFAULT '',
            change_summary TEXT NOT NULL DEFAULT '',
            apply_condition TEXT NOT NULL DEFAULT '',
            attachment_path TEXT DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


# ── 플랫폼 마스터 ──

def get_platforms():
    conn = get_conn()
    rows = conn.execute("SELECT name FROM platforms ORDER BY name").fetchall()
    conn.close()
    return [r["name"] for r in rows]


def add_platform(name: str):
    conn = get_conn()
    try:
        conn.execute("INSERT INTO platforms (name) VALUES (?)", (name.strip(),))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_platform(name: str):
    conn = get_conn()
    conn.execute("DELETE FROM platforms WHERE name = ?", (name,))
    conn.commit()
    conn.close()


# ── ECO CRUD ──

def add_eco(eco_number: str, platforms: list, change_category: str,
            change_summary: str, apply_condition: str, attachment_path: str = ""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    try:
        conn.execute(
            """INSERT INTO eco
               (eco_number, platforms, change_category, change_summary,
                apply_condition, attachment_path, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (eco_number.strip(), json.dumps(platforms, ensure_ascii=False),
             change_category, change_summary, apply_condition,
             attachment_path, now, now)
        )
        conn.commit()
        return True, "등록 완료"
    except sqlite3.IntegrityError:
        return False, "이미 존재하는 ECO 번호입니다."
    finally:
        conn.close()


def update_eco(eco_id: int, eco_number: str, platforms: list,
               change_category: str, change_summary: str,
               apply_condition: str, attachment_path: str = ""):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_conn()
    try:
        conn.execute(
            """UPDATE eco SET eco_number=?, platforms=?, change_category=?,
               change_summary=?, apply_condition=?, attachment_path=?, updated_at=?
               WHERE id=?""",
            (eco_number.strip(), json.dumps(platforms, ensure_ascii=False),
             change_category, change_summary, apply_condition,
             attachment_path, now, eco_id)
        )
        conn.commit()
        return True, "수정 완료"
    except sqlite3.IntegrityError:
        return False, "이미 존재하는 ECO 번호입니다."
    finally:
        conn.close()


def delete_eco(eco_id: int):
    conn = get_conn()
    conn.execute("DELETE FROM eco WHERE id = ?", (eco_id,))
    conn.commit()
    conn.close()


def get_all_ecos():
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM eco ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_ecos_by_platform(platform: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM eco ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    results = []
    for r in rows:
        platforms = json.loads(r["platforms"])
        if platform in platforms:
            results.append(dict(r))
    return results


def search_ecos(platforms_filter: list = None, category_filter: str = None,
                keyword: str = None):
    all_ecos = get_all_ecos()
    results = []
    for eco in all_ecos:
        eco_platforms = json.loads(eco["platforms"])

        if platforms_filter:
            if not any(p in eco_platforms for p in platforms_filter):
                continue

        if category_filter and category_filter != "전체":
            if eco["change_category"] != category_filter:
                continue

        if keyword:
            kw = keyword.lower()
            if (kw not in eco["eco_number"].lower()
                    and kw not in eco["change_summary"].lower()):
                continue

        results.append(eco)
    return results


def get_eco_stats():
    all_ecos = get_all_ecos()
    platform_counts = {}
    for eco in all_ecos:
        for p in json.loads(eco["platforms"]):
            platform_counts[p] = platform_counts.get(p, 0) + 1
    return {"total": len(all_ecos), "by_platform": platform_counts}
