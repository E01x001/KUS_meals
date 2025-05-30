# KUS Meals (고려대학교 세종캠퍼스 학식 알리미)

고려대학교 세종캠퍼스의 학식 메뉴를 쉽게 확인하고 AI 기반 메뉴 추천을 받을 수 있는 웹 애플리케이션입니다.

## 주요 기능

- 🍽️ 오늘의 학식 메뉴 확인
- 📅 주간 메뉴 확인
- 🤖 AI 기반 메뉴 추천
- ⭐ 메뉴 리뷰 및 평가
- 👤 사용자 취향 설정

## 설치 방법

1. 저장소 클론
```bash
git clone https://github.com/[YOUR_USERNAME]/KUS_meals.git
cd KUS_meals
```

2. 가상환경 생성 및 활성화
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

4. Streamlit secrets 설정
- `.streamlit/secrets.toml` 파일 생성
```toml
GEMINI_API_KEY = "your-api-key-here"
```

## 실행 방법

```bash
streamlit run app.py
```

## 환경 설정

- Python 3.8 이상
- Streamlit 1.31.1
- Google Generative AI API 키 필요

## 기여 방법

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 라이선스

MIT License를 따릅니다. 자세한 내용은 `LICENSE` 파일을 참고하세요.

## 개발자 연락처

- 이메일: [YOUR_EMAIL]
- GitHub: [YOUR_GITHUB_PROFILE] 