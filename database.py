import json
from datetime import datetime

import gspread
import streamlit as st
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1Q1LMeYITwWmXWAcwZqKBEEN6dFwCtm4_RxUFGMMZEWY"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

ECO_HEADERS = [
    "id", "eco_number", "platforms", "change_category",
    "change_summary", "apply_condition", "attachment_path",
    "created_at", "updated_at",
]
PLATFORM_HEADERS = ["id", "name"]


@st.cache_resource(ttl=300)
def get_client():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    return client


def get_sheet(sheet_name: str):
    client = get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    return spreadsheet.worksheet(sheet_name)


def init_db():
    """시트에 헤더가 없으면 추가"""
    try:
        eco_ws = get_sheet("eco")
        if not eco_ws.row_values(1):
            eco_ws.append_row(ECO_HEADERS)
    except Exception:
        pass

    try:
        pf_ws = get_sheet("platforms")
        if not pf_ws.row_values(1):
            pf_ws.append_row(PLATFORM_HEADERS)
    except Exception:
        pass


# ── 플랫폼 마스터 ──

def get_platforms():
    ws = get_sheet("platforms")
    records = ws.get_all_records()
    return sorted([r["name"] for r in records if r.get("name")])


def add_platform(name: str):
    ws = get_sheet("platforms")
    records = ws.get_all_records()
    existing = [r["name"] for r in records]
    if name.strip() in existing:
        return False
    next_id = max([r["id"] for r in records], default=0) + 1
    ws.append_row([next_id, name.strip()])
    return True


def delete_platform(name: str):
    ws = get_sheet("platforms")
    records = ws.get_all_records()
    for i, r in enumerate(records):
        if r["name"] == name:
            ws.delete_rows(i + 2)  # +2: 헤더(1) + 0-index(1)
            return True
    return False


# ── ECO CRUD ──

def _next_eco_id():
    ws = get_sheet("eco")
    records = ws.get_all_records()
    if not records:
        return 1
    return max(r["id"] for r in records) + 1


def add_eco(eco_number: str, platforms: list, change_category: str,
            change_summary: str, apply_condition: str, attachment_path: str = ""):
    ws = get_sheet("eco")
    records = ws.get_all_records()
    for r in records:
        if r["eco_number"] == eco_number.strip():
            return False, "이미 존재하는 ECO 번호입니다."

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_id = _next_eco_id()
    row = [
        new_id, eco_number.strip(),
        json.dumps(platforms, ensure_ascii=False),
        change_category, change_summary, apply_condition,
        attachment_path, now, now,
    ]
    ws.append_row(row)
    return True, "등록 완료"


def update_eco(eco_id: int, eco_number: str, platforms: list,
               change_category: str, change_summary: str,
               apply_condition: str, attachment_path: str = ""):
    ws = get_sheet("eco")
    records = ws.get_all_records()

    for r in records:
        if r["eco_number"] == eco_number.strip() and r["id"] != eco_id:
            return False, "이미 존재하는 ECO 번호입니다."

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for i, r in enumerate(records):
        if r["id"] == eco_id:
            row_num = i + 2
            ws.update(f"A{row_num}:I{row_num}", [[
                eco_id, eco_number.strip(),
                json.dumps(platforms, ensure_ascii=False),
                change_category, change_summary, apply_condition,
                attachment_path, r["created_at"], now,
            ]])
            return True, "수정 완료"
    return False, "해당 ECO를 찾을 수 없습니다."


def delete_eco(eco_id: int):
    ws = get_sheet("eco")
    records = ws.get_all_records()
    for i, r in enumerate(records):
        if r["id"] == eco_id:
            ws.delete_rows(i + 2)
            return True
    return False


def get_all_ecos():
    ws = get_sheet("eco")
    records = ws.get_all_records()
    for r in records:
        r["id"] = int(r["id"]) if r.get("id") else 0
    return sorted(records, key=lambda x: x.get("created_at", ""), reverse=True)


def get_ecos_by_platform(platform: str):
    all_ecos = get_all_ecos()
    results = []
    for eco in all_ecos:
        try:
            platforms = json.loads(eco["platforms"])
        except (json.JSONDecodeError, TypeError):
            platforms = []
        if platform in platforms:
            results.append(eco)
    return results


def search_ecos(platforms_filter: list = None, category_filter: str = None,
                keyword: str = None):
    all_ecos = get_all_ecos()
    results = []
    for eco in all_ecos:
        try:
            eco_platforms = json.loads(eco["platforms"])
        except (json.JSONDecodeError, TypeError):
            eco_platforms = []

        if platforms_filter:
            if not any(p in eco_platforms for p in platforms_filter):
                continue

        if category_filter and category_filter != "전체":
            if eco["change_category"] != category_filter:
                continue

        if keyword:
            kw = keyword.lower()
            if (kw not in str(eco["eco_number"]).lower()
                    and kw not in str(eco["change_summary"]).lower()):
                continue

        results.append(eco)
    return results


def get_eco_stats():
    all_ecos = get_all_ecos()
    platform_counts = {}
    for eco in all_ecos:
        try:
            platforms = json.loads(eco["platforms"])
        except (json.JSONDecodeError, TypeError):
            platforms = []
        for p in platforms:
            platform_counts[p] = platform_counts.get(p, 0) + 1
    return {"total": len(all_ecos), "by_platform": platform_counts}


# ── 백업/복원 ──

def get_all_data_for_backup():
    eco_ws = get_sheet("eco")
    pf_ws = get_sheet("platforms")
    return {
        "eco": eco_ws.get_all_records(),
        "platforms": pf_ws.get_all_records(),
    }


def restore_from_backup(eco_data: list, platform_data: list):
    # 플랫폼 복원
    pf_ws = get_sheet("platforms")
    pf_ws.clear()
    pf_ws.append_row(PLATFORM_HEADERS)
    for row in platform_data:
        pf_ws.append_row([row.get("id", 0), row.get("name", "")])

    # ECO 복원
    eco_ws = get_sheet("eco")
    eco_ws.clear()
    eco_ws.append_row(ECO_HEADERS)
    for row in eco_data:
        eco_ws.append_row([
            row.get("id", 0), row.get("eco_number", ""),
            row.get("platforms", "[]"), row.get("change_category", ""),
            row.get("change_summary", ""), row.get("apply_condition", ""),
            row.get("attachment_path", ""), row.get("created_at", ""),
            row.get("updated_at", ""),
        ])
    return True
