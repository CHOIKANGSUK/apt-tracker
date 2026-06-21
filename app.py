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

# 전역 CSS (모바일 최적화 및 테이블 디자인)
st.markdown("""
<style>
    @media (max-width: 768px) {
        h1 { font-size: 1.5rem !important; }
        h2 { font-size: 1.2rem !important; }
        .stSelectbox label { font-size: 0.8rem !important; }
    }
    .highlight-table { width: 100%; border-collapse: collapse; font-size: 9.5pt; margin-bottom: 20px; }
    .highlight-table th { border-bottom: 2px solid #cbd5e1; padding: 10px; color: #64748b; font-weight: normal; }
    .highlight-table td { border-bottom: 1px solid #e2e8f0; padding: 12px 10px; text-align: center; }
    .score-badge { background-color: #f1f5f9; padding: 2px 8px; border-radius: 10px; font-weight: bold; color: #1e3a8a; }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=600)
def load_data_v6_34():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
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

# === [강석의 비밀 사전] 입지 평가 마스터 데이터 ===
# 실제 운영 시에는 이 내용을 더 풍성하게 채우시면 됩니다.
APT_VALUE_MAP = {
    "리센츠": {"입지점수": 98, "지형": "평지", "학군": "S(잠신초중고)", "교통": "2호선 초역세권"},
    "래미안대치팰리스": {"입지점수": 99, "지형": "평지", "학군": "S(대치동학원가)", "교통": "3호선/수인분당"},
    "마포프레스티지자이": {"입지점수": 92, "지형": "약경사", "학군": "A(염리초)", "교통": "2호선 이대역"},
    "경희궁자이 2단지": {"입지점수": 94, "지형": "평지", "학군": "A(독립문초)", "교통": "3호선 독립문역"},
    "북한산 아이파크": {"입지점수": 78, "지형": "평지", "학군": "B(창동초)", "교통": "1/4호선 창동역"},
    "e편한세상서울대입구": {"입지점수": 82, "지형": "경사", "학군": "B(관악중)", "교통": "2호선 봉천역"},
    "롯데캐슬 SKY-L65": {"입지점수": 88, "지형": "평지", "학군": "B(성일중)", "교통": "GTX/1호선 청량리"},
    "동아에코빌": {"입지점수": 75, "지형": "경사", "학군": "C(상월곡초)", "교통": "6호선 상월곡역"},
    "신도림4차 e-편한세상": {"입지점수": 86, "지형": "평지", "학군": "A(신도림중)", "교통": "1/2호선 신도림역"}
}

def get_gu_name(dong_name):
    dong = str(dong_name).strip().replace(" ", "")
    if any(k in dong for k in ['중화', '상봉', '면목', '신내']): return '중랑구'
    elif any(k in dong for k in ['상월곡', '하월곡', '길음', '장위', '석관', '돈암']): return '성북구'
    elif any(k in dong for k in ['만리', '회현', '명동', '신당']): return '중구'
    elif any(k in dong for k in ['염리', '아현', '공덕', '도화']): return '마포구'
    elif any(k in dong for k in ['대치', '압구정', '삼성', '개포']): return '강남구'
    elif any(k in dong for k in ['반포', '방배', '서초', '잠원']): return '서초구'
    elif any(k in dong for k in ['잠실', '신천', '문정', '가락']): return '송파구'
    elif any(k in dong for k in ['창동', '방학', '쌍문']): return '도봉구'
    elif any(k in dong for k in ['신도림', '구로', '고척']): return '구로구'
    return '기타/미분류'

def format_price(price_man):
    price = int(price_man)
    if price % 10000 == 0: return f"{price // 10000}억"
    else: return f"{price // 10000}억 {(price % 10000):,}만"

df = load_data_v6_34()

if not df.empty:
    df['단지선택명'] = df['법정동'].astype(str).str.strip() + " " + df['아파트명'].astype(str).str.strip()
    df['자치구'] = df['법정동'].apply(get_gu_name)
    df['거래금액(숫자)'] = df['거래금액(만)'].astype(str).str.replace(',', '').astype(int)
    df['평형'] = df['전용면적(㎡)'].apply(lambda x: round(float(x)))
    
    max_prices = df.groupby(['단지선택명', '평형'])['거래금액(숫자)'].max().to_dict()

    st.title("🏢 강석의 서울 랜드마크 시세 마스터 v6.34")

    # 탭 구성 (💰 예산별 가성비 비교 탭 추가)
    main_tab0, main_tab_new, main_tab_budget, main_tab1, main_tab2 = st.tabs([
        "👑 시세트래킹 지도", "🚨 주간 하이라이트", "💰 예산별 가성비 비교", "📊 단지별 분석", "⚖️ 단지간 비교"
    ])

    # [1] 시세 지도 / [2] 주간 하이라이트 코드는 기존 유지 (생략)
    # ... (기존 v6.33의 main_tab0, main_tab_new 코드 동일하게 배치)

    # ==================== [신규] TAB: 예산별 가성비 비교 ====================
    with main_tab_budget:
        st.subheader("💰 내 예산에 맞는 최적의 대장주 찾기")
        st.caption("최근 3개월간의 실거래가 평균액을 기준으로 예산대별 단지를 추천합니다.")
        
        # 예산대 선택 필터
        budget_options = {
            "4억~6억": (40000, 60000),
            "6억~8억": (60000, 80000),
            "8억~10억": (80000, 100000),
            "10억~13억": (100000, 130000),
            "13억~16억": (130000, 160000),
            "16억~20억": (160000, 200000),
            "20억 이상": (200000, 999999)
        }
        
        col_b1, col_b2 = st.columns([1, 1])
        with col_b1:
            chosen_budget = st.selectbox("💵 가용 예산 범위를 선택하세요", list(budget_options.keys()), index=2)
        with col_b2:
            chosen_pyung_type = st.radio("🏠 평형 타입", ["전체", "59㎡(25평)", "84㎡(34평)"], horizontal=True)

        min_b, max_b = budget_options[chosen_budget]
        
        # 최근 3개월 데이터 기반 필터링
        three_months_ago = datetime.now() - timedelta(days=90)
        b_df = df[df['거래일자'] >= three_months_ago].copy()
        
        # 평형 필터 적용
        if "59㎡" in chosen_pyung_type: b_df = b_df[b_df['평형'].between(58, 61)]
        elif "84㎡" in chosen_pyung_type: b_df = b_df[b_df['평형'].between(83, 85)]
        
        # 단지별 평균가 계산
        budget_rank = b_df.groupby(['자치구', '아파트명', '평형'])['거래금액(숫자)'].mean().reset_index()
        budget_rank = budget_rank[budget_rank['거래금액(숫자)'].between(min_b, max_b)]
        
        if budget_rank.empty:
            st.info(f"해당 가격대({chosen_budget})에 거래된 대장주 데이터가 최근 3개월간 없습니다.")
        else:
            # 입지 정보 합치기
            results = []
            for _, row in budget_rank.iterrows():
                apt_nm = row['아파트명']
                # 딕셔너리에서 입지 정보 검색 (없으면 기본값)
                info = next((v for k, v in APT_VALUE_MAP.items() if k in apt_nm), {"입지점수": 0, "지형": "-", "학군": "-", "교통": "-"})
                
                results.append({
                    "지역": row['자치구'],
                    "아파트명": apt_nm,
                    "평형": f"{row['평형']}㎡",
                    "평균 실거래": format_price(row['거래금액(숫자)']),
                    "입지점수": info['입지점수'],
                    "지형": info['지형'],
                    "학군": info['학군'],
                    "교통": info['교통'],
                    "score": info['입지점수']
                })
            
            # 입지 점수 높은 순으로 정렬
            results_df = pd.DataFrame(results).sort_values(by='score', ascending=False)
            
            # 실까 스타일 HTML 표 렌더링
            html = """<div class='scroll-container' style='overflow-x:auto;'><table class='highlight-table'>
            <tr><th>랭킹</th><th>지역</th><th style='text-align:left;'>아파트명</th><th>평형</th><th>평균 실거래</th><th>입지점수</th><th>지형</th><th>학군</th><th style='text-align:left;'>핵심교통</th></tr>"""
            
            for i, res in enumerate(results_df.to_dict('records')):
                medal = "🥇" if i==0 else ("🥈" if i==1 else ("🥉" if i==2 else i+1))
                html += f"""<tr>
                <td>{medal}</td>
                <td>{res['지역']}</td>
                <td style='text-align:left; font-weight:bold;'>{res['아파트명']}</td>
                <td>{res['평형']}</td>
                <td style='color:#ef4444; font-weight:bold;'>{res['평균 실거래']}</td>
                <td><span class='score-badge'>{res['입지점수']}점</span></td>
                <td>{res['지형']}</td>
                <td>{res['학군']}</td>
                <td style='text-align:left; font-size:8.5pt; color:#64748b;'>{res['교통']}</td>
                </tr>"""
            html += "</table></div>"
            st.markdown(html, unsafe_allow_html=True)
            st.caption("※ 입지점수는 강석 아파트 연구소의 자체 기준(교통+학군+환경)에 의해 산정되었습니다.")

    # [3] 단지별 분석 / [4] 단지간 비교 코드는 기존 유지 (생략)
    # ... (v6.33의 main_tab1, main_tab2 코드 배치)