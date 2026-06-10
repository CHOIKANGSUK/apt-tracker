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
def load_data_v6_3():
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

# 아파트 메타 정보
def get_apt_info(apt_name):
    if "중화동" in apt_name and "한신" in apt_name:
        return {"세대수": "1,544세대", "준공": "1997.10", "용적률": "376%"}
    elif "상월곡동" in apt_name and "동아에코빌" in apt_name:
        return {"세대수": "1,253세대", "준공": "2003.06", "용적률": "281%"}
    elif "이문동" in apt_name and "쌍용" in apt_name:
        return {"세대수": "1,318세대", "준공": "2000.11", "용적률": "343%"}
    elif "이문동" in apt_name and "현대" in apt_name:
        return {"세대수": "483세대", "준공": "2000.09", "용적률": "319%"}
    elif "상봉동" in apt_name and "더샵" in apt_name:
        return {"세대수": "497세대", "준공": "2013.11", "용적률": "599%"}
    else:
        return {"세대수": "- ", "준공": "-", "용적률": "-"}

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
    else: return '기타/미분류'

df = load_data_v6_3()

if not df.empty:
    # 데이터 기본 전처리
    df['단지선택명'] = df['법정동'] + " " + df['아파트명']
    df['거래금액(숫자)'] = df['거래금액(만)'].astype(str).str.replace(',', '').astype(int)
    df['평형'] = df['전용면적(㎡)'].apply(lambda x: round(float(x)))
    df['월_한글텍스트'] = df['거래일자'].dt.strftime('%y년 %m월')
    df['월_날짜객체'] = df['거래일자'].dt.to_period('M').dt.to_timestamp()
    df['자치구'] = df['법정동'].apply(get_gu_name)

    # 역대 최고가/최저가 계산용 전역 딕셔너리 구축 (브리핑 피드 추출용)
    max_prices = df.groupby(['단지선택명', '평형'])['거래금액(숫자)'].max().to_dict()

    st.title("🏢 강석의 아파트 시세트래킹 포털")
    st.caption("국토부 API 연동 실시간 대시보드 v6.3 (7일 시황 브리핑 뉴스피드 엔진 탑재)")

    # ==================== 상단 자치구 퀵 필터 시스템 ====================
    if 'selected_gu' not in st.session_state:
        st.session_state['selected_gu'] = '중랑구'

    seoul_gus = [
        "전체구", "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구", "노원구", "도봉구",
        "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구", "성북구", "송파구", "양천구", "영등포구",
        "용산구", "은평구", "종로구", "중구", "중랑구"
    ]

    with st.expander(f"🗺️ 현재 선택된 지역: [ {st.session_state['selected_gu']} ] (터치하여 변경)", expanded=False):
        st.markdown("<p style='font-size:11pt; color:gray; margin-bottom:5px;'>'전체구'를 누르시면 서울 전역의 아파트 단지를 조건 없이 자유롭게 조회 및 비교할 수 있습니다.</p>", unsafe_allow_html=True)
        
        grid_cols = st.columns(4)
        for idx, gu in enumerate(seoul_gus):
            button_label = f"🌐 {gu}" if gu == "전체구" and gu == st.session_state['selected_gu'] else (f"📍 {gu}" if gu == st.session_state['selected_gu'] else gu)
            
            with grid_cols[idx % 4]:
                if st.button(button_label, key=f"gu_btn_{gu}", use_container_width=True):
                    st.session_state['selected_gu'] = gu
                    st.rerun()

    # ==================== [아이디어 2] 최근 7일 시황 브리핑 피드 엔진 ====================
    st.markdown("### 🔔 실시간 관심 지역 시황 브리핑 센터")
    
    # 최근 7일 기준선 설정 (가장 최근 데이터 일자로부터 7일 전)
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
            
            # 단지 평형의 역대 최고가 호출
            max_p = max_prices.get((apt_key, pyung_key), price)
            drop_r = ((price - max_p) / max_p) * 100 if max_p > 0 else 0
            
            # 조건 1: 🔴 신고가 감지 (최고가와 같거나 큰 경우)
            if price >= max_p and max_p > 0:
                briefing_messages.append(f"🔴 **[{gu_belong}] 신고가 발생 ({date_str})** | {apt_key} {pyung_key}㎡형이 **{price:,}만원**에 역대 최고가로 거래되었습니다.")
            # 조건 2: 📉 급매/가격조정 감지 (최고가 대비 -15% 이하 하락)
            elif drop_r <= -15.0:
                briefing_messages.append(f"📉 **[{gu_belong}] 가격 조정 포착 ({date_str})** | {apt_key} {pyung_key}㎡형이 고점 대비 **{drop_r:.1f}%** 조정된 **{price:,}만원**에 거래되었습니다.")
            # 조건 3: 일반 최신 실거래 요약
            else:
                briefing_messages.append(f"📢 **[{gu_belong}] 신규 실거래 수집 ({date_str})** | {apt_key} {pyung_key}㎡형 {row['층']}층이 **{price:,}만원**에 거래 완료되었습니다.")
    else:
        briefing_messages.append("⚪ **최근 7일간 서울 관심 지역 내에 새로 접수된 실거래 내역이 없습니다.** 국토부 API에 데이터가 업데이트되면 실시간 피드가 활성화됩니다.")

    # 브리핑 메시지를 스타일리시한 뉴스 컴팩트 박스 형태로 출력 (최대 4개 노출하여 간결성 유지)
    briefing_html = "<div style='background-color:#f8fafc; border-left:5px solid #1e3a8a; padding:12px; border-radius:4px; margin-bottom:15px;'>"
    for msg in briefing_messages[:4]:
        briefing_html += f"<p style='margin: 0 0 6px 0; font-size:11pt; color:#334155;'>{msg}</p>"
    briefing_html += "</div>"
    st.markdown(briefing_html, unsafe_allow_html=True)

    # ----------------------------------------------------------------------------------

    if st.session_state['selected_gu'] == '전체구':
        gu_filtered_df = df.copy()
    else:
        gu_filtered_df = df[df['자치구'] == st.session_state['selected_gu']].copy()

    # 상단 탭 구성
    tab1, tab2 = st.tabs(["📊 단일 단지 시황 분석", "⚖️ 다중 단지 비교 평가"])
    
    # ==================== TAB 1: 단일 단지 시황 분석 ====================
    with tab1:
        st.sidebar.header("📍 단지 및 평형 선택")
        
        if not gu_filtered_df.empty:
            apt_list = sorted(gu_filtered_df['단지선택명'].unique())
            selected_apt = st.sidebar.selectbox("단지 선택", apt_list, key="single_apt")
            
            filtered_df = gu_filtered_df[gu_filtered_df['단지선택명'] == selected_apt].copy()
            pyung_list = sorted(filtered_df['평형'].unique())
            selected_pyung = st.sidebar.selectbox("평형 선택(㎡)", pyung_list, key="single_pyung")
            
            final_df = filtered_df[filtered_df['평형'] == selected_pyung].copy()
            
            if not final_df.empty:
                info = get_apt_info(selected_apt)
                st.subheader(f"📍 {selected_apt} ({selected_pyung}㎡)")
                st.markdown(f"**정보:** {info['세대수']} | {info['준공']} 준공 | 용적률 {info['용적률']}")
                st.markdown("---")
                
                monthly_stats = final_df.groupby('월_날짜객체').agg(
                    월텍스트=('월_한글텍스트', 'first'),
                    평균가=('거래금액(숫자)', 'mean'),
                    거래량=('거래금액(숫자)', 'count')
                ).reset_index()
                monthly_stats['평균가'] = monthly_stats['평균가'].round(0).astype(int)
                
                max_idx = final_df['거래금액(숫자)'].idxmax()
                min_idx = final_df['거래금액(숫자)'].idxmin()
                
                recent_price = final_df.iloc[-1]['거래금액(숫자)']
                max_price = final_df.loc[max_idx, '거래금액(숫자)']
                min_price = final_df.loc[min_idx, '거래금액(숫자)']
                drop_rate = ((recent_price - max_price) / max_price) * 100
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("최근 실거래가", f"{recent_price:,}만", f"{final_df.iloc[-1]['거래일자'].strftime('%Y-%m-%d')}")
                with col2:
                    st.metric("역대 최고가", f"{max_price:,}만", f"{final_df.loc[max_idx, '거래일자'].strftime('%Y-%m-%d')}")
                    
                col3, col4 = st.columns(2)
                with col3:
                    st.metric("고점 대비 하락률", f"{drop_rate:.1f}%")
                with col4:
                    st.metric("역대 최저가", f"{min_price:,}만", f"{final_df.loc[min_idx, '거래일자'].strftime('%Y-%m-%d')}")
                    
                st.markdown("---")
                
                st.write("📈 시세 추이 및 거래량")
                fig = make_subplots(specs=[[{"secondary_y": True}]])
                
                fig.add_trace(go.Bar(
                    x=monthly_stats['월텍스트'], y=monthly_stats['거래량'], 
                    name='월 거래량', marker_color='rgba(200, 220, 240, 0.6)'
                ), secondary_y=True)
                
                fig.add_trace(go.Scatter(
                    x=final_df['월_한글텍스트'], y=final_df['거래금액(숫자)'], 
                    mode='markers', name='개별 실거래',
                    marker=dict(size=7, color='rgba(135, 206, 250, 0.8)'),
                    hovertemplate='금액: %{y}만원'
                ), secondary_y=False)
                
                fig.add_trace(go.Scatter(
                    x=monthly_stats['월텍스트'], y=monthly_stats['평균가'], 
                    mode='lines+markers', name='월 평균가',
                    line=dict(color='#1e3a8a', width=3)
                ), secondary_y=False)
                
                fig.add_annotation(
                    x=final_df.loc[max_idx, '월_한글텍스트'], y=final_df.loc[max_idx, '거래금액(숫자)'],
                    text="최고", showarrow=True, arrowhead=1, ax=0, ay=-30,
                    bgcolor="#ef4444", font=dict(color="white", size=10)
                )
                fig.add_annotation(
                    x=final_df.loc[min_idx, '월_한글텍스트'], y=final_df.loc[min_idx, '거래금액(숫자)'],
                    text="최저", showarrow=True, arrowhead=1, ax=0, ay=30,
                    bgcolor="#3b82f6", font=dict(color="white", size=10)
                )
                
                fig.update_layout(
                    margin=dict(l=10, r=10, t=30, b=10),
                    hovermode='x unified',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    paper_bgcolor='white', plot_bgcolor='white'
                )
                fig.update_xaxes(categoryorder='category ascending', showgrid=True, gridcolor='#f1f5f9')
                fig.update_yaxes(title_text="거래금액(만)", secondary_y=False, showgrid=True, gridcolor='#f1f5f9')
                fig.update_yaxes(title_text="거래량(건)", secondary_y=True, showgrid=False)
                
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
                st.warning("선택한 평형의 거래 데이터가 존재하지 않습니다.")
        else:
            st.warning(f"선택하신 지역구에 축적된 데이터가 아직 없습니다.")

    # ==================== TAB 2: 다중 단지 비교 평가 ====================
    with tab2:
        st.subheader("⚖️ 단지별 시세 흐름 다중 비교 분석")
        st.markdown("비교할 단지들을 선택한 후, 각 단지별로 비교 대상 평형을 각각 지정하여 정밀하게 비교합니다.")
        
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
                
                comp_stats = comp_df.groupby(['월_날짜객체', '비교단지명']).agg(
                    평균가=('거래금액(숫자)', 'mean')
                ).reset_index()
                comp_stats['평균가'] = comp_stats['평균가'].round(0).astype(int)
                
                fig_comp = go.Figure()
                for label in sorted(comp_df['비교단지명'].unique()):
                    label_data = comp_stats[comp_stats['비교단지명'] == label].sort_values('월_날짜객체')
                    fig_comp.add_trace(go.Scatter(
                        x=label_data['월_날짜객체'], y=label_data['평균가'],
                        mode='lines+markers', name=label,
                        line=dict(width=2.5), connectgaps=True,
                        hovertemplate='일자: %{x|%y년 %m월}<br>금액: %{y}만원'
                    ))
                
                fig_comp.update_layout(
                    margin=dict(l=10, r=10, t=30, b=10),
                    hovermode='x unified',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                    paper_bgcolor='white', plot_bgcolor='white'
                )
                fig_comp.update_xaxes(type='date', tickformat="%y년 %m월", dtick="M1", ticklabelmode="period", showgrid=True, gridcolor='#f1f5f9')
                fig_comp.update_yaxes(title_text="월평균 거래금액(만)", showgrid=True, gridcolor='#f1f5f9')
                st.plotly_chart(fig_comp, use_container_width=True)
                
                st.write("📊 평형 매칭 종합 요약 지표")
                summary_records = []
                for label in sorted(comp_df['비교단지명'].unique()):
                    unit_df = comp_df[comp_df['비교단지명'] == label]
                    if not unit_df.empty:
                        recent = unit_df.iloc[-1]['거래금액(숫자)']
                        mx = unit_df['거래금액(숫자)'].max()
                        mn = unit_df['거래금액(숫자)'].min()
                        dr = ((recent - mx) / mx) * 100
                        summary_records.append({
                            "비교 대상 단지 (평형)": label, "최근거래가(만)": recent, "역대최고가(만)": mx, "역대최저가(만)": mn, "고점대비하락률": f"{dr:.1f}%"
                        })
                
                summary_df = pd.DataFrame(summary_records)
                styled_summary = summary_df.style.format({
                    '최근거래가(만)': '{:,.0f}', '역대최고가(만)': '{:,.0f}', '역대최저가(만)': '{:,.0f}'
                }).set_properties(**{'text-align': 'center'})
                st.dataframe(styled_summary, use_container_width=True, hide_index=True)
        else:
            st.info("비교 분석을 진행할 아파트 단지를 1개 이상 선택해 주세요.")
else:
    st.error("데이터를 가져오지 못했습니다.")