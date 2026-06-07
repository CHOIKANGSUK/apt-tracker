import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="강석의 아파트 시세트래킹",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 구글 시트 데이터 로드
@st.cache_data(ttl=600)
def load_data_v5_6():
    try:
        creds_dict = st.secrets["gcp_service_account"]
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        gc = gspread.authorize(creds)
        worksheet = gc.open("도권_아파트_실거래가_트래킹").get_worksheet(0)
        
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        # 실제 날짜 객체로 변환 (정렬의 기준)
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

df = load_data_v5_6()

if not df.empty:
    st.title("🏢 강석의 아파트 시세트래킹")
    st.caption("국토부 API 연동 실시간 대시보드 v5.6 (X축 날짜 섞임 문제 완벽 해결)")
    
    # 공통 데이터 전처리
    df['단지선택명'] = df['법정동'] + " " + df['아파트명']
    df['거래금액(숫자)'] = df['거래금액(만)'].astype(str).str.replace(',', '').astype(int)
    df['평형'] = df['전용면적(㎡)'].apply(lambda x: round(float(x)))
    
    # X축 표기용 한글 년월 생성 (탭1 전용)
    df['월_한글텍스트'] = df['거래일자'].dt.strftime('%y년 %m월')
    # 실제 정렬용 월 단위 날짜 생성 (탭2 비교 분석 전용)
    df['월_날짜객체'] = df['거래일자'].dt.to_period('M').dt.to_timestamp()

    # 상단 탭 구성
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
            
            # 최고/최저 어노테이션 텍스트 기반 유지 (탭1 전용)
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
            # 탭1 X축 텍스트 정렬 보장 (강제 정렬 옵션 추가)
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

    # ==================== TAB 2: 다중 단지 비교 평가 (X축 섞임 문제 완벽 해결 버전) ====================
    with tab2:
        st.subheader("⚖️ 단지별 시세 흐름 다중 비교 분석")
        st.markdown("비교할 단지들을 선택한 후, **각 단지별로 비교 대상 평형을 각각 지정**하여 정밀하게 비교합니다.")
        
        all_apts = sorted(df['단지선택명'].unique())
        selected_apts = st.multiselect("비교할 아파트 단지들을 선택하세요", all_apts, default=all_apts[:2] if len(all_apts) >= 2 else all_apts)
        
        if selected_apts:
            # 단지별 선택된 평형 정보를 담을 딕셔너리
            apt_pyung_mapping = {}
            
            st.markdown("#### 🔍 단지별 비교 평형(전용면적) 지정")
            # 선택된 단지 수에 맞춰 화면 분할 배치하여 사용자 UI 레이아웃 최적화
            cols = st.columns(min(len(selected_apts), 3)) 
            for idx, apt in enumerate(selected_apts):
                with cols[idx % 3]:
                    apt_df = df[df['단지선택명'] == apt]
                    available_pyungs = sorted(apt_df['평형'].unique())
                    # 단지별 평형 선택창 생성 (동적 key 부여)
                    chosen_pyung = st.selectbox(f"{apt}", available_pyungs, key=f"comp_pyung_{idx}")
                    apt_pyung_mapping[apt] = chosen_pyung
            
            # 각 단지별로 선택된 평형 데이터만 필터링하여 결합
            matched_records = []
            for apt, pyung in apt_pyung_mapping.items():
                target_condition = (df['단지선택명'] == apt) & (df['평형'] == pyung)
                matched_records.append(df[target_condition])
                
            if matched_records:
                comp_df = pd.concat(matched_records)
                comp_df['비교단지명'] = comp_df['단지선택명'] + " (" + comp_df['평형'].astype(str) + "㎡)"
                
                # [문제 해결 핵심] 집계 시 한글 텍스트 대신 '월_날짜객체'를 사용하여 groupby 진행
                comp_stats = comp_df.groupby(['월_날짜객체', '비교단지명']).agg(
                    평균가=('거래금액(숫자)', 'mean')
                ).reset_index()
                comp_stats['평균가'] = comp_stats['평균가'].round(0).astype(int)
                
                # 1. 정밀 비교 그래프 시각화 (X축 정렬 문제 해결 완료)
                fig_comp = go.Figure()
                for label in sorted(comp_df['비교단지명'].unique()):
                    # [문제 해결 핵심] 날짜 기반으로 데이터 추출 및 정렬 보장
                    label_data = comp_stats[comp_stats['비교단지명'] == label].sort_values('월_날짜객체')
                    fig_comp.add_trace(go.Scatter(
                        # [문제 해결 핵심] X축 좌표로 텍스트 대신 실제 날짜(datetime) 전달
                        x=label_data['월_날짜객체'], 
                        y=label_data['평균가'],
                        mode='lines+markers', name=label,
                        line=dict(width=2.5),
                        connectgaps=True,
                        # 호버링 시 날짜 포맷 정의
                        hovertemplate='일자: %{x|%y년 %m월}<br>금액: %{y}만원'
                    ))
                
                fig_comp.update_layout(
                    margin=dict(l=10, r=10, t=30, b=10),
                    hovermode='x unified',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                    paper_bgcolor='white', plot_bgcolor='white'
                )
                
                # [문제 해결 핵심] Plotly 엔진에게 X축이 날짜(date)임을 명시하고, 화면에 보일 때만 한글 포맷으로 변환
                fig_comp.update_xaxes(
                    type='date',
                    tickformat="%y년 %m월", # 화면 표기 형식 정의
                    dtick="M1", # 1개월 단위로 눈금 표시
                    ticklabelmode="period", # 눈금 라벨 위치 조정
                    showgrid=True, gridcolor='#f1f5f9'
                )
                fig_comp.update_yaxes(title_text="월평균 거래금액(만)", showgrid=True, gridcolor='#f1f5f9')
                st.plotly_chart(fig_comp, use_container_width=True)
                
                # 2. 요약 지표 테이블 시각화
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
                }).set_properties(**{
                    'text-align': 'center'
                })
                st.dataframe(styled_summary, use_container_width=True, hide_index=True)
        else:
            st.info("비교 분석을 진행할 아파트 단지를 1개 이상 선택해 주세요.")
else:
    st.error("데이터를 가져오지 못했습니다.")