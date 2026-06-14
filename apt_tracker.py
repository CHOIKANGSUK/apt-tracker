iimport requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

API_KEY = "ff4474946de928765829a43d472cc18fbf5fd438b70cbdaf11c7768e5043c961"

target_month = datetime.now().strftime("%Y%m")

# 기존 관심 단지 + 서울 25개 구 랜드마크 통합 리스트
target_list = [
    # --- 기존 강석님 관심 단지 ---
    {"lawd_cd": "11260", "dong": "중화동", "keyword": "한신"},
    {"lawd_cd": "11260", "dong": "상봉동", "keyword": "더샵"},
    {"lawd_cd": "11230", "dong": "이문동", "keyword": "현대"},
    {"lawd_cd": "11290", "dong": "상월곡동", "keyword": "동아에코빌"},
    {"lawd_cd": "11230", "dong": "이문동", "keyword": "쌍용"},
    
    # --- 👑 서울 25개 구 랜드마크 아파트 타겟 ---
    {"lawd_cd": "11680", "dong": "대치동", "keyword": "래미안대치팰리스"},   # 강남구
    {"lawd_cd": "11650", "dong": "반포동", "keyword": "아크로리버파크"},     # 서초구
    {"lawd_cd": "11710", "dong": "잠실동", "keyword": "리센츠"},           # 송파구
    {"lawd_cd": "11170", "dong": "이촌동", "keyword": "한가람"},           # 용산구
    {"lawd_cd": "11590", "dong": "흑석동", "keyword": "아크로리버하임"},     # 동작구
    {"lawd_cd": "11110", "dong": "홍파동", "keyword": "경희궁자이"},         # 종로구
    {"lawd_cd": "11560", "dong": "당산동", "keyword": "당산센트럴아이파크"},   # 영등포구
    {"lawd_cd": "11140", "dong": "만리동", "keyword": "서울역센트럴자이"},     # 중구
    {"lawd_cd": "11215", "dong": "광장동", "keyword": "광장힐스테이트"},     # 광진구
    {"lawd_cd": "11440", "dong": "염리동", "keyword": "마포프레스티지자이"},   # 마포구
    {"lawd_cd": "11740", "dong": "둔촌동", "keyword": "올림픽파크포레온"},   # 강동구
    {"lawd_cd": "11200", "dong": "옥수동", "keyword": "래미안옥수리버젠"},     # 성동구
    {"lawd_cd": "11470", "dong": "신정동", "keyword": "목동힐스테이트"},     # 양천구
    {"lawd_cd": "11500", "dong": "마곡동", "keyword": "마곡엠밸리7단지"},     # 강서구
    {"lawd_cd": "11410", "dong": "북아현동", "keyword": "e편한세상신촌"},      # 서대문구
    {"lawd_cd": "11290", "dong": "길음동", "keyword": "래미안길음센터피스"},   # 성북구
    {"lawd_cd": "11230", "dong": "전농동", "keyword": "SKY-L65"},        # 동대문구
    {"lawd_cd": "11620", "dong": "봉천동", "keyword": "e편한세상서울대입구"},   # 관악구
    {"lawd_cd": "11350", "dong": "중계동", "keyword": "청구3"},            # 노원구
    {"lawd_cd": "11530", "dong": "신도림동", "keyword": "신도림4차"},          # 구로구
    {"lawd_cd": "11260", "dong": "면목동", "keyword": "사가정센트럴아이파크"},   # 중랑구
    {"lawd_cd": "11380", "dong": "응암동", "keyword": "녹번역e편한세상캐슬"},   # 은평구
    {"lawd_cd": "11305", "dong": "미아동", "keyword": "북서울자이폴라리스"},   # 강북구
    {"lawd_cd": "11545", "dong": "독산동", "keyword": "롯데캐슬골드파크3차"},   # 금천구
    {"lawd_cd": "11320", "dong": "창동", "keyword": "북한산아이파크"}          # 도봉구
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

# 25개 자치구를 순회하며 데이터 수집
for cd in unique_lawd_cds:
    raw_data = get_apt_transactions(cd, target_month)
    for target in target_list:
        if target['lawd_cd'] == cd:
            for item in raw_data:
                # 대소문자 상관없이 영문 아파트 이름도 완벽 매칭되도록 .lower() 처리
                if target['dong'] in item['법정동'] and target['keyword'].lower() in item['아파트명'].lower():
                    all_filtered_data.append(item)
    time.sleep(0.5) # 구글 API 서버에 부담을 주지 않기 위한 딜레이

if all_filtered_data:
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("secret.json", scope)
    gc = gspread.authorize(creds)
    worksheet = gc.open("도권_아파트_실거래가_트래킹").get_worksheet(0)
    
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
        print(f"자동화 전송 완료: 랜드마크 포함 총 {len(rows_to_append)}건 추가됨!")
    else:
        print("오늘 기준 추가된 새로운 신고 내역이 없습니다.")
else:
    print("해당 월의 실거래 데이터가 없습니다.")