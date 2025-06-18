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

class Login:
    def __init__(self):
        st.title("🔐 Login")
        st.write("로그인 기능이 아직 구현되어 있지 않습니다.")

class Register:
    def __init__(self):
        st.title("📝 Register")
        st.write("회원가입 기능이 아직 구현되어 있지 않습니다.")

class FindPassword:
    def __init__(self):
        st.title("🔎 Find Password")
        st.write("비밀번호 찾기 기능이 아직 구현되어 있지 않습니다.")

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
        st.title("👤 My Info")
        st.write("유저 정보 페이지입니다.")

class Logout:
    def __init__(self):
        st.title("🔓 Logout")
        st.session_state.logged_in = False
        st.success("성공적으로 로그아웃되었습니다.")

class EDA:
    def __init__(self):
        st.title("📊 Population EDA")
        uploaded_file = st.file_uploader("Upload population_trends.csv", type=["csv"])
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)

            # 전처리
            df.replace('-', 0, inplace=True)
            for col in ['인구', '출생아수(명)', '사망자수(명)']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df.fillna(0, inplace=True)

            tab1, tab2, tab3, tab4, tab5 = st.tabs(["기초 통계", "연도별 추이", "지역별 분석", "변화량 분석", "시각화"])

            with tab1:
                st.subheader("Descriptive Statistics")
                st.dataframe(df.describe())
                buffer = io.StringIO()
                df.info(buf=buffer)
                st.text(buffer.getvalue())

            with tab2:
                st.subheader("Total Population Over Time")
                df_total = df[df['지역'] == '전국']
                plt.figure(figsize=(10, 4))
                sns.lineplot(data=df_total, x='연도', y='인구')
                plt.title("Population Trend")
                plt.xlabel("Year")
                plt.ylabel("Population")
                st.pyplot(plt.gcf())

            with tab3:
                st.subheader("Regional Population Change")
                latest_year = df['연도'].max()
                recent = df[df['연도'].isin([latest_year, latest_year - 5])]
                pivot = recent.pivot(index='지역', columns='연도', values='인구').drop('전국', errors='ignore')
                pivot['change'] = pivot[latest_year] - pivot[latest_year - 5]
                pivot['rate'] = pivot['change'] / pivot[latest_year - 5] * 100
                sorted_change = pivot.sort_values('change', ascending=False)
                plt.figure(figsize=(10, 6))
                sns.barplot(x=sorted_change['change'] / 1000, y=sorted_change.index)
                plt.title("Population Change (thousands)")
                plt.xlabel("Change")
                st.pyplot(plt.gcf())

            with tab4:
                st.subheader("Top Changes")
                df_no_total = df[df['지역'] != '전국']
                df_no_total['증감'] = df_no_total.groupby('지역')['인구'].diff()
                top100 = df_no_total.sort_values('증감', ascending=False).head(100)
                def colorize(val):
                    color = '#ffdddd' if val < 0 else '#ddeeff'
                    return f'background-color: {color}'
                st.dataframe(top100.style.format({"증감": ","}).applymap(colorize, subset=['증감']))

            with tab5:
                st.subheader("Heatmap")
                pivot = df.pivot(index='지역', columns='연도', values='인구')
                plt.figure(figsize=(12, 6))
                sns.heatmap(pivot, cmap='coolwarm')
                plt.title("Population Heatmap")
                st.pyplot(plt.gcf())

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
