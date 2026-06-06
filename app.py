import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

st.set_page_config(page_title="강석의 아파트 시세트래킹", layout="wide")

def get_apt_info(apt_name):
    if "중화동" in apt_name and "한신" in apt_name:
        return {"세대수": "1,544세대", "준공": "1997.10 (29년차)", "용적률": "376%", "건폐율": "20%"}
    elif "상봉동" in apt_name and "더샵" in apt_name:
        return {"세대수": "497세대", "준공": "2013.11 (14년차)", "용적률": "599%", "건폐율": "53%"}
    elif "이문동" in apt_name and "현대" in apt_name:
        return {"세대수": "531세대", "준공": "2001.03 (26년차)", "용적률": "341%", "건폐율": "24%"}
    elif "상월곡동" in apt_name and "동아에코빌" in apt_name:
        return {"세대수": "1,253세대", "준공": "2003.06 (23년차)", "용적률": "281%", "건폐율": "20%"}
    elif "이문동" in apt_name and "쌍용" in apt_name:
        return {"세대수": "1,318세대", "준공": "2000.11 (26년차)", "용적률": "343%", "건폐율": "22%"}
    else:
        return {"세대수": "정보없음", "준공": "정보없음", "용적률": "정보없음", "건폐율": "정보없음"}
st.markdown("""
    <style>
    .main { background-color: #f8fafc; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; border: 1px solid #e2e8f0; }
    
    .apt-header { background-color: #ffffff; padding: 20px; border-radius: 12px; margin-bottom: 25px; border-left: 5px solid #1e293b; }
    .apt-title { font-size: 32px; font-weight: bold; color: #1e293b; margin-bottom: 8px; }
    .apt-desc { font-size: 16px; color: #64748b; line-height: 1.5; }
    
    .naver-table-container { width: 100%; display: flex; justify-content: center; margin-top: 20px; }
    .naver-table { width: 50% !important; border-collapse: collapse; font-size: 17px; background-color: #ffffff; font-family: 'Malgun Gothic', sans-serif; }
    .naver-table th { background-color: #f8f9fa; padding: 12px; text-align: center !important; border-top: 2px solid #222222; border-bottom: 1px solid #e2e8f0; color: #333333; font-weight: bold; }
    .naver-table td { padding: 12px; text-align: center !important; border-bottom: 1px solid #e2e8f0; color: #444444; position: relative; }
    .naver-table tr:hover { background-color: #f4f6f8; }
    
    .label-tag { font-size: 12px; padding: 2px 6px; border-radius: 3px; margin-left: 5px; vertical-align: middle; }
    .label-high { background-color: #fff1f2; color: #e11d48; border: 1px solid #fecdd3; }
    .label-low { background-color: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }
    .price-bold { font-weight: bold; color: #1e293b; }
    </style>
    """, unsafe_allow_html=True)

st.title("강석의 아파트 시세트래킹")
st.markdown("##### 국토부 API 연동 데이터베이스 기반 시황 대시보드 v5.2")
st.write("---")

@st.cache_data(ttl=600)
def load_data_v5_2():
    # 깃허브 secret.json 파일 대신 Streamlit의 Secrets 금고를 엽니다.
    creds_dict = st.secrets["gcp_service_account"]
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    gc = gspread.authorize(creds)
    doc = gc.open("도권_아파트_실거래가_트래킹")
    worksheet = doc.get_worksheet(0)
    df = pd.DataFrame(worksheet.get_all_records())
    df['거래금액(만)'] = df['거래금액(만)'].astype(str).str.replace(',', '').astype(float)
    df['거래일자'] = pd.to_datetime(df['거래일자'])
    df['고유단지명'] = df['법정동'] + " " + df['아파트명']
    df['평형'] = df['전용면적(㎡)'].astype(float).round(1)
    df['비교식별자'] = df['고유단지명'] + " (" + df['평형'].astype(str) + "㎡)"
    df['연월_sort'] = df['거래일자'].dt.to_period('M') 
    df['조회년월'] = df['거래일자'].apply(lambda x: f"{x.year}년 {x.month}월")
    return df

try:
    df = load_data_v5_2()
    tab1, tab2 = st.tabs(["단일 단지 시황 분석", "다중 단지 비교 평가"])
    
    with tab1:
        st.sidebar.header("단일 분석 필터")
        apt_name = st.sidebar.selectbox("단지 선택", sorted(df['고유단지명'].unique()), key="single_apt")
        area_options = sorted(df[df['고유단지명'] == apt_name]['평형'].unique())
        selected_area = st.sidebar.selectbox("평형 선택(㎡)", area_options, key="single_area")
        
        target_df = df[(df['고유단지명'] == apt_name) & (df['평형'] == selected_area)].sort_values('거래일자')
        
        if not target_df.empty:
            info = get_apt_info(apt_name)
            st.markdown(f"""
                <div class="apt-header">
                    <div class="apt-title">{apt_name}</div>
                    <div class="apt-desc">
                        <b>아파트</b> | {info['세대수']} | {info['준공']}<br>
                        용적률 {info['용적률']} | 건폐율 {info['건폐율']}
                    </div>
                </div>
            """, unsafe_allow_html=True)

            ath = target_df['거래금액(만)'].max()
            atl = target_df['거래금액(만)'].min()
            ath_idx = target_df['거래금액(만)'].idxmax()
            atl_idx = target_df['거래금액(만)'].idxmin()
            
            ath_row = target_df.loc[ath_idx]
            atl_row = target_df.loc[atl_idx]
            
            ath_date = ath_row['거래일자'].strftime('%y.%m.%d')
            atl_date = atl_row['거래일자'].strftime('%y.%m.%d')
            last_price = target_df.iloc[-1]['거래금액(만)']
            drawdown = ((last_price - ath) / ath) * 100
            
            monthly_df = target_df.groupby(['연월_sort', '조회년월']).agg({'거래금액(만)': 'mean', '아파트명': 'count'}).reset_index().rename(columns={'아파트명': '거래건수'})
            current_change = monthly_df.iloc[-1]['거래금액(만)'] / monthly_df.iloc[-2]['거래금액(만)'] - 1 if len(monthly_df) > 1 else 0

            m1, m2, m3, m4 = st.columns(4)
            with m1: st.metric("최근 월평균가", f"{last_price:,.0f}만", f"{current_change:+.1f}%")
            with m2: st.metric(f"역대 최고가 ({ath_date})", f"{ath:,.0f}만")
            with m3: st.metric("고점 대비 하락률", f"{drawdown:+.1f}%")
            with m4: st.metric(f"역대 최저가 ({atl_date})", f"{atl:,.0f}만")

            fig = make_subplots(specs=[[{"secondary_y": True}]])
            
            # 1. 거래량 바 차트
            fig.add_trace(go.Bar(x=monthly_df['조회년월'], y=monthly_df['거래건수'], name="거래건수", opacity=0.3, marker_color='#94a3b8'), secondary_y=True)
            
            # 2. 개별 실거래가 산점도 (데이터 흐름 파악용 점)
            fig.add_trace(go.Scatter(x=target_df['조회년월'], y=target_df['거래금액(만)'], name="개별 실거래가", mode='markers', marker=dict(color='#cbd5e1', size=6, line=dict(color='#94a3b8', width=1)), hovertemplate='%{x}<br>거래가: %{y:,.0f}만원<extra></extra>'), secondary_y=False)
            
            # 3. 월별 평균가 선 차트
            fig.add_trace(go.Scatter(x=monthly_df['조회년월'], y=monthly_df['거래금액(만)'], name="월별 평균가", mode='lines+markers', line=dict(color='#1e3a8a', width=3), hovertemplate='%{x}<br>평균가: %{y:,.0f}만원<extra></extra>'), secondary_y=False)
            
            # 최고/최저 라벨을 '개별 실거래가' 기준 좌표로 고정
            fig.add_annotation(
                x=ath_row['조회년월'], y=ath_row['거래금액(만)'],
                text="최고", showarrow=True, arrowhead=1, ax=0, ay=-30,
                font=dict(color="white", size=11), bgcolor="#e11d48", bordercolor="#e11d48", borderpad=3
            )
            fig.add_annotation(
                x=atl_row['조회년월'], y=atl_row['거래금액(만)'],
                text="최저", showarrow=True, arrowhead=1, ax=0, ay=30,
                font=dict(color="white", size=11), bgcolor="#2563eb", bordercolor="#2563eb", borderpad=3
            )

            fig.update_layout(hovermode="x unified", plot_bgcolor='white', margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)

            st.subheader("실거래 상세 리스트")
            table_df = target_df[['거래일자', '층', '거래금액(만)']].sort_values('거래일자', ascending=False)
            
            html_table = "<div class='naver-table-container'><table class='naver-table'><thead><tr><th>거래일자</th><th>층</th><th>거래금액(만)</th></tr></thead><tbody>"
            for _, row in table_df.iterrows():
                date_str = row['거래일자'].strftime('%Y.%m.%d')
                price = row['거래금액(만)']
                label = ""
                if price == ath: label = "<span class='label-tag label-high'>최고</span>"
                elif price == atl: label = "<span class='label-tag label-low'>최저</span>"
                html_table += f"<tr><td>{date_str}</td><td>{row['층']}층</td><td><span class='price-bold'>{price:,.0f}</span>{label}</td></tr>"
            html_table += "</tbody></table></div>"
            st.markdown(html_table, unsafe_allow_html=True)

    with tab2:
        st.subheader("관심 단지 다중 비교 평가")
        compare_list = sorted(df['비교식별자'].unique())
        selected_compares = st.multiselect("비교 단지 선택", compare_list, default=compare_list[:2] if len(compare_list) >= 2 else compare_list)
        if selected_compares:
            compare_df = df[df['비교식별자'].isin(selected_compares)]
            comp_monthly = compare_df.groupby(['비교식별자', '연월_sort', '조회년월'])['거래금액(만)'].mean().reset_index().sort_values('연월_sort')
            fig_comp = px.line(comp_monthly, x='조회년월', y='거래금액(만)', color='비교식별자', markers=True)
            st.plotly_chart(fig_comp, use_container_width=True)
            
            summary = []
            for comp in selected_compares:
                temp = compare_df[compare_df['비교식별자'] == comp]
                c_ath = temp['거래금액(만)'].max()
                c_last = temp.iloc[-1]['거래금액(만)']
                summary.append({"단지명": comp, "최고가": f"{c_ath:,.0f}", "현재가": f"{c_last:,.0f}", "하락률": f"{((c_last-c_ath)/c_ath)*100:+.1f}%"})
            st.table(pd.DataFrame(summary))

except Exception as e:
    st.error(f"오류 발생: {e}")