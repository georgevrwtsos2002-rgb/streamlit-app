import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.title("⚽ Football Shot Map Dashboard")

uploaded_file = st.file_uploader("Upload shots CSV", type=["csv"])

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.write("Data preview")
    st.dataframe(df)

    fig, ax = plt.subplots()

    goals = df[df["result"]=="Goal"]
    others = df[df["result"]!="Goal"]

    ax.scatter(others["x"], others["y"], alpha=0.6)
    ax.scatter(goals["x"], goals["y"], marker="*", s=200)

    ax.set_xlim(0,100)
    ax.set_ylim(0,100)

    ax.set_title("Shot Map")

    st.pyplot(fig)
