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
def load_data_v6_16():
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

def get_apt_info(apt_name, pyung=None):
    info = {"세대수": "-", "준공": "-", "용적률": "-", "구조": "-"}
    clean_name = str(apt_name).replace(" ", "")
    if "중화동" in clean_name and "한신" in clean_name:
        info.update({"세대수": "1,544세대", "준공": "1997.10", "용적률": "376%", "구조": "방2/화1"})
    return info

df = load_data_v6_16()

if not df.empty:
    # 매칭 누수 방지를 위한 강력한 대소문자/특수문자 제거 전처리
    df['단지선택명'] = df['법정동'] + " " + df['아파트명']
    df['단지선택명_공백제거'] = df['단지선택명'].astype(str).str.replace(' ', '').str.replace('-', '').str.lower()
    df['거래금액(숫자)'] = df['거래금액(만)'].astype(str).str.replace(',', '').astype(int)
    df['평형'] = df['전용면적(㎡)'].apply(lambda x: round(float(x)))
    df['월_날짜객체'] = df['거래일자'].dt.to_period('M').dt.to_timestamp()
    df['월_한글텍스트'] = df['거래일자'].dt.strftime('%y년 %m월')
    df['자치구'] = df['법정동'].apply(get_gu_name)

    max_prices = df.groupby(['단지선택명', '평형'])['거래금액(숫자)'].max().to_dict()

    # 초강력 와일드카드 토큰 매칭 사전 (리버zen, 하이픈 등 완벽 방어)
    search_keywords = {
        "도봉구": "북한산아이파크", "강북구": "북서울자이", "노원구": "청구3", "성북구": "래미안길음",
        "은평구": "녹번역", "서대문구": "e편한세상신촌", "종로구": "경희궁자이", "동대문구": "sky", "중랑구": "사가정센트럴",
        "마포구": "마포프레스티지", "용산구": "한가람", "중구": "서울역센트럴", "성동구": "옥수", "광진구": "광장힐스테이트", "강동구": "올림픽파크포레온",
        "강서구": "마곡엠밸리7", "양천구": "목동힐스테이트", "영등포구": "당산센트럴", "동작구": "아크로리버하임", "서초구": "아크로리버파크", "강남구": "래미안대치팰리스", "송파구": "리센츠",
        "구로구": "신도림4", "금천구": "롯데캐슬골드파크3", "관악구": "서울대입구"
    }

    display_names = {
        "도봉구": "북한산 아이파크", "강북구": "북서울자이폴라리스", "노원구": "중계 청구3차", "성북구": "래미안길음센터피스",
        "은평구": "녹번역e편한세상캐슬", "서대문구": "e편한세상신촌", "종로구": "경희궁자이 2단지", "동대문구": "롯데캐슬 SKY-L65", "중랑구": "사가정센트럴아이파크",
        "마포구": "마포프레스티지자이", "용산구": "이촌동 한가람", "중구": "서울역센트럴자이", "성동구": "래미안옥수리버젠", "광진구": "광장힐스테이트", "강동구": "올림픽파크포레온",
        "강서구": "마곡엠밸리7단지", "양천구": "목동힐스테이트", "영등포구": "당산센트럴아이파크", "동작구": "아크로리버하임", "서초구": "아크로리버파크", "강남구": "래미안대치팰리스", "송파구": "리센츠",
        "구로구": "신도림4차 e편한세상", "금천구": "롯데캐슬골드파크3차", "관악구": "e편한세상서울대입구"
    }

    df['is_landmark'] = df['단지선택명_공백제거'].apply(lambda x: any(k in x for k in search_keywords.values()))

    st.title("🏢 강석의 서울 랜드마크 시세 마스터 v6.16")

    main_tab0, main_tab1, main_tab2 = st.tabs(["👑 서울 랜드마크 지도 & 지수", "📊 단지별 정밀 분석", "⚖️ 단지간 비교 평가"])

    # ==================== TAB 0: 전면 와이드 지도 배치 개편 ====================
    with main_tab0:
        latest_month_str = df['월_날짜객체'].max().strftime('%y년 %m월')
        
        # 상단 타이틀 구성
        head_c1, head_c2 = st.columns([8, 2])
        with head_c1:
            st.subheader("🗺️ 서울 25개 자치구 고증 시세판")
        with head_c2:
            st.markdown(f"<div style='text-align: right; padding-top: 15px; font-size: 11pt; font-weight: bold; color: #3b82f6;'>💡 {latest_month_str} 평균값</div>", unsafe_allow_html=True)
        
        st.caption("제공해주신 바둑판 도면(가로 7칸)을 완벽 고증하여 유실되었던 북부 4개 구 및 성동/구로구를 완벽 복구한 마스터 맵입니다.")

        # [고증 패치] 가로 7열 격자 구조로 성북, 노원, 강북, 도봉 완벽 부활
        map_grid = [
            [None, None, None, None, "강북구", "도봉구", None],
            [None, None, None, None, "성북구", "노원구", None],
            [None, "은평구", None, None, None, None, None],
            [None, None, "서대문구", "종로구", "동대문구", "중랑구", None],
            [None, None, "마포구", "용산구", "중구", "성동구", "광진구"],
            ["한강_SPAN"], # 가로 7칸 전체를 관통하는 완벽한 이어진 강줄기
            ["강서구", None, None, None, None, None, "강동구"],
            [None, "양천구", "영등포구", "동작구", "서초구", "강남구", "송파구"],
            [None, "구로구", "금천구", "관악구", None, None, None]
        ]

        current_prices = {}
        for area_name, search_k in search_keywords.items():
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

        # 가로 7열(repeat(7, 1fr)) 반응형 그리드 선언
        html_map = "<div style='display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; background-color: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0;'>"
        
        for row in map_grid:
            if row == ["한강_SPAN"]:
                html_map += "<div style='grid-column: 1 / -1; height: 38px; background: linear-gradient(90deg, #60a5fa, #2563eb, #60a5fa); border-radius: 6px; display: flex; align-items: center; justify-content: center; color: white; font-size: 10pt; font-weight: bold; letter-spacing: 15px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);'>HAN RIVER</div>"
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
                    html_map += f"<div style='font-size: 7.5pt; color: #475569; padding: 2px 4px; line-height: 1.15; word-break: keep-all; flex-grow: 1; display: flex; align-items: center; justify-content: center;'>{data['name']}</div>"
                    html_map += f"<div style='font-size: 13pt; {text_weight} color: {text_c}; padding-bottom: 4px;'>{data['price']}</div>"
                    html_map += "</div>"
        
        html_map += "</div>"
        st.markdown(html_map, unsafe_allow_html=True)

        # [수정] 차트를 시세판 밑으로 배치하여 공간 확보
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.subheader("📈 서울 랜드마크 종합 지수 추이")
        landmark_df = df[df['is_landmark'] == True].copy()
        landmark_stats = landmark_df.groupby('월_날짜객체').agg({'거래금액(숫자)': 'mean'}).reset_index()
        
        fig_idx = go.Figure()
        fig_idx.add_trace(go.Scatter(x=landmark_stats['월_날짜객체'], y=landmark_stats['거래금액(숫자)'], mode='lines+markers', line=dict(color='#3b82f6', width=4), marker=dict(size=8, color='white', line=dict(width=2, color='#3b82f6')), name="서울 대장주 평균"))
        fig_idx.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=400, paper_bgcolor='white', plot_bgcolor='white', hovermode='x unified')
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
                st.subheader(f"📍 {selected_apt} ({selected_pyung}㎡)")
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
                        recent = unit_df.iloc[-1]['거래금액(숫자)']
                        mx = unit_df['거래금액(숫자)'].max()
                        mn = unit_df['거래금액(숫자)'].min()
                        dr = ((recent - mx) / mx) * 100
                        summary_records.append({
                            "지역구": sample_row['자치구'], "비교 대상 단지 (평형)": label, "최근거래가(만)": recent, "역대최고가(만)": mx, "역대최저가(만)": mn, "고점대비하락률": f"{dr:.1f}%"
                        })
                
                summary_df = pd.DataFrame(summary_records)
                styled_summary = summary_df.style.format({'최근거래가(만)': '{:,.0f}', '역대최고가(만)': '{:,.0f}', '역대최저가(만)': '{:,.0f}'}).set_properties(**{'text-align': 'center'})
                st.dataframe(styled_summary, use_container_width=True, hide_index=True)
else:
    st.error("데이터를 가져오지 못했습니다.")