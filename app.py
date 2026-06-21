import requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

# 국토부 실거래가 API 키
API_KEY = "ff4474946de928765829a43d472cc18fbf5fd438b70cbdaf11c7768e5043c961"

current_year = datetime.now().year
current_month = datetime.now().month

# 2025년 1월부터 현재까지 타겟 설정
target_months = []
for m in range(1, 13):
    target_months.append(f"2025{str(m).zfill(2)}")
for m in range(1, current_month + 1):
    target_months.append(f"{current_year}{str(m).zfill(2)}")

# [핵심 패치 1] 국토부 이름 꼬임 방지를 위해 키워드를 극단적으로 단축 ('동' 제외, 핵심 키워드만)
target_list = [
    {"lawd_cd": "11260", "dong": "중화", "keyword": "한신"},
    {"lawd_cd": "11260", "dong": "상봉", "keyword": "더샵"},
    {"lawd_cd": "11230", "dong": "이문", "keyword": "현대"},
    {"lawd_cd": "11290", "dong": "상월곡", "keyword": "동아에코빌"},
    {"lawd_cd": "11230", "dong": "이문", "keyword": "쌍용"},
    {"lawd_cd": "11680", "dong": "대치", "keyword": "래미안대치"},
    {"lawd_cd": "11650", "dong": "반포", "keyword": "아크로리버파크"},
    {"lawd_cd": "11710", "dong": "잠실", "keyword": "리센츠"},
    {"lawd_cd": "11170", "dong": "이촌", "keyword": "한가람"},
    {"lawd_cd": "11590", "dong": "흑석", "keyword": "아크로리버하임"},
    {"lawd_cd": "11110", "dong": "홍파", "keyword": "경희궁자이"},
    {"lawd_cd": "11560", "dong": "당산", "keyword": "당산센트럴"},
    {"lawd_cd": "11140", "dong": "만리", "keyword": "서울역센트럴"},
    {"lawd_cd": "11215", "dong": "광장", "keyword": "광장힐스테이트"},
    {"lawd_cd": "11440", "dong": "염리", "keyword": "마포프레스티지"},
    {"lawd_cd": "11740", "dong": "둔촌", "keyword": "올림픽파크포레온"},
    
    # 🔥 성동구 긴급 처방: '리버zen', '리버젠' 모두 잡히도록 '리버' 로 통일
    {"lawd_cd": "11200", "dong": "옥수", "keyword": "리버"},      
    
    {"lawd_cd": "11470", "dong": "신정", "keyword": "목동힐스테이트"},
    {"lawd_cd": "11500", "dong": "마곡", "keyword": "마곡엠밸리"},
    {"lawd_cd": "11410", "dong": "북아현", "keyword": "e편한세상신촌"},
    {"lawd_cd": "11290", "dong": "길음", "keyword": "래미안길음"},
    {"lawd_cd": "11230", "dong": "전농", "keyword": "sky"},           
    {"lawd_cd": "11620", "dong": "봉천", "keyword": "서울대입구"},
    {"lawd_cd": "11350", "dong": "중계", "keyword": "청구3"},
    
    # 🔥 구로구 긴급 처방: '대림e-편한세상4' 등 하이픈 오류 극복을 위해 '4차' 로 통일
    {"lawd_cd": "11530", "dong": "신도림", "keyword": "4차"},    
    
    {"lawd_cd": "11260", "dong": "면목", "keyword": "사가정센트럴"},
    {"lawd_cd": "11380", "dong": "응암", "keyword": "녹번"},          
    {"lawd_cd": "11305", "dong": "미아", "keyword": "북서울자이"},
    {"lawd_cd": "11545", "dong": "독산", "keyword": "롯데캐슬골드파크3"},
    {"lawd_cd": "11320", "dong": "창동", "keyword": "북한산아이파크"}
]

def get_apt_transactions(lawd_cd, deal_ymd):
    url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
    params = {"serviceKey": API_KEY, "LAWD_CD": lawd_cd, "DEAL_YMD": deal_ymd, "numOfRows": "1000", "pageNo": "1"}
    try:
        response = requests.get(url, params=params)
        if response.status_code != 200: return []
        root = ET.fromstring(response.content)
        items = root.find("body").find("items")
        if items is None: return []
        
        parsed_data = []
        for item in items.findall("item"):
            dong = item.findtext("umdNm").strip() if item.findtext("umdNm") else ""
            apt_name = item.findtext("aptNm").strip() if item.findtext("aptNm") else ""
            price = item.findtext("dealAmount").strip() if item.findtext("dealAmount") else ""
            area = item.findtext("excluUseAr").strip() if item.findtext("excluUseAr") else ""
            day = item.findtext("dealDay").strip() if item.findtext("dealDay") else ""
            floor = item.findtext("floor").strip() if item.findtext("floor") else ""
            
            parsed_data.append({
                "법정동": dong, "아파트명": apt_name, "전용면적(㎡)": area,
                "층": floor, "거래금액(만)": price, 
                "거래일자": f"{deal_ymd[0:4]}-{deal_ymd[4:6]}-{day.zfill(2)}"
            })
        return parsed_data
    except Exception: return []

all_filtered_data = []
unique_lawd_cds = set([target['lawd_cd'] for target in target_list])

print("🚀 2025년 1월 ~ 현재 누락된 성동구/구로구 대장 아파트 정밀 스캔 시작...")

for ym in target_months:
    print(f"📅 데이터 스캔 중: {ym[0:4]}년 {ym[4:6]}월...")
    for cd in unique_lawd_cds:
        raw_data = get_apt_transactions(cd, ym)
        for target in target_list:
            if target['lawd_cd'] == cd:
                for item in raw_data:
                    # [핵심 패치 2] 데이터 파싱 시 하이픈(-)과 띄어쓰기를 완전히 박살 낸 후 검사
                    fetched_dong = item.get('법정동', '').replace(" ", "")
                    fetched_apt_clean = item.get('아파트명', '').replace(" ", "").replace("-", "").lower()
                    
                    target_keyword_clean = target['keyword'].replace(" ", "").replace("-", "").lower()
                    
                    # 동 이름이 포함되고, 키워드가 포함되어 있으면 무조건 수집
                    if target['dong'] in fetched_dong and target_keyword_clean in fetched_apt_clean:
                        all_filtered_data.append(item)
        time.sleep(0.1)
    time.sleep(1.0)

if all_filtered_data:
    # 구글 시트 연동 설정
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("secret.json", scope)
    gc = gspread.authorize(creds)
    worksheet = gc.open("도권_아파트_실거래가_트래킹").get_worksheet(0)
    
    # 기존 데이터 중복 방지 로직
    existing_records = worksheet.get_all_records()
    existing_keys = set(
        f"{row.get('거래일자', '')}_{row.get('법정동', '')}_{row.get('아파트명', '')}_{row.get('전용면적(㎡)', '')}_{str(row.get('거래금액(만)', '')).replace(',', '')}"
        for row in existing_records
    )
    
    rows_to_append = []
    for data in all_filtered_data:
        key = f"{data['거래일자']}_{data['법정동']}_{data['아파트명']}_{data['전용면적(㎡)']}_{str(data['거래금액(만)']).replace(',', '')}"
        if key not in existing_keys:
            rows_to_append.append([data['법정동'], data['아파트명'], data['전용면적(㎡)'], data['층'], data['거래금액(만)'], data['거래일자']])
            
    if rows_to_append:
        worksheet.append_rows(rows_to_append)
        print(f"✨ 동기화 완료! 그동안 국토부 이름 꼬임으로 누락되었던 성동구, 구로구 포함 총 {len(rows_to_append)}건이 구글 시트에 추가되었습니다.")
    else:
        print("💡 이미 모든 실거래 데이터가 구글 시트에 들어있습니다.")
else:
    print("수집된 데이터가 없습니다.")