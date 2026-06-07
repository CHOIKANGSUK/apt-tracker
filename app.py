import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# 1. 페이지 기본 설정 (모바일 대응 wide 유지)
st.set_page_config(
    page_title="강석의 아파트 시세트래킹",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 구글 시트 데이터 로드
@st.cache_data(ttl=600)
def load_data_final():
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

# 아파트 정보
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

df = load_data_final()

if not df.empty:
    st.title("🏢 강석의 아파트 시세트래킹")
    st.caption("국토부 API 연동 실시간 대시보드 (디테일 분석 + 모바일 최적화 적용)")
    
    # 사이드바
    st.sidebar.header("📍 단지 및 평형 선택")
    df['단지선택명'] = df['법정동'] + " " + df['아파트명']
    apt_list = sorted(df['단지선택명'].unique())
    selected_apt = st.sidebar.selectbox("단지 선택", apt_list)
    
    filtered_df = df[df['단지선택명'] == selected_apt].copy()
    filtered_df['평형'] = filtered_df['전용면적(㎡)'].apply(lambda x: round(float(x)))
    pyung_list = sorted(filtered_df['평형'].unique())
    selected_pyung = st.sidebar.selectbox("평형 선택(㎡)", pyung_list)
    
    final_df = filtered_df[filtered_df['평형'] == selected_pyung].copy()
    
    if not final_df.empty:
        info = get_apt_info(selected_apt)
        st.subheader(f"📍 {selected_apt} ({selected_pyung}㎡)")
        st.markdown(f"**정보:** {info['세대수']} | {info['준공']} 준공 | 용적률 {info['용적률']}")
        st.markdown("---")
        
        final_df['거래금액(숫자)'] = final_df['거래금액(만)'].astype(str).str.replace(',', '').astype(int)
        
        # === 데이터 전처리 (월평균, 거래량, 최고/최저점 찾기) ===
        final_df['월'] = final_df['거래일자'].dt.strftime('%y년 %m월') # X축 한글 년월
        final_df['월별_정렬기준'] = final_df['거래일자'].dt.to_period('M')
        
        # 월별 통계 추출 (평균가, 거래량)
        monthly_stats = final_df.groupby('월별_정렬기준').agg(
            월=('월', 'first'),
            평균가=('거래금액(숫자)', 'mean'),
            거래량=('거래금액(숫자)', 'count')
        ).reset_index()
        monthly_stats['평균가'] = monthly_stats['평균가'].round(0).astype(int)
        
        # 최고/최저가 식별
        max_idx = final_df['거래금액(숫자)'].idxmax()
        min_idx = final_df['거래금액(숫자)'].idxmin()
        
        recent_price = final_df.iloc[-1]['거래금액(숫자)']
        max_price = final_df.loc[max_idx, '거래금액(숫자)']
        min_price = final_df.loc[min_idx, '거래금액(숫자)']
        drop_rate = ((recent_price - max_price) / max_price) * 100
        
        # 상단 핵심 지표 모바일 2열 배치
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
        
        # === 1. 시세 추이 그래프 복구 (평균선 + 개별점 + 거래량 + 최고/최저 표시) ===
        st.write("📈 시세 추이 및 거래량")
        
        # 이중 Y축 그래프 생성
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # 거래량 (막대그래프)
        fig.add_trace(go.Bar(
            x=monthly_stats['월'], y=monthly_stats['거래량'], 
            name='월 거래량', marker_color='rgba(200, 220, 240, 0.6)'
        ), secondary_y=True)
        
        # 개별 실거래가 (점)
        fig.add_trace(go.Scatter(
            x=final_df['월'], y=final_df['거래금액(숫자)'], 
            mode='markers', name='개별 실거래',
            marker=dict(size=7, color='rgba(135, 206, 250, 0.8)'),
            hovertemplate='금액: %{y}만원'
        ), secondary_y=False)
        
        # 월 평균가 (선)
        fig.add_trace(go.Scatter(
            x=monthly_stats['월'], y=monthly_stats['평균가'], 
            mode='lines+markers', name='월 평균가',
            line=dict(color='#1e3a8a', width=3)
        ), secondary_y=False)
        
        # 최고가/최저가 깃발(어노테이션) 복구
        fig.add_annotation(
            x=final_df.loc[max_idx, '월'], y=final_df.loc[max_idx, '거래금액(숫자)'],
            text="최고", showarrow=True, arrowhead=1, ax=0, ay=-30,
            bgcolor="#ef4444", font=dict(color="white", size=10)
        )
        fig.add_annotation(
            x=final_df.loc[min_idx, '월'], y=final_df.loc[min_idx, '거래금액(숫자)'],
            text="최저", showarrow=True, arrowhead=1, ax=0, ay=30,
            bgcolor="#3b82f6", font=dict(color="white", size=10)
        )
        
        # 레이아웃 정리 (모바일 친화적 마진 유지)
        fig.update_layout(
            margin=dict(l=10, r=10, t=30, b=10),
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            paper_bgcolor='white', plot_bgcolor='white'
        )
        fig.update_yaxes(title_text="거래금액(만)", secondary_y=False, showgrid=True, gridcolor='#f1f5f9')
        fig.update_yaxes(title_text="거래량(건)", secondary_y=True, showgrid=False)
        
        st.plotly_chart(fig, use_container_width=True)
        
        # === 2. 실거래 내역 리스트 복구 (비고란 추가 및 가운데 정렬) ===
        st.write("📋 전체 실거래 내역 리스트")
        
        # 표에 들어갈 데이터 정리
        final_df['비고'] = ""
        final_df.loc[max_idx, '비고'] = "🔴 최고가"
        final_df.loc[min_idx, '비고'] = "🔵 최저가"
        
        display_df = final_df[['거래일자', '층', '거래금액(만)', '비고']].copy()
        display_df['거래일자'] = display_df['거래일자'].dt.strftime('%Y-%m-%d')
        display_df = display_df.sort_values(by='거래일자', ascending=False)
        
        # 가운데 정렬 및 글씨 색상 강조 로직 (Pandas Styler 사용)
        def style_dataframe(row):
            styles = ['text-align: center'] * len(row)
            if '최고가' in str(row['비고']):
                return ['text-align: center; color: #ef4444; font-weight: bold'] * len(row)
            elif '최저가' in str(row['비고']):
                return ['text-align: center; color: #3b82f6; font-weight: bold'] * len(row)
            return styles

        # 스타일 적용하여 표 출력
        styled_df = display_df.style.apply(style_dataframe, axis=1).set_properties(**{'text-align': 'center'})
        
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

    else:
        st.warning("선택한 평형의 거래 데이터가 존재하지 않습니다.")
else:
    st.error("데이터를 가져오지 못했습니다.")