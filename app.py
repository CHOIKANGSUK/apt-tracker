import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="강석의 아파트 시세트래킹",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 구글 시트 데이터 로드
@st.cache_data(ttl=600)
def load_data_v6_15():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        gc = gspread.authorize(creds)
        worksheet = gc.open("도권_아파트_실거래가_트래킹").get_worksheet(0)
        
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        df['거래일자'] = pd.to_datetime(df['거래일자'])
        df = df.sort_values(by='거래일자', ascending=True)
        return df
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return pd.DataFrame()

# === 법정동-자치구 정밀 매핑 ===
def get_gu_name(dong_name):
    dong = str(dong_name).strip()
    if dong in ['중화동', '상봉동', '면목동', '신내동', '망우동', '묵동']: return '중랑구'
    elif dong in ['상월곡동', '하월곡동', '길음동', '장위동', '석관동', '돈암동', '정릉동', '보문동']: return '성북구'
    elif dong in ['이문동', '휘경동', '전농동', '답십리동', '장안동', '청량리동', '제기동', '용두동']: return '동대문구'
    elif dong in ['만리동', '회현동', '명동', '신당동', '황학동']: return '중구'
    elif dong in ['염리동', '아현동', '공덕동', '대흥동', '망원동']: return '마포구'
    elif dong in ['이촌동', '서빙고동', '한남동', '보광동']: return '용산구'
    elif dong in ['옥수동', '성수동', '금호동', '응봉동', '행당동']: return '성동구'
    elif dong in ['홍파동', '무악동', '평창동', '혜화동']: return '종로구'
    elif dong in ['북아현동', '남가좌동', '연희동', '홍은동']: return '서대문구'
    elif dong in ['창동', '방학동', '쌍문동']: return '도봉구'
    elif dong in ['미아동', '수유동', '번동']: return '강북구'
    elif dong in ['상계동', '중계동', '하계동', '공릉동', '월계동']: return '노원구'
    elif dong in ['은평동', '응암동', '불광동', '수색동']: return '은평구'
    elif dong in ['광장동', '구의동', '자양동', '화양동']: return '광진구'
    elif dong in ['대치동', '압구정동', '삼성동', '개포동', '역삼동', '도곡동']: return '강남구'
    elif dong in ['반포동', '방배동', '서초동', '잠원동', '양재동']: return '서초구'
    elif dong in ['잠실동', '신천동', '문정동', '가락동', '오금동']: return '송파구'
    elif dong in ['둔촌동', '명일동', '고덕동', '상일동', '천호동', '암사동']: return '강동구'
    elif dong in ['당산동', '신길동', '문래동', '양평동', '영등포동']: return '영등포구'
    elif dong in ['흑석동', '상도동', '노량진동', '사당동']: return '동작구'
    elif dong in ['봉천동', '신림동', '남현동']: return '관악구'
    elif dong in ['신정동', '목동', '신월동']: return '양천구'
    elif dong in ['마곡동', '가양동', '화곡동', '등촌동']: return '강서구'
    elif dong in ['신도림동', '구로동', '고척동', '개봉동']: return '구로구'
    elif dong in ['독산동', '시흥동', '가산동']: return '금천구'
    return '기타/미분류'

# 아파트 메타 정보 백과사전
def get_apt_info(apt_name, pyung=None):
    info = {"세대수": "-", "준공": "-", "용적률": "-", "구조": "-"}
    clean_name = str(apt_name).replace(" ", "")
    if "중화동" in clean_name and "한신" in clean_name:
        info.update({"세대수": "1,544세대", "준공": "1997.10 (29년차)", "용적률": "376%"})
        if pyung: info["구조"] = "방2/화1" if pyung <= 60 else "방3/화2"
    elif "상월곡동" in clean_name and "동아에코빌" in clean_name:
        info.update({"세대수": "1,253세대", "준공": "2003.06 (23년차)", "용적률": "281%"})
        if pyung: info["구조"] = "방3/화1" if pyung <= 60 else "방3/화2"
    elif "이문동" in clean_name and "쌍용" in clean_name:
        info.update({"세대수": "1,318세대", "준공": "2000.11 (26년차)", "용적률": "343%"})
        if pyung: info["구조"] = "방3/화1" if pyung <= 60 else "방3/화2"
    elif "이문동" in clean_name and "현대" in clean_name:
        info.update({"세대수": "483세대", "준공": "2000.09 (26년차)", "용적률": "319%"})
        if pyung: info["구조"] = "방2/화1" if pyung <= 60 else "방3/화2"
    elif "상봉동" in clean_name and "더샵" in clean_name:
        info.update({"세대수": "497세대", "준공": "2013.11 (13년차)", "용적률": "599%"})
        if pyung: info["구조"] = "방3/화2" if pyung >= 84 else "방2/화1"
    elif "대치동" in clean_name and "래미안대치팰리스" in clean_name:
        info.update({"세대수": "1,607세대", "준공": "2015.09 (11년차)", "용적률": "259%", "구조": "방3/화2"})
    elif "반포동" in clean_name and "아크로리버파크" in clean_name:
        info.update({"세대수": "1,612세대", "준공": "2016.08 (10년차)", "용적률": "299%", "구조": "방3/화2"})
    elif "잠실동" in clean_name and "리센츠" in clean_name:
        info.update({"세대수": "5,563세대", "준공": "2008.07 (18년차)", "용적률": "275%", "구조": "방3/화2"})
    elif "이촌동" in clean_name and "한가람" in clean_name:
        info.update({"세대수": "2,036세대", "준공": "1998.09 (28년차)", "용적률": "358%", "구조": "방3/화2"})
    elif "흑석동" in clean_name and "아크로리버하임" in clean_name:
        info.update({"세대수": "1,073세대", "준공": "2019.05 (7년차)", "용적률": "205%", "구조": "방3/화2"})
    elif "홍파동" in clean_name and "경희궁자이" in clean_name:
        info.update({"세대수": "1,148세대", "준공": "2017.02 (9년차)", "용적률": "252%", "구조": "방3/화2"})
    elif "당산동" in clean_name and "당산센트럴" in clean_name:
        info.update({"세대수": "802세대", "준공": "2020.05 (6년차)", "용적률": "299%", "구조": "방3/화2"})
    elif "만리동" in clean_name and "서울역센트럴자이" in clean_name:
        info.update({"세대수": "1,341세대", "준공": "2017.08 (9년차)", "용적률": "243%", "구조": "방3/화2"})
    elif "광장동" in clean_name and "광장힐스테이트" in clean_name:
        info.update({"세대수": "453세대", "준공": "2012.03 (14년차)", "용적률": "228%", "구조": "방3/화2"})
    elif "염리동" in clean_name and "마포프레스티지자이" in clean_name:
        info.update({"세대수": "1,694세대", "준공": "2021.03 (5년차)", "용적률": "250%", "구조": "방3/화2"})
    elif "둔촌동" in clean_name and "올림픽파크포레온" in clean_name:
        info.update({"세대수": "12,032세대", "준공": "2025.01 (1년차)", "용적률": "273%", "구조": "방3/화2"})
    elif "옥수동" in clean_name and "래미안옥수" in clean_name:
        info.update({"세대수": "1,511세대", "준공": "2012.12 (14년차)", "용적률": "246%", "구조": "방3/화2"})
    elif "신정동" in clean_name and "목동힐스테이트" in clean_name:
        info.update({"세대수": "1,081세대", "준공": "2016.05 (10년차)", "용적률": "241%", "구조": "방3/화2"})
    elif "마곡동" in clean_name and "마곡엠밸리7" in clean_name:
        info.update({"세대수": "1,004세대", "준공": "2014.05 (12년차)", "용적률": "221%", "구조": "방3/화2"})
    elif "북아현동" in clean_name and "e편한세상신촌" in clean_name:
        info.update({"세대수": "1,910세대", "준공": "2018.05 (8년차)", "용적률": "271%", "구조": "방3/화2"})
    elif "길음동" in clean_name and "래미안길음" in clean_name:
        info.update({"세대수": "2,352세대", "준공": "2019.02 (7년차)", "용적률": "272%", "구조": "방3/화2"})
    elif "전농동" in clean_name and "sky" in clean_name.lower():
        info.update({"세대수": "1,425세대", "준공": "2023.07 (3년차)", "용적률": "999%", "구조": "방3/화2"})
    elif "봉천동" in clean_name and "서울대입구" in clean_name:
        info.update({"세대수": "1,531세대", "준공": "2019.06 (7년차)", "용적률": "237%", "구조": "방3/화2"})
    elif "중계동" in clean_name and "청구3" in clean_name:
        info.update({"세대수": "780세대", "준공": "1996.03 (30년차)", "용적률": "242%", "구조": "방3/화2"})
    elif "신도림동" in clean_name and "신도림4차" in clean_name:
        info.update({"세대수": "853세대", "준공": "2003.05 (23년차)", "용적률": "299%", "구조": "방3/화2"})
    elif "면목동" in clean_name and "사가정센트럴" in clean_name:
        info.update({"세대수": "1,505세대", "준공": "2020.07 (6년차)", "용적률": "299%", "구조": "방3/화2"})
    elif "응암동" in clean_name and "녹번역" in clean_name:
        info.update({"세대수": "2,569세대", "준공": "2020.05 (6년차)", "용적률": "242%", "구조": "방3/화2"})
    elif "미아동" in clean_name and "북서울자이" in clean_name:
        info.update({"세대수": "1,045세대", "준공": "2024.08 (2년차)", "용적률": "240%", "구조": "방3/화2"})
    elif "독산동" in clean_name and "롯데캐슬골드파크3" in clean_name:
        info.update({"세대수": "1,236세대", "준공": "2018.10 (8년차)", "용적률": "399%", "구조": "방3/화2"})
    elif "창동" in clean_name and "북한산아이파크" in clean_name:
        info.update({"세대수": "2,061세대", "준공": "2004.07 (22년차)", "용적률": "247%", "구조": "방3/화2"})
    return info

df = load_data_v6_15()

if not df.empty:
    # 기본 전처리 및 공백 제거 가상 컬럼 추가 (매칭 정확도 향상용)
    df['단지선택명'] = df['법정동'] + " " + df['아파트명']
    df['단지선택명_공백제거'] = df['단지선택명'].astype(str).str.replace(' ', '').str.replace('-', '')
    df['거래금액(숫자)'] = df['거래금액(만)'].astype(str).str.replace(',', '').astype(int)
    df['평형'] = df['전용면적(㎡)'].apply(lambda x: round(float(x)))
    df['월_날짜객체'] = df['거래일자'].dt.to_period('M').dt.to_timestamp()
    df['월_한글텍스트'] = df['거래일자'].dt.strftime('%y년 %m월')
    df['자치구'] = df['법정동'].apply(get_gu_name)

    max_prices = df.groupby(['단지선택명', '평형'])['거래금액(숫자)'].max().to_dict()

    # 랜드마크 검색 키워드 (공백 제거 버전 매칭)
    search_keywords = {
        "중랑구": "사가정센트럴", "강남구": "래미안대치팰리스", "서초구": "아크로리버파크", "송파구": "리센츠",
        "용산구": "한가람", "동작구": "아크로리버하임", "종로구": "경희궁자이", "영등포구": "당산센트럴",
        "중구": "서울역센트럴", "광진구": "광장힐스테이트", "마포구": "마포프레스티지", "강동구": "올림픽파크포레온",
        "성동구": "래미안옥수", "양천구": "목동힐스테이트", "강서구": "마곡엠밸리7", "서대문구": "e편한세상신촌",
        "성북구": "래미안길음", "동대문구": "SKY", "관악구": "서울대입구", "노원구": "청구3",
        "구로구": "신도림4차", "은평구": "녹번역", "강북구": "북서울자이", "금천구": "롯데캐슬골드파크3",
        "도봉구": "북한산아이파크"
    }

    display_names = {
        "중랑구": "사가정센트럴아이파크", "강남구": "래미안대치팰리스", "서초구": "아크로리버파크", "송파구": "리센츠",
        "용산구": "이촌동 한가람", "동작구": "아크로리버하임", "종로구": "경희궁자이", "영등포구": "당산센트럴아이파크",
        "중구": "서울역센트럴자이", "광진구": "광장힐스테이트", "마포구": "마포프레스티지자이", "강동구": "올림픽파크포레온",
        "성동구": "래미안옥수리버젠", "양천구": "목동힐스테이트", "강서구": "마곡엠밸리7단지", "서대문구": "e편한세상신촌",
        "성북구": "래미안길음센터피스", "동대문구": "SKY-L65", "관악구": "e편한세상서울대입구", "노원구": "중계청구3차",
        "구로구": "신도림4차 e편한세상", "은평구": "녹번역e편한세상캐슬", "강북구": "북서울자이폴라리스", "금천구": "롯데캐슬골드파크3차",
        "도봉구": "북한산아이파크"
    }

    df['is_landmark'] = df['단지선택명_공백제거'].apply(lambda x: any(k in x for k in search_keywords.values()))

    st.title("🏢 강석의 서울 랜드마크 시세 마스터 v6.15")

    main_tab0, main_tab1, main_tab2 = st.tabs(["👑 서울 랜드마크 지도 & 지수", "📊 단지별 정밀 분석", "⚖️ 단지간 비교 평가"])

    # ==================== TAB 0: 서울 고증 그리드 지도 ====================
    with main_tab0:
        col_map, col_chart = st.columns([1.3, 1.0])

        with col_map:
            latest_month_str = df['월_날짜객체'].max().strftime('%y년 %m월')
            
            head_c1, head_c2 = st.columns([7, 3])
            with head_c1:
                st.subheader("🗺️ 서울 25개 자치구 고증 시세판")
            with head_c2:
                st.markdown(f"<div style='text-align: right; padding-top: 15px; font-size: 11pt; font-weight: bold; color: #3b82f6;'>💡 {latest_month_str} 평균값</div>", unsafe_allow_html=True)
            
            st.caption("실제 지리적 방위와 인접 구 경계선을 정밀 고증하여 재배치한 마스터 시세 그리드 맵입니다.")

            # [고증 패치] 서울 25개 자치구 정밀 5x8 맵 구조 리배치
            map_grid = [
                [None, "은평구", "종로구", "동대문구", "중랑구"],
                ["서대문구", "마포구", "용산구", "성동구", "광진구"],
                ["한강_SPAN"], # 완벽하게 북부와 남부를 가르는 한강 라인 고증
                ["강서구", "양천구", "영등포구", "동작구", "서초구"],
                [None, "구로구", "금천구", "관악구", "강남구"],
                [None, None, None, "송파구", "강동구"]
            ]

            current_prices = {}
            for area_name, search_k in search_keywords.items():
                # 공백 제거 컬럼 기준으로 매칭하여 누수 방지
                sub_data = df[df['단지선택명_공백제거'].str.contains(search_k, case=False, na=False)]
                if not sub_data.empty:
                    latest_m = sub_data['월_날짜객체'].max()
                    price_mean = sub_data[sub_data['월_날짜객체'] == latest_m]['거래금액(숫자)'].mean()
                    price_eok = price_mean / 10000 
                    
                    current_prices[area_name] = {
                        "price": f"{price_eok:.1f}억", 
                        "name": display_names[area_name], 
                        "active": True
                    }

            html_map = "<div style='display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; background-color: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0;'>"
            
            for row in map_grid:
                if row == ["한강_SPAN"]:
                    html_map += "<div style='grid-column: 1 / -1; height: 34px; background: linear-gradient(90deg, #60a5fa, #2563eb, #60a5fa); border-radius: 6px; display: flex; align-items: center; justify-content: center; color: white; font-size: 10pt; font-weight: bold; letter-spacing: 12px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);'>HAN RIVER</div>"
                    continue
                
                for loc in row:
                    if loc is None:
                        html_map += "<div style='height: 85px;'></div>"
                    else:
                        data = current_prices.get(loc, {"price": "-", "name": "미수집", "active": False})
                        
                        bg = "background-color: white; border: 1px solid #cbd5e1; box-shadow: 1px 2px 4px rgba(0,0,0,0.08);" if data['active'] else "background-color: #f1f5f9; border: 1px solid #e2e8f0; opacity: 0.5;"
                        text_c = "#1e3a8a" if data['active'] else "#94a3b8"
                        text_weight = "font-weight: 800;" if data['active'] else "font-weight: normal;"
                        t_bg = "background-color: #facc15; color: #1e293b;" if data['active'] else "background-color: #e2e8f0; color: #94a3b8;"
                        
                        html_map += f"<div style='{bg} border-radius: 6px; height: 85px; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden; text-align: center;'>"
                        html_map += f"<div style='{t_bg} font-size: 8.5pt; font-weight: bold; padding: 4px 0;'>{loc}</div>"
                        html_map += f"<div style='font-size: 7pt; color: #475569; padding: 2px 4px; line-height: 1.15; word-break: keep-all; flex-grow: 1; display: flex; align-items: center; justify-content: center;'>{data['name']}</div>"
                        html_map += f"<div style='font-size: 13pt; {text_weight} color: {text_c}; padding-bottom: 4px;'>{data['price']}</div>"
                        html_map += "</div>"
            
            html_map += "</div>"
            st.markdown(html_map, unsafe_allow_html=True)

        with col_chart:
            st.subheader("📈 서울 랜드마크 종합 지수 추이")
            landmark_df = df[df['is_landmark'] == True].copy()
            landmark_stats = landmark_df.groupby('월_날짜객체').agg({'거래금액(숫자)': 'mean'}).reset_index()
            
            fig_idx = go.Figure()
            fig_idx.add_trace(go.Scatter(x=landmark_stats['월_날짜객체'], y=landmark_stats['거래금액(숫자)'], mode='lines+markers', line=dict(color='#3b82f6', width=4), marker=dict(size=8, color='white', line=dict(width=2, color='#3b82f6')), name="서울 대장주 평균"))
            fig_idx.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=430, paper_bgcolor='white', plot_bgcolor='white', hovermode='x unified')
            fig_idx.update_xaxes(type='date', tickformat="%y년 %m월", dtick="M3", showgrid=True, gridcolor='#f1f5f9')
            fig_idx.update_yaxes(showgrid=True, gridcolor='#f1f5f9')
            st.plotly_chart(fig_idx, use_container_width=True)

    # ==================== TAB 1: 단일 단지 시황 분석 ====================
    with main_tab1:
        if 'selected_gu' not in st.session_state: 
            st.session_state['selected_gu'] = '전체구'
            
        seoul_gus = ["전체구", "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"]

        with st.expander(f"🗺️ 현재 선택된 지역: [ {st.session_state['selected_gu']} ] (터치하여 변경)", expanded=False):
            grid_cols = st.columns(4)
            for idx, gu in enumerate(seoul_gus):
                button_label = f"🌐 {gu}" if gu == "전체구" and gu == st.session_state['selected_gu'] else (f"📍 {gu}" if gu == st.session_state['selected_gu'] else gu)
                with grid_cols[idx % 4]:
                    if st.button(button_label, key=f"gu_btn_{gu}", use_container_width=True):
                        st.session_state['selected_gu'] = gu
                        st.rerun()

        st.markdown("### 🔔 실시간 관심 지역 시황 브리핑 센터")
        latest_data_date = df['거래일자'].max()
        seven_days_ago = latest_data_date - timedelta(days=7)
        recent_7d_df = df[df['거래일자'] >= seven_days_ago].copy()
        
        briefing_messages = []
        if not recent_7d_df.empty:
            for idx, row in recent_7d_df.sort_values(by='거래일자', ascending=False).iterrows():
                apt_key = row['단지선택명']
                pyung_key = row['평형']
                price = row['거래금액(숫자)']
                date_str = row['거래일자'].strftime('%m/%d')
                gu_belong = row['자치구']
                max_p = max_prices.get((apt_key, pyung_key), price)
                drop_r = ((price - max_p) / max_p) * 100 if max_p > 0 else 0
                
                if price >= max_p and max_p > 0:
                    briefing_messages.append(f"🔴 **[{gu_belong}] 신고가 발생 ({date_str})** | {apt_key} {pyung_key}㎡형이 **{price:,}만원**에 최고가 거래되었습니다.")
                elif drop_r <= -15.0:
                    briefing_messages.append(f"📉 **[{gu_belong}] 가격 조정 포착 ({date_str})** | {apt_key} {pyung_key}㎡형이 고점 대비 **{drop_r:.1f}%** 조정된 **{price:,}만원**에 거래되었습니다.")
                else:
                    briefing_messages.append(f"📢 **[{gu_belong}] 신규 실거래 수집 ({date_str})** | {apt_key} {pyung_key}㎡형 {row['층']}층이 **{price:,}만원**에 거래 완료되었습니다.")
        else:
            briefing_messages.append("⚪ **최근 7일간 새로 접수된 관심지역 실거래 내역이 없습니다.**")

        briefing_html = "<div style='background-color:#f8fafc; border-left:5px solid #facc15; padding:12px; border-radius:4px; margin-bottom:15px;'>"
        for msg in briefing_messages[:4]: 
            briefing_html += f"<p style='margin: 0 0 6px 0; font-size:11pt; color:#334155;'>{msg}</p>"
        briefing_html += "</div>"
        st.markdown(briefing_html, unsafe_allow_html=True)

        if st.session_state['selected_gu'] == '전체구': 
            gu_filtered_df = df.copy()
        else: 
            gu_filtered_df = df[df['자치구'] == st.session_state['selected_gu']].copy()

        st.sidebar.header("📍 단지 및 평형 선택")
        if not gu_filtered_df.empty:
            apt_list = sorted(gu_filtered_df['단지선택명'].unique())
            selected_apt = st.sidebar.selectbox("단지 선택", apt_list, key="single_apt")
            filtered_df = gu_filtered_df[gu_filtered_df['단지선택명'] == selected_apt].copy()
            pyung_list = sorted(filtered_df['평형'].unique())
            selected_pyung = st.sidebar.selectbox("평형 선택(㎡)", pyung_list, key="single_pyung")
            final_df = filtered_df[filtered_df['평형'] == selected_pyung].copy()
            
            if not final_df.empty:
                info = get_apt_info(selected_apt, selected_pyung)
                st.subheader(f"📍 {selected_apt} ({selected_pyung}㎡)")
                st.markdown(f"**정보:** {info['세대수']} | {info['준공']} 준공 | 용적률 {info['용적률']} | **구조:** <span style='color:#1e3a8a; font-weight:bold;'>{info['구조']}</span>", unsafe_allow_html=True)
                st.markdown("---")
                
                monthly_stats = final_df.groupby('월_날짜객체').agg(월텍스트=('월_한글텍스트', 'first'), 평균가=('거래금액(숫자)', 'mean'), 거래량=('거래금액(숫자)', 'count')).reset_index()
                monthly_stats['평균가'] = monthly_stats['평균가'].round(0).astype(int)
                max_idx = final_df['거래금액(숫자)'].idxmax()
                min_idx = final_df['거래금액(숫자)'].idxmin()
                recent_price = final_df.iloc[-1]['거래금액(숫자)']
                max_price = final_df.loc[max_idx, '거래금액(숫자)']
                min_price = final_df.loc[min_idx, '거래금액(숫자)']
                drop_rate = ((recent_price - max_price) / max_price) * 100
                
                card_cols = st.columns(2)
                with card_cols[0]:
                    st.markdown(f"<div style='background-color:#f8fafc; border:1px solid #e2e8f0; padding:12px; border-radius:6px; margin-bottom:8px; text-align:center;'><p style='margin:0; color:#64748b; font-size:10pt; font-weight:bold;'>최근 실거래가</p><h3 style='margin:4px 0; color:#1e3a8a; font-size:16pt;'>{recent_price:,}만</h3><p style='margin:0; color:#94a3b8; font-size:9pt;'>{final_df.iloc[-1]['거래일자'].strftime('%Y-%m-%d')}</p></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='background-color:#f8fafc; border:1px solid #e2e8f0; padding:12px; border-radius:6px; margin-bottom:8px; text-align:center;'><p style='margin:0; color:#64748b; font-size:10pt; font-weight:bold;'>고점 대비 하락률</p><h3 style='margin:4px 0; color:{'#ef4444' if drop_rate >= 0 else '#3b82f6'}; font-size:16pt;'>{drop_rate:.1f}%</h3><p style='margin:0; color:#94a3b8; font-size:9pt;'>최고가 대비 변동폭</p></div>", unsafe_allow_html=True)
                with card_cols[1]:
                    st.markdown(f"<div style='background-color:#f8fafc; border:1px solid #e2e8f0; padding:12px; border-radius:6px; margin-bottom:8px; text-align:center;'><p style='margin:0; color:#64748b; font-size:10pt; font-weight:bold;'>역대 최고가</p><h3 style='margin:4px 0; color:#ef4444; font-size:16pt;'>{max_price:,}만</h3><p style='margin:0; color:#94a3b8; font-size:9pt;'>{final_df.loc[max_idx, '거래일자'].strftime('%Y-%m-%d')}</p></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='background-color:#f8fafc; border:1px solid #e2e8f0; padding:12px; border-radius:6px; margin-bottom:8px; text-align:center;'><p style='margin:0; color:#64748b; font-size:10pt; font-weight:bold;'>역대 최저가</p><h3 style='margin:4px 0; color:#3b82f6; font-size:16pt;'>{min_price:,}만</h3><p style='margin:0; color:#94a3b8; font-size:9pt;'>{final_df.loc[min_idx, '거래일자'].strftime('%Y-%m-%d')}</p></div>", unsafe_allow_html=True)
                
                st.write("📈 시세 추이 및 거래량")
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Bar(x=monthly_stats['월텍스트'], y=monthly_stats['거래량'], name='월 거래량', marker_color='rgba(200, 220, 240, 0.6)'), secondary_y=True)
                fig.add_trace(go.Scatter(x=final_df['월_한글텍스트'], y=final_df['거래금액(숫자)'], mode='markers', name='개별 실거래', marker=dict(size=7, color='rgba(135, 206, 250, 0.8)'), hovertemplate='금액: %{y}만원'), secondary_y=False)
                fig.add_trace(go.Scatter(x=monthly_stats['월텍스트'], y=monthly_stats['평균가'], mode='lines+markers', name='월 평균가', line=dict(color='#1e3a8a', width=3)), secondary_y=False)
                fig.add_annotation(x=final_df.loc[max_idx, '월_한글텍스트'], y=final_df.loc[max_idx, '거래금액(숫자)'], text="최고", showarrow=True, arrowhead=1, ax=0, ay=-30, bgcolor="#ef4444", font=dict(color="white", size=10))
                fig.add_annotation(x=final_df.loc[min_idx, '월_한글텍스트'], y=final_df.loc[min_idx, '거래금액(숫자)'], text="최저", showarrow=True, arrowhead=1, ax=0, ay=30, bgcolor="#3b82f6", font=dict(color="white", size=10))
                fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), hovermode='x unified', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), paper_bgcolor='white', plot_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)
                
                st.write("📋 전체 실거래 내역 리스트")
                final_df['비고'] = ""
                final_df.loc[max_idx, '비고'] = "🔴 최고가"
                final_df.loc[min_idx, '비고'] = "🔵 최저가"
                display_df = final_df[['거래일자', '층', '거래금액(숫자)', '비고']].copy()
                display_df['거래일자'] = display_df['거래일자'].dt.strftime('%Y-%m-%d')
                display_df = display_df.sort_values(by='거래일자', ascending=False)
                display_df.columns = ['거래일자', '층', '거래금액(만)', '비고']
                styled_df = display_df.style.format({'거래금액(만)': '{:,.0f}'}).set_properties(**{'text-align': 'center'})
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
            else:
                st.warning("선택한 평형의 데이터가 없습니다.")
        else:
            st.warning("데이터가 아직 수집되지 않았습니다.")

    # ==================== TAB 2: 다중 단지 비교 평가 ====================
    with main_tab2:
        st.subheader("⚖️ 단지별 시세 흐름 다중 비교 분석")
        all_apts = sorted(df['단지선택명'].unique())
        selected_apts = st.multiselect("비교할 아파트 단지들을 선택하세요", all_apts, default=all_apts[:2] if len(all_apts) >= 2 else all_apts)
        
        if selected_apts:
            apt_pyung_mapping = {}
            st.markdown("#### 🔍 단지별 비교 평형(전용면적) 지정")
            cols = st.columns(min(len(selected_apts), 3)) 
            for idx, apt in enumerate(selected_apts):
                with cols[idx % 3]:
                    apt_df = df[df['단지선택명'] == apt]
                    available_pyungs = sorted(apt_df['평형'].unique())
                    chosen_pyung = st.selectbox(f"{apt}", available_pyungs, key=f"comp_pyung_{idx}")
                    apt_pyung_mapping[apt] = chosen_pyung
            
            matched_records = []
            for apt, pyung in apt_pyung_mapping.items():
                target_condition = (df['단지선택명'] == apt) & (df['평형'] == pyung)
                matched_records.append(df[target_condition])
                
            if matched_records:
                comp_df = pd.concat(matched_records)
                comp_df['비교단지명'] = comp_df['단지선택명'] + " (" + comp_df['평형'].astype(str) + "㎡)"
                comp_stats = comp_df.groupby(['월_날짜객체', '비교단지명']).agg(평균가=('거래금액(숫자)', 'mean')).reset_index()
                comp_stats['평균가'] = comp_stats['평균가'].round(0).astype(int)
                
                fig_comp = go.Figure()
                for label in sorted(comp_df['비교단지명'].unique()):
                    label_data = comp_stats[comp_stats['비교단지명'] == label].sort_values('월_날짜객체')
                    fig_comp.add_trace(go.Scatter(x=label_data['월_날짜객체'], y=label_data['평균가'], mode='lines+markers', name=label, line=dict(width=2.5), connectgaps=True, hovertemplate='일자: %{x|%y년 %m월}<br>금액: %{y}만원'))
                
                fig_comp.update_layout(margin=dict(l=10, r=10, t=30, b=10), hovermode='x unified', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0), paper_bgcolor='white', plot_bgcolor='white')
                fig_comp.update_xaxes(type='date', tickformat="%y년 %m월", dtick="M3", showgrid=True, gridcolor='#f1f5f9')
                fig_comp.update_yaxes(title_text="월평균 거래금액(만)", showgrid=True, gridcolor='#f1f5f9')
                st.plotly_chart(fig_comp, use_container_width=True)
                
                st.write("📊 평형 매칭 종합 요약 지표")
                summary_records = []
                for label in sorted(comp_df['비교단지명'].unique()):
                    unit_df = comp_df[comp_df['비교단지명'] == label]
                    if not unit_df.empty:
                        sample_row = unit_df.iloc[0]
                        apt_meta = get_apt_info(sample_row['단지선택명'], sample_row['평형'])
                        recent = unit_df.iloc[-1]['거래금액(숫자)']
                        mx = unit_df['거래금액(숫자)'].max()
                        mn = unit_df['거래금액(숫자)'].min()
                        dr = ((recent - mx) / mx) * 100
                        summary_records.append({
                            "지역구": sample_row['자치구'], "비교 대상 단지 (평형)": label, "연식 (준공일)": apt_meta['준공'], "구조 (방/화)": apt_meta['구조'], "최근거래가(만)": recent, "역대최고가(만)": mx, "역대최저가(만)": mn, "고점대비하락률": f"{dr:.1f}%"
                        })
                
                summary_df = pd.DataFrame(summary_records)
                styled_summary = summary_df.style.format({'최근거래가(만)': '{:,.0f}', '역대최고가(만)': '{:,.0f}', '역대최저가(만)': '{:,.0f}'}).set_properties(**{'text-align': 'center'})
                st.dataframe(styled_summary, use_container_width=True, hide_index=True)
else:
    st.error("데이터를 가져오지 못했습니다.")