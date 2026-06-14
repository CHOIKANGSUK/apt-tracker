import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta

# 1. 페이지 기본 설정 (모바일 대응 wide 유지)
st.set_page_config(
    page_title="강석의 아파트 시세트래킹",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 구글 시트 데이터 로드
@st.cache_data(ttl=600)
def load_data_v6_6():
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
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# === 아파트 메타 정보 및 구조 백과사전 사전 등록 완료 ===
def get_apt_info(apt_name, pyung=None):
    info = {"세대수": "- ", "준공": "-", "용적률": "-", "구조": "-"}
    
    # 랜드마크 및 기존 관심단지 통합 메타 DB
    if "중화동" in apt_name and "한신" in apt_name:
        info.update({"세대수": "1,544세대", "준공": "1997.10 (29년차)", "용적률": "376%"})
        if pyung: info["구조"] = "방2/화1" if pyung <= 60 else "방3/화2"
    elif "상월곡동" in apt_name and "동아에코빌" in apt_name:
        info.update({"세대수": "1,253세대", "준공": "2003.06 (23년차)", "용적률": "281%"})
        if pyung: info["구조"] = "방3/화1" if pyung <= 60 else "방3/화2"
    elif "이문동" in apt_name and "쌍용" in apt_name:
        info.update({"세대수": "1,318세대", "준공": "2000.11 (26년차)", "용적률": "343%"})
        if pyung: info["구조"] = "방3/화1" if pyung <= 60 else "방3/화2"
    elif "이문동" in apt_name and "현대" in apt_name:
        info.update({"세대수": "483세대", "준공": "2000.09 (26년차)", "용적률": "319%"})
        if pyung: info["구조"] = "방2/화1" if pyung <= 60 else "방3/화2"
    elif "상봉동" in apt_name and "더샵" in apt_name:
        info.update({"세대수": "497세대", "준공": "2013.11 (13년차)", "용적률": "599%"})
        if pyung: info["구조"] = "방3/화2" if pyung >= 84 else "방2/화1"
    elif "대치동" in apt_name and "래미안대치팰리스" in apt_name:
        info.update({"세대수": "1,607세대", "준공": "2015.09 (11년차)", "용적률": "259%", "구조": "방3/화2"})
    elif "반포동" in apt_name and "아크로리버파크" in apt_name:
        info.update({"세대수": "1,612세대", "준공": "2016.08 (10년차)", "용적률": "299%", "구조": "방3/화2"})
    elif "잠실동" in apt_name and "리센츠" in apt_name:
        info.update({"세대수": "5,563세대", "준공": "2008.07 (18년차)", "용적률": "275%", "구조": "방3/화2"})
    elif "이촌동" in apt_name and "한가람" in apt_name:
        info.update({"세대수": "2,036세대", "준공": "1998.09 (28년차)", "용적률": "358%", "구조": "방3/화2"})
    elif "흑석동" in apt_name and "아크로리버하임" in apt_name:
        info.update({"세대수": "1,073세대", "준공": "2019.05 (7년차)", "용적률": "205%", "구조": "방3/화2"})
    elif "홍파동" in apt_name and "경희궁자이" in apt_name:
        info.update({"세대수": "1,148세대", "준공": "2017.02 (9년차)", "용적률": "252%", "구조": "방3/화2"})
    elif "당산동" in apt_name and "당산센트럴아이파크" in apt_name:
        info.update({"세대수": "802세대", "준공": "2020.05 (6년차)", "용적률": "299%", "구조": "방3/화2"})
    elif "만리동" in apt_name and "서울역센트럴자이" in apt_name:
        info.update({"세대수": "1,341세대", "준공": "2017.08 (9년차)", "용적률": "243%", "구조": "방3/화2"})
    elif "광장동" in apt_name and "광장힐스테이트" in apt_name:
        info.update({"세대수": "453세대", "준공": "2012.03 (14년차)", "용적률": "228%", "구조": "방3/화2"})
    elif "염리동" in apt_name and "마포프레스티지자이" in apt_name:
        info.update({"세대수": "1,694세대", "준공": "2021.03 (5년차)", "용적률": "250%", "구조": "방3/화2"})
    elif "둔촌동" in apt_name and "올림픽파크포레온" in apt_name:
        info.update({"세대수": "12,032세대", "준공": "2025.01 (1년차)", "용적률": "273%", "구조": "방3/화2"})
    elif "옥수동" in apt_name and "래미안옥수리버젠" in apt_name:
        info.update({"세대수": "1,511세대", "준공": "2012.12 (14년차)", "용적률": "246%", "구조": "방3/화2"})
    elif "신정동" in apt_name and "목동힐스테이트" in apt_name:
        info.update({"세대수": "1,081세대", "준공": "2016.05 (10년차)", "용적률": "241%", "구조": "방3/화2"})
    elif "마곡동" in apt_name and "마곡엠밸리7단지" in apt_name:
        info.update({"세대수": "1,004세대", "준공": "2014.05 (12년차)", "용적률": "221%", "구조": "방3/화2"})
    elif "북아현동" in apt_name and "e편한세상신촌" in apt_name:
        info.update({"세대수": "1,910세대", "준공": "2018.05 (8년차)", "용적률": "271%", "구조": "방3/화2"})
    elif "길음동" in apt_name and "래미안길음센터피스" in apt_name:
        info.update({"세대수": "2,352세대", "준공": "2019.02 (7년차)", "용적률": "272%", "구조": "방3/화2"})
    elif "전농동" in apt_name and "SKY-L65" in apt_name:
        info.update({"세대수": "1,425세대", "준공": "2023.07 (3년차)", "용적률": "999%", "구조": "방3/화2"})
    elif "봉천동" in apt_name and "e편한세상서울대입구" in apt_name:
        info.update({"세대수": "1,531세대", "준공": "2019.06 (7년차)", "용적률": "237%", "구조": "방3/화2"})
    elif "중계동" in apt_name and "청구3" in apt_name:
        info.update({"세대수": "780세대", "준공": "1996.03 (30년차)", "용적률": "242%", "구조": "방3/화2"})
    elif "신도림동" in apt_name and "신도림4차" in apt_name:
        info.update({"세대수": "853세대", "준공": "2003.05 (23년차)", "용적률": "299%", "구조": "방3/화2"})
    elif "면목동" in apt_name and "사가정센트럴아이파크" in apt_name:
        info.update({"세대수": "1,505세대", "준공": "2020.07 (6년차)", "용적률": "299%", "구조": "방3/화2"})
    elif "응암동" in apt_name and "녹번역e편한세상캐슬" in apt_name:
        info.update({"세대수": "2,569세대", "준공": "2020.05 (6년차)", "용적률": "242%", "구조": "방3/화2"})
    elif "미아동" in apt_name and "북서울자이폴라리스" in apt_name:
        info.update({"세대수": "1,045세대", "준공": "2024.08 (2년차)", "용적률": "240%", "구조": "방3/화2"})
    elif "독산동" in apt_name and "롯데캐슬골드파크3차" in apt_name:
        info.update({"세대수": "1,236세대", "준공": "2018.10 (8년차)", "용적률": "399%", "구조": "방3/화2"})
    elif "창동" in apt_name and "북한산아이파크" in apt_name:
        info.update({"세대수": "2,061세대", "준공": "2004.07 (22년차)", "용적률": "247%", "구조": "방3/화2"})
        
    return info

# 법정동 기반 자치구 자동 매핑 사전
def get_gu_name(dong_name):
    if dong_name in ['중화동', '상봉동', '면목동', '신내동', '망우동', '묵동']: return '중랑구'
    elif dong_name in ['상월곡동', '하월곡동', '길음동', '장위동', '석관동', '돈암동', '정릉동', '보문동']: return '성북구'
    elif dong_name in ['이문동', '휘경동', '전농동', '답십리동', '장안동', '청량리동', '제기동', '용두동']: return '동대문구'
    elif dong_name in ['반포동', '방배동', '서초동', '잠원동']: return '서초구'
    elif dong_name in ['대치동', '압구정동', '삼성동', '개포동', '역삼동', '도곡동']: return '강남구'
    elif dong_name in ['잠실동', '신천동', '문정동', '가락동', '오금동']: return '송파구'
    elif dong_name in ['명일동', '고덕동', '상일동', '길동', '천호동', '암사동']: return '강동구'
    elif dong_name in ['상계동', '중계동', '하계동', '공릉동', '월계동']: return '노원구'
    elif dong_name in ['아현동', '공덕동', '도화동', '용강동', '상암동']: return '마포구'
    elif dong_name in ['여의도동', '당산동', '신길동', '문래동']: return '영등포구'
    elif dong_name in ['한남동', '이촌동', '이태원동']: return '용산구'
    elif dong_name in ['성수동', '옥수동', '금호동', '행당동']: return '성동구'
    elif dong_name in ['홍파동', '무악동']: return '종로구'
    elif dong_name in ['만리동', '회현동']: return '중구'
    elif dong_name in ['흑석동']: return '동작구'
    elif dong_name in ['광장동']: return '광진구'
    elif dong_name in ['마곡동']: return '강서구'
    elif dong_name in ['북아현동']: return '서대문구'
    elif dong_name in ['봉천동']: return '관악구'
    elif dong_name in ['신도림동']: return '구로구'
    elif dong_name in ['응암동']: return '은평구'
    elif dong_name in ['미아동']: return '강북구'
    elif dong_name in ['독산동']: return '금천구'
    elif dong_name in ['창동']: return '도봉구'
    else: return '기타/미분류'

df = load_data_v6_6()

if not df.empty:
    # 데이터 전처리
    df['단지선택명'] = df['법정동'] + " " + df['아파트명']
    df['거래금액(숫자)'] = df['거래금액(만)'].astype(str).str.replace(',', '').astype(int)
    df['평형'] = df['전용면적(㎡)'].apply(lambda x: round(float(x)))
    df['월_한글텍스트'] = df['거래일자'].dt.strftime('%y년 %m월')
    df['월_날짜객체'] = df['거래일자'].dt.to_period('M').dt.to_timestamp()
    df['자치구'] = df['법정동'].apply(get_gu_name)

    max_prices = df.groupby(['단지선택명', '평형'])['거래금액(숫자)'].max().to_dict()

    st.title("🏢 강석의 아파트 시세트래킹 포털")
    st.caption("국토부 API 연동 실시간 대시보드 v6.6 (서울 25개구 랜드마크 마스터 지수 시스템 가동)")

    # 랜드마크 목록 정의
    landmark_keywords = [
        "래미안대치팰리스", "아크로리버파크", "리센츠", "한가람", "아크로리버하임", "경희궁자이", 
        "당산센트럴아이파크", "서울역센트럴자이", "광장힐스테이트", "마포프레스티지자이", "올림픽파크포레온", 
        "래미안옥수리버젠", "목동힐스테이트", "마곡엠밸리7단지", "e편한세상신촌", "래미안길음센터피스", 
        "SKY-L65", "e편한세상서울대입구", "청구3", "신도림4차", "사가정센트럴아이파크", 
        "녹번역e편한세상캐슬", "북서울자이폴라리스", "롯데캐슬골드파크3차", "북한산아이파크"
    ]
    df['is_landmark'] = df['아파트명'].apply(lambda x: any(lk.lower() in x.lower() for lk in landmark_keywords))

    # 최상단 메인 탭 마스터 구조 재설계
    main_tab0, main_tab1, main_tab2 = st.tabs(["👑 서울 랜드마크 시장 지수", "📊 단일 단지 시황 분석", "⚖️ 다중 단지 비교 평가"])

    # ==================== [신규] TAB 0: 서울 랜드마크 시장 지수 ====================
    with main_tab0:
        st.subheader("📊 서울 25개 자치구 대장 아파트 종합 시세 트렌드")
        st.markdown("2025년 1월부터 현재까지 수집된 각 구별 랜드마크 단지들의 평균 거래가격 추이를 분석하여 거시적 흐름을 도출합니다.")
        
        landmark_df = df[df['is_landmark'] == True].copy()
        
        if not landmark_df.empty:
            # 월별 랜드마크 종합 지수 연산
            landmark_stats = landmark_df.groupby('월_날짜객체').agg(
                평균지수가=('거래금액(숫자)', 'mean'),
                총거래량=('거래금액(숫자)', 'count')
            ).reset_index()
            landmark_stats['평균지수가'] = landmark_stats['평균지수가'].round(0).astype(int)
            landmark_stats = landmark_stats.sort_values('월_날짜객체')
            
            # 거시 지수 차트 시각화
            fig_index = make_subplots(specs=[[{"secondary_y": True}]])
            fig_index.add_trace(go.Bar(
                x=landmark_stats['월_날짜객체'], y=landmark_stats['총거래량'],
                name='대장주 총 거래량(건)', marker_color='rgba(30, 58, 138, 0.15)'
            ), secondary_y=True)
            
            fig_index.add_trace(go.Scatter(
                x=landmark_stats['월_날짜객체'], y=landmark_stats['평균지수가'],
                mode='lines+markers', name='서울 대장주 평균가(만)',
                line=dict(color='#ef4444', width=3.5),
                connectgaps=True
            ), secondary_y=False)
            
            fig_index.update_layout(
                margin=dict(l=10, r=10, t=20, b=10), hovermode='x unified',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                paper_bgcolor='white', plot_bgcolor='white'
            )
            fig_index.update_xaxes(type='date', tickformat="%y년 %m월", dtick="M2", showgrid=True, gridcolor='#f1f5f9')
            fig_index.update_yaxes(title_text="종합 평균 가격(만)", secondary_y=False, showgrid=True, gridcolor='#f1f5f9')
            fig_index.update_yaxes(title_text="총 거래량(건)", secondary_y=True, showgrid=False)
            
            st.plotly_chart(fig_index, use_container_width=True)
            
            # 대장 아파트 25개 구 정렬 현황판
            st.write("📋 25개 자치구 대장주 핵심 요약 브리핑")
            land_summary = []
            for lk in landmark_keywords:
                sub_df = landmark_df[landmark_df['아파트명'].str.contains(lk, case=False, na=False)]
                if not sub_df.empty:
                    last_row = sub_df.iloc[-1]
                    meta = get_apt_info(last_row['단지선택명'], last_row['평형'])
                    land_summary.append({
                        "지역구": last_row['자치구'], "랜드마크 단지명": last_row['단지선택명'], "연식": meta['준공'],
                        "최근 거래가(만)": sub_df.iloc[-1]['거래금액(숫자)'], "역대 최고가(만)": sub_df['거래금액(숫자)'].max()
                    })
            
            land_summary_df = pd.DataFrame(land_summary).sort_values(by="지역구")
            styled_land = land_summary_df.style.format({
                '최근 거래가(만)': '{:,.0f}', '역대 최고가(만)': '{:,.0f}'
            }).set_properties(**{'text-align': 'center'})
            st.dataframe(styled_land, use_container_width=True, hide_index=True)
        else:
            st.info("랜드마크 축적 데이터 분석 데이터가 부족합니다.")

    # ==================== TAB 1: 단일 단지 시황 분석 ====================
    with main_tab1:
        if 'selected_gu' not in st.session_state: st.session_state['selected_gu'] = '중랑구'
        seoul_gus = ["전체구", "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"]

        with st.expander(f"🗺️ 현재 선택된 지역: [ {st.session_state['selected_gu']} ] (터치하여 변경)", expanded=False):
            grid_cols = st.columns(4)
            for idx, gu in enumerate(seoul_gus):
                button_label = f"🌐 {gu}" if gu == "전체구" and gu == st.session_state['selected_gu'] else (f"📍 {gu}" if gu == st.session_state['selected_gu'] else gu)
                with grid_cols[idx % 4]:
                    if st.button(button_label, key=f"gu_btn_{gu}", use_container_width=True):
                        st.session_state['selected_gu'] = gu
                        st.rerun()

        # 브리핑 피드 센터
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

        briefing_html = "<div style='background-color:#f8fafc; border-left:5px solid #1e3a8a; padding:12px; border-radius:4px; margin-bottom:15px;'>"
        for msg in briefing_messages[:4]: briefing_html += f"<p style='margin: 0 0 6px 0; font-size:11pt; color:#334155;'>{msg}</p>"
        briefing_html += "</div>"
        st.markdown(briefing_html, unsafe_allow_html=True)

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
                fig.update_xaxes(categoryorder='category ascending')
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
                fig_comp.update_xaxes(type='date', tickformat="%y년 %m월", dtick="M2", showgrid=True, gridcolor='#f1f5f9')
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