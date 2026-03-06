import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go

st.set_page_config(page_title="Super League Shot Helper", layout="wide")

RESULTS = ["Goal", "Miss", "Saved", "Blocked"]

# ---------------------------
# Helpers
# ---------------------------
def init_state():
    if "shots" not in st.session_state:
        st.session_state.shots = pd.DataFrame(columns=[
            "match_id", "competition", "season", "date", "home", "away",
            "team", "player", "minute", "x", "y", "xg", "result", "shot_type"
        ])
    if "selected_x" not in st.session_state:
        st.session_state.selected_x = 88.0
    if "selected_y" not in st.session_state:
        st.session_state.selected_y = 50.0

def validate_row(row: dict) -> tuple[bool, str]:
    try:
        minute = float(row["minute"])
        x = float(row["x"])
        y = float(row["y"])
        if not (0 <= x <= 100 and 0 <= y <= 100):
            return False, "Το x και το y πρέπει να είναι από 0 έως 100."
        if minute < 0 or minute > 130:
            return False, "Το minute πρέπει να είναι από 0 έως 130."
    except Exception:
        return False, "minute / x / y πρέπει να είναι αριθμοί."

    if str(row["team"]).strip() == "" or str(row["player"]).strip() == "":
        return False, "Τα team και player δεν μπορούν να είναι κενά."

    if row["result"] not in RESULTS:
        return False, f"Το result πρέπει να είναι ένα από: {RESULTS}"

    try:
        xg = float(row["xg"])
        if not (0 <= xg <= 1):
            return False, "Το xg πρέπει να είναι από 0 έως 1."
    except Exception:
        return False, "Το xg πρέπει να είναι αριθμός."

    return True, ""

def draw_pitch_matplotlib(ax):
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")

    # Outer lines
    ax.plot([0, 100, 100, 0, 0], [0, 0, 100, 100, 0], linewidth=2)
    # Halfway line
    ax.plot([50, 50], [0, 100], linewidth=2)
    # Center circle
    ax.add_patch(plt.Circle((50, 50), 8.7, fill=False, linewidth=2))

    # Penalty boxes
    ax.plot([0, 16], [21, 21], linewidth=2)
    ax.plot([16, 16], [21, 79], linewidth=2)
    ax.plot([16, 0], [79, 79], linewidth=2)

    ax.plot([100, 84], [21, 21], linewidth=2)
    ax.plot([84, 84], [21, 79], linewidth=2)
    ax.plot([84, 100], [79, 79], linewidth=2)

# 6-yard boxes (small boxes)
ax.plot([0, 6], [37, 37], linewidth=2)
ax.plot([6, 6], [37, 63], linewidth=2)
ax.plot([6, 0], [63, 63], linewidth=2)

ax.plot([100, 94], [37, 37], linewidth=2)
ax.plot([94, 94], [37, 63], linewidth=2)
ax.plot([94, 100], [63, 63], linewidth=2)

def shot_map(df, title="Shot Map"):
    fig, ax = plt.subplots(figsize=(10, 6))
    draw_pitch_matplotlib(ax)

    if len(df) == 0:
        ax.set_title(title)
        st.pyplot(fig, clear_figure=True)
        return

    is_goal = df["result"].astype(str).str.lower().eq("goal")
    sizes = (pd.to_numeric(df["xg"], errors="coerce").fillna(0).clip(0, 1) * 900) + 40

    ax.scatter(
        df.loc[~is_goal, "x"], df.loc[~is_goal, "y"],
        s=sizes[~is_goal], alpha=0.65, marker="o", linewidths=0
    )
    ax.scatter(
        df.loc[is_goal, "x"], df.loc[is_goal, "y"],
        s=sizes[is_goal], alpha=0.9, marker="*", linewidths=0
    )

    ax.set_title(title)
    st.pyplot(fig, clear_figure=True)

def make_pitch_figure():
    fig = go.Figure()

    # Pitch lines
    pitch_x = [0, 100, 100, 0, 0]
    pitch_y = [0, 0, 100, 100, 0]
    fig.add_trace(go.Scatter(
        x=pitch_x, y=pitch_y, mode="lines", name="Pitch",
        hoverinfo="skip", showlegend=False
    ))

    fig.add_trace(go.Scatter(
        x=[50, 50], y=[0, 100], mode="lines",
        hoverinfo="skip", showlegend=False
    ))

    # Center circle (approx)
    theta = np.linspace(0, 2 * np.pi, 200)
    cx = 50 + 8.7 * np.cos(theta)
    cy = 50 + 8.7 * np.sin(theta)
    fig.add_trace(go.Scatter(
        x=cx, y=cy, mode="lines",
        hoverinfo="skip", showlegend=False
    ))

    # Penalty boxes
    fig.add_trace(go.Scatter(x=[0, 16, 16, 0], y=[21, 21, 79, 79], mode="lines", hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=[100, 84, 84, 100], y=[21, 21, 79, 79], mode="lines", hoverinfo="skip", showlegend=False))

    # 6-yard boxes (small boxes)
fig.add_trace(go.Scatter(
    x=[0, 6, 6, 0],
    y=[37, 37, 63, 63],
    mode="lines",
    hoverinfo="skip",
    showlegend=False
))

fig.add_trace(go.Scatter(
    x=[100, 94, 94, 100],
    y=[37, 37, 63, 63],
    mode="lines",
    hoverinfo="skip",
    showlegend=False
))

    # Clickable grid points
    xs = np.arange(0, 101, 1)
    ys = np.arange(0, 101, 1)
    grid_x, grid_y = np.meshgrid(xs, ys)

    fig.add_trace(go.Scatter(
        x=grid_x.ravel(),
        y=grid_y.ravel(),
        mode="markers",
        marker=dict(size=8, opacity=0.01),
        customdata=np.column_stack([grid_x.ravel(), grid_y.ravel()]),
        hovertemplate="x=%{x}<br>y=%{y}<extra></extra>",
        name="click-grid",
        showlegend=False
    ))

    # Current selected point
    fig.add_trace(go.Scatter(
        x=[st.session_state.selected_x],
        y=[st.session_state.selected_y],
        mode="markers",
        marker=dict(size=14, symbol="x"),
        name="selected",
        showlegend=False,
        hovertemplate="Selected: x=%{x}, y=%{y}<extra></extra>"
    ))

    fig.update_layout(
        height=600,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(range=[0, 100], showgrid=False, zeroline=False, visible=False),
        yaxis=dict(range=[0, 100], showgrid=False, zeroline=False, visible=False, scaleanchor="x", scaleratio=1),
        dragmode="select"
    )
    return fig

# ---------------------------
# App
# ---------------------------
init_state()

st.title("⚽ Super League Shot Helper")
st.caption("Κάνε κλικ πάνω στο γήπεδο για να ορίσεις το σημείο του σουτ.")

left, right = st.columns([1.1, 0.9])

with left:
    st.subheader("1) Επίλεξε σημείο σουτ πάνω στο γήπεδο")

    pitch_fig = make_pitch_figure()
    event = st.plotly_chart(
        pitch_fig,
        key="pitch_selector",
        on_select="rerun",
        use_container_width=True
    )

    # Read selected point from plotly selection
    if event and "selection" in event and event["selection"].get("points"):
        p = event["selection"]["points"][0]
        st.session_state.selected_x = round(float(p["x"]), 1)
        st.session_state.selected_y = round(float(p["y"]), 1)

    st.info(f"Επιλεγμένο σημείο: x={st.session_state.selected_x}, y={st.session_state.selected_y}")

with right:
    st.subheader("2) Στοιχεία αγώνα")
    c1, c2, c3, c4 = st.columns(4)
    match_id = c1.text_input("match_id", value="1")
    season = c2.text_input("season", value="2025-26")
    date = c3.text_input("date", value="")
    competition = c4.text_input("competition", value="Greece - Super League")

    c5, c6 = st.columns(2)
    home = c5.text_input("home", value="Panathinaikos")
    away = c6.text_input("away", value="Opponent")

    st.subheader("3) Στοιχεία σουτ")
    with st.form("add_shot_form", clear_on_submit=True):
        a1, a2, a3, a4 = st.columns(4)
        team = a1.text_input("team", value=home)
        player = a2.text_input("player")
        minute = a3.number_input("minute", min_value=0, max_value=130, value=1, step=1)
        result = a4.selectbox("result", RESULTS, index=1)

        b1, b2, b3, b4 = st.columns(4)
        x = b1.number_input("x", min_value=0.0, max_value=100.0, value=float(st.session_state.selected_x), step=0.5)
        y = b2.number_input("y", min_value=0.0, max_value=100.0, value=float(st.session_state.selected_y), step=0.5)
        xg = b3.number_input("xg", min_value=0.0, max_value=1.0, value=0.10, step=0.01)
        shot_type = b4.text_input("shot_type", value="Open Play")

        submitted = st.form_submit_button("Add shot")

    if submitted:
        row = {
            "match_id": match_id,
            "competition": competition,
            "season": season,
            "date": date if date else np.nan,
            "home": home,
            "away": away,
            "team": team,
            "player": player,
            "minute": minute,
            "x": x,
            "y": y,
            "xg": xg,
            "result": result,
            "shot_type": shot_type
        }

        ok, msg = validate_row(row)
        if not ok:
            st.error(msg)
        else:
            st.session_state.shots = pd.concat(
                [st.session_state.shots, pd.DataFrame([row])],
                ignore_index=True
            )
            st.success("✅ Το σουτ προστέθηκε.")

st.divider()

cA, cB, cC = st.columns(3)

if cA.button("↩️ Remove last shot"):
    if len(st.session_state.shots) > 0:
        st.session_state.shots = st.session_state.shots.iloc[:-1]
        st.success("Αφαιρέθηκε το τελευταίο σουτ.")
    else:
        st.info("Δεν υπάρχουν σουτ.")

if cB.button("🗑️ Clear shots"):
    st.session_state.shots = st.session_state.shots.iloc[0:0]
    st.success("Καθαρίστηκαν όλα τα σουτ.")

csv_bytes = st.session_state.shots.to_csv(index=False).encode("utf-8")
cC.download_button(
    "⬇️ Download CSV",
    data=csv_bytes,
    file_name="superleague_shots.csv",
    mime="text/csv"
)

st.subheader("Shots table")
st.dataframe(st.session_state.shots, use_container_width=True, height=260)

st.subheader("Shot map")
shot_map(st.session_state.shots, title="Shot Map")
