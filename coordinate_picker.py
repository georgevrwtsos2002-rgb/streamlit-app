import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(page_title="Shot Coordinate Picker", layout="wide")

if "x" not in st.session_state:
    st.session_state.x = 89.0
if "y" not in st.session_state:
    st.session_state.y = 50.0


def draw_half_pitch(ax):
    ax.set_xlim(50, 103)
    ax.set_ylim(0, 100)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    # Outer lines
    ax.plot([50, 100], [0, 0], linewidth=2, color="black")
    ax.plot([50, 100], [100, 100], linewidth=2, color="black")
    ax.plot([50, 50], [0, 100], linewidth=2, color="black")
    ax.plot([100, 100], [0, 100], linewidth=2, color="black")

    # Penalty area
    ax.plot([84, 100], [21, 21], linewidth=2, color="black")
    ax.plot([84, 84], [21, 79], linewidth=2, color="black")
    ax.plot([84, 100], [79, 79], linewidth=2, color="black")

    # Small box
    ax.plot([94, 100], [37, 37], linewidth=2, color="black")
    ax.plot([94, 94], [37, 63], linewidth=2, color="black")
    ax.plot([94, 100], [63, 63], linewidth=2, color="black")

    # Goal
    ax.plot([100, 102], [45, 45], linewidth=2, color="black")
    ax.plot([102, 102], [45, 55], linewidth=2, color="black")
    ax.plot([102, 100], [55, 55], linewidth=2, color="black")

    # Penalty spot
    ax.scatter([89], [50], s=25, color="black")

    # Penalty arc
    theta = np.linspace(-0.95, 0.95, 200)
    r = 8.7
    x_arc = 89 - r * np.cos(theta)
    y_arc = 50 + r * np.sin(theta)
    mask = x_arc <= 84
    ax.plot(x_arc[mask], y_arc[mask], linewidth=2, color="black")


def make_figure(x, y):
    fig, ax = plt.subplots(figsize=(7, 10))
    draw_half_pitch(ax)

    # Selected point
    ax.scatter(
        [x], [y],
        s=180,
        color="red",
        edgecolors="black",
        linewidths=1.2,
        zorder=5
    )

    ax.text(
        51, 97,
        f"x={x:.1f}, y={y:.1f}",
        fontsize=12,
        verticalalignment="top"
    )

    return fig


st.title("⚽ Shot Coordinate Picker")
st.write("Χρησιμοποίησε τα sliders και δες live το σημείο του σουτ πάνω στο γήπεδο.")

col1, col2 = st.columns([0.35, 0.65])

with col1:
    st.subheader("Συντεταγμένες")

    x = st.slider(
        "x",
        min_value=50.0,
        max_value=100.0,
        value=float(st.session_state.x),
        step=0.5
    )

    y = st.slider(
        "y",
        min_value=0.0,
        max_value=100.0,
        value=float(st.session_state.y),
        step=0.5
    )

    st.session_state.x = x
    st.session_state.y = y

    st.code(f"x = {x}")
    st.code(f"y = {y}")

    st.markdown("**Χρήσιμος οδηγός**")
    st.write("89, 50 = πέναλτι")
    st.write("94-100 = μικρή περιοχή")
    st.write("84-100 = μέσα μεγάλη περιοχή")
    st.write("y κοντά στο 50 = πιο κεντρικά")
    st.write("y χαμηλά = δεξιά πλευρά")
    st.write("y ψηλά = αριστερή πλευρά")

with col2:
    st.subheader("Οπτικοποίηση")
    fig = make_figure(x, y)
    st.pyplot(fig, clear_figure=True)
