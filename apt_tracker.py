import requests
import pandas as pd
import xml.etree.ElementTree as ET
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import time

API_KEY = "ff4474946de928765829a43d472cc18fbf5fd438b70cbdaf11c7768e5043c961"

# 2025년 1월 ~ 2026년 5월까지 과거 달력
months_list = [
    "202501", "202502", "202503", "202504", "202505", "202506",
    "202507", "202508", "202509", "202510", "202511", "202512",
    "202601", "202602", "202603", "202604", "202605"
]

target_list = [
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

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("secret.json", scope)
gc = gspread.authorize(creds)
worksheet = gc.open("도권_아파트_실거래가_트래킹").get_worksheet(0)

all_rows_to_append = []
for month in months_list:
    for target in target_list:
        raw_data = get_apt_transactions(target['lawd_cd'], month)
        for item in raw_data:
            if target['dong'] in item['법정동'] and target['keyword'] in item['아파트명']:
                all_rows_to_append.append([item['법정동'], item['아파트명'], item['전용면적(㎡)'], item['층'], item['거래금액(만)'], item['거래일자']])
        time.sleep(0.5)

if all_rows_to_append:
    worksheet.append_rows(all_rows_to_append)