import streamlit as st
from database import init_db, get_eco_stats, get_platforms

init_db()

st.set_page_config(
    page_title="ECO 관리 시스템",
    page_icon="📋",
    layout="wide",
)

# ── 사이드바: 현황 요약 ──
with st.sidebar:
    st.header("ECO 현황")
    stats = get_eco_stats()
    st.metric("전체 ECO 건수", f"{stats['total']}건")

    if stats["by_platform"]:
        st.subheader("플랫폼별 건수")
        for name, cnt in sorted(stats["by_platform"].items()):
            st.write(f"- **{name}**: {cnt}건")
    else:
        st.caption("등록된 ECO가 없습니다.")

# ── 메인 영역 ──
st.title("ECO 관리 및 체크시트 자동 생성")

st.markdown("""
### 사용 안내

| 메뉴 | 기능 |
|------|------|
| **ECO 등록관리** | ECO 신규 등록, 수정, 삭제 및 플랫폼 마스터 관리 |
| **ECO 조회필터** | 플랫폼별/변경구분별 필터링, 키워드 검색 |
| **체크시트 생성** | 플랫폼 선택 후 검사용 체크시트 Excel 다운로드 |

왼쪽 사이드바의 페이지 메뉴에서 원하는 기능을 선택하세요.
""")
