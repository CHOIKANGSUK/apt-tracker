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
def load_data_v6_17():
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

# === 법정동-자치구 정밀 매핑 (공백 및 유령 문자 예방 포함) ===
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

def get_apt_info(apt_name, pyung=None):
    info = {"세대수": "-", "준공": "-", "용적률": "-", "구조": "-"}
    return info

df = load_data_v6_17()

if not df.empty:
    # 텍스트 비교 표준화 (모든 공백, 특수문자 제거 및 소문자 통일)
    df['단지선택명'] = df['법정동'] + " " + df['아파트명']
    df['법정동_클린'] = df['법정동'].astype(str).str.replace(' ', '').str.replace('-', '')
    df['아파트명_클린'] = df['아파트명'].astype(str).str.replace(' ', '').str.replace('-', '').str.lower()
    df['거래금액(숫자)'] = df['거래금액(만)'].astype(str).str.replace(',', '').astype(int)
    df['평형'] = df['전용면적(㎡)'].apply(lambda x: round(float(x)))
    df['월_날짜객체'] = df['거래일자'].dt.to_period('M').dt.to_timestamp()
    df['월_한글텍스트'] = df['거래일자'].dt.strftime('%y년 %m월')
    df['자치구'] = df['법정동'].apply(get_gu_name)

    max_prices = df.groupby(['단지선택명', '평형'])['거래금액(숫자)'].max().to_dict()

    # 데이터 매칭용 와일드카드 2중 토큰 키워드 (동네 키워드, 아파트 키워드)
    # 구글 시트에 띄어쓰기나 오차가 있어도 무조건 바인딩 성공하도록 설계
    match_rules = {
        "도봉구": ("창동", "북한산아이파크"),
        "강북구": ("미아", "북서울자이"),
        "노원구": ("중계", "청구3"),
        "성북구": ("길음", "래미안길음"),
        "은평구": ("녹번", "녹번역"),
        "서대문구": ("북아현", "e편한세상"),
        "종로구": ("홍파", "경희궁자이"),
        "동대문구": ("전농", "sky"),
        "중랑구": ("면목", "사가정센트럴"),
        "마포구": ("염리", "마포프레스티지"),
        "용산구": ("이촌", "한가람"),
        "중구": ("만리", "서울역센트럴"),
        "성동구": ("옥수", "래미안"),  # 성동구 긴급 해결책 (옥수동 래미안 포함시 무조건 수집)
        "광진구": ("광장", "광장힐스테이트"),
        "강동구": ("둔촌", "올림픽파크포레온"),
        "강서구": ("마곡", "마곡엠밸리7"),
        "양천구": ("신정", "목동힐스테이트"),
        "영등포구": ("당산", "당산센트럴"),
        "동작구": ("흑석", "아크로리버하임"),
        "서초구": ("반포", "아크로리버파크"),
        "강남구": ("대치", "래미안대치팰리스"),
        "송파구": ("잠실", "리센츠"),
        "구로구": ("신도림", "4차"),    # 구로구 긴급 해결책 (신도림동 4차 포함시 무조건 수집)
        "금천구": ("독산", "롯데캐슬골드파크3"),
        "관악구": ("봉천", "서울대입구")
    }

    display_names = {
        "도봉구": "북한산 아이파크", "강북구": "북서울자이폴라리스", "노원구": "중계 청구3차", "성북구": "래미안길음센터피스",
        "은평구": "녹번역e편한세상캐슬", "서대문구": "e편한세상신촌", "종로구": "경희궁자이 2단지", "동대문구": "롯데캐슬 SKY-L65", "중랑구": "사가정센트럴아이파크",
        "마포구": "마포프레스티지자이", "용산구": "이촌동 한가람", "중구": "서울역센트럴자이", "성동구": "래미안옥수리버젠", "광진구": "광장힐스테이트", "강동구": "올림픽파크포레온",
        "강서구": "마곡엠밸리7단지", "양천구": "목동힐스테이트", "영등포구": "당산센트럴아이파크", "동작구": "아크로리버하임", "서초구": "아크로리버파크", "강남구": "래미안대치팰리스", "송파구": "리센츠",
        "구로구": "신도림4차 e편한세상", "금천구": "롯데캐슬골드파크3차", "관악구": "e편한세상서울대입구"
    }

    landmark_match_keys = []
    current_prices = {}
    
    # 강력해진 와일드카드 매칭 루프 가동
    for gu_name, (dong_k, apt_k) in match_rules.items():
        cond = df['법정동_클린'].str.contains(dong_k) & df['아파트명_클린'].str.contains(apt_k)
        sub_data = df[cond]
        if not sub_data.empty:
            latest_m = sub_data['월_날짜객체'].max()
            price_mean = sub_data[sub_data['월_날짜객체'] == latest_m]['거래금액(숫자)'].mean()
            price_eok = price_mean / 10000 
            
            current_prices[gu_name] = {
                "price": f"{price_eok:.1f}억", 
                "name": display_names[gu_name], 
                "active": True
            }
            # 전역 지점 판단용 단지 리스트업 백업
            landmark_match_keys.extend(sub_data['단지선택명'].unique())

    df['is_landmark'] = df['단지선택명'].isin(landmark_match_keys)

    # 대시보드 메인 레이아웃 가동
    main_tab0, main_tab1, main_tab2 = st.tabs(["👑 서울 랜드마크 지도 & 지수", "📊 단지별 정밀 분석", "⚖️ 단지간 비교 평가"])

    # ==================== TAB 0: 요청 양식 100% 싱크로 고증 지도 ====================
    with main_tab0:
        latest_month_str = df['월_날짜객체'].max().strftime('%y년 %m월')
        
        head_c1, head_c2 = st.columns([8, 2])
        with head_c1:
            st.subheader("🗺️ 서울 25개 자치구 고증 시세판")
        with head_c2:
            st.markdown(f"<div style='text-align: right; padding-top: 15px; font-size: 11pt; font-weight: bold; color: #3b82f6;'>💡 {latest_month_str} 평균값</div>", unsafe_allow_html=True)
        
        st.caption("송부해주신 디자인 시안 도면(가로 8열 x 세로 6열)의 행렬 좌표 및 블루 한강 벨트를 완벽하게 이식한 화면입니다.")

        # [고증 패치] 강석님이 도려 붙여주신 랜드마크 사진.png 도면의 8열 그리드 좌표 배열 완벽 동기화
        map_grid = [
            [None, None, None, None, "강북구", "도봉구", None, None],
            [None, None, None, None, "성북구", "노원구", None, None],
            [None, "은평구", None, None, None, None, None, None],
            [None, None, "서대문구", "종로구", "동대문구", "중랑구", None, None],
            [None, None, "마포구", "용산구", "중구", "성동구", "광진구", None],
            ["한강_SPAN"], # 강서구와 양천구 사이를 부드럽게 뚫고 가로지르는 리얼 한강 통합 라인
            ["강서구", "양천구", "영등포구", "동작구", "서초구", "강남구", "송파구", "강동구"],
            [None, "구로구", "금천구", "관악구", None, None, None, None]
        ]

        # 가로 8열(repeat(8, 1fr)) 광역 격자판 렌더링 시작
        html_map = "<div style='display: grid; grid-template-columns: repeat(8, 1fr); gap: 6px; background-color: #f8fafc; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0;'>"
        
        for row in map_grid:
            if row == ["한강_SPAN"]:
                # 8열을 꽉 채워서 완벽하게 이어지는 강줄기 구현 (grid-column: 1 / -1)
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
                    
                    html_map += f"<div style='{bg} border-radius: 6px; height: 85px; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden; text-align: center;'>\
                                    <div style='{t_bg} font-size: 8.5pt; font-weight: bold; padding: 4px 0;'>{loc}</div>\
                                    <div style='font-size: 7.5pt; color: #475569; padding: 2px 4px; line-height: 1.15; word-break: keep-all; flex-grow: 1; display: flex; align-items: center; justify-content: center;'>{data['name']}</div>\
                                    <div style='font-size: 13pt; {text_weight} color: {text_c}; padding-bottom: 4px;'>{data['price']}</div>\
                                 </div>"
        
        html_map += "</div>"
        st.markdown(html_map, unsafe_allow_html=True)

        # 차트를 시세판 밑으로 전면 격리 조치 완료
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.subheader("📈 서울 랜드마크 종합 지수 추и")
        
        if landmark_match_keys:
            landmark_stats = df[df['is_landmark']].groupby('월_날짜객체').agg({'거래금액(숫자)': 'mean'}).reset_index()
            fig_idx = go.Figure()
            fig_idx.add_trace(go.Scatter(x=landmark_stats['월_날짜객체'], y=landmark_stats['거래금액(숫자)'], mode='lines+markers', line=dict(color='#3b82f6', width=4), marker=dict(size=8, color='white', line=dict(width=2, color='#3b82f6')), name="서울 대장주 평균"))
            fig_idx.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=400, paper_bgcolor='white', plot_bgcolor='white', hovermode='x unified')
            fig_idx.update_xaxes(type='date', tickformat="%y년 %m월", dtick="M3", showgrid=True, gridcolor='#f1f5f9')
            fig_idx.update_yaxes(showgrid=True, gridcolor='#f1f5f9')
            st.plotly_chart(fig_idx, use_container_width=True)
        else:
            st.info("차트 연산을 위한 기반 랜드마크 데이터셋을 파싱하지 못했습니다.")

    # ==================== TAB 1: 단일 단지 시황 분석 ====================
    with main_tab1:
        if 'selected_gu' not in st.session_state: st.session_state['selected_gu'] = '전체구'
        seoul_gus = ["전체구", "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구"]

        with st.expander(f"🗺️ 현재 선택된 지역: [ {st.session_state['selected_gu']} ] (터치하여 변경)", expanded=False):
            grid_cols = st.columns(4)
            for idx, gu in enumerate(seoul_gus):
                button_label = f"🌐 {gu}" if gu == "전체구" and gu == st.session_state['selected_gu'] else (f"📍 {gu}" if gu == st.session_state['selected_gu'] else gu)
                with grid_cols[idx % 4]:
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
                fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), hovermode='x unified', legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), paper_bgcolor='white', plot_bgcolor='white')
                st.plotly_chart(fig, use_container_width=True)

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
                    fig_comp.add_trace(go.Scatter(x=label_data['월_날짜객체'], y=label_data['평균가'], mode='lines+markers', name=label, line=dict(width=2.5), connectgaps=True, hovertemplate='금액: %{y}만원'))
                fig_comp.update_layout(margin=dict(l=10, r=10, t=30, b=10), hovermode='x unified', paper_bgcolor='white', plot_bgcolor='white')
                st.plotly_chart(fig_comp, use_container_width=True)
else:
    st.error("데이터를 가져오지 못했습니다.")