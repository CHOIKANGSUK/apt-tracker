import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# 1. 페이지 기본 설정 (가로 폭을 전체 화면으로 유연하게 설정)
st.set_page_config(
    page_title="강석의 아파트 시세트래킹",
    page_icon="🏢",
    layout="wide", # 모바일 및 태블릿 대응을 위해 wide 유지
    initial_sidebar_state="collapsed" # 모바일에서 사이드바가 화면을 가리지 않도록 기본 닫힘 설정
)

# 구글 시트 데이터 로드 함수 (이전 Secrets 금고 연동 유지)
@st.cache_data(ttl=600)
def load_data_v5_3():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        gc = gspread.authorize(creds)
        worksheet = gc.open("도권_아파트_실거래가_트래킹").get_worksheet(0)
        
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        # 날짜 정렬 및 전처리
        df['거래일자'] = pd.to_datetime(df['거래일자'])
        df = df.sort_values(by='거래일자', ascending=True)
        return df
    except Exception as e:
        st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# 아파트 단지 메타 정보 라이브러리
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

# 데이터 가져오기
df = load_data_v5_3()

if not df.empty:
    # 2. 메인 헤더 영역 (모바일 가독성을 위해 자잘한 문구 축소)
    st.title("🏢 강석의 아파트 시세트래킹 v5.3")
    st.caption("국토부 API 연동 실시간 대시보드 (모바일 최적화 버전)")
    
    # 3. 사이드바 필터 구성
    st.sidebar.header("📍 단지 및 평형 선택")
    df['단지선택명'] = df['법정동'] + " " + df['아파트명']
    apt_list = sorted(df['단지선택명'].unique())
    selected_apt = st.sidebar.selectbox("단지 선택", apt_list)
    
    # 선택된 단지 데이터 필터링
    filtered_df = df[df['단지선택명'] == selected_apt].copy()
    
    # 평형 선택 (소수점 버림 처리하여 보기 편하게 변환)
    filtered_df['평형'] = filtered_df['전용면적(㎡)'].apply(lambda x: round(float(x)))
    pyung_list = sorted(filtered_df['평형'].unique())
    selected_pyung = st.sidebar.selectbox("평형 선택(㎡)", pyung_list)
    
    final_df = filtered_df[filtered_df['평형'] == selected_pyung].copy()
    
    if not final_df.empty:
        # 단지 정보 가져오기
        info = get_apt_info(selected_apt)
        
        # 단지 헤더 출력
        st.subheader(f"📍 {selected_apt} ({selected_pyung}㎡)")
        st.markdown(f"**정보:** {info['세대수']} | {info['준공']} 준공 | 용적률 {info['용적률']}")
        st.markdown("---")
        
        # 4. 핵심 지표 계산
        final_df['거래금액(숫자)'] = final_df['거래금액(만)'].astype(str).str.replace(',', '').astype(int)
        
        recent_deal = final_df.iloc[-1]
        max_deal = final_df.loc[final_df['거래금액(숫자)'].idxmax()]
        min_deal = final_df.loc[final_df['거래금액(숫자)'].idxmin()]
        
        recent_price = recent_deal['거래금액(숫자)']
        max_price = max_deal['거래금액(숫자)']
        min_price = min_deal['거래금액(숫자)']
        
        drop_rate = ((recent_price - max_price) / max_price) * 100
        
        # 5. [모바일 최적화 핵심] 레이아웃 분기
        # 모바일에서는 4열이 너무 좁으므로 상단에 2열씩 2줄로 배치되도록 스트림릿이 알아서 조절합니다.
        col1, col2 = st.columns(2)
        with col1:
            st.metric("최근 실거래가", f"{recent_price:,}만", f"{recent_deal['거래일자'].strftime('%Y-%m-%d')}")
        with col2:
            st.metric("역대 최고가", f"{max_price:,}만", f"{max_deal['거래일자'].strftime('%Y-%m-%d')}")
            
        col3, col4 = st.columns(2)
        with col3:
            st.metric("고점 대비 하락률", f"{drop_rate:.1f}%")
        with col4:
            st.metric("역대 최저가", f"{min_price:,}만", f"{min_deal['거래일자'].strftime('%Y-%m-%d')}")
            
        st.markdown("---")
        
        # 6. [모바일 최적화] 그래프 영역
        st.write("📈 시세 추이 그래프")
        
        fig = go.Figure()
        # 개별 거래 점 데이터
        fig.add_trace(go.Scatter(
            x=final_df['거래일자'], y=final_df['거래금액(숫자)'],
            mode='markers', name='개별 실거래',
            marker=dict(size=8, color='rgba(135, 206, 250, 0.6)'),
            hovertemplate='일자: %{x}<br>금액: %{y}만원'
        ))
        # 시세 흐름 선 데이터
        fig.add_trace(go.Scatter(
            x=final_df['거래일자'], y=final_df['거래금액(숫자)'],
            mode='lines', name='시세 흐름',
            line=dict(color='#1e3a8a', width=2)
        ))
        
        # 모바일 화면 크기에 맞게 내부 여백(margin) 최소화 및 범례 위치 조정
        fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            hovermode='x',
            showlegend=False, # 모바일 좁은 화면을 위해 범례 숨김
            paper_bgcolor='white',
            plot_bgcolor='white',
            xaxis=dict(showgrid=True, gridcolor='#f1f5f9'),
            yaxis=dict(showgrid=True, gridcolor='#f1f5f9')
        )
        
        # use_container_width=True를 설정하여 스마트폰 가로 크기에 무조건 맞춤
        st.plotly_chart(fig, use_container_width=True)
        
        # 7. [모바일 최적화] 표 영역
        st.write("📋 전체 실거래 내역 리스트")
        display_df = final_df[['거래일자', '층', '거래금액(만)']].copy()
        display_df['거래일자'] = display_df['거래일자'].dt.strftime('%Y-%m-%d')
        display_df = display_df.sort_values(by='거래일자', ascending=False)
        
        # 표도 마찬가지로 가로폭 100% 강제 맞춤
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    else:
        st.warning("선택한 평형의 거래 데이터가 존재하지 않습니다.")
else:
    st.error("구글 스프레드시트에서 데이터를 가져오지 못했습니다. 수집 로봇 작동 여부를 확인해 주세요.")