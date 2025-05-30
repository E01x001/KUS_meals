import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import pytz
from utils import get_current_date

def get_today_menu():
    """오늘의 메뉴를 크롤링"""
    try:
        # 선택된 날짜 사용
        current_date = get_current_date()
        
        # URL 파라미터 생성
        temp_date = current_date.strftime("%Y%m%d")
        search_day = current_date.strftime("%Y.%m.%d")
        
        # 식단 페이지 URL
        url = f"https://sejong.korea.ac.kr/dietMa/koreaSejong/artclView.do?siteId=koreaSejong&tempDate={temp_date}&day30=&searchDay={search_day}"
        
        # 헤더 설정
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Referer': 'https://sejong.korea.ac.kr/',
        }
        
        # 세션 생성
        with requests.Session() as session:
            # 메인 페이지 먼저 방문
            session.get('https://sejong.korea.ac.kr/', headers=headers)
            
            # 식단 페이지 요청
            response = session.get(url, headers=headers)
            
            if response.status_code != 200:
                return pd.DataFrame(columns=['날짜', '구분', '메뉴']), pd.DataFrame(columns=['날짜', '구분', '메뉴']), f"메뉴 페이지 접속 실패: {response.status_code}"
            
            # HTML 파싱
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 학생식당과 교직원식당 메뉴 파싱
            student_menu = parse_menu(soup, current_date, "학생식당")
            staff_menu = parse_menu(soup, current_date, "교직원식당")
            
            return student_menu, staff_menu, None
            
    except Exception as e:
        import traceback
        return pd.DataFrame(columns=['날짜', '구분', '메뉴']), pd.DataFrame(columns=['날짜', '구분', '메뉴']), f"메뉴를 가져오는 중 오류가 발생했습니다: {str(e)}"

def get_weekly_menu():
    """이번 주 전체 메뉴를 크롤링"""
    try:
        # 선택된 날짜 사용
        current_date = get_current_date()
        
        # 해당 주의 월요일 찾기
        monday = current_date - timedelta(days=current_date.weekday())
        
        student_menus = []
        staff_menus = []
        
        # 월요일부터 금요일까지의 메뉴 크롤링
        for i in range(5):  # 0=월요일, 4=금요일
            date = monday + timedelta(days=i)
            
            # URL 파라미터 생성
            temp_date = date.strftime("%Y%m%d")
            search_day = date.strftime("%Y.%m.%d")
            
            # 식단 페이지 URL
            url = f"https://sejong.korea.ac.kr/dietMa/koreaSejong/artclView.do?siteId=koreaSejong&tempDate={temp_date}&day30=&searchDay={search_day}"
            
            # 페이지 크롤링
            response = requests.get(url)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 학생식당과 교직원식당 메뉴 파싱
                student_menu = parse_menu(soup, date, "학생식당")
                staff_menu = parse_menu(soup, date, "교직원식당")
                
                if not student_menu.empty:
                    student_menus.append(student_menu)
                if not staff_menu.empty:
                    staff_menus.append(staff_menu)
        
        # 메뉴 데이터 합치기
        student_df = pd.concat(student_menus, ignore_index=True) if student_menus else pd.DataFrame(columns=['날짜', '구분', '메뉴'])
        staff_df = pd.concat(staff_menus, ignore_index=True) if staff_menus else pd.DataFrame(columns=['날짜', '구분', '메뉴'])
        
        return student_df, staff_df, None
        
    except Exception as e:
        return pd.DataFrame(columns=['날짜', '구분', '메뉴']), pd.DataFrame(columns=['날짜', '구분', '메뉴']), f"메뉴를 가져오는 중 오류가 발생했습니다: {str(e)}"

def parse_menu(soup, date, menu_type):
    """메뉴 HTML 파싱"""
    try:
        menu_data = []
        date_str = date.strftime("%m.%d")
        
        # 테이블 찾기 (summary 대신 내용으로 찾기)
        target_table = None
        tables = soup.find_all('table')
        for table in tables:
            # 테이블의 모든 텍스트 내용 확인
            table_text = table.get_text()
            
            if menu_type == "교직원식당" and "교직원 식단표" in table_text:
                target_table = table
                break
            elif menu_type == "학생식당" and "학생 식단표" in table_text:
                target_table = table
                break
        
        if not target_table:
            return pd.DataFrame(columns=['날짜', '구분', '메뉴'])
        
        # 날짜 열 찾기
        headers = target_table.find('tr').find_all('th')
        date_col = -1
        
        for i, header in enumerate(headers):
            header_text = header.get_text(strip=True)
            if date_str in header_text:
                date_col = i
                break
                
        if date_col == -1:
            return pd.DataFrame(columns=['날짜', '구분', '메뉴'])
        
        # 메뉴 카테고리 정의
        categories = {
            "조식": "조식 (07:30 ~ 09:00)",
            "중식 - 한식": "중식 - 한식 (11:30 ~ 13:30)",
            "중식 - 일품": "중식 - 일품 (11:30 ~ 13:30)",
            "중식 - 분식": "중식 - 분식 (11:30 ~ 13:30)",
            "중식 - plus": "중식 - plus (11:30 ~ 13:30)",
            "석식": "석식 (17:00 ~ 18:30)",
            "중식": "중식"  # 교직원식당용
        }
        
        # 메뉴 추출
        rows = target_table.find_all('tr')[1:]  # 헤더 제외
        
        for row_idx, row in enumerate(rows):
            cells = row.find_all(['th', 'td'])
            
            if len(cells) <= date_col:
                continue
                
            menu_time = cells[0].get_text(strip=True)
            
            menu_cell = cells[date_col]
            
            # 카테고리 매칭
            category = menu_time
            for key, value in categories.items():
                if key in menu_time:
                    category = value
                    break
            
            # 메뉴 항목 추출
            menu_items = []
            
            # 메뉴 텍스트 정제
            menu_text = menu_cell.get_text(strip=True)
            
            if menu_text and menu_text != "-" and not "식당을 운영하지 않습니다" in menu_text:
                # 쌀밥/백미밥으로 시작하는 경우 처리
                if menu_text.startswith("쌀밥") or menu_text.startswith("백미밥"):
                    menu_items.append("쌀밥")
                    menu_text = menu_text[2:] if menu_text.startswith("쌀밥") else menu_text[3:]
                
                # 메뉴 항목 분리 (메뉴 구분자로 사용되는 문자들 처리)
                items = []
                for item in menu_text.split('*'):  # * 구분자로 분리
                    for sub_item in item.split('/'):  # / 구분자로 분리
                        cleaned_item = sub_item.strip()
                        if cleaned_item and cleaned_item != "-":
                            items.append(cleaned_item)
                
                menu_items.extend(items)
            
            if menu_items:
                # 메뉴 포맷팅
                formatted_menu = ' | '.join(menu_items)
                
                menu_data.append({
                    '날짜': date_str,
                    '구분': category,
                    '메뉴': formatted_menu
                })
        
        # 결과를 데이터프레임으로 변환
        df = pd.DataFrame(menu_data) if menu_data else pd.DataFrame(columns=['날짜', '구분', '메뉴'])
        
        if not df.empty:
            # 메뉴 종류 순서 정의
            category_order = [
                "조식 (07:30 ~ 09:00)",
                "중식 - 한식 (11:30 ~ 13:30)",
                "중식 - 일품 (11:30 ~ 13:30)",
                "중식 - 분식 (11:30 ~ 13:30)",
                "중식 - plus (11:30 ~ 13:30)",
                "석식 (17:00 ~ 18:30)",
                "중식"  # 교직원식당용
            ]
            df['구분'] = pd.Categorical(df['구분'], categories=category_order, ordered=True)
            df = df.sort_values('구분')
        
        return df
        
    except Exception as e:
        return pd.DataFrame(columns=['날짜', '구분', '메뉴']) 