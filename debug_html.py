import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

def analyze_html():
    url = "https://sejong.korea.ac.kr/koreaSejong/8028/subview.do"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 현재 날짜 가져오기
    korea_tz = pytz.timezone('Asia/Seoul')
    today = datetime.now(korea_tz)
    today_str = today.strftime("%m.%d")
    print(f"Looking for date: {today_str}\n")
    
    print("=== Available Tables ===")
    tables = soup.find_all('table')
    
    for idx, table in enumerate(tables):
        print(f"\nTable #{idx + 1}")
        print("Classes:", table.get('class', []))
        print("Summary:", table.get('summary', ''))
        
        # 모든 행 출력
        print("\nAll rows content:")
        for row_idx, row in enumerate(table.find_all('tr')):
            print(f"\nRow {row_idx}:")
            for col_idx, col in enumerate(row.find_all(['th', 'td'])):
                print(f"  Column {col_idx}: {col.text.strip()}")
        print("-" * 50)

if __name__ == "__main__":
    analyze_html() 