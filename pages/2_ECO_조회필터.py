import json
import pandas as pd
import streamlit as st
from database import init_db, search_ecos, get_platforms

init_db()

CHANGE_CATEGORIES = ["전체", "기구 변경", "회로 변경", "S/W 변경", "부품 변경", "기타"]

st.set_page_config(page_title="ECO 조회/필터", page_icon="🔍", layout="wide")
st.title("ECO 조회 및 필터")

# ── 필터 영역 ──
platforms = get_platforms()

col1, col2, col3 = st.columns(3)
with col1:
    sel_platforms = st.multiselect("플랫폼 필터", options=platforms)
with col2:
    sel_category = st.selectbox("변경 구분", options=CHANGE_CATEGORIES)
with col3:
    keyword = st.text_input("키워드 검색 (ECO 번호, 변경 내용)")

# ── 검색 결과 ──
results = search_ecos(
    platforms_filter=sel_platforms if sel_platforms else None,
    category_filter=sel_category,
    keyword=keyword.strip() if keyword.strip() else None,
)

st.write(f"**검색 결과: {len(results)}건**")

if results:
    df = pd.DataFrame(results)
    df["platforms"] = df["platforms"].apply(
        lambda x: ", ".join(json.loads(x)) if x else ""
    )
    display_cols = ["eco_number", "platforms", "change_category",
                    "change_summary", "apply_condition", "created_at"]
    rename_map = {
        "eco_number": "ECO 번호", "platforms": "플랫폼",
        "change_category": "변경 구분", "change_summary": "변경 내용",
        "apply_condition": "적용 시점", "created_at": "등록일시",
    }
    st.dataframe(
        df[display_cols].rename(columns=rename_map),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("조건에 맞는 ECO가 없습니다.")
