import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="Shot Coordinate Picker", layout="wide")

if "x" not in st.session_state:
    st.session_state.x = 90
if "y" not in st.session_state:
    st.session_state.y = 50


def make_pitch():

    fig = go.Figure()

    # outer lines
    fig.add_trace(go.Scatter(
        x=[50,100,100,50,50],
        y=[0,0,100,100,0],
        mode="lines",
        showlegend=False
    ))

    # penalty box
    fig.add_trace(go.Scatter(
        x=[100,84,84,100],
        y=[21,21,79,79],
        mode="lines",
        showlegend=False
    ))

    # small box
    fig.add_trace(go.Scatter(
        x=[100,94,94,100],
        y=[37,37,63,63],
        mode="lines",
        showlegend=False
    ))

    # penalty spot
    fig.add_trace(go.Scatter(
        x=[89],
        y=[50],
        mode="markers",
        marker=dict(size=6),
        showlegend=False
    ))

    # arc
    theta = np.linspace(-0.95,0.95,200)
    r = 8.7
    x_arc = 89 - r*np.cos(theta)
    y_arc = 50 + r*np.sin(theta)
    mask = x_arc <= 84

    fig.add_trace(go.Scatter(
        x=x_arc[mask],
        y=y_arc[mask],
        mode="lines",
        showlegend=False
    ))

    # invisible click grid
    xs = np.arange(50,101,1)
    ys = np.arange(0,101,1)
    gx,gy = np.meshgrid(xs,ys)

    fig.add_trace(go.Scatter(
        x=gx.ravel(),
        y=gy.ravel(),
        mode="markers",
        marker=dict(size=10,opacity=0.01),
        showlegend=False
    ))

    # selected point
    fig.add_trace(go.Scatter(
        x=[st.session_state.x],
        y=[st.session_state.y],
        mode="markers",
        marker=dict(size=14,symbol="x"),
        showlegend=False
    ))

    fig.update_layout(
        height=700,
        xaxis=dict(range=[50,103],visible=False),
        yaxis=dict(range=[0,100],visible=False,scaleanchor="x",scaleratio=1),
        dragmode="select"
    )

    return fig


st.title("⚽ Shot Coordinate Picker")

fig = make_pitch()

event = st.plotly_chart(fig, on_select="rerun", use_container_width=True)

if event and "selection" in event and event["selection"].get("points"):
    p = event["selection"]["points"][0]
    st.session_state.x = round(float(p["x"]),1)
    st.session_state.y = round(float(p["y"]),1)

st.subheader("Coordinates")

st.code(f"x = {st.session_state.x}")
st.code(f"y = {st.session_state.y}")

st.write("Χρησιμοποίησε αυτά τα νούμερα στο CSV.")
