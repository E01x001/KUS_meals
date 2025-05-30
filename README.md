# KUS Meals (고려대학교 세종캠퍼스 학식 알리미)

고려대학교 세종캠퍼스의 학생식당과 교직원식당의 메뉴를 쉽게 확인할 수 있는 웹 애플리케이션입니다.

## 주요 기능

- 🍱 오늘의 메뉴 확인
- 📅 주간 메뉴 확인
- 🕒 시간대별 메뉴 구분 (조식, 중식, 석식)
- 👤 사용자 계정 관리
- ⭐ 메뉴 리뷰 및 평점
- 🤖 AI 기반 메뉴 추천 (준비 중)

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/[username]/KUS_meals.git
cd KUS_meals
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

## 실행 방법

```bash
streamlit run app.py
```

## 기술 스택

- Python
- Streamlit
- BeautifulSoup4
- Pandas
- Google Gemini API (준비 중)

## 개발자 도구

개발 모드에서는 다음과 같은 기능을 사용할 수 있습니다:
- 날짜 변경 기능
- 디버그 정보 확인

## 라이선스

MIT License

## 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request 