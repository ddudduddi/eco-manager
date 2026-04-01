import json
import streamlit as st
from database import (
    init_db, get_all_ecos, add_eco, update_eco, delete_eco,
    get_platforms, add_platform, delete_platform,
)

init_db()

CHANGE_CATEGORIES = ["기구 변경", "회로 변경", "S/W 변경", "부품 변경", "기타"]

st.set_page_config(page_title="ECO 등록관리", page_icon="📝", layout="wide")
st.title("ECO 등록관리")

# ── 플랫폼 마스터 관리 ──
with st.expander("플랫폼 마스터 관리", expanded=False):
    platforms = get_platforms()
    col1, col2 = st.columns([3, 1])
    with col1:
        new_pf = st.text_input("새 플랫폼명", key="new_platform")
    with col2:
        st.write("")  # 정렬용
        st.write("")
        if st.button("추가", key="add_pf"):
            if new_pf.strip():
                if add_platform(new_pf):
                    st.success(f"'{new_pf.strip()}' 추가 완료")
                    st.rerun()
                else:
                    st.warning("이미 존재하는 플랫폼입니다.")
            else:
                st.warning("플랫폼명을 입력하세요.")

    if platforms:
        st.write("**등록된 플랫폼:**")
        for pf in platforms:
            c1, c2 = st.columns([4, 1])
            c1.write(pf)
            if c2.button("삭제", key=f"del_pf_{pf}"):
                delete_platform(pf)
                st.success(f"'{pf}' 삭제 완료")
                st.rerun()
    else:
        st.info("등록된 플랫폼이 없습니다. 먼저 플랫폼을 추가하세요.")

st.divider()

# ── 신규 ECO 등록 ──
st.subheader("신규 ECO 등록")
platforms = get_platforms()

with st.form("eco_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        eco_number = st.text_input("ECO 번호 *")
        selected_platforms = st.multiselect("적용 플랫폼 *", options=platforms)
        change_category = st.selectbox("변경 구분 *", options=CHANGE_CATEGORIES)
    with col2:
        apply_condition = st.text_input("적용 시점 (S/N 또는 날짜)")
        attachment_path = st.text_input("첨부 파일 경로")
    change_summary = st.text_area("변경 내용 요약 *")

    submitted = st.form_submit_button("등록", type="primary")
    if submitted:
        if not eco_number.strip():
            st.error("ECO 번호를 입력하세요.")
        elif not selected_platforms:
            st.error("적용 플랫폼을 하나 이상 선택하세요.")
        elif not change_summary.strip():
            st.error("변경 내용 요약을 입력하세요.")
        else:
            ok, msg = add_eco(eco_number, selected_platforms, change_category,
                              change_summary, apply_condition, attachment_path)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

st.divider()

# ── ECO 목록 및 수정/삭제 ──
st.subheader("등록된 ECO 목록")

ecos = get_all_ecos()
if not ecos:
    st.info("등록된 ECO가 없습니다.")
else:
    import pandas as pd

    df = pd.DataFrame(ecos)
    df["platforms"] = df["platforms"].apply(
        lambda x: ", ".join(json.loads(x)) if x else ""
    )
    display_cols = ["id", "eco_number", "platforms", "change_category",
                    "change_summary", "apply_condition", "created_at"]
    rename_map = {
        "id": "ID", "eco_number": "ECO 번호", "platforms": "플랫폼",
        "change_category": "변경 구분", "change_summary": "변경 내용",
        "apply_condition": "적용 시점", "created_at": "등록일시",
    }
    st.dataframe(
        df[display_cols].rename(columns=rename_map),
        use_container_width=True,
        hide_index=True,
    )

    # ── 수정/삭제 영역 ──
    st.subheader("ECO 수정/삭제")
    eco_ids = [e["id"] for e in ecos]
    eco_labels = [f"{e['eco_number']} (ID: {e['id']})" for e in ecos]
    selected_label = st.selectbox("수정/삭제할 ECO 선택", options=eco_labels)
    selected_idx = eco_labels.index(selected_label)
    sel = ecos[selected_idx]

    tab_edit, tab_del = st.tabs(["수정", "삭제"])

    with tab_edit:
        with st.form("edit_form"):
            col1, col2 = st.columns(2)
            with col1:
                e_number = st.text_input("ECO 번호", value=sel["eco_number"])
                e_platforms = st.multiselect(
                    "적용 플랫폼", options=platforms,
                    default=[p for p in json.loads(sel["platforms"]) if p in platforms],
                )
                e_category = st.selectbox(
                    "변경 구분", options=CHANGE_CATEGORIES,
                    index=CHANGE_CATEGORIES.index(sel["change_category"])
                    if sel["change_category"] in CHANGE_CATEGORIES else 0,
                )
            with col2:
                e_condition = st.text_input("적용 시점", value=sel["apply_condition"])
                e_attach = st.text_input("첨부 파일 경로", value=sel["attachment_path"] or "")
            e_summary = st.text_area("변경 내용 요약", value=sel["change_summary"])

            if st.form_submit_button("수정 저장", type="primary"):
                ok, msg = update_eco(sel["id"], e_number, e_platforms,
                                     e_category, e_summary, e_condition, e_attach)
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with tab_del:
        st.warning(f"**{sel['eco_number']}** 을(를) 삭제하시겠습니까?")
        if st.button("삭제 확인", type="primary"):
            delete_eco(sel["id"])
            st.success("삭제 완료")
            st.rerun()
