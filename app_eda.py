import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Firebase 설정
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.appspot.com",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# 세션 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# 필수 클래스 정의가 누락되어 있을 수 있어 아래에 기본 틀을 추가합니다.
class Login:
    def __init__(self):
        st.title("Login")

class Register:
    def __init__(self):
        st.title("Register")

class FindPassword:
    def __init__(self):
        st.title("Find Password")

class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        st.markdown("""
        ---
        **EDA 메뉴 안내**  
        - EDA 탭에서는 자전거 수요 분석 외에도 지역 인구 분석 기능이 추가되었습니다.  
        - 좌측 사이드바의 `EDA` 메뉴에서 Population 분석 탭을 선택해 보세요!
        """)

class UserInfo:
    def __init__(self):
        st.title("My Info")

class Logout:
    def __init__(self):
        st.title("Logout")
        st.session_state.logged_in = False

class EDA:
    def __init__(self):
        st.title("📊 EDA 메뉴")
        menu = st.radio("분석 선택", ["Bike Sharing Demand", "Population Trends"])

        if menu == "Bike Sharing Demand":
            uploaded = st.file_uploader("데이터셋 업로드 (train.csv)", type="csv", key="bike")
            if not uploaded:
                st.info("train.csv 파일을 업로드 해주세요.")
                return

            df = pd.read_csv(uploaded, parse_dates=['datetime'])
            st.subheader("샘플 데이터")
            st.dataframe(df.head())

        elif menu == "Population Trends":
            st.subheader("📊 Population Trends Analysis")
            uploaded = st.file_uploader("Upload population_trends.csv", type="csv", key="pop")
            if uploaded is None:
                st.info("Please upload population_trends.csv")
                return

            try:
                df = pd.read_csv(uploaded)
            except Exception as e:
                st.error(f"File read error: {e}")
                return

            df.loc[df['지역'] == '세종'] = df[df['지역'] == '세종'].replace('-', 0)
            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju', '전국': 'Nationwide'
            }
            df['지역'] = df['지역'].replace(region_map)

            try:
                df[['인구', '출생아수(명)', '사망자수(명)']] = df[['인구', '출생아수(명)', '사망자수(명)']].apply(pd.to_numeric)
            except Exception as e:
                st.error(f"Column type conversion failed: {e}")
                return

            tab1, tab2, tab3, tab4, tab5 = st.tabs(["Summary", "Trend", "Regional", "Changes", "Visualization"])

            with tab1:
                st.subheader("🔍 Data Overview")
                buffer = io.StringIO()
                df.info(buf=buffer)
                st.text(buffer.getvalue())
                st.subheader("Descriptive Statistics")
                st.dataframe(df.describe())

            with tab2:
                st.subheader("📈 Yearly Population Trend")
                df_nat = df[df['지역'] == 'Nationwide']
                fig, ax = plt.subplots()
                sns.lineplot(data=df_nat, x='연도', y='인구', ax=ax)
                ax.set_title("Population Trend by Year")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")

                recent = df_nat.sort_values('연도').tail(3)
                if len(recent) == 3:
                    avg_birth = recent['출생아수(명)'].mean()
                    avg_death = recent['사망자수(명)'].mean()
                    latest = recent.iloc[-1]
                    pred_pop = latest['인구'] + (avg_birth - avg_death) * (2035 - latest['연도'])
                    ax.axhline(pred_pop, color='gray', linestyle='--')
                    ax.text(2035, pred_pop, f"2035 Prediction: {int(pred_pop):,}", color='black')

                st.pyplot(fig)

            with tab3:
                st.subheader("📊 5-Year Population Change by Region")
                years = sorted(df['연도'].unique())
                if len(years) < 6:
                    st.warning("Dataset must include at least 6 years of data")
                else:
                    df_5 = df[df['연도'].isin([years[-1], years[-6]])]
                    pivot = df_5.pivot(index='지역', columns='연도', values='인구')
                    pivot = pivot.drop('Nationwide', errors='ignore')
                    pivot['Change'] = pivot[years[-1]] - pivot[years[-6]]
                    pivot['Rate (%)'] = (pivot['Change'] / pivot[years[-6]]) * 100
                    top_diff = pivot.sort_values('Change', ascending=False)

                    fig1, ax1 = plt.subplots()
                    sns.barplot(x='Change', y=top_diff.index, data=top_diff.reset_index(), ax=ax1)
                    ax1.set_title("Population Change (5 years)")
                    ax1.set_xlabel("Change (in people)")
                    st.pyplot(fig1)

                    fig2, ax2 = plt.subplots()
                    sns.barplot(x='Rate (%)', y=top_diff.index, data=top_diff.reset_index(), ax=ax2)
                    ax2.set_title("Change Rate (%)")
                    ax2.set_xlabel("Rate of Change (%)")
                    st.pyplot(fig2)

            with tab4:
                st.subheader("📈 Top 100 Change Cases")
                df_sorted = df[df['지역'] != 'Nationwide'].copy()
                df_sorted['Change'] = df_sorted.groupby('지역')['인구'].diff()
                top100 = df_sorted.nlargest(100, 'Change')

                def color_scale(val):
                    color = 'background-color: '
                    if val > 0:
                        color += '#add8e6'
                    elif val < 0:
                        color += '#f4cccc'
                    else:
                        color += 'white'
                    return color

                try:
                    styled_df = top100.style.format({'인구': "{:,}", 'Change': "{:,}"}).applymap(color_scale, subset=['Change'])
                    st.dataframe(styled_df)
                except:
                    st.dataframe(top100[['연도', '지역', '인구', 'Change']])

            with tab5:
                st.subheader("📊 Heatmap")
                try:
                    pivot = df.pivot(index='지역', columns='연도', values='인구')
                    fig, ax = plt.subplots(figsize=(12, 8))
                    sns.heatmap(pivot, cmap='YlGnBu', annot=False, ax=ax)
                    st.pyplot(fig)
                    st.markdown(
                        "- This heatmap shows yearly population distribution by region.\n"
                        "- Brighter colors indicate higher population.\n"
                        "- Useful for identifying regional trends over time.")
                except:
                    st.warning("Heatmap could not be generated. Check for proper data format.")

# 페이지 등록 및 실행
Page_Login    = {"id": "login", "title": "Login", "icon": "🔐", "func": Login}
Page_Register = {"id": "register", "title": "Register", "icon": "📝", "func": Register}
Page_FindPW   = {"id": "find-password", "title": "Find PW", "icon": "🔎", "func": FindPassword}
Page_Home     = {"id": "home", "title": "Home", "icon": "🏠", "func": lambda: Home(Login, Register, FindPassword)}
Page_User     = {"id": "user-info", "title": "My Info", "icon": "👤", "func": UserInfo}
Page_Logout   = {"id": "logout", "title": "Logout", "icon": "🔓", "func": Logout}
Page_EDA      = {"id": "eda", "title": "EDA", "icon": "📊", "func": EDA}

PAGES = [Page_Home, Page_Login, Page_Register, Page_FindPW, Page_User, Page_Logout, Page_EDA]
if st.session_state.logged_in:
    nav_pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    nav_pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected = st.sidebar.radio("Navigation", nav_pages, format_func=lambda x: x["title"])
selected["func"]()
