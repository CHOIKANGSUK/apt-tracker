import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="강석의 아파트 시세트래킹",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# [전역 디자인 패치] 밝은 테마 유지 및 드롭다운 목록('popover') 선명도 극대화 CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700;900&display=swap');

    html, body, [class*="st-"], .stApp, div[data-baseweb="popover"], ul[role="listbox"] {
        font-family: 'Noto Sans KR', -apple-system, sans-serif !important;
        -webkit-font-smoothing: antialiased !important;
    }
    
    /* 선택 박스 및 펼쳐지는 목록 글자 뿌연 현상 완전 제거 (선명한 검은색 + 두껍게) */
    div[data-baseweb="select"] > div { font-weight: 600 !important; color: #0f172a !important; }
    div[data-baseweb="popover"] li[role="option"],
    div[data-baseweb="popover"] li[role="option"] span,
    div[data-baseweb="popover"] li[role="option"] div {
        color: #111827 !important; 
        font-weight: 600 !important; 
        font-size: 15px !important;
        letter-spacing: -0.01em !important;
    }
    div[data-baseweb="popover"] li[role="option"]:hover { background-color: #f1f5f9 !important; }

    /* 멀티셀렉트 태그 스카이블루 정돈 */
    span[data-baseweb="tag"] {
        background-color: #e0f2fe !important; color: #0369a1 !important;
        border: 1px solid #7dd3fc !important; font-weight: 700 !important;
    }

    /* 실까 스타일 테이블 상세 CSS 디자인 */
    .highlight-table { width: 100%; border-collapse: collapse; font-size: 9.5pt; margin-bottom: 30px; }
    .highlight-table th { border-bottom: 2px solid #cbd5e1; border-top: 1px solid #cbd5e1; padding: 10px 5px; text-align: center; color: #64748b; font-weight: normal; }
    .highlight-table td { border-bottom: 1px solid #e2e8f0; padding: 12px 5px; text-align: center; color: #334155; }
    .price-col { font-weight: 800; font-size: 11pt; color: #0f172a; text-align: right !important; padding-right: 15px !important; }
    .badge-new-high { background-color: #ef4444; color: white; font-size: 7.5pt; padding: 2px 6px; border-radius: 3px; margin-left: 6px; vertical-align: middle; font-weight: bold; }
    .score-badge { background-color: #f8fafc; border: 1px solid #cbd5e1; padding: 2px 8px; border-radius: 10px; font-weight: bold; color: #1e3a8a; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def load_data():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        gc = gspread.authorize(creds)
        worksheet = gc.open("도권_아파트_실거래가_트래킹").get_worksheet(0)
        df = pd.DataFrame(worksheet.get_all_records())
        df['거래일자'] = pd.to_datetime(df['거래일자'])
        if '수집일자' in df.columns:
            df['수집일자'] = pd.to_datetime(df['수집일자'].astype(str).str.strip(), errors='coerce')
            df['수집일자'] = df['수집일자'].fillna(df['거래일자'])
        else:
            df['수집일자'] = df['거래일자']
        return df.sort_values(by='거래일자', ascending=True)
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

APT_VALUE_MAP = {
    "리센츠": {"입지점수": 98, "지형": "평지", "학군": "S(잠신초중고)", "교통": "2호선 초역세권"},
    "래미안대치팰리스": {"입지점수": 99, "지형": "평지", "학군": "S(대치동학원가)", "교통": "3호선/수인분당"},
    "마포프레스티지자이": {"입지점수": 92, "지형": "약경사", "학군": "A(염리초)", "교통": "2호선 이대역"},
    "경희궁자이 2단지": {"입지점수": 94, "지형": "평지", "학군": "A(독립문초)", "교통": "3호선 독립문역"},
    "북한산아이파크": {"입지점수": 78, "지형": "평지", "학군": "B(창동초)", "교통": "1/4호선 창동역"},
    "e편한세상서울대입구": {"입지점수": 82, "지형": "경사", "학군": "B(관악중)", "교통": "2호선 봉천역"},
    "롯데캐슬 SKY-L65": {"입지점수": 88, "지형": "평지", "학군": "B(성일중)", "교통": "GTX/1호선 청량리"},
    "동아에코빌": {"입지점수": 75, "지형": "경사", "학군": "C(상월곡초)", "교통": "6호선 상월곡역"},
    "신도림4차e-편한세상": {"입지점수": 86, "지형": "평지", "학군": "A(신도림중)", "교통": "1/2호선 신도림역"}
}

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

df = load_data()

if not df.empty:
    df['단지선택명'] = df['법정동'].astype(str).str.strip() + " " + df['아파트명'].astype(str).str.strip()
    df['자치구'] = df['법정동'].apply(get_gu_name)
    df['거래금액(숫자)'] = df['거래금액(만)'].astype(str).str.replace(',', '').astype(int)
    df['평형'] = df['전용면적(㎡)'].apply(lambda x: round(float(x)))
    df['월_날짜객체'] = df['거래일자'].dt.to_period('M').dt.to_timestamp()
    df['월_한글텍스트'] = df['거래일자'].dt.strftime('%y년 %m월')

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
        "마포구": "마포프레스티지자이", "용산구": "이촌동 한가람", "중구": "서울역센트럴자이", "성동구": "래미안옥수리버zen", "광진구": "광장힐스테이트", "강동구": "올림픽파크포레온",
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

    main_tab0, main_tab_new, main_tab_budget, main_tab1, main_tab2 = st.tabs([
        "🗺️ 시세트래킹 지도", "🎯 주간 하이라이트", "💰 가성비 비교", "📊 단지 분석", "⚖️ 비교 평가"
    ])

    # ==================== TAB 0: 시세트래킹 지도 ====================
    with main_tab0:
        all_available_months = sorted(df['월_날짜객체'].unique())
        month_options = [pd.to_datetime(m).strftime('%y년 %m월') for m in all_available_months]
        reversed_month_options = month_options[::-1]
        
        st.subheader("🗺️ 서울 랜드마크 시세트래킹 지도")
        st.caption("각 자치구 대장주의 국민평형(84㎡) 월간 평균 실거래 스냅샷입니다. (모바일 좌우 스와이프 가능)")
        
        chosen_month_str = st.selectbox("📅 분석 기준월 선택", options=reversed_month_options, index=0)
        chosen_month_date = all_available_months[month_options.index(chosen_month_str)]

        processed_prices = {}
        for gu_name, rows in collected_data.items():
            if len(rows) > 0:
                g_df = pd.DataFrame(rows)
                g_df_84 = g_df[g_df['평형'].between(83, 85)]
                g_df_month = g_df_84[g_df_84['월_날짜객체'] == chosen_month_date]
                if not g_df_month.empty:
                    processed_prices[gu_name] = {"price": f"{g_df_month['거래금액(숫자)'].mean()/10000:.1f}억", "name": display_names[gu_name], "active": True}
                else: processed_prices[gu_name] = {"price": "-", "name": display_names[gu_name], "active": False}
            else: processed_prices[gu_name] = {"price": "-", "name": "미수집", "active": False}

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

        html_map = "<div class='scroll-container' style='width: 100%; overflow-x: auto; white-space: nowrap; padding-bottom: 10px;'><div style='display: grid; grid-template-columns: repeat(8, minmax(100px, 1fr)); gap: 6px; background-color: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; min-width: 850px;'>"
        for row in map_grid:
            if row == ["한강_SPAN"]:
                html_map += "<div style='grid-column: 1 / -1; height: 38px; background: linear-gradient(90deg, #60a5fa, #2563eb, #60a5fa); border-radius: 6px; display: flex; align-items: center; justify-content: center; color: white; font-size: 10pt; font-weight: bold; letter-spacing: 15px;'>HAN RIVER</div>"
                continue
            for loc in row:
                if loc is None: html_map += "<div style='height: 90px;'></div>"
                else:
                    data = processed_prices.get(loc, {"price": "-", "name": "미수집", "active": False})
                    bg = "background-color: white; border: 1px solid #cbd5e1; box-shadow: 1px 2px 4px rgba(0,0,0,0.08);" if data['active'] else "background-color: #f1f5f9; border: 1px solid #e2e8f0; opacity: 0.5;"
                    text_c = "#1e3a8a" if data['active'] else "#94a3b8"
                    t_bg = "background-color: #facc15; color: #1e293b;" if data['active'] else "background-color: #e2e8f0; color: #94a3b8;"
                    html_map += f"""<div style='{bg} border-radius: 6px; height: 90px; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden; text-align: center; white-space: normal;'>
                                    <div style='{t_bg} font-size: 8.5pt; font-weight: bold; padding: 4px 0;'>{loc}</div>
                                    <div style='font-size: 7.5pt; color: #475569; padding: 2px 4px; line-height: 1.2; word-break: break-word; flex-grow: 1; display: flex; align-items: center; justify-content: center;'>{data['name']}</div>
                                    <div style='font-size: 13pt; font-weight: 800; color: {text_c}; padding-bottom: 4px;'>{data['price']}</div>
                                 </div>"""
        html_map += "</div></div>"
        st.markdown(html_map, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        landmark_df = df[df['is_landmark'] == True].copy()
        landmark_df_84 = landmark_df[landmark_df['평형'].between(83, 85)]
        if not landmark_df_84.empty:
            landmark_stats = landmark_df_84.groupby('월_날짜객체').agg(거래금액=('거래금액(숫자)', 'mean')).reset_index()
            fig_idx = go.Figure()
            fig_idx.add_trace(go.Scatter(x=landmark_stats['월_날짜객체'], y=landmark_stats['거래금액'], mode='lines+markers', line=dict(color='#3b82f6', width=4), marker=dict(size=8, color='white', line=dict(width=2, color='#3b82f6')), name="서울 대장주 84㎡ 평균"))
            fig_idx.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=300, paper_bgcolor='white', plot_bgcolor='white', hovermode='x unified')
            st.plotly_chart(fig_idx, use_container_width=True)

    # ==================== TAB 1: 주간 하이라이트 ====================
    with main_tab_new:
        st.markdown("<h2>🎯 서울 랜드마크 주간 실거래 하이라이트</h2>", unsafe_allow_html=True)
        unique_dates = sorted(df['수집일자'].dropna().dt.date.unique(), reverse=True)[:30]
        
        def format_korean_date(d):
            weekdays = ["월", "화", "수", "목", "금", "토", "일"]
            return f"🗓️ {d.month}.{d.day}({weekdays[d.weekday()]}) 공개분"

        date_options = {"🌟 최근 30일 통합 보기 (기본값)": "30days"}
        for d in unique_dates: date_options[format_korean_date(d)] = d
            
        chosen_date_str = st.selectbox("📅 스캔할 국토부 공개(수집) 일자 선택", list(date_options.keys()), index=0)
        target_val = date_options[chosen_date_str]
        
        if target_val == "30days":
            recent_df = df[df['수집일자'] >= (df['수집일자'].max() - timedelta(days=30))].copy()
        else:
            recent_df = df[df['수집일자'].dt.date == target_val].copy()

        if recent_df.empty: st.info("선택하신 기간 내에 새롭게 수집된 실거래 내역이 없습니다.")
        else:
            recent_df = recent_df.sort_values(by=['거래일자', '거래금액(숫자)'], ascending=[False, False])
            new_highs, trades_59, trades_84 = [], [], []
            
            for idx, row in recent_df.iterrows():
                apt_key, pyung_key, price, t_date = row['단지선택명'], row['평형'], row['거래금액(숫자)'], row['거래일자']
                past_df = df[(df['단지선택명'] == apt_key) & (df['평형'] == pyung_key) & (df['거래일자'] < t_date)]
                is_new_high, diff_str = False, ""
                
                if not past_df.empty:
                    prev_max = past_df['거래금액(숫자)'].max()
                    if price > prev_max:
                        is_new_high = True
                        diff = price - prev_max
                        eok, man = diff // 10000, diff % 10000
                        diff_str = f" <span style='color:#ef4444; font-size:8.5pt;'>(▲{eok}억 {man:,}만)</span>" if eok > 0 else f" <span style='color:#ef4444; font-size:8.5pt;'>(▲{man:,}만)</span>"
                else: is_new_high = True
                
                apt_display_name = apt_key.split()[1] if len(apt_key.split())>1 else apt_key
                trade_info = {"시군구": row['자치구'], "아파트명": apt_display_name, "면적": f"{pyung_key}㎡", "층": f"{row['층']}층", "가격": format_price(price), "is_new_high": is_new_high, "diff_str": diff_str, "date": t_date}
                
                if is_new_high: new_highs.append(trade_info)
                if 58 <= pyung_key <= 60: trades_59.append(trade_info)
                if 83 <= pyung_key <= 85: trades_84.append(trade_info)
                
            def make_highlight_table(data_list, title, title_color="#ef4444"):
                if not data_list: return f"<div style='text-align:center; color:#94a3b8; padding:12px;'>해당 세그먼트 거래가 없습니다.</div>"
                html = f"<div style='text-align:center; margin:15px 0;'><span style='font-weight:bold; color:{title_color};'>━━━ {title} ━━━</span></div><div class='scroll-container'><table class='highlight-table'><tr><th>#</th><th>시군구</th><th style='text-align:left;'>아파트명</th><th>면적</th><th>층</th><th>실거래일</th><th style='text-align:right;'>가격</th></tr>"""
                for i, item in enumerate(data_list[:15]):
                    badge = "<span class='badge-new-high'>신고가</span>" if item['is_new_high'] else ""
                    html += f"<tr><td>{i+1}</td><td>{item['시군구']}</td><td style='text-align:left; font-weight:bold;'>{item['아파트명']} {badge}{item['diff_str']}</td><td>{item['면적']}</td><td>{item['층']}</td><td>{item['date'].strftime('%m.%d')}</td><td class='price-col'>{item['가격']}</td></tr>"
                return html + "</table></div>"

            st.markdown(make_highlight_table(new_highs, "신고가 주요거래", "#ef4444"), unsafe_allow_html=True)
            st.markdown(make_highlight_table(trades_84, "84㎡ 주요거래", "#334155"), unsafe_allow_html=True)
            st.markdown(make_highlight_table(trades_59, "59㎡ 주요거래", "#334155"), unsafe_allow_html=True)

    # ==================== TAB 2: 예산별 가성비 비교 ====================
    with main_tab_budget:
        st.subheader("💰 내 예산에 맞는 최적의 대장주 찾기")
        budget_options = {"4억~6억": (40000, 60000), "6억~8억": (60000, 80000), "8억~10억": (80000, 100000), "10억~13억": (100000, 130000), "13억~16억": (130000, 160000), "16억~20억": (160000, 200000), "20억 이상": (200000, 999999)}
        col_b1, col_b2 = st.columns([1, 1])
        with col_b1: chosen_budget = st.selectbox("💵 가용 예산 범위 선택", list(budget_options.keys()), index=2)
        with col_b2: chosen_pyung_type = st.radio("🏠 평형 타입", ["전체", "59㎡(25평)", "84㎡(34평)"], horizontal=True)

        min_b, max_b = budget_options[chosen_budget]
        b_df = df[df['거래일자'] >= (datetime.now() - timedelta(days=90))].copy()
        if "59㎡" in chosen_pyung_type: b_df = b_df[b_df['평형'].between(58, 61)]
        elif "84㎡" in chosen_pyung_type: b_df = b_df[b_df['평형'].between(83, 85)]
        
        budget_rank = b_df.groupby(['자치구', '아파트명', '평형'])['거래금액(숫자)'].mean().reset_index()
        budget_rank = budget_rank[budget_rank['거래금액(숫자)'].between(min_b, max_b)]
        
        if budget_rank.empty: st.info("최근 3개월간 해당 예산대 조건의 데이터가 없습니다.")
        else:
            results = []
            for _, row in budget_rank.iterrows():
                info = next((v for k, v in APT_VALUE_MAP.items() if k in row['아파트명']), {"입지점수": 0, "지형": "-", "학군": "-", "교통": "-"})
                results.append({"지역": row['자치구'], "아파트명": row['아파트명'], "평형": f"{row['평형']}㎡", "평균 실거래": format_price(row['거래금액(숫자)']), "입지점수": info['입지점수'], "지형": info['지형'], "학군": info['학군'], "교통": info['교통'], "score": info['입지점수']})
            results_df = pd.DataFrame(results).sort_values(by='score', ascending=False)
            
            html = "<div class='scroll-container'><table class='highlight-table'><tr><th>랭킹</th><th>지역</th><th style='text-align:left;'>아파트명</th><th>평형</th><th>평균 실거래</th><th>입지점수</th><th>지형</th><th>학군</th></tr>"
            medals = ["🥇","🥈","🥉"]
            for i, res in enumerate(results_df.to_dict('records')):
                medal = medals[i] if i < 3 else str(i+1)
                html += f"<tr><td>{medal}</td><td>{res['지역']}</td><td style='text-align:left; font-weight:bold;'>{res['아파트명']} <br><span style='font-size:8pt; color:#94a3b8;'>{res['교통']}</span></td><td>{res['평형']}</td><td style='color:#ef4444; font-weight:bold;'>{res['평균 실거래']}</td><td><span class='score-badge'>{res['입지점수']}점</span></td><td>{res['지형']}</td><td>{res['학군']}</td></tr>"
            st.markdown(html + "</table></div>", unsafe_allow_html=True)

    # ==================== TAB 3: 단일 단지 시황 분석 (🔥 arrow_down 버그 차단) ====================
    with main_tab1:
        if 'selected_gu' not in st.session_state: st.session_state['selected_gu'] = '중랑구'
        
        st.markdown(f"<div style='font-size:1.15rem; font-weight:bold; color:#0f172a; margin-bottom:12px;'>📍 현재 분석 자치구 : <span style='color:#3b82f6;'>{st.session_state['selected_gu']}</span></div>", unsafe_allow_html=True)
        
        # expander를 제거하고 고정 격자형 버튼 스위치로 버그 완벽 차단
        seoul_gus = ["중랑구", "성북구", "동대문구", "중구", "마포구", "용산구", "성동구", "종로구", "도봉구", "강남구", "서초구", "송파구", "영등포구", "양천구", "구로구"]
        cols = st.columns(5)
        for idx, gu in enumerate(seoul_gus):
            btn_label = f"✅ {gu}" if gu == st.session_state['selected_gu'] else gu
            if cols[idx % 5].button(btn_label, key=f"gu_btn_{gu}", use_container_width=True):
                st.session_state['selected_gu'] = gu
                st.rerun()

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
                st.markdown(f"**정보:** 세대수 {info['세대수']} | 준공 {info['준공']} | 용적률 {info['용적률']} | **구조:** {info['구조']}")
                st.markdown("---")
                
                monthly_stats = final_df.groupby('월_날짜객체').agg(월텍스트=('월_한글텍스트', 'first'), 평균가=('거래금액(숫자)', 'mean'), 거래량=('거래금액(숫자)', 'count')).reset_index()
                max_idx, min_idx = final_df['거래금액(숫자)'].idxmax(), final_df['거래금액(숫자)'].idxmin()
                recent_p, max_p, min_p = final_df.iloc[-1]['거래금액(숫자)'], final_df.loc[max_idx, '거래금액(숫자)'], final_df.loc[min_idx, '거래금액(숫자)']
                
                card_cols = st.columns(4)
                card_cols[0].metric("최근 실거래가", f"{format_price(recent_p)}", final_df.iloc[-1]['거래일자'].strftime('%Y-%m-%d'), delta_color="off")
                card_cols[1].metric("역대 최고가", f"{format_price(max_p)}", final_df.loc[max_idx, '거래일자'].strftime('%Y-%m-%d'), delta_color="inverse")
                card_cols[2].metric("역대 최저가", f"{format_price(min_p)}", final_df.loc[min_idx, '거래일자'].strftime('%Y-%m-%d'))
                card_cols[3].metric("고점대비 변동률", f"{((recent_p - max_p) / max_p * 100):.1f}%", "최고가 대비 하락폭")
                
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                fig.add_trace(go.Bar(x=monthly_stats['월텍스트'], y=monthly_stats['거래량'], name='월 거래량', marker_color='rgba(200, 220, 240, 0.5)'), secondary_y=True)
                fig.add_trace(go.Scatter(x=monthly_stats['월텍스트'], y=monthly_stats['평균가'], mode='lines+markers', name='월 평균가', line=dict(color='#1e3a8a', width=3)), secondary_y=False)
                fig.update_layout(height=300, margin=dict(l=10, r=10, t=20, b=10), paper_bgcolor='white', plot_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)

                final_df['비고'] = ""
                final_df.loc[max_idx, '비고'] = "🔴 최고가"
                final_df.loc[min_idx, '비고'] = "🔵 최저가"
                display_df = final_df[['거래일자', '층', '거래금액(숫자)', '비고']].copy().sort_values(by='거래일자', ascending=False)
                display_df['거래일자'] = display_df['거래일자'].dt.strftime('%Y-%m-%d')
                st.dataframe(display_df, use_container_width=True, hide_index=True)
        else: st.warning("선택된 자치구에 수집된 데이터가 없습니다.")

    # ==================== TAB 4: 단지간 비교 평가 ====================
    with main_tab2:
        st.subheader("⚖️ 단지별 시세 흐름 다중 비교 분석")
        all_apts = sorted(df['단지선택명'].unique())
        selected_apts = st.multiselect("비교할 아파트 단지들을 선택하세요", all_apts, default=all_apts[:2] if len(all_apts) >= 2 else all_apts)
        
        if selected_apts:
            apt_pyung_mapping = {}
            cols = st.columns(min(len(selected_apts), 2)) 
            for idx, apt in enumerate(selected_apts):
                apt_df = df[df['단지선택명'] == apt]
                chosen_pyung = cols[idx % 2].selectbox(f" 평형 선택: {apt.split()[1] if len(apt.split())>1 else apt}", sorted(apt_df['평형'].unique()), key=f"comp_pyung_{idx}")
                apt_pyung_mapping[apt] = chosen_pyung
            
            matched_records = [df[(df['단지선택명'] == apt) & (df['평형'] == pyung)] for apt, pyung in apt_pyung_mapping.items()]
            if matched_records:
                comp_df = pd.concat(matched_records)
                comp_df['비교단지명'] = comp_df['단지선택명'] + " (" + comp_df['평형'].astype(str) + "㎡)"
                comp_stats = comp_df.groupby(['월_날짜객체', '비교단지명']).agg(평균가=('거래금액(숫자)', 'mean')).reset_index()
                
                fig_comp = go.Figure()
                for label in sorted(comp_df['비교단지명'].unique()):
                    label_data = comp_stats[comp_stats['비교단지명'] == label].sort_values('월_날짜객체')
                    fig_comp.add_trace(go.Scatter(x=label_data['월_날짜객체'], y=label_data['평균가'], mode='lines+markers', name=label))
                fig_comp.update_layout(margin=dict(l=10, r=10, t=20, b=10), height=320, paper_bgcolor='white', plot_bgcolor='white')
                st.plotly_chart(fig_comp, use_container_width=True)

                summary_records = []
                for label in sorted(comp_df['비교단지명'].unique()):
                    unit_df = comp_df[comp_df['비교단지명'] == label]
                    if not unit_df.empty:
                        sample_row = unit_df.iloc[0]
                        apt_meta = get_apt_info(sample_row['단지선택명'], sample_row['평형'])
                        mx, mn, recent = unit_df['거래금액(숫자)'].max(), unit_df['거래금액(숫자)'].min(), unit_df.iloc[-1]['거래금액(숫자)']
                        summary_records.append({"지역구": sample_row['자치구'], "단지명": label, "연식": apt_meta['준공'], "구조": apt_meta['구조'], "최근가": f"{recent:,}", "최고가": f"{mx:,}", "최저가": f"{mn:,}", "하락률": f"{((recent - mx) / mx * 100):.1f}%"})
                st.dataframe(pd.DataFrame(summary_records), use_container_width=True, hide_index=True)
else:
    st.error("데이터를 가져오지 못했습니다.")