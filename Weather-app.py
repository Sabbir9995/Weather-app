import streamlit as st
import pandas as pd
import altair as alt
from fpdf import FPDF
import tempfile
import random

st.set_page_config(page_title="Weather Forecasting App", layout="wide")
st.title("🌤️ Weather Forecasting Web Application")

tabs = st.tabs([
    "1. Data Processing",
    "2. Data Visualization",
    "3. Weather Prediction",
    "4. Generate Report"
])

# --- 1. Data Upload & Processing ---
with tabs[0]:
    st.header("📥 Upload Weather Data Files")
    files = {
        "Humidity": st.file_uploader("Upload Humidity.xlsx", type="xlsx"),
        "MaxTemp": st.file_uploader("Upload Maximum Temperature.xlsx", type="xlsx"),
        "MinTemp": st.file_uploader("Upload Minimum Temperature.xlsx", type="xlsx"),
        "Rainfall": st.file_uploader("Upload Rainfall.xlsx", type="xlsx"),
        "Sunshine": st.file_uploader("Upload Sunshine.xlsx", type="xlsx"),
        "CloudCoverage": st.file_uploader("Upload Cloud Coverage.xlsx", type="xlsx"),
        "WindSpeed": st.file_uploader("Upload Wind Speed.xlsx", type="xlsx")
    }

    def process_excel(file):
        df = pd.read_excel(file, skiprows=3)
        df.columns = ['SL', 'Station', 'Year', 'Month', 'Value']
        return df[['Year', 'Month', 'Value']]

    if st.button("📊 Process Data"):
        try:
            merged_df = None
            for key, file in files.items():
                if file is not None:
                    df = process_excel(file)
                    df = df.rename(columns={"Value": key})
                    if merged_df is None:
                        merged_df = df
                    else:
                        merged_df = pd.merge(merged_df, df, on=["Year", "Month"], how="inner")
                else:
                    st.warning(f"Missing file: {key}")
                    st.stop()

            st.success("✅ Files processed and merged successfully!")

            # Feature Engineering
            merged_df["RainfallCategory"] = pd.cut(merged_df["Rainfall"],
                                                   bins=[-float('inf'), 50, 150, float('inf')],
                                                   labels=["Low", "Medium", "High"])
            merged_df["WindspeedCategory"] = pd.cut(merged_df["WindSpeed"],
                                                    bins=[-float('inf'), 1.5, 3.5, float('inf')],
                                                    labels=["Calm", "Moderate", "Windy"])

            st.subheader("Merged Weather Data (First 5 Rows)")
            st.dataframe(merged_df.head())

            st.session_state.weather_data = merged_df

        except Exception as e:
            st.error(f"❌ Error processing files: {e}")

# --- 2. Visualization ---
with tabs[1]:
    st.header("📈 Data Visualization")

    if "weather_data" in st.session_state:
        df = st.session_state.weather_data.copy()

        col1, col2 = st.columns(2)
        with col1:
            start_year = st.number_input("Start Year", min_value=1961, max_value=2023, value=1961)
        with col2:
            end_year = st.number_input("End Year", min_value=1961, max_value=2023, value=2023)

        df_filtered = df[(df["Year"] >= start_year) & (df["Year"] <= end_year)]

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Rainfall Distribution by Category")
            rain_chart = alt.Chart(df_filtered).mark_bar().encode(
                x=alt.X('RainfallCategory:N', title="Rainfall Category"),
                y=alt.Y('count()', title="Count"),
                color='RainfallCategory:N'
            ).properties(height=300)
            st.altair_chart(rain_chart, use_container_width=True)

        with col2:
            st.subheader("Wind Speed Distribution by Category")
            wind_chart = alt.Chart(df_filtered).mark_bar().encode(
                x=alt.X('WindspeedCategory:N', title="Wind Speed Category"),
                y=alt.Y('count()', title="Count"),
                color='WindspeedCategory:N'
            ).properties(height=300)
            st.altair_chart(wind_chart, use_container_width=True)

    else:
        st.info("ℹ️ Please process data in the first tab.")

# --- 3. Prediction ---
with tabs[2]:
    st.header("🔮 Weather Prediction ")

    if "weather_data" in st.session_state:
        st.markdown("Provide input values below:")

        col1, col2, col3 = st.columns(3)
        year = col1.number_input("Year", min_value=1961, max_value=2023, step=1)
        month = col2.number_input("Month", min_value=1, max_value=12)
        humidity = col3.number_input("Humidity (%)", min_value=0.0, max_value=100.0, step=0.1)

        col4, col5, col6 = st.columns(3)
        max_temp = col4.number_input("Max Temperature (°C)", min_value=10.0, max_value=50.0, step=0.1)
        min_temp = col5.number_input("Min Temperature (°C)", min_value=0.0, max_value=40.0, step=0.1)
        sunshine = col6.number_input("Sunshine (hours)", min_value=0.0, max_value=15.0, step=0.1)

        cloud_coverage = st.number_input("Cloud Coverage (oktas)", min_value=0.0, max_value=100.0, step=0.1)

        if st.button("🧠 Predict Weather"):
            if humidity > 80 and min_temp < 20:
                rainfall = 180 + (random.uniform(-25, 25))
            elif humidity > 60 and max_temp < 35:
                rainfall = 80 + (random.uniform(-20, 20))
            else:
                rainfall = 20 + (random.uniform(-5, 5))

            if sunshine < 5 and cloud_coverage > 6:
                wind_speed = 4.0 + (random.uniform(-0.5, 0.5))
            elif sunshine < 8 and cloud_coverage > 3:
                wind_speed = 2.5 + (random.uniform(-0.4, 0.4))
            else:
                wind_speed = 1.0 + (random.uniform(-0.25, 0.25))

            st.success(f"🌧️ **Predicted Rainfall:** {rainfall:.2f} mm")
            st.success(f"💨 **Predicted Wind Speed:** {wind_speed:.2f} m/s")

            st.session_state.rainfall = rainfall
            st.session_state.wind_speed = wind_speed

    else:
        st.warning("⚠️ Please upload and process data first.")

# --- 4. Report Generation ---
with tabs[3]:
    st.header("📝 Generate Weather Report")

    if "weather_data" in st.session_state:
        df = st.session_state.weather_data.copy()

        st.markdown("Click below to generate a summary report of the uploaded and predicted data.")

        if st.button("📄 Generate PDF Report"):
            try:
                class PDF(FPDF):
                    def header(self):
                        self.set_font("Arial", "B", 12)
                        self.cell(0, 10, "Weather Summary Report", ln=True, align="C")

                    def footer(self):
                        self.set_y(-15)
                        self.set_font("Arial", "I", 8)
                        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

                pdf = PDF()
                pdf.add_page()
                pdf.set_font("Arial", size=12)

                pdf.cell(200, 10, txt="Data Summary:", ln=True, align="L")
                pdf.ln(5)
                summary = df.describe().round(2).to_string()
                for line in summary.split('\n'):
                    pdf.cell(200, 8, txt=line, ln=True)

                pdf.ln(10)
                pdf.cell(200, 10, txt="Category Counts:", ln=True)
                pdf.ln(5)

                rain_counts = df["RainfallCategory"].value_counts().to_string()
                wind_counts = df["WindspeedCategory"].value_counts().to_string()

                pdf.cell(200, 8, txt="Rainfall Categories:", ln=True)
                for line in rain_counts.split('\n'):
                    pdf.cell(200, 8, txt=line, ln=True)

                pdf.cell(200, 8, txt="Wind Speed Categories:", ln=True)
                for line in wind_counts.split('\n'):
                    pdf.cell(200, 8, txt=line, ln=True)

                if "rainfall" in st.session_state and "wind_speed" in st.session_state:
                    pdf.ln(10)
                    pdf.cell(200, 10, txt="Predicted Results:", ln=True)
                    pdf.ln(5)
                    pdf.cell(200, 8, txt=f"Predicted Rainfall: {st.session_state.rainfall:.2f} mm", ln=True)
                    pdf.cell(200, 8, txt=f"Predicted Wind Speed: {st.session_state.wind_speed:.2f} m/s", ln=True)

                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    pdf.output(tmp_file.name)
                    st.success("✅ Report generated successfully!")
                    with open(tmp_file.name, "rb") as file:
                        st.download_button("⬇️ Download Report", file, file_name="weather_report.pdf", mime="application/pdf")
            except Exception as e:
                st.error(f"❌ Failed to generate report: {e}")
    else:
        st.warning("⚠️ Please process data first to generate a report.")
