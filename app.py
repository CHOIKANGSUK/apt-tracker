import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# 1. 페이지 기본 설정 및 모바일 반응형 뷰포트 고정
st.set_page_config(
    page_title="강석의 아파트 시세트래킹",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# [전역 패치] 모바일 가독성 최적화 및 실까 스타일 테이블 전역 CSS 추가
st.markdown("""
<style>
    @media (max-width: 768px) {
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.3rem !important; }
        h3 { font-size: 1.1rem !important; }
        .stSelectbox label { font-size: 0.9rem !important; }
    }
    .block-container {
        padding-top: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .scroll-container::-webkit-scrollbar { display: none; }
    .scroll-container {
        -ms-overflow-style: none;
        scrollbar-width: none;
    }
    
    /* 실까 스타일 테이블 상세 CSS 디자인 */
    .highlight-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
        font-size: 9.5pt;
        margin-bottom: 10px;
    }
    .highlight-table th {
        border-bottom: 2px solid #cbd5e1;
        border-top: 1px solid #cbd5e1;
        padding: 10px 10px;
        text-align: center;
        color: #64748b;
        font-weight: normal;
    }
    .highlight-table td {
        border-bottom: 1px solid #e2e8f0;
        padding: 12px 10px;
        text-align: center;
        color: #334155;
    }
    .price-col {
        font-weight: 800;
        font-size: 11pt;
        color: #0f172a;
        text-align: right !important;
        padding-right: 15px !important;
    }
    .badge-new-high {
        background-color: #ef4444;
        color: white;
        font-size: 7.5pt;
        padding: 2px 6px;
        border-radius: 3px;
        margin-left: 6px;
        vertical-align: middle;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def load_data_v6_33():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
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

def get_gu_name(dong_name):
    dong = str(dong_name).strip().replace(" ", "")
    if any(k in dong for k in ['중화', '상봉', '면목', '신내', '망우', '묵']): return '중랑구'
    elif any(k in dong for k in ['상월곡', '하월곡', '길음', '장위', '석관', '돈암', '정릉', '보문']): return '성북구'
    elif any(k in dong for k in ['이문', '휘경', '전농', '답십리', '장안', '청량리', '제기', '용두']): return '동대문구'
    elif any(k in dong for k in ['만리', '회현', '명동', '신당', '황학']): return '중구'
    elif any(k in dong for k in ['염리', '아현', '공덕', '도화', '대흥', '망원']): return '마포구'
    elif any(k in dong for k in ['이촌', '서빙고', '한남', '보광']): return '용산구'
    elif any(k in dong for k in ['옥수', '성수', '금호', '응봉', '행당']): return '성동구'
    elif any(k in dong for k in ['홍파', '무악', '평창', '혜화', '교북', '견지']): return '종로구'
    elif any(k in dong for k in ['북아현', '남가좌', '홍은', '연희', '창천']): return '서대문구'
    elif any(k in dong for k in ['창동', '방학', '쌍문', '도봉']): return '도봉구'
    elif any(k in dong for k in ['미아', '수유', '번동']): return '강북구'
    elif any(k in dong for k in ['상계', '중계', '하계', '공릉', '월계']): return '노원구'
    elif any(k in dong for k in ['은평', '응암', '불광', '수색', '갈현', '녹번', '대조']): return '은평구'
    elif any(k in dong for k in ['광장', '구의', '자양', '화양', '군자']): return '광진구'
    elif any(k in dong for k in ['대치', '압구정', '삼성', '개포', '역삼', '도곡', '일원', '수서']): return '강남구'
    elif any(k in dong for k in ['반포', '방배', '서초', '잠원', '양재', '우면']): return '서초구'
    elif any(k in dong for k in ['잠실', '신천', '문정', '가락', '오금', '방이', '삼전']): return '송파구'
    elif any(k in dong for k in ['둔촌', '명일', '고덕', '상일', '천호', '암사', '성내']): return '강동구'
    elif any(k in dong for k in ['당산', '신길', '문래', '양평', '영등포', '여의도']): return '영등포구'
    elif any(k in dong for k in ['흑석', '상도', '노량진', '사당', '대방', '신대방']): return '동작구'
    elif any(k in dong for k in ['봉천', '신림', '남현']): return '관악구'
    elif any(k in dong for k in ['신정', '목동', '신월']): return '양천구'
    elif any(k in dong for k in ['마곡', '가양', '화곡', '등촌', '방화', '염창']): return '강서구'
    elif any(k in dong for k in ['신도림', '구로', '고척', '개봉', '오류', '궁동']): return '구로구'
    elif any(k in dong for k in ['독산', '시흥', '가산']): return '금천구'
    return '기타/미분류'

def format_price(price_man):
    price = int(price_man)
    if price % 10000 == 0: return f"{price // 10000}억"
    else: return f"{price // 10000}억 {(price % 10000):,}만"

def get_apt_info(apt_name, pyung=None):
    info = {"세대수": "-", "준공": "-", "용적률": "-", "구조": "-"}
    clean_name = str(apt_name).replace(" ", "").lower()
    if "중화동" in clean_name and "한신" in clean_name: info.update({"세대수": "1,544세대", "준공": "1997.10", "용적률": "376%", "구조": "방2/화1"})
    elif "동아에코빌" in clean_name: info.update({"세대수": "1,253세대", "준공": "2003.06", "용적률": "281%", "구조": "방3/화2"})
    elif "쌍용" in clean_name and "이문" in clean_name: info.update({"세대수": "1,318세대", "준공": "2000.11", "용적률": "343%", "구조": "방3/화2"})
    elif "이문" in clean_name and "현대" in clean_name: info.update({"세대수": "483세대", "준공": "2000.09", "용적률": "319%", "구조": "방3/화2"})
    elif "상봉" in clean_name and "더샵" in clean_name: info.update({"세대수": "497세대", "준공": "2013.11", "용적률": "599%", "구조": "방3/화2"})
    elif "래미안대치" in clean_name: info.update({"세대수": "1,607세대", "준공": "2015.09", "용적률": "259%", "구조": "방3/화2"})
    elif "아크로리버파크" in clean_name: info.update({"세대수": "1,612세대", "준공": "2016.08", "용적률": "299%", "구조": "방3/화2"})
    elif "리센츠" in clean_name: info.update({"세대수": "5,563세대", "준공": "2008.07", "용적률": "275%", "구조": "방3/화2"})
    elif "한가람" in clean_name: info.update({"세대수": "2,036세대", "준공": "1998.09", "용적률": "358%", "구조": "방3/화2"})
    elif "아크로리버하임" in clean_name: info.update({"세대수": "1,073세대", "준공": "2019.05", "용적률": "205%", "구조": "방3/화2"})
    elif "경희궁자이" in clean_name: info.update({"세대수": "1,148세대", "준공": "2017.02", "용적률": "252%", "구조": "방3/화2"})
    elif "당산센트럴" in clean_name: info.update({"세대수": "802세대", "준공": "2020.05", "용적률": "299%", "구조": "방3/화2"})
    elif "서울역센트럴" in clean_name: info.update({"세대수": "1,341세대", "준공": "2017.08", "용적률": "243%", "구조": "방3/화2"})
    elif "광장힐스테이트" in clean_name: info.update({"세대수": "453세대", "준공": "2012.03", "용적률": "228%", "구조": "방3/화2"})
    elif "마포프레스티지" in clean_name: info.update({"세대수": "1,694세대", "준공": "2021.03", "용적률": "250%", "구조": "방3/화2"})
    elif "올림픽파크포레온" in clean_name: info.update({"세대수": "12,032세대", "준공": "2025.01", "용적률": "273%", "구조": "방3/화2"})
    elif "옥수" in clean_name and "래미안" in clean_name: info.update({"세대수": "1,511세대", "준공": "2012.12", "용적률": "246%", "구조": "방3/화2"})
    elif "목동힐스테이트" in clean_name: info.update({"세대수": "1,081세대", "준공": "2016.05", "용적률": "241%", "구조": "방3/화2"})
    elif "마곡엠밸리7" in clean_name: info.update({"세대수": "1,004세대", "준공": "2014.05", "용적률": "221%", "구조": "방3/화2"})
    elif "e편한세상신촌" in clean_name: info.update({"세대수": "1,910세대", "준공": "2018.05", "용적률": "271%", "구조": "방3/화2"})
    elif "래미안길음" in clean_name: info.update({"세대수": "2,352세대", "준공": "2019.02", "용적률": "272%", "구조": "방3/화2"})
    elif "sky" in clean_name: info.update({"세대수": "1,425세대", "준공": "2023.07", "용적률": "999%", "구조": "방3/화2"})
    elif "서울대입구" in clean_name: info.update({"세대수": "1,531세대", "준공": "2019.06", "용적률": "237%", "구조": "방3/화2"})
    elif "청구3" in clean_name: info.update({"세대수": "780세대", "준공": "1996.03", "용적률": "242%", "구조": "방3/화2"})
    elif "신도림" in clean_name and "편한" in clean_name: info.update({"세대수": "853세대", "준공": "2003.05", "용적률": "249%", "구조": "방3/화2"})
    elif "사가정센트럴" in clean_name: info.update({"세대수": "1,505세대", "준공": "2020.07", "용적률": "299%", "구조": "방3/화2"})
    elif "녹번" in clean_name: info.update({"세대수": "2,569세대", "준공": "2020.05", "용적률": "242%", "구조": "방3/화2"})
    elif "북서울자이" in clean_name: info.update({"세대수": "1,045세대", "준공": "2024.08", "용적률": "240%", "구조": "방3/화2"})
    elif "롯데캐슬골드파크3" in clean_name: info.update({"세대수": "1,236세대", "준공": "2018.10", "용적률": "399%", "구조": "방3/화2"})
    elif "북한산아이파크" in clean_name: info.update({"세대수": "2,061세대", "준공": "2004.07", "용적률": "247%", "구조": "방3/화2"})
    return info

df = load_data_v6_33()

if not df.empty:
    df['단지선택명'] = df['법정동'].astype(str).str.strip() + " " + df['아파트명'].astype(str).str.strip()
    df['자치구'] = df['법정동'].apply(get_gu_name)
    df['거래금액(숫자)'] = df['거래금액(만)'].astype(str).str.replace(',', '').astype(int)
    df['평형'] = df['전용면적(㎡)'].apply(lambda x: round(float(x)))
    df['월_날짜객체'] = df['거래일자'].dt.to_period('M').dt.to_timestamp()
    df['월_한글텍스트'] = df['거래일자'].dt.strftime('%y년 %m월')

    max_prices = df.groupby(['단지선택명', '평형'])['거래금액(숫자)'].max().to_dict()

    match_rules = {
        "도봉구": "북한산아이파크", "강북구": "북서울자이", "노원구": "청구3", "성북구": "래미안길음",
        "은평구": "녹번역", "서대문구": "e편한세상신촌", "종로구": "경희궁자이", "동대문구": "sky",
        "중랑구": "사가정센트럴", "마포구": "마포프레스티지", "용산구": "한가람", "중구": "서울역센트럴",
        "성동구": "래미안옥수", "광진구": "광장힐스테이트", "강동구": "올림픽파크포레온", "강서구": "마곡엠밸리7",
        "양천구": "목동힐스테이트", "영등포구": "당산센트럴", "동작구": "아크로리버하임", "서초구": "아크로리버파크",
        "강남구": "래미안대치팰리스", "송파구": "리센츠", "구로구": "신도림4차", "금천구": "롯데캐슬골드파크3",
        "관악구": "서울대입구"
    }

    display_names = {
        "도봉구": "북한산 아이파크", "강북구": "북서울자이폴라리스", "노원구": "중계 청구3차", "성북구": "래미안길음센터피스",
        "은평구": "녹번역e편한세상캐슬", "서대문구": "e편한세상신촌", "종로구": "경희궁자이 2단지", "동대문구": "롯데캐슬 SKY-L65", "중랑구": "사가정센트럴아이파크",
        "마포구": "마포프레스티지자이", "용산구": "이촌동 한가람", "중구": "서울역센트럴자이", "성동구": "래미안옥수리버젠", "광진구": "광장힐스테이트", "강동구": "올림픽파크포레온",
        "강서구": "마곡엠밸리7단지", "양천구": "목동힐스테이트", "영등포구": "당산센트럴아이파크", "동작구": "아크로리버하임", "서초구": "아크로리버파크", "강남구": "래미안대치팰리스", "송파구": "리센츠",
        "구로구": "신도림4차 e-편한세상", "금천구": "롯데캐슬골드파크3차", "관악구": "e편한세상서울대입구"
    }

    collected_data = {gu: [] for gu in match_rules.keys()}
    landmark_match_keys = []

    for idx, row in df.iterrows():
        search_str = (str(row['법정동']).replace(" ", "") + str(row['아파트명']).replace(" ", "")).lower()
        for gu_name, keyword in match_rules.items():
            if keyword.lower() in search_str:
                collected_data[gu_name].append(row)
                landmark_match_keys.append(row['단지선택명'])

    df['is_landmark'] = df['단지선택명'].isin(landmark_match_keys)

    st.title("🏢 강석의 서울 랜드마크 시세 마스터 v6.33")

    main_tab0, main_tab_new, main_tab1, main_tab2 = st.tabs([
        "👑 서울 랜드마크 시세트래킹 지도", 
        "🚨 주간 실거래 하이라이트", 
        "📊 단지별 정밀 분석", 
        "⚖️ 단지간 비교 평가"
    ])

    # ==================== TAB 0: 모바일 스와이프 최적화 지도 ====================
    with main_tab0:
        all_available_months = sorted(df['월_날짜객체'].unique())
        month_options = [pd.to_datetime(m).strftime('%y년 %m월') for m in all_available_months]
        reversed_month_options = month_options[::-1]
        
        st.subheader("🗺️ 서울 랜드마크 시세트래킹 지도")
        st.caption("각 자치구 대장주의 **'국민평형(84㎡)'** 월간 평균 실거래 금액 스냅샷입니다. (모바일에서는 지도를 좌우로 밀어서 보세요👉)")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            chosen_month_str = st.selectbox("📅 분석 기준월 (클릭하여 변경)", options=reversed_month_options, index=0)
            chosen_month_date = all_available_months[month_options.index(chosen_month_str)]

        processed_prices = {}
        for gu_name, rows in collected_data.items():
            if len(rows) > 0:
                g_df = pd.DataFrame(rows)
                g_df_84 = g_df[g_df['평형'].between(83, 85)]
                g_df_month = g_df_84[g_df_84['월_날짜객체'] == chosen_month_date]
                
                if not g_df_month.empty:
                    price_mean = g_df_month['거래금액(숫자)'].mean()
                    price_eok = price_mean / 10000
                    processed_prices[gu_name] = {"price": f"{price_eok:.1f}억", "name": display_names[gu_name], "active": True}
                else:
                    processed_prices[gu_name] = {"price": "-", "name": display_names[gu_name], "active": False}
            else:
                processed_prices[gu_name] = {"price": "-", "name": display_names[gu_name], "active": False}

        map_grid = [
            [None, None, None, None, None, None, None, None],
            [None, None, None, None, "강북구", "도봉구", None, None],
            [None, None, None, None, "성북구", "노원구", None, None],
            [None, None, "서대문구", "종로구", "동대문구", "중랑구", None, None],
            [None, "은평구", "마포구", "용산구", "중구", "성동구", "광진구", None],
            ["한강_SPAN"],
            ["강서구", "양천구", "영등포구", "동작구", "서초구", "강남구", "송파구", "강동구"],
            [None, "구로구", "금천구", "관악구", None, None, None, None]
        ]

        html_map = "<div class='scroll-container' style='width: 100%; overflow-x: auto; white-space: nowrap; padding-bottom: 10px;'>"
        html_map += "<div style='display: grid; grid-template-columns: repeat(8, minmax(100px, 1fr)); gap: 6px; background-color: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; min-width: 850px;'>"
        
        for row in map_grid:
            if row == ["한강_SPAN"]:
                html_map += "<div style='grid-column: 1 / -1; height: 38px; background: linear-gradient(90deg, #60a5fa, #2563eb, #60a5fa); border-radius: 6px; display: flex; align-items: center; justify-content: center; color: white; font-size: 10pt; font-weight: bold; letter-spacing: 15px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);'>HAN RIVER</div>"
                continue
            
            for loc in row:
                if loc is None:
                    html_map += "<div style='height: 90px;'></div>"
                else:
                    data = processed_prices.get(loc, {"price": "-", "name": "미수집", "active": False})
                    bg = "background-color: white; border: 1px solid #cbd5e1; box-shadow: 1px 2px 4px rgba(0,0,0,0.08);" if data['active'] else "background-color: #f1f5f9; border: 1px solid #e2e8f0; opacity: 0.5;"
                    text_c = "#1e3a8a" if data['active'] else "#94a3b8"
                    text_weight = "font-weight: 800;" if data['active'] else "font-weight: normal;"
                    t_bg = "background-color: #facc15; color: #1e293b;" if data['active'] else "background-color: #e2e8f0; color: #94a3b8;"
                    
                    html_map += f"<div style='{bg} border-radius: 6px; height: 90px; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden; text-align: center; white-space: normal;'>\
                                    <div style='{t_bg} font-size: 8.5pt; font-weight: bold; padding: 4px 0;'>{loc}</div>\
                                    <div style='font-size: 7.5pt; color: #475569; padding: 2px 4px; line-height: 1.2; word-break: break-word; flex-grow: 1; display: flex; align-items: center; justify-content: center;'>{data['name']}</div>\
                                    <div style='font-size: 13pt; {text_weight} color: {text_c}; padding-bottom: 4px;'>{data['price']}</div>\
                                 </div>"
        html_map += "</div></div>"
        st.markdown(html_map, unsafe_allow_html=True)

        st.markdown("<br><br>", unsafe_allow_html=True)
        st.subheader("📈 서울 랜드마크 84㎡ 종합 지수 추이")
        
        landmark_df = df[df['is_landmark'] == True].copy()
        landmark_df_84 = landmark_df[landmark_df['평형'].between(83, 85)]
        
        if not landmark_df_84.empty:
            landmark_stats = landmark_df_84.groupby('월_날짜객체').agg(거래금액=('거래금액(숫자)', 'mean')).reset_index()
            fig_idx = go.Figure()
            fig_idx.add_trace(go.Scatter(x=landmark_stats['월_날짜객체'], y=landmark_stats['거래금액'], mode='lines+markers', line=dict(color='#3b82f6', width=4), marker=dict(size=8, color='white', line=dict(width=2, color='#3b82f6')), name="서울 대장주 84㎡ 평균"))
            fig_idx.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=350, paper_bgcolor='white', plot_bgcolor='white', hovermode='x unified')
            fig_idx.update_xaxes(type='date', tickformat="%y년 %m월", dtick="M3", showgrid=True, gridcolor='#f1f5f9')
            fig_idx.update_yaxes(showgrid=True, gridcolor='#f1f5f9')
            fig_idx.update_layout(legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
            st.plotly_chart(fig_idx, use_container_width=True)

    # ==================== TAB 1: 주간 실거래 하이라이트 (🔥 모바일 스와이프 및 줄바꿈 방지 적용) ====================
    with main_tab_new:
        latest_date = df['거래일자'].max()
        week_ago = latest_date - timedelta(days=7)
        
        st.markdown(f"<h2>🚨 서울 랜드마크 주간 주요거래 <span style='font-size:12pt; color:#64748b; font-weight:normal;'>({week_ago.strftime('%m/%d')} ~ {latest_date.strftime('%m/%d')} 기준)</span></h2>", unsafe_allow_html=True)
        
        recent_df = df[df['거래일자'] >= week_ago].copy()
        
        if recent_df.empty:
            st.info("최근 7일간 업데이트된 실거래 내역이 없습니다.")
        else:
            recent_df = recent_df.sort_values(by=['거래일자', '거래금액(숫자)'], ascending=[False, False])
            
            new_highs = []
            trades_59 = []
            trades_84 = []
            
            for idx, row in recent_df.iterrows():
                apt_key = row['단지선택명']
                pyung_key = row['평형']
                price = row['거래금액(숫자)']
                t_date = row['거래일자']
                
                past_df = df[(df['단지선택명'] == apt_key) & (df['평형'] == pyung_key) & (df['거래일자'] < t_date)]
                
                is_new_high = False
                diff_str = ""
                
                if not past_df.empty:
                    prev_max = past_df['거래금액(숫자)'].max()
                    if price > prev_max:
                        is_new_high = True
                        diff = price - prev_max
                        
                        eok = diff // 10000
                        man = diff % 10000
                        if eok > 0 and man > 0:
                            diff_str = f" <span style='color:#ef4444; font-size:8.5pt;'>(▲{eok}억 {man:,}만원)</span>"
                        elif eok > 0 and man == 0:
                            diff_str = f" <span style='color:#ef4444; font-size:8.5pt;'>(▲{eok}억원)</span>"
                        else:
                            diff_str = f" <span style='color:#ef4444; font-size:8.5pt;'>(▲{man:,}만원)</span>"
                else:
                    is_new_high = True
                    diff_str = ""
                
                apt_display_name = apt_key.split()[1] if len(apt_key.split())>1 else apt_key
                
                trade_info = {
                    "시군구": row['자치구'],
                    "아파트명": apt_display_name,
                    "면적": f"{pyung_key}㎡",
                    "층": f"{row['층']}층",
                    "가격": format_price(price),
                    "is_new_high": is_new_high,
                    "diff_str": diff_str,
                    "date": t_date
                }
                
                if is_new_high: new_highs.append(trade_info)
                if 58 <= pyung_key <= 60: trades_59.append(trade_info)
                if 83 <= pyung_key <= 85: trades_84.append(trade_info)
                
            # [핵심 패치] 모바일에서 표가 줄바꿈되지 않고 좌우로 스크롤되도록 CSS 클래스와 래퍼(wrapper) 적용
            def make_highlight_table(data_list, title, title_color="#ef4444"):
                if not data_list: return f"<div style='text-align:center; color:#94a3b8; padding:20px; font-size:9.5pt;'>조건에 맞는 주간 거래가 없습니다.</div>"
                
                # min-width: 650px 와 white-space: nowrap 을 적용하여 모바일 스와이프 활성화
                html = f"""<div style="text-align:center; margin-top:20px; margin-bottom:10px;">
<span style="background-color:white; padding:0 15px; font-weight:bold; font-size:12pt; color:{title_color}; position:relative; z-index:2;">━━━ {title} ━━━</span>
</div>
<div class='scroll-container' style='width: 100%; overflow-x: auto; padding-bottom: 10px;'>
<table class="highlight-table" style="min-width: 650px; white-space: nowrap;">
<tr>
<th style="width:5%;">#</th>
<th style="width:12%;">시군구</th>
<th style="width:33%; text-align:left;">아파트명</th>
<th style="width:10%;">면적</th>
<th style="width:10%;">층</th>
<th style="width:12%;">실거래일</th>
<th style="width:18%; text-align:right; padding-right:15px;">가격</th>
</tr>"""
                
                for i, item in enumerate(data_list[:15]):
                    badge = "<span class='badge-new-high'>신고가</span>" if item['is_new_high'] else ""
                    d_str = item['diff_str']
                    date_str = item['date'].strftime('%y.%m.%d')
                    
                    html += f"""
<tr>
<td style="color:#94a3b8; font-weight:bold;">{i+1}</td>
<td>{item['시군구']}</td>
<td style="text-align:left; font-weight:bold;">{item['아파트명']} {badge}{d_str}</td>
<td>{item['면적']}</td>
<td>{item['층']}</td>
<td style="color:#64748b; font-size:8.5pt;">{date_str}</td>
<td class="price-col">{item['가격']}</td>
</tr>"""
                html += "\n</table></div>"
                return html

            st.markdown(make_highlight_table(new_highs, "신고가 주요거래", "#ef4444"), unsafe_allow_html=True)
            st.markdown(make_highlight_table(trades_84, "84㎡ 주요거래", "#334155"), unsafe_allow_html=True)
            st.markdown(make_highlight_table(trades_59, "59㎡ 주요거래", "#334155"), unsafe_allow_html=True)

            st.markdown("""<div style="text-align:center; margin-top:30px; margin-bottom:10px;">
<span style="background-color:white; padding:0 15px; font-weight:bold; font-size:12pt; color:#3b82f6; position:relative; z-index:2;">━━━ 시군구별 거래 현황 ━━━</span>
</div>""", unsafe_allow_html=True)
            
            gu_counts = recent_df['자치구'].value_counts().reset_index()
            gu_counts.columns = ['자치구', '거래건수']
            
            gu_html = "<div style='display:flex; flex-wrap:wrap; gap:10px; justify-content:center; margin-bottom:30px;'>"
            for _, row in gu_counts.iterrows():
                gu_html += f"<div style='background-color:#f8fafc; border:1px solid #e2e8f0; padding:8px 15px; border-radius:20px; font-size:9pt;'><span style='color:#64748b;'>{row['자치구']}</span> <span style='font-weight:bold; color:#1e3a8a;'>{row['거래건수']}건</span></div>"
            gu_html += "</div>"
            st.markdown(gu_html, unsafe_allow_html=True)

    # ==================== TAB 2: 단일 단지 시황 분석 ====================
    with main_tab1:
        if 'selected_gu' not in st.session_state: st.session_state['selected_gu'] = '전체구'
        seoul_gus = ["전체구", "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"]

        with st.expander(f"🗺️ 현재 선택된 지역: [ {st.session_state['selected_gu']} ] (터치하여 변경)", expanded=False):
            grid_cols = st.columns(3)
            for idx, gu in enumerate(seoul_gus):
                button_label = f"🌐 {gu}" if gu == "전체구" and gu == st.session_state['selected_gu'] else (f"📍 {gu}" if gu == st.session_state['selected_gu'] else gu)
                with grid_cols[idx % 3]:
                    if st.button(button_label, key=f"gu_btn_{gu}", use_container_width=True):
                        st.session_state['selected_gu'] = gu
                        st.rerun()

        if st.session_state['selected_gu'] == '전체구': gu_filtered_df = df.copy()
        else: gu_filtered_df = df[df['자치구'] == st.session_state['selected_gu']].copy()

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
                st.markdown(f"**정보:** 세대수 {info['세대수']} | 준공 {info['준공']} | 용적률 {info['용적률']} | **구조:** <span style='color:#1e3a8a; font-weight:bold;'>{info['구조']}</span>", unsafe_allow_html=True)
                st.markdown(f"---")
                
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
                    st.markdown(f"<div style='background-color:#f8fafc; border:1px solid #e2e8f0; padding:12px; border-radius:6px; margin-bottom:8px; text-align:center;'><p style='margin:0; color:#64748b; font-size:10pt; font-weight:bold;'>최근 실거래가</p><h3 style='margin:4px 0; color:#1e3a8a; font-size:15pt;'>{recent_price:,}만</h3><p style='margin:0; color:#94a3b8; font-size:9pt;'>{final_df.iloc[-1]['거래일자'].strftime('%Y-%m-%d')}</p></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='background-color:#f8fafc; border:1px solid #e2e8f0; padding:12px; border-radius:6px; margin-bottom:8px; text-align:center;'><p style='margin:0; color:#64748b; font-size:10pt; font-weight:bold;'>고점 대비 하락률</p><h3 style='margin:4px 0; color:{'#ef4444' if drop_rate >= 0 else '#3b82f6'}; font-size:15pt;'>{drop_rate:.1f}%</h3><p style='margin:0; color:#94a3b8; font-size:9pt;'>최고가 대비 변동폭</p></div>", unsafe_allow_html=True)
                with card_cols[1]:
                    st.markdown(f"<div style='background-color:#f8fafc; border:1px solid #e2e8f0; padding:12px; border-radius:6px; margin-bottom:8px; text-align:center;'><p style='margin:0; color:#64748b; font-size:10pt; font-weight:bold;'>역대 최고가</p><h3 style='margin:4px 0; color:#ef4444; font-size:15pt;'>{max_price:,}만</h3><p style='margin:0; color:#94a3b8; font-size:9pt;'>{final_df.loc[max_idx, '거래일자'].strftime('%Y-%m-%d')}</p></div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='background-color:#f8fafc; border:1px solid #e2e8f0; padding:12px; border-radius:6px; margin-bottom:8px; text-align:center;'><p style='margin:0; color:#64748b; font-size:10pt; font-weight:bold;'>역대 최저가</p><h3 style='margin:4px 0; color:#3b82f6; font-size:15pt;'>{min_price:,}만</h3><p style='margin:0; color:#94a3b8; font-size:9pt;'>{final_df.loc[min_idx, '거래일자'].strftime('%Y-%m-%d')}</p></div>", unsafe_allow_html=True)
                
                st.write("📈 시 추이 및 거래량")
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Bar(x=monthly_stats['월텍스트'], y=monthly_stats['거래량'], name='월 거래량', marker_color='rgba(200, 220, 240, 0.6)'), secondary_y=True)
                fig.add_trace(go.Scatter(x=final_df['월_한글텍스트'], y=final_df['거래금액(숫자)'], mode='markers', name='개별 실거래', marker=dict(size=7, color='rgba(135, 206, 250, 0.8)'), hovertemplate='금액: %{y}만원'), secondary_y=False)
                fig.add_trace(go.Scatter(x=monthly_stats['월텍스트'], y=monthly_stats['평균가'], mode='lines+markers', name='월 평균가', line=dict(color='#1e3a8a', width=3)), secondary_y=False)
                
                fig.add_annotation(x=final_df.loc[max_idx, '월_한글텍스트'], y=final_df.loc[max_idx, '거래금액(숫자)'], text="최고", showarrow=True, arrowhead=1, ax=0, ay=-30, bgcolor="#ef4444", font=dict(color="white", size=10))
                fig.add_annotation(x=final_df.loc[min_idx, '월_한글텍스트'], y=final_df.loc[min_idx, '거래금액(숫자)'], text="최저", showarrow=True, arrowhead=1, ax=0, ay=30, bgcolor="#3b82f6", font=dict(color="white", size=10))
                
                fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=350, hovermode='x unified', paper_bgcolor='white', plot_bgcolor='white', legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5))
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

    # ==================== TAB 3: 다중 단지 비교 평가 ====================
    with main_tab2:
        st.subheader("⚖️ 단지별 시세 흐름 다중 비교 분석")
        all_apts = sorted(df['단지선택명'].unique())
        selected_apts = st.multiselect("비교할 아파트 단지들을 선택하세요", all_apts, default=all_apts[:2] if len(all_apts) >= 2 else all_apts)
        
        if selected_apts:
            apt_pyung_mapping = {}
            st.markdown("#### 🔍 단지별 비교 평형 지정")
            cols = st.columns(min(len(selected_apts), 2)) 
            for idx, apt in enumerate(selected_apts):
                with cols[idx % 2]:
                    apt_df = df[df['단지선택명'] == apt]
                    available_pyungs = sorted(apt_df['평형'].unique())
                    chosen_pyung = st.selectbox(f"{apt.split()[1] if len(apt.split())>1 else apt}", available_pyungs, key=f"comp_pyung_{idx}")
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
                    fig_comp.add_trace(go.Scatter(x=label_data['월_날짜객체'], y=label_data['평균가'], mode='lines+markers', name=label, line=dict(width=2.5), connectgaps=True, hovertemplate='금액: %{y}만원'))
                fig_comp.update_layout(margin=dict(l=10, r=10, t=30, b=10), height=350, hovermode='x unified', paper_bgcolor='white', plot_bgcolor='white', legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
                st.plotly_chart(fig_comp, use_container_width=True)

                st.write("📊 매칭 종합 요약 지표 (좌우 스크롤👉)")
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
                        
                        built_str = apt_meta['준공']
                        age_text = ""
                        if built_str != "-" and "." in built_str:
                            try:
                                b_year = int(built_str.split(".")[0])
                                age_text = f" ({2026 - b_year}년차)"
                            except:
                                pass

                        summary_records.append({
                            "지역구": sample_row['자치구'],
                            "단지명": label.split()[1] if len(label.split())>1 else label,
                            "연식": f"{built_str}{age_text}",
                            "구조": apt_meta['구조'],
                            "최근가(만)": f"{recent:,}",
                            "최고가(만)": f"{mx:,}",
                            "최저가(만)": f"{mn:,}",
                            "고점대비 하락률": f"{dr:.1f}%"
                        })
                
                summary_df = pd.DataFrame(summary_records)
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
else:
    st.error("데이터를 가져오지 못했습니다.")