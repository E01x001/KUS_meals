import pytz
from datetime import datetime

def get_current_date():
    """현재 날짜 반환 (테스트 날짜 또는 실제 날짜)"""
    import streamlit as st
    
    # 개발자 도구에서 날짜가 선택되었는지 확인
    if 'selected_date' in st.session_state:
        return st.session_state.selected_date
    
    # 기본값으로 현재 날짜 사용
    if 'test_date' not in st.session_state:
        korea_tz = pytz.timezone('Asia/Seoul')
        st.session_state.test_date = datetime.now(korea_tz)
    return st.session_state.test_date 