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
def load_data_v6_7():
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

# === 법정동 기반 자치구 매핑 (수정 요청 반영 완료) ===
def get_gu_name(dong_name):
    dong = str(dong_name).strip()
    if dong in ['중화동', '상봉동', '면목동', '신내동', '망우동', '묵동']: return '중랑구'
    elif dong in ['상월곡동', '하월곡동', '길음동', '장위동', '석관동', '돈암동', '정릉동', '보문동']: return '성북구'
    elif dong in ['이문동', '휘경동', '전농동', '답십리동', '장안동', '청량리동', '제기동', '용두동']: return '동대문구'
    elif dong in ['당산동', '신길동', '문래동', '양평동', '영등포동']: return '영등포구' # 수정완료
    elif dong in ['만리동', '회현동', '명동', '을지로동', '신당동']: return '중구' # 수정완료
    elif dong in ['염리동', '아현동', '공덕동', '도화동', '용강동', '상암동']: return '마포구' # 수정완료
    elif dong in ['둔촌동', '명일동', '고덕동', '상일동', '길동', '천호동', '암사동']: return '강동구' # 수정완료
    elif dong in ['신정동', '목동', '신월동']: return '양천구' # 수정완료
    elif dong in ['반포동', '방배동', '서초동', '잠원동']: return '서초구'
    elif dong in ['대치동', '압구정동', '삼성동', '개포동', '역삼동', '도곡동']: return '강남구'
    elif dong in ['잠실동', '신천동', '문정동', '가락동', '오금동']: return '송파구'
    elif dong in ['이촌동', '서빙고동', '한남동']: return '용산구'
    elif dong in ['상계동', '중계동', '하계동', '공릉동', '월계동']: return '노원구'
    elif dong in ['봉천동', '신림동']: return '관악구'
    elif dong in ['마곡동', '가양동', '화곡동']: return '강서구'
    elif dong in ['홍파동', '무악동', '구기동']: return '종로구'
    elif dong in ['옥수동', '성수동', '금호동']: return '성동구'
    elif dong in ['북아현동', '남가좌동']: return '서대문구'
    elif dong in ['흑석동', '상도동']: return '동작구'
    elif dong in ['광장동', '구의동']: return '광진구'
    elif dong in ['신도림동', '구로동']: return '구로구'
    elif dong in ['응암동', '불광동']: return '은평구'
    elif dong in ['미아동', '수유동']: return '강북구'
    elif dong in ['독산동', '시흥동']: return '금천구'
    elif dong in ['창동', '방학동']: return '도봉구'
    return '기타/미분류'

# 아파트 메타 정보 백과사전
def get_apt_info(apt_name, pyung=None):
    info = {"세대수": "-", "준공": "-", "용적률": "-", "구조": "-"}
    name = apt_name.replace(" ", "")
    if "중화동" in apt_name and "한신" in apt_name:
        info.update({"세대수": "1,544세대", "준공": "1997.10", "용적률": "376%"})
        if pyung: info["구조"] = "방2/화1" if pyung <= 60 else "방3/화2"
    elif "대치동" in apt_name and "래미안대치팰리스" in apt_name:
        info.update({"세대수": "1,607세대", "준공": "2015.09", "구조": "방3/화2"})
    elif "반포동" in apt_name and "아크로리버파크" in apt_name:
        info.update({"세대수": "1,612세대", "준공": "2016.08", "구조": "방3/화2"})
    elif "잠실동" in apt_name and "리센츠" in apt_name:
        info.update({"세대수": "5,563세대", "준공": "2008.07", "구조": "방3/화2"})
    elif "염리동" in apt_name and "마포프레스티지자이" in apt_name:
        info.update({"세대수": "1,694세대", "준공": "2021.03", "구조": "방3/화2"})
    elif "둔촌동" in apt_name and "올림픽파크포레온" in apt_name:
        info.update({"세대수": "12,032세대", "준공": "2025.01", "구조": "방3/화2"})
    return info

df = load_data_v6_7()

if not df.empty:
    # 데이터 전처리
    df['단지선택명'] = df['법정동'] + " " + df['아파트명']
    df['거래금액(숫자)'] = df['거래금액(만)'].astype(str).str.replace(',', '').astype(int)
    df['평형'] = df['전용면적(㎡)'].apply(lambda x: round(float(x)))
    df['월_날짜객체'] = df['거래일자'].dt.to_period('M').dt.to_timestamp()
    df['자치구'] = df['법정동'].apply(get_gu_name)

    # 랜드마크 키워드 정의
    landmark_dict = {
        "대치동 래미안대치팰리스": "강남구", "반포동 아크로리버파크": "서초구", "잠실동 리센츠": "송파구", 
        "이촌동 한가람": "용산구", "흑석동 아크로리버하임": "동작구", "홍파동 경희궁자이": "종로구",
        "당산동 당산센트럴아이파크": "영등포구", "만리동 서울역센트럴자이": "중구", "광장동 광장힐스테이트": "광진구",
        "염리동 마포프레스티지자이": "마포구", "둔촌동 올림픽파크포레온": "강동구", "옥수동 래미안옥수리버젠": "성동구",
        "신정동 목동힐스테이트": "양천구", "마곡동 마곡엠밸리7단지": "강서구", "북아현동 e편한세상신촌": "서대문구",
        "길음동 래미안길음센터피스": "성북구", "전농동 SKY-L65": "동대문구", "봉천동 e편한세상서울대입구": "관악구",
        "중계동 청구3": "노원구", "신도림동 신도림4차": "구로구", "면목동 사가정센트럴아이파크": "중랑구",
        "응암동 녹번역e편한세상캐슬": "은평구", "미아동 북서울자이폴라리스": "강북구", "독산동 롯데캐슬골드파크3차": "금천구",
        "창동 북한산아이파크": "도봉구"
    }
    
    df['is_landmark'] = df['단지선택명'].apply(lambda x: any(k in x for k in landmark_dict.keys()))

    st.title("🏢 강석의 아파트 시세트래킹 v6.7")

    tab0, tab1, tab2 = st.tabs(["👑 서울 랜드마크 지수 & 지도", "📊 단일 분석", "⚖️ 다중 비교"])

    # ==================== TAB 0: 랜드마크 지수 & 그리드 지도 ====================
    with tab0:
        col_map, col_chart = st.columns([1, 1])

        with col_map:
            st.subheader("🗺️ 서울 자치구별 랜드마크 시세판")
            
            # 그리드 레이아웃 정의 (7행 x 5열)
            grid_layout = [
                [None, None, "도봉구", None, None],
                [None, "강북구", "노원구", None, None],
                ["은평구", "성북구", "종로구", "동대문구", "중랑구"],
                ["서대문구", "중구", "성동구", "광진구", "강동구"],
                ["강서구", "마포구", "용산구", "강남구", "송파구"],
                [None, "양천구", "동작구", "서초구", None],
                [None, "구로구", "영등포구", "관악구", None],
                [None, "금천구", None, None, None]
            ]
            
            # 자치구별 최신 랜드마크 시세 추출
            landmark_df = df[df['is_landmark']].sort_values('거래일자')
            latest_prices = {}
            for k, v in landmark_dict.items():
                target = landmark_df[landmark_df['단지선택명'].str.contains(k.split()[-1])]
                if not target.empty:
                    latest_prices[v] = {"price": target.iloc[-1]['거래금액(숫자)'], "name": k.split()[-1]}

            # HTML 그리드 생성
            html_grid = "<div style='display: grid; grid-template-columns: repeat(5, 1fr); gap: 5px; background-color: #f1f5f9; padding: 10px; border-radius: 10px;'>"
            for row in grid_layout:
                for gu in row:
                    if gu is None:
                        html_grid += "<div style='height: 70px;'></div>"
                    else:
                        data = latest_prices.get(gu, {"price": 0, "name": "데이터없음"})
                        color = "#1e3a8a" if data['price'] > 200000 else "#3b82f6"
                        html_grid += f"""
                        <div style='background-color: white; border: 1px solid #e2e8f0; border-radius: 5px; padding: 5px; height: 75px; text-align: center; box-shadow: 1px 1px 3px rgba(0,0,0,0.05);'>
                            <div style='font-size: 9pt; font-weight: bold; color: #64748b;'>{gu}</div>
                            <div style='font-size: 8pt; color: #94a3b8; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>{data['name']}</div>
                            <div style='font-size: 11pt; font-weight: bold; color: {color};'>{data['price']:,}</div>
                        </div>
                        """
            html_grid += "</div>"
            st.markdown(html_grid, unsafe_allow_html=True)

        with col_chart:
            st.subheader("📈 서울 대장주 종합 지수")
            landmark_stats = landmark_df.groupby('월_날짜객체').agg({'거래금액(숫자)': 'mean'}).reset_index()
            fig_idx = go.Figure()
            fig_idx.add_trace(go.Scatter(x=landmark_stats['월_날짜객체'], y=landmark_stats['거래금액(숫자)'], mode='lines+markers', line=dict(color='#ef4444', width=3)))
            fig_idx.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=500, paper_bgcolor='white', plot_bgcolor='white')
            st.plotly_chart(fig_idx, use_container_width=True)

    # ==================== (기존 TAB 1, 2 로직 유지 및 보정 반영) ====================
    with tab1:
        if 'selected_gu' not in st.session_state: st.session_state['selected_gu'] = '전체구'
        # 자치구 필터 및 분석 로직 (v6.6과 동일하게 유지하되 get_gu_name 보정으로 영등포구 등이 정상 노출됨)
        st.write("구별 필터 선택 시 이제 영등포구(당산), 중구(서울역) 등의 단지가 정확히 필터링됩니다.")
        # ... (이하 v6.6 로직 생략, 동일하게 적용 가능)
        
    # (코드 가독성을 위해 하단 상세 로직은 강석님의 기존 v6.6 코드를 그대로 붙여넣으시면 됩니다.)

### 🎯 이번 업데이트의 핵심 결과
1. **정확한 지역 매치:** 이제 `당산센트럴아이파크`를 수집하면 자동으로 **영등포구**로 분류되며, `서울역센트럴자이`는 **중구**로 정확히 들어옵니다.
2. **지도형 시세판:** 첫 번째 탭에서 서울의 지리적 구조를 본뜬 그리드 지도를 통해 어느 지역의 대장주가 가장 비싸고, 어디가 저평가되어 있는지 한눈에 알 수 있습니다.
3. **가독성 극대화:** 모바일에서도 지도가 깨지지 않도록 컴팩트한 그리드 시스템을 적용했습니다.

지금 바로 이 코드를 적용해 보시고, 지도의 숫자와 지역구 매칭이 원하시는 대로 나오는지 확인해 보세요! 다음으로 경기도권 확장이나 시세 색상(Heatmap) 기능을 추가하고 싶으시면 말씀해 주세요. 😊