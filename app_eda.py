# --- population_eda.py ---
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import io

class PopulationEDA:
    def __init__(self):
        st.title("📊 Population Trends Analysis")

        uploaded = st.file_uploader("Upload population_trends.csv", type="csv")
        if uploaded is None:
            st.info("Please upload population_trends.csv")
            return

        try:
            df = pd.read_csv(uploaded)
        except Exception as e:
            st.error(f"File read error: {e}")
            return

        df.replace('-', 0, inplace=True)
        missing_cols = [col for col in ['인구', '출생아수(명)', '사망자수(명)'] if col not in df.columns]
        if missing_cols:
            st.error(f"Missing required columns: {', '.join(missing_cols)}")
            return

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
            df_nat = df[df['지역'] == '전국']
            fig, ax = plt.subplots()
            sns.lineplot(data=df_nat, x='연도', y='인구', ax=ax)
            ax.set_title("National Population Trend")

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
                pivot = pivot.drop('전국', errors='ignore')
                pivot['증가량'] = pivot[years[-1]] - pivot[years[-6]]
                pivot['변화율'] = (pivot['증가량'] / pivot[years[-6]]) * 100
                top_diff = pivot.sort_values('증가량', ascending=False)

                fig1, ax1 = plt.subplots()
                sns.barplot(x='증가량', y=top_diff.index, data=top_diff.reset_index(), ax=ax1)
                ax1.set_title("Population Change (5 years)")
                st.pyplot(fig1)

                fig2, ax2 = plt.subplots()
                sns.barplot(x='변화율', y=top_diff.index, data=top_diff.reset_index(), ax=ax2)
                ax2.set_title("Change Rate (%)")
                st.pyplot(fig2)

        with tab4:
            st.subheader("📈 Top 100 Change Cases")
            df_sorted = df[df['지역'] != '전국'].copy()
            df_sorted['증감'] = df_sorted.groupby('지역')['인구'].diff()
            top100 = df_sorted.nlargest(100, '증감')

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
                styled_df = top100.style.format({'인구': "{:,}", '증감': "{:,}"}).applymap(color_scale, subset=['증감'])
                st.dataframe(styled_df)
            except:
                st.dataframe(top100[['연도', '지역', '인구', '증감']])

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

if __name__ == "__main__":
    PopulationEDA()
