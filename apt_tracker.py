import requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
from dateutil.relativedelta import relativedelta

# ==========================================
# 1. 기본 설정 (API 키 입력)
# ==========================================
# 공공데이터포털에서 발급받은 '일반 인증키(Decoding)'를 아래에 넣으세요.
API_KEY = "ff4474946de928765829a43d472cc18fbf5fd438b70cbdaf11c7768e5043c961" 

# 이번 달을 기준으로 최근 거래를 조회 (예: 202606)
# (실거래가 신고 기한이 30일이므로 보통 1~2달 전 데이터를 조회하는 것이 좋습니다)
target_month = datetime.now().strftime("%Y%m")
# target_month = "202604"

# ==========================================
# 2. 강석님의 타겟 아파트 리스트
# ==========================================
# 중랑구(11260), 동대문구(11230), 노원구(11350)
target_list = [
    {"lawd_cd": "11260", "dong": "중화동", "keyword": "한신"},
    {"lawd_cd": "11260", "dong": "상봉동", "keyword": "더샵"}, # '더샾'의 정식 등록명 감안
    {"lawd_cd": "11230", "dong": "이문동", "keyword": "현대"}, # 현대아이파크
    {"lawd_cd": "11350", "dong": "월계동", "keyword": "현대"}  # 월계동 현대
]

# ==========================================
# 3. 데이터 수집 및 필터링 함수
# ==========================================
def get_apt_transactions(lawd_cd, deal_ymd):
    url = "https://apis.data.go.kr/1613000/RTMSDataSvcAptTradeDev/getRTMSDataSvcAptTradeDev"
    params = {
        "serviceKey": API_KEY,
        "LAWD_CD": lawd_cd,
        "DEAL_YMD": deal_ymd,
        "numOfRows": "1000", # 한 달 치 넉넉하게 가져오기
        "pageNo": "1"
    }
    
    response = requests.get(url, params=params)
    print(response.text)
    
    # 데이터가 없거나 에러가 났을 경우 예외 처리
    if response.status_code != 200:
        return []

    root = ET.fromstring(response.content)
    items = root.find("body").find("items")
    
    if items is None:
        return []

    parsed_data = []
    for item in items.findall("item"):
        # API에서 제공하는 각 항목 추출 (빈 값 처리 포함)
        dong = item.findtext("umdNm").strip() if item.findtext("umdNm") else ""
        apt_name = item.findtext("aptNm").strip() if item.findtext("aptNm") else ""
        price = item.findtext("dealAmount").strip() if item.findtext("dealAmount") else ""
        area = item.findtext("excluUseAr").strip() if item.findtext("excluUseAr") else ""
        day = item.findtext("dealDay").strip() if item.findtext("dealDay") else ""
        floor = item.findtext("floor").strip() if item.findtext("floor") else ""
        
        parsed_data.append({
            "법정동": dong,
            "아파트명": apt_name,
            "전용면적(㎡)": area,
            "층": floor,
            "거래금액(만)": price,
            "거래일자": f"{deal_ymd[:4]}-{deal_ymd[4:]}-{day.zfill(2)}"
        })
        
    return parsed_data

# ==========================================
# # 4. 실행 및 결과 출력 및 구글 시트 전송 (일일 자동화 버전)
# ==========================================
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

target_month = datetime.now().strftime("%Y%m")
print(f"--- {target_month} 기준 최신 실거래가 자동 수집 --- \n")

all_filtered_data = []
unique_lawd_cds = set([target['lawd_cd'] for target in target_list])

for cd in unique_lawd_cds:
    print(f"지역코드 {cd} 최신 데이터 확인 중...")
    raw_data = get_apt_transactions(cd, target_month)
    
    for target in target_list:
        if target['lawd_cd'] == cd:
            for item in raw_data:
                if target['dong'] in item['법정동'] and target['keyword'] in item['아파트명']:
                    all_filtered_data.append(item)
    time.sleep(0.5)

if all_filtered_data:
    print("\n⚡ 구글 스프레드시트로 최신 데이터를 전송합니다...")
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("secret.json", scope)
        gc = gspread.authorize(creds)
        
        doc = gc.open("도권_아파트_실거래가_트래킹")
        worksheet = doc.get_worksheet(0)
        
        rows_to_append = []
        for data in all_filtered_data:
            row = [
                data['법정동'], 
                data['아파트명'], 
                data['전용면적(㎡)'], 
                data['층'], 
                data['거래금액(만)'], 
                data['거래일자']
            ]
            rows_to_append.append(row)
            
        worksheet.append_rows(rows_to_append)
        print(f"\n[🎉] 자동화 전송 완료: {len(rows_to_append)}건의 신규 데이터가 추가되었습니다!")
        
    except Exception as e:
        print(f"\n[!] 구글 시트 전송 중 오류 발생: {e}")
else:
    print("\n[i] 오늘 기준 추가된 새로운 실거래가 신고 내역이 없습니다.")
