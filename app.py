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
def load_data_v5_4():
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

df = load_data_v5_4()

if not df.empty:
    st.title("🏢 강석의 아파트 시세트래킹")
    st.caption("국토부 API 연동 실시간 대시보드 v5.4 (다중 비교 + 데이터 정렬 및 포맷 완벽 복구)")
    
    # 공통 데이터 전처리
    df['단지선택명'] = df['법정동'] + " " + df['아파트명']
    df['거래금액(숫자)'] = df['거래금액(만)'].astype(str).str.replace(',', '').astype(int)
    df['평형'] = df['전용면적(㎡)'].apply(lambda x: round(float(x)))
    df['월'] = df['거래일자'].dt.strftime('%y년 %m월')
    df['월별_정렬기준'] = df['거래일자'].dt.to_period('M')

    # 상단 탭 구성 (유실되었던 탭 기능 전면 복구)
    tab1, tab2 = st.tabs(["📊 단일 단지 시황 분석", "⚖️ 다중 단지 비교 평가"])
    
    # ==================== TAB 1: 단일 단지 시황 분석 ====================
    with tab1:
        st.sidebar.header("📍 단지 및 평형 선택")
        apt_list = sorted(df['단지선택명'].unique())
        selected_apt = st.sidebar.selectbox("단지 선택", apt_list, key="single_apt")
        
        filtered_df = df[df['단지선택명'] == selected_apt].copy()
        pyung_list = sorted(filtered_df['평형'].unique())
        selected_pyung = st.sidebar.selectbox("평형 선택(㎡)", pyung_list, key="single_pyung")
        
        final_df = filtered_df[filtered_df['평형'] == selected_pyung].copy()
        
        if not final_df.empty:
            info = get_apt_info(selected_apt)
            st.subheader(f"📍 {selected_apt} ({selected_pyung}㎡)")
            st.markdown(f"**정보:** {info['세대수']} | {info['준공']} 준공 | 용적률 {info['용적률']}")
            st.markdown("---")
            
            # 월별 통계 추출 (평균가, 거래량)
            monthly_stats = final_df.groupby('월별_정렬기준').agg(
                월=('월', 'first'),
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
            
            # 상단 지표 영역 (모바일 대응)
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
            
            # 시세 추이 그래프 복구
            st.write("📈 시세 추이 및 거래량")
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            fig.add_trace(go.Bar(
                x=monthly_stats['월'], y=monthly_stats['거래량'], 
                name='월 거래량', marker_color='rgba(200, 220, 240, 0.6)'
            ), secondary_y=True)
            
            fig.add_trace(go.Scatter(
                x=final_df['월'], y=final_df['거래금액(숫자)'], 
                mode='markers', name='개별 실거래',
                marker=dict(size=7, color='rgba(135, 206, 250, 0.8)'),
                hovertemplate='금액: %{y}만원'
            ), secondary_y=False)
            
            fig.add_trace(go.Scatter(
                x=monthly_stats['월'], y=monthly_stats['평균가'], 
                mode='lines+markers', name='월 평균가',
                line=dict(color='#1e3a8a', width=3)
            ), secondary_y=False)
            
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
            
            fig.update_layout(
                margin=dict(l=10, r=10, t=30, b=10),
                hovermode='x unified',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                paper_bgcolor='white', plot_bgcolor='white'
            )
            fig.update_yaxes(title_text="거래금액(만)", secondary_y=False, showgrid=True, gridcolor='#f1f5f9')
            fig.update_yaxes(title_text="거래량(건)", secondary_y=True, showgrid=False)
            
            st.plotly_chart(fig, use_container_width=True)
            
            # 실거래 내역 리스트 정렬 및 포맷 적용
            st.write("📋 전체 실거래 내역 리스트")
            
            final_df['비고'] = ""
            final_df.loc[max_idx, '비고'] = "🔴 최고가"
            final_df.loc[min_idx, '비고'] = "🔵 최저가"
            
            display_df = final_df[['거래일자', '층', '거래금액(숫자)', '비고']].copy()
            display_df['거래일자'] = display_df['거래일자'].dt.strftime('%Y-%m-%d')
            display_df = display_df.sort_values(by='거래일자', ascending=False)
            
            # 컬럼명 변경 및 세단위 콤마 서식 적용
            display_df.columns = ['거래일자', '층', '거래금액(만)', '비고']
            
            # 표 디자인 콘텐트 제어 (가운데 정렬 + 천단위 쉼표 포맷 보장)
            styled_df = display_df.style.format({
                '거래금액(만)': '{:,.0f}'
            }).set_properties(**{
                'text-align': 'center'
            })
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.warning("선택한 평형의 거래 데이터가 존재하지 않습니다.")

    # ==================== TAB 2: 다중 단지 비교 평가 ====================
    with tab2:
        st.subheader("⚖️ 단지별 시세 흐름 다중 비교 분석")
        st.markdown("여러 아파트 단지를 동시에 선택하여 가격 흐름과 트렌드를 통합 비교합니다.")
        
        all_apts = sorted(df['단지선택명'].unique())
        selected_apts = st.multiselect("비교할 아파트 단지들을 선택하세요", all_apts, default=all_apts[:2] if len(all_apts) >= 2 else all_apts)
        
        if selected_apts:
            comp_df = df[df['단지선택명'].isin(selected_apts)].copy()
            
            # 월별 단지별 평균 거래금액 피벗 생성
            comp_stats = comp_df.groupby(['월별_정렬기준', '단지선택명']).agg(
                월=('월', 'first'),
                평균가=('거래금액(숫자)', 'mean')
            ).reset_index()
            comp_stats['평균가'] = comp_stats['평균가'].round(0).astype(int)
            
            # 비교 그래프 그리기
            fig_comp = go.Figure()
            for apt in selected_apts:
                apt_data = comp_stats[comp_stats['단지선택명'] == apt].sort_values('월별_정렬기준')
                fig_comp.add_trace(go.Scatter(
                    x=apt_data['월'], y=apt_data['평균가'],
                    mode='lines+markers', name=apt,
                    line=dict(width=2.5),
                    connectgaps=True
                ))
            
            fig_comp.update_layout(
                margin=dict(l=10, r=10, t=30, b=10),
                hovermode='x unified',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                paper_bgcolor='white', plot_bgcolor='white'
            )
            fig_comp.update_yaxes(title_text="월평균 거래금액(만)", showgrid=True, gridcolor='#f1f5f9')
            st.plotly_chart(fig_comp, use_container_width=True)
            
            # 요약 데이터프레임 표시 (가운데 정렬 + 포맷 적용)
            st.write("📊 단지별 종합 요약 지표")
            summary_records = []
            for apt in selected_apts:
                apt_full = comp_df[comp_df['단지선택명'] == apt]
                if not apt_full.empty:
                    recent = apt_full.iloc[-1]['거래금액(숫자)']
                    mx = apt_full['거래금액(숫자)'].max()
                    mn = apt_full['거래금액(숫자)'].min()
                    dr = ((recent - mx) / mx) * 100
                    summary_records.append({
                        "단지명": apt, "최근거래가(만)": recent, "역대최고가(만)": mx, "역대최저가(만)": mn, "고점대비하락률": f"{dr:.1f}%"
                    })
            
            summary_df = pd.DataFrame(summary_records)
            styled_summary = summary_df.style.format({
                '최근거래가(만)': '{:,.0f}', '역대최고가(만)': '{:,.0f}', '역대최저가(만)': '{:,.0f}'
            }).set_properties(**{
                'text-align': 'center'
            })
            st.dataframe(styled_summary, use_container_width=True, hide_index=True)
        else:
            st.info("비교 분석을 진행할 아파트 단지를 1개 이상 선택해 주세요.")
else:
    st.error("데이터를 가져오지 못했습니다.")