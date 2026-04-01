import io
import json
from datetime import datetime

import pandas as pd
import streamlit as st

from database import init_db, get_all_data_for_backup, restore_from_backup

init_db()

st.set_page_config(page_title="백업/복원", page_icon="💾", layout="wide")
st.title("데이터 백업 및 복원")

# ── 백업 ──
st.subheader("데이터 백업")
st.write("현재 Google Sheets에 저장된 전체 데이터를 Excel 파일로 다운로드합니다.")

if st.button("백업 파일 생성", type="primary"):
    with st.spinner("데이터 가져오는 중..."):
        data = get_all_data_for_backup()

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        eco_df = pd.DataFrame(data["eco"])
        if not eco_df.empty:
            eco_df.to_excel(writer, sheet_name="eco", index=False)
        else:
            pd.DataFrame(columns=[
                "id", "eco_number", "platforms", "change_category",
                "change_summary", "apply_condition", "attachment_path",
                "created_at", "updated_at",
            ]).to_excel(writer, sheet_name="eco", index=False)

        pf_df = pd.DataFrame(data["platforms"])
        if not pf_df.empty:
            pf_df.to_excel(writer, sheet_name="platforms", index=False)
        else:
            pd.DataFrame(columns=["id", "name"]).to_excel(
                writer, sheet_name="platforms", index=False
            )

    filename = f"ECO_백업_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    st.download_button(
        label=f"📥 {filename} 다운로드",
        data=buf.getvalue(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.document",
    )
    st.success(f"백업 파일 준비 완료! (ECO {len(data['eco'])}건, 플랫폼 {len(data['platforms'])}건)")

st.divider()

# ── 복원 ──
st.subheader("데이터 복원")
st.warning("복원 시 현재 데이터가 **모두 삭제**되고 백업 데이터로 대체됩니다. 신중하게 진행하세요.")

uploaded = st.file_uploader("백업 Excel 파일 업로드", type=["xlsx"])

if uploaded:
    try:
        eco_df = pd.read_excel(uploaded, sheet_name="eco")
        pf_df = pd.read_excel(uploaded, sheet_name="platforms")

        st.write(f"**파일 내용:** ECO {len(eco_df)}건, 플랫폼 {len(pf_df)}건")

        col1, col2 = st.columns(2)
        with col1:
            st.write("**ECO 미리보기**")
            st.dataframe(eco_df.head(10), use_container_width=True, hide_index=True)
        with col2:
            st.write("**플랫폼 미리보기**")
            st.dataframe(pf_df, use_container_width=True, hide_index=True)

        confirm = st.checkbox("현재 데이터를 삭제하고 위 백업 데이터로 복원하겠습니다.")
        if confirm and st.button("복원 실행", type="primary"):
            with st.spinner("복원 중..."):
                eco_data = eco_df.fillna("").to_dict("records")
                pf_data = pf_df.fillna("").to_dict("records")
                restore_from_backup(eco_data, pf_data)
            st.success("복원 완료!")
            st.rerun()
    except Exception as e:
        st.error(f"파일 읽기 실패: {e}")
