import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.unicode_minus'] = False

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

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "Unknown"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

class Login:
    def __init__(self):
        st.title("🔐 Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']
                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "Unknown")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")
                st.success("Login successful!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("Login failed")

class Register:
    def __init__(self):
        st.title("📝 Register")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        name = st.text_input("Name")
        gender = st.selectbox("Gender", ["Unknown", "Male", "Female"])
        phone = st.text_input("Phone Number")
        if st.button("Register"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("Registration successful! Redirecting to login page.")
                time.sleep(1)
                st.switch_page("login")
            except Exception:
                st.error("Registration failed")

class FindPassword:
    def __init__(self):
        st.title("🔎 Find Password")
        email = st.text_input("Email")
        if st.button("Send Reset Email"):
            try:
                auth.send_password_reset_email(email)
                st.success("Reset email sent.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("Failed to send email")

class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"Welcome, {st.session_state.get('user_email')}")
        st.markdown("""
        ---
        **EDA Menu Guide**  
        - In the EDA tab, population trend analysis is available in addition to bike demand analysis.  
        - Go to the `EDA` page from the sidebar to check it out!
        """)

class UserInfo:
    def __init__(self):
        st.title("👤 My Info")
        st.write("User information page.")

class Logout:
    def __init__(self):
        st.title("🔓 Logout")
        st.session_state.logged_in = False
        st.success("You have been logged out.")
        time.sleep(1)
        st.rerun()

class EDA:
    def __init__(self):
        st.title("📊 Population EDA")
        uploaded_file = st.file_uploader("Upload population_trends.csv", type=["csv"])
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file)

            df.replace('-', 0, inplace=True)
            for col in ['인구', '출생아수(명)', '사망자수(명)']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df.fillna(0, inplace=True)

            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju', '전국': 'Nationwide'
            }
            df['region_en'] = df['지역'].map(region_map)

            tab1, tab2, tab3, tab4, tab5 = st.tabs(["Descriptive", "Trend", "Region", "Change", "Heatmap"])

            with tab1:
                st.subheader("Descriptive Statistics")
                st.dataframe(df.describe())
                buffer = io.StringIO()
                df.info(buf=buffer)
                st.text(buffer.getvalue())

            with tab2:
                st.subheader("Total Population Over Time")
                df_total = df[df['region_en'] == 'Nationwide']
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
                pivot = recent.pivot(index='region_en', columns='연도', values='인구').drop('Nationwide', errors='ignore')
                pivot['change'] = pivot[latest_year] - pivot[latest_year - 5]
                pivot['rate'] = pivot['change'] / pivot[latest_year - 5] * 100
                sorted_change = pivot.sort_values('change', ascending=False).reset_index()
                plt.figure(figsize=(10, 6))
                sns.barplot(x='change', y='region_en', data=sorted_change)
                plt.title("Population Change (thousands)")
                plt.xlabel("Change")
                st.pyplot(plt.gcf())

            with tab4:
                st.subheader("Top Changes")
                df_no_total = df[df['region_en'] != 'Nationwide']
                df_no_total['change'] = df_no_total.groupby('region_en')['인구'].diff()
                top100 = df_no_total.sort_values('change', ascending=False).head(100)
                def colorize(val):
                    color = '#ffdddd' if val < 0 else '#ddeeff'
                    return f'background-color: {color}'
                st.dataframe(top100.style.format({"change": ","}).applymap(colorize, subset=['change']))

            with tab5:
                st.subheader("Population Heatmap")
                pivot = df.pivot(index='region_en', columns='연도', values='인구')
                plt.figure(figsize=(12, 6))
                sns.heatmap(pivot, cmap='coolwarm')
                plt.title("Population Heatmap")
                st.pyplot(plt.gcf())

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