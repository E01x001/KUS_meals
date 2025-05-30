# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import hashlib
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
import pytz
import sqlite3
from crawling import get_today_menu, get_weekly_menu
from utils import get_current_date

# 개발 모드 설정
DEV_MODE = True  # 개발 중일 때만 True로 설정

# 페이지 기본 설정
st.set_page_config(
    page_title="KUS Meals",
    page_icon="🍽️",
    layout="wide"  # 전체 화면 사용
)

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect('data.db', check_same_thread=False)
    c = conn.cursor()
    
    # 사용자 테이블 생성
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, password TEXT, name TEXT)''')
    
    # 리뷰 테이블 생성
    c.execute('''CREATE TABLE IF NOT EXISTS reviews
                 (date TEXT, username TEXT, rating INTEGER, 
                  review_text TEXT, recommended BOOLEAN)''')
    
    # 선호도 테이블 생성
    c.execute('''CREATE TABLE IF NOT EXISTS preferences
                 (username TEXT PRIMARY KEY, preferences TEXT)''')
    
    conn.commit()
    return conn

# 데이터베이스 연결
if 'db_connection' not in st.session_state:
    st.session_state.db_connection = init_db()

# 캐시 설정
@st.cache_data(ttl=3600)  # 1시간 캐시
def cached_get_today_menu():
    return get_today_menu()

@st.cache_data(ttl=3600)  # 1시간 캐시
def cached_get_weekly_menu():
    return get_weekly_menu()

# 현재 날짜 정보
korea_tz = pytz.timezone('Asia/Seoul')
now = datetime.now(korea_tz)

# 세션 상태 초기화
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'test_date' not in st.session_state:
    st.session_state.test_date = now

def get_current_date():
    """현재 날짜 반환 (테스트 날짜 또는 실제 날짜)"""
    return st.session_state.test_date

# 음식 취향 관련 상수
TASTE_PREFERENCES = {
    "좋아하는 음식 종류": [
        "한식", "중식", "일식", "양식",
        "매운 음식", "담백한 음식", "해산물", "육류",
        "채식", "면류", "밥류"
    ],
    "싫어하는 재료": [
        "마늘", "양파", "파", "생강",
        "해산물", "육류", "달걀", "유제품",
        "견과류", "버섯"
    ],
    "선호하는 맛": [
        "매운맛", "단맛", "짠맛", "신맛",
        "담백한맛", "고소한맛", "얼큰한맛"
    ],
    "알레르기 정보": [
        "난류", "우유", "메밀", "땅콩",
        "대두", "밀", "고등어", "게",
        "새우", "돼지고기", "복숭아", "토마토",
        "아황산류", "호두", "닭고기", "쇠고기",
        "오징어", "조개류"
    ]
}

def load_users():
    """사용자 목록 로드"""
    conn = st.session_state.db_connection
    return pd.read_sql_query("SELECT * FROM users", conn)

def register_user(username, password, name):
    """사용자 등록"""
    try:
        conn = st.session_state.db_connection
        c = conn.cursor()
        
        # 중복 사용자 확인
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        if c.fetchone() is not None:
            return False, "이미 존재하는 사용자 아이디입니다."
        
        # 새 사용자 추가
        c.execute("INSERT INTO users (username, password, name) VALUES (?, ?, ?)",
                 (username, hash_password(password), name))
        conn.commit()
        return True, "회원가입이 완료되었습니다!"
    except Exception as e:
        return False, f"회원가입 중 오류가 발생했습니다: {str(e)}"

def verify_login(username, password):
    """로그인 확인"""
    try:
        conn = st.session_state.db_connection
        c = conn.cursor()
        
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        
        if user is None:
            return False, "존재하지 않는 사용자입니다."
        
        if user[1] == hash_password(password):  # user[1]은 password 컬럼
            return True, user[2]  # user[2]는 name 컬럼
        return False, "비밀번호가 일치하지 않습니다."
    except Exception as e:
        return False, f"로그인 중 오류가 발생했습니다: {str(e)}"

def logout():
    st.session_state.is_logged_in = False
    st.session_state.username = None
    st.session_state.user_name = None

def get_todays_reviews():
    """오늘의 리뷰 가져오기"""
    conn = st.session_state.db_connection
    current_date = get_current_date()
    today_date = current_date.strftime("%Y-%m-%d")
    return pd.read_sql_query(
        "SELECT * FROM reviews WHERE date = ?",
        conn,
        params=(today_date,)
    )

def save_review(username, rating, review_text, recommended):
    """리뷰 저장"""
    try:
        conn = st.session_state.db_connection
        c = conn.cursor()
        current_date = get_current_date()
        today_date = current_date.strftime("%Y-%m-%d")
        
        # 같은 날짜의 기존 리뷰 삭제
        c.execute("DELETE FROM reviews WHERE date = ? AND username = ?",
                 (today_date, username))
        
        # 새 리뷰 추가
        c.execute("""INSERT INTO reviews 
                    (date, username, rating, review_text, recommended)
                    VALUES (?, ?, ?, ?, ?)""",
                 (today_date, username, rating, review_text, recommended))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"리뷰 저장 중 오류가 발생했습니다: {str(e)}")
        return False

def save_preferences(username, preferences):
    """사용자 선호도 저장"""
    try:
        conn = st.session_state.db_connection
        c = conn.cursor()
        preferences_json = json.dumps(preferences, ensure_ascii=False)
        
        c.execute("INSERT OR REPLACE INTO preferences (username, preferences) VALUES (?, ?)",
                 (username, preferences_json))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"선호도 저장 중 오류가 발생했습니다: {str(e)}")
        return False

def load_preferences():
    """모든 사용자의 선호도 로드"""
    try:
        conn = st.session_state.db_connection
        c = conn.cursor()
        preferences = {}
        
        for row in c.execute("SELECT * FROM preferences"):
            preferences[row[0]] = json.loads(row[1])
        return preferences
    except Exception as e:
        st.error(f"선호도 로드 중 오류가 발생했습니다: {str(e)}")
        return {}

def get_menu_recommendation(menu_df, user_preferences):
    # 메뉴 텍스트 추출
    menu_text = "오늘의 메뉴:\n"
    for _, row in menu_df.iterrows():
        if today_str in row['날짜']:
            menu_text += f"{row['구분']}: {row['메뉴']}\n"
    
    # 사용자 취향 텍스트 생성
    pref_text = "사용자 취향:\n"
    for category, items in user_preferences.items():
        if items:  # 선택된 항목이 있는 경우만
            if category == "알레르기 정보":
                pref_text += f"⚠️ 알레르기: {', '.join(items)}\n"
            else:
                pref_text += f"{category}: {', '.join(items)}\n"
    
    # Gemini 프롬프트 생성
    prompt = f"""
당신은 사용자의 음식 취향과 알레르기를 고려하여 학식 메뉴를 추천하는 전문가입니다.
다음 정보를 바탕으로 오늘 학식을 먹을지 추천해주세요:

{menu_text}

{pref_text}

다음 형식으로 답변해주세요:
1. 추천 여부 (한 문장)
2. 추천 이유 또는 비추천 이유 (2-3문장)
3. 주의사항 (알레르기 관련 주의사항이 있다면 반드시 포함)
"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"메뉴 추천 중 오류가 발생했습니다: {str(e)}"

def display_preference_settings():
    st.subheader("🍽️ 음식 취향 설정")
    
    # 현재 사용자의 취향 불러오기
    all_prefs = load_preferences()
    user_prefs = all_prefs.get(st.session_state.username, {})
    
    # 취향 설정 UI
    new_prefs = {}
    
    # 알레르기 정보를 맨 위로 이동
    categories = ["알레르기 정보"] + [cat for cat in TASTE_PREFERENCES.keys() if cat != "알레르기 정보"]
    
    for category in categories:
        if category == "알레르기 정보":
            st.write("### ⚠️ 알레르기 정보")
            st.write("알레르기가 있는 식재료를 모두 선택해주세요.")
        else:
            st.write(f"### {category}")
        
        selected = st.multiselect(
            "선택해주세요 (여러 개 선택 가능)",
            TASTE_PREFERENCES[category],
            default=user_prefs.get(category, []),
            key=f"pref_{category}"
        )
        new_prefs[category] = selected
        
        # 알레르기 선택 시 주의사항 표시
        if category == "알레르기 정보" and selected:
            st.warning("⚠️ 선택하신 알레르기 유발 식품이 포함된 메뉴는 피하시는 것이 좋습니다.")
    
    # 저장 버튼
    if st.button("취향 저장"):
        save_preferences(st.session_state.username, new_prefs)
        st.success("취향이 저장되었습니다!")
        return new_prefs
    
    return user_prefs

def format_menu_text(menu_text):
    """메뉴 텍스트를 보기 좋게 포맷팅"""
    if pd.isna(menu_text):
        return ""
    
    # 메뉴 항목을 쉼표나 슬래시로 구분
    items = []
    for item in str(menu_text).replace('/', ',').split(','):
        # 각 항목 앞뒤 공백 제거
        item = item.strip()
        # 긴 단어에 띄어쓰기 추가 (예: 치킨마요덮밥 -> 치킨마요 덮밥)
        if len(item) > 4 and '덮밥' in item:
            item = item.replace('덮밥', ' 덮밥')
        if len(item) > 4 and '김밥' in item:
            item = item.replace('김밥', ' 김밥')
        if len(item) > 4 and '라면' in item:
            item = item.replace('라면', ' 라면')
        if len(item) > 4 and '우동' in item:
            item = item.replace('우동', ' 우동')
        if len(item) > 4 and '국수' in item:
            item = item.replace('국수', ' 국수')
        items.append(item)
    
    # 쉼표와 공백으로 메뉴 항목 구분
    return ', '.join(items)

def align_menus_by_date(student_df, staff_df):
    """학생식당과 교직원식당 메뉴를 날짜별로 정렬"""
    # 데이터프레임 복사
    student = student_df.copy()
    staff = staff_df.copy()
    
    # 메뉴 텍스트 포맷팅
    student['메뉴'] = student['메뉴'].apply(format_menu_text)
    staff['메뉴'] = staff['메뉴'].apply(format_menu_text)
    
    # 날짜별로 정렬
    student = student.sort_values(['날짜', '구분'])
    staff = staff.sort_values(['날짜', '구분'])
    
    return student, staff

def display_menu_dataframe(df, title, current_date_str=None):
    """
    메뉴 데이터프레임을 표시
    current_date_str: 현재 날짜 문자열 (MM.DD 형식)
    """
    if df.empty:
        st.info(f"{title}의 메뉴 정보가 없습니다.")
    else:
        # 오늘 날짜 행 강조를 위한 스타일링
        def highlight_today(row):
            if current_date_str and current_date_str in row['날짜']:
                return ['background-color: #FFE4B5'] * len(row)
            return [''] * len(row)
        
        # 스타일이 적용된 데이터프레임 표시
        styled_df = df.style.apply(highlight_today, axis=1)
        st.dataframe(
            styled_df,
            hide_index=True,
            column_config={
                "날짜": st.column_config.TextColumn(
                    "날짜",
                    width="small",
                    help="식단 제공 날짜"
                ),
                "구분": st.column_config.TextColumn(
                    "구분",
                    width="small",
                    help="조식/중식/석식"
                ),
                "메뉴": st.column_config.TextColumn(
                    "메뉴",
                    width="large",
                    help="제공되는 메뉴"
                )
            },
            height=min(35 + len(df) * 35, 500)  # 행 수에 따른 적절한 높이 설정
        )

def get_weekday_name(date_str):
    """날짜 문자열(MM.DD)을 받아서 해당 요일을 반환"""
    try:
        # 현재 연도와 날짜 문자열을 조합
        current_year = now.year
        date_obj = datetime.strptime(f"{current_year}.{date_str}", "%Y.%m.%d")
        weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
        return weekdays[date_obj.weekday()]
    except:
        return ""

def display_weekly_menu(student_df, staff_df):
    """주간 메뉴를 요일별로 표시"""
    # 데이터프레임에 요일 정보 추가
    student_df = student_df.copy()
    staff_df = staff_df.copy()
    
    student_df['요일'] = student_df['날짜'].apply(get_weekday_name)
    staff_df['요일'] = staff_df['날짜'].apply(get_weekday_name)
    
    # 주말 제외
    weekdays = ["월요일", "화요일", "수요일", "목요일", "금요일"]
    student_df = student_df[student_df['요일'].isin(weekdays)]
    staff_df = staff_df[staff_df['요일'].isin(weekdays)]
    
    # 현재 날짜
    current_date_str = get_current_date().strftime("%m.%d")
    
    # 요일별로 탭 생성
    for weekday in weekdays:
        with st.expander(f"📅 {weekday}", expanded=(weekday == "월요일")):
            col1, col2 = st.columns(2)
            
            # 학생 식당 메뉴
            with col1:
                st.markdown(f"#### 📍 학생 식당")
                day_student = student_df[student_df['요일'] == weekday].copy()
                if not day_student.empty:
                    # 표시할 열 선택 및 이름 변경
                    display_df = day_student[['날짜', '구분', '메뉴']].copy()
                    display_menu_dataframe(display_df, f"학생 식당 - {weekday}", current_date_str)
                else:
                    st.info(f"{weekday} 학생 식당 메뉴 정보가 없습니다.")
            
            # 교직원 식당 메뉴
            with col2:
                st.markdown(f"#### 📍 교직원 식당")
                day_staff = staff_df[staff_df['요일'] == weekday].copy()
                if not day_staff.empty:
                    # 표시할 열 선택 및 이름 변경
                    display_df = day_staff[['날짜', '구분', '메뉴']].copy()
                    display_menu_dataframe(display_df, f"교직원 식당 - {weekday}", current_date_str)
                else:
                    st.info(f"{weekday} 교직원 식당 메뉴 정보가 없습니다.")

def is_weekend():
    """현재 날짜가 주말인지 확인"""
    return get_current_date().weekday() >= 5

def display_date_override():
    """개발자 도구: 날짜 변경"""
    st.sidebar.markdown("### 🛠️ 개발자 도구")
    
    # 날짜 선택
    selected_date = st.sidebar.date_input(
        "날짜 선택",
        value=st.session_state.test_date.date(),
        key="date_override"
    )
    
    # 시간 선택 (시간대 유지)
    current_time = st.session_state.test_date.time()
    
    # datetime 객체 생성 및 세션 상태 업데이트
    new_datetime = datetime.combine(selected_date, current_time)
    new_datetime = pytz.timezone('Asia/Seoul').localize(new_datetime)
    
    # 날짜가 변경되었을 때만 업데이트
    if new_datetime.date() != st.session_state.test_date.date():
        st.session_state.test_date = new_datetime
        st.session_state.selected_date = new_datetime  # utils.py에서 사용할 selected_date 설정
        st.rerun()  # 페이지 새로고침

def display_menu_section():
    # 현재 시간 표시
    current_date = get_current_date()
    today_str = current_date.strftime("%m.%d")
    today_date = current_date.strftime("%Y-%m-%d")
    
    st.write(f"현재 시간: {current_date.strftime('%Y년 %m월 %d일 %H:%M')}")
    
    # 개발자 도구 표시
    if DEV_MODE:
        display_date_override()
        st.sidebar.markdown("---")
        
        # 실제 시간으로 초기화 버튼
        if st.sidebar.button("실제 시간으로 초기화"):
            if 'selected_date' in st.session_state:
                del st.session_state.selected_date
            st.session_state.test_date = datetime.now(pytz.timezone('Asia/Seoul'))
            st.rerun()

    # 주말 체크
    if is_weekend():
        st.info("🏖️ 오늘은 주말입니다. 즐거운 주말 보내세요!")
        
        # 다음 주 메뉴 보기 버튼
        if st.button("📅 다음 주 메뉴 보기"):
            st.session_state.menu_mode = "이번 주 전체 메뉴"
            st.rerun()
        return
    
    # 메뉴 보기 모드 선택
    mode = st.radio(
        "메뉴 보기 모드",
        ["오늘의 메뉴", "이번 주 전체 메뉴"],
        horizontal=True,
        key="menu_mode"
    )
    
    if mode == "오늘의 메뉴":
        st.subheader("🍱 오늘의 학식 메뉴")
        
        student_df, staff_df, error = cached_get_today_menu()  # 캐시된 함수 사용
        
        if error:
            st.error(error)
        else:
            # 메뉴 정렬 및 포맷팅
            student_df, staff_df = align_menus_by_date(student_df, staff_df)
            
            # 오늘의 메뉴만 필터링
            student_today = student_df[student_df['날짜'].str.contains(today_str)]
            staff_today = staff_df[staff_df['날짜'].str.contains(today_str)]
            
            if student_today.empty and staff_today.empty:
                st.info("🏖️ 오늘은 식당을 운영하지 않습니다.")
                return
            
            # 메뉴 표시
            display_menu(student_today, staff_today, error)
            
            # AI 추천 섹션 (로그인한 경우에만)
            if st.session_state.is_logged_in:
                st.markdown("---")
                st.subheader("🤖 AI 메뉴 추천")
                
                # 취향 설정 탭과 추천 결과 탭
                tab1, tab2 = st.tabs(["취향 설정", "추천 결과"])
                
                with tab1:
                    user_prefs = display_preference_settings()
                
                with tab2:
                    st.info("🚀 AI 메뉴 추천 기능이 곧 제공될 예정입니다!")
                    st.markdown("""
                    ### Coming Soon!
                    - 사용자 취향 기반 메뉴 추천
                    - 알레르기 정보를 고려한 안전한 추천
                    - 영양 균형을 고려한 식단 제안
                    """)
            else:
                st.info("AI 메뉴 추천을 이용하시려면 로그인이 필요합니다.")
            
            # 리뷰 섹션
            st.markdown("---")
            st.subheader("🌟 리뷰")
            
            # 리뷰 목록 표시 (모든 사용자가 볼 수 있음)
            display_reviews()
            
            # 리뷰 작성 UI (로그인한 사용자만)
            if st.session_state.is_logged_in:
                with st.expander("리뷰 작성하기"):
                    rating = st.slider("별점", 1, 5, 3)
                    review_text = st.text_area("리뷰 내용", placeholder="오늘의 학식은 어떠셨나요?")
                    recommended = st.checkbox("오늘의 학식 추천")
                    
                    if st.button("리뷰 저장"):
                        if review_text.strip():
                            if save_review(
                                st.session_state.username,
                                rating,
                                review_text,
                                recommended
                            ):
                                st.success("리뷰가 저장되었습니다!")
                                st.rerun()
                        else:
                            st.error("리뷰 내용을 입력해주세요.")
            else:
                st.info("리뷰 작성하려면 로그인이 필요합니다.")
    else:
        st.subheader("📅 이번 주 전체 메뉴")
        student_df, staff_df, error = cached_get_weekly_menu()  # 캐시된 함수 사용
        
        if error:
            st.error(error)
        else:
            # 메뉴 정렬 및 포맷팅
            student_df, staff_df = align_menus_by_date(student_df, staff_df)
            
            # 요일별로 메뉴 표시
            display_weekly_menu(student_df, staff_df)
    
    # 새로고침 버튼
    if st.button("🔄 메뉴 새로고침"):
        st.rerun()

def main():
    # 상단에 사용자 정보 표시
    if st.session_state.is_logged_in:
        st.markdown(
            f"""
            <div style='text-align: right; color: #666; padding: 1em;'>
                👤 {st.session_state.user_name}님 환영합니다!
            </div>
            """,
            unsafe_allow_html=True
        )

    # 사이드바에 로그인/회원가입 기능 배치
    with st.sidebar:
        if st.session_state.is_logged_in:
            st.write(f"환영합니다, {st.session_state.user_name}님! 👋")
            if st.button("로그아웃", key="logout"):
                logout()
                st.rerun()
        else:
            st.info("리뷰 작성과 AI 추천을 이용하시려면 로그인이 필요합니다.")
            tab1, tab2 = st.tabs(["로그인", "회원가입"])
            
            # 로그인 탭
            with tab1:
                st.subheader("로그인")
                login_username = st.text_input("아이디", key="login_username")
                login_password = st.text_input("비밀번호", type="password", key="login_password")
                
                if st.button("로그인"):
                    if login_username.strip() and login_password.strip():
                        success, result = verify_login(login_username, login_password)
                        if success:
                            st.session_state.is_logged_in = True
                            st.session_state.username = login_username
                            st.session_state.user_name = result
                            st.rerun()
                        else:
                            st.error(result)
                    else:
                        st.error("아이디와 비밀번호를 모두 입력해주세요.")
            
            # 회원가입 탭
            with tab2:
                st.subheader("회원가입")
                new_username = st.text_input("아이디", key="new_username")
                new_password = st.text_input("비밀번호", type="password", key="new_password")
                confirm_password = st.text_input("비밀번호 확인", type="password", key="confirm_password")
                new_name = st.text_input("이름", key="new_name")
                
                if st.button("회원가입"):
                    if new_username.strip() and new_password.strip() and new_name.strip():
                        if new_password != confirm_password:
                            st.error("비밀번호가 일치하지 않습니다.")
                        else:
                            success, message = register_user(new_username, new_password, new_name)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                    else:
                        st.error("모든 필드를 입력해주세요.")
    
    # 메인 영역에 메뉴 표시
    display_menu_section()

# 비밀번호 해싱 함수
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def display_reviews():
    reviews_df = get_todays_reviews()
    if reviews_df.empty:
        st.info("아직 작성된 리뷰가 없습니다.")
        return
    
    # 전체 평균 평점 계산
    avg_rating = reviews_df['rating'].mean()
    recommendation_rate = (reviews_df['recommended'].sum() / len(reviews_df)) * 100
    
    # 통계 표시
    col1, col2 = st.columns(2)
    with col1:
        st.metric("평균 평점", f"⭐ {avg_rating:.1f} / 5")
    with col2:
        st.metric("추천률", f"👍 {recommendation_rate:.1f}%")
    
    # 개별 리뷰 표시
    st.subheader("📝 오늘의 리뷰")
    for _, review in reviews_df.iterrows():
        with st.container():
            col1, col2 = st.columns([1, 4])
            with col1:
                st.write(f"⭐ {review['rating']}/5")
                if review['recommended']:
                    st.write("👍 추천")
            with col2:
                st.write(f"**{review['username']}**님의 리뷰")
                st.write(review['review_text'])
            st.divider()

# 테이블 스타일 정의
table_style = """
<style>
    .menu-table {
        width: 100%;
        border-collapse: collapse;
        margin: 10px 0;
        background-color: rgb(17, 17, 17);
        color: rgb(238, 238, 238);
    }
    .menu-table th {
        background-color: rgb(38, 39, 48);
        color: rgb(238, 238, 238);
        padding: 12px;
        text-align: left;
        border: 1px solid rgb(38, 39, 48);
    }
    .menu-table td {
        padding: 12px;
        border: 1px solid rgb(38, 39, 48);
        background-color: rgb(17, 17, 17);
    }
    .menu-table tr:hover td {
        background-color: rgb(38, 39, 48);
    }
    .section-title {
        color: rgb(238, 238, 238);
        margin: 20px 0 10px 0;
        font-size: 1.2em;
    }
</style>
"""

def display_menu(student_menu, staff_menu, error_message):
    """메뉴 표시"""
    if error_message:
        st.error(error_message)
        return

    # 스타일 적용
    st.markdown(table_style, unsafe_allow_html=True)
    
    # 학생 식당 메뉴
    st.markdown("### 🍽️ 오늘의 학식 메뉴", unsafe_allow_html=True)
    
    if not student_menu.empty:
        st.markdown("#### 🎈 학생 식당", unsafe_allow_html=True)
        
        # 데이터프레임을 HTML 테이블로 변환
        html_table = "<table class='menu-table'>"
        # 헤더 추가
        html_table += "<tr><th>날짜</th><th>구분</th><th>메뉴</th></tr>"
        
        # 각 행 추가
        for _, row in student_menu.iterrows():
            html_table += f"<tr><td>{row['날짜']}</td><td>{row['구분']}</td><td>{row['메뉴']}</td></tr>"
        
        html_table += "</table>"
        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.info("🍽️ AI 메뉴 추천을 이용하시려면 로그인이 필요합니다.")
    
    # 교직원 식당 메뉴
    if not staff_menu.empty:
        st.markdown("#### 📍 교직원 식당", unsafe_allow_html=True)
        
        # 데이터프레임을 HTML 테이블로 변환
        html_table = "<table class='menu-table'>"
        # 헤더 추가
        html_table += "<tr><th>날짜</th><th>구분</th><th>메뉴</th></tr>"
        
        # 각 행 추가
        for _, row in staff_menu.iterrows():
            html_table += f"<tr><td>{row['날짜']}</td><td>{row['구분']}</td><td>{row['메뉴']}</td></tr>"
        
        html_table += "</table>"
        st.markdown(html_table, unsafe_allow_html=True)
    else:
        st.info("AI 메뉴 추천을 이용하시려면 로그인이 필요합니다.")

if __name__ == "__main__":
    main()
