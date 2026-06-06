import requests
import pandas as pd
import xml.etree.ElementTree as ET
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

API_KEY = "ff4474946de928765829a43d472cc18fbf5fd438b70cbdaf11c7768e5043c961"

target_month = datetime.now().strftime("%Y%m")

target_list = [
    {"lawd_cd": "11260", "dong": "중화동", "keyword": "한신"},
    {"lawd_cd": "11260", "dong": "상봉동", "keyword": "더샵"},
    {"lawd_cd": "11230", "dong": "이문동", "keyword": "현대"},
    {"lawd_cd": "11290", "dong": "상월곡동", "keyword": "동아에코빌"},
    {"lawd_cd": "11230", "dong": "이문동", "keyword": "쌍용"}
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

for cd in unique_lawd_cds:
    raw_data = get_apt_transactions(cd, target_month)
    for target in target_list:
        if target['lawd_cd'] == cd:
            for item in raw_data:
                if target['dong'] in item['법정동'] and target['keyword'] in item['아파트명']:
                    all_filtered_data.append(item)
    time.sleep(0.5)

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
        print(f"자동화 전송 완료: {len(rows_to_append)}건 추가됨!")
    else:
        print("오늘 기준 추가된 새로운 신고 내역이 없습니다.")
else:
    print("해당 월의 실거래 데이터가 없습니다.")