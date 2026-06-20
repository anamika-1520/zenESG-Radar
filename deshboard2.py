from radar import render_daily_radar
from db_schema import ensure_database_schema
import streamlit as st

st.set_page_config(
    page_title="ZenESG Regulatory Radar",
    page_icon="🌍",
    layout="wide",
)

def main():
    ensure_database_schema()
    render_daily_radar()

if __name__ == "__main__":
    main()