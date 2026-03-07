import io
import os
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Player Shot Maps", layout="wide")

DATA_FILE = "season_shots.csv"

RESULT_COLORS = {
    "Goal": "green",
    "Saved": "orange",
    "Blocked": "red",
    "Miss": "gray"
}

REQUIRED_COLUMNS = ["player", "x", "y", "result"]

OPTIONAL_COLUMNS = [
    "team", "season", "opponent", "date", "minute",
    "xg", "shot_type", "body_part"
]


@st.cache_data
def load_data():
    if not os.path.exists(DATA_FILE):
        return pd.DataFrame(columns=REQUIRED_COLUMNS + OPTIONAL_COLUMNS)

    df = pd.read_csv(DATA_FILE)

    for col in REQUIRED_COLUMNS + OPTIONAL_COLUMNS:
        if col not in df.columns:
            df[col] = np.nan

    df["x"] = pd.to_numeric(df["x"], errors="coerce")
    df["y"] = pd.to_numeric(df["y"], errors="coerce")
    df["xg"] = pd.to_numeric(df["xg"], errors="coerce").fillna(0)

    return df


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
    ax.scatter([89], [50], s=20, color="black")

    # Penalty arc
    theta = np.linspace(-0.95, 0.95, 200)
    r = 8.7
    x_arc = 89 - r * np.cos(theta)
    y_arc = 50 + r * np.sin(theta)
    mask = x_arc <= 84
    ax.plot(x_arc[mask], y_arc[mask], linewidth=2, color="black")


def get_zone(x, y):
    if x >= 94 and 37 <= y <= 63:
        return "Small Box"
    if x >= 84 and 37 <= y <= 63:
        return "Central Box"
    if x >= 84 and y < 37:
        return "Right Side Box"
    if x >= 84 and y > 63:
        return "Left Side Box"
    if x < 84 and 30 <= y <= 70:
        return "Central Outside Box"
    if x < 84 and y < 30:
        return "Right Outside Box"
    return "Left Outside Box"


def enrich_df(df):
    d = df.copy()
    if len(d) == 0:
        return d

    d["x"] = pd.to_numeric(d["x"], errors="coerce")
    d["y"] = pd.to_numeric(d["y"], errors="coerce")
    d["xg"] = pd.to_numeric(d["xg"], errors="coerce").fillna(0)
    d["is_goal"] = d["result"].astype(str).str.lower().eq("goal")
    d["zone"] = d.apply(lambda r: get_zone(r["x"], r["y"]), axis=1)
    return d


def build_player_shot_map(df, player_name):
    fig, ax = plt.subplots(figsize=(8, 10))
    draw_half_pitch(ax)
    ax.set_title(f"{player_name} — Shot Map", fontsize=16)

    if len(df) > 0:
        d = enrich_df(df)
        for _, row in d.iterrows():
            color = RESULT_COLORS.get(str(row["result"]), "gray")
            marker = "*" if row["is_goal"] else "o"
            size = (row["xg"] * 900) + 50

            ax.scatter(
                row["x"],
                row["y"],
                s=size,
                marker=marker,
                color=color,
                alpha=0.80,
                edgecolors="black",
                linewidths=0.5
            )

    return fig


def fig_to_png_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    buf.seek(0)
    return buf.getvalue()


def player_stats(df):
    if len(df) == 0:
        return {
            "shots": 0,
            "goals": 0,
            "xg": 0.0,
            "xg_per_shot": 0.0
        }

    d = enrich_df(df)
    shots = len(d)
    goals = int(d["is_goal"].sum())
    xg = float(d["xg"].sum())
    xg_per_shot = xg / shots if shots > 0 else 0.0

    return {
        "shots": shots,
        "goals": goals,
        "xg": round(xg, 2),
        "xg_per_shot": round(xg_per_shot, 3)
    }


def zone_table(df):
    if len(df) == 0:
        return pd.DataFrame(columns=["zone", "shots", "goals", "xg"])

    d = enrich_df(df)
    out = d.groupby("zone", as_index=False).agg(
        shots=("zone", "size"),
        goals=("is_goal", "sum"),
        xg=("xg", "sum")
    )
    out["xg"] = out["xg"].round(2)
    return out.sort_values(["shots", "xg"], ascending=False)


def shots_by_result(df):
    if len(df) == 0:
        return pd.DataFrame(columns=["result", "shots"])

    out = df.groupby("result", as_index=False).size()
    out.columns = ["result", "shots"]
    return out.sort_values("shots", ascending=False)


st.title("⚽ Player Shot Maps")
st.caption("Shot maps ανά παίκτη για όλη τη σεζόν.")

df = load_data()

if len(df) == 0:
    st.warning("Δεν βρέθηκε το αρχείο season_shots.csv ή είναι κενό.")
    st.stop()

players = sorted(df["player"].dropna().astype(str).unique().tolist())

with st.sidebar:
    st.header("Filters")

    selected_player = st.selectbox("Player", players)

    seasons = sorted(df["season"].dropna().astype(str).unique().tolist())
    selected_seasons = st.multiselect("Season", seasons, default=seasons) if seasons else []

    shot_types = sorted(df["shot_type"].dropna().astype(str).unique().tolist())
    selected_shot_types = st.multiselect("Shot Type", shot_types, default=shot_types) if shot_types else []

    body_parts = sorted(df["body_part"].dropna().astype(str).unique().tolist())
    selected_body_parts = st.multiselect("Body Part", body_parts, default=body_parts) if body_parts else []

    results = sorted(df["result"].dropna().astype(str).unique().tolist())
    selected_results = st.multiselect("Result", results, default=results)

player_df = df[df["player"].astype(str) == selected_player].copy()

if selected_seasons:
    player_df = player_df[player_df["season"].astype(str).isin(selected_seasons)]

if selected_shot_types:
    player_df = player_df[player_df["shot_type"].astype(str).isin(selected_shot_types)]

if selected_body_parts:
    player_df = player_df[player_df["body_part"].astype(str).isin(selected_body_parts)]

if selected_results:
    player_df = player_df[player_df["result"].astype(str).isin(selected_results)]

stats = player_stats(player_df)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Shots", stats["shots"])
k2.metric("Goals", stats["goals"])
k3.metric("xG", stats["xg"])
k4.metric("xG / Shot", stats["xg_per_shot"])

left, right = st.columns([1.15, 0.85])

with left:
    fig = build_player_shot_map(player_df, selected_player)
    st.pyplot(fig, clear_figure=False)

    png_bytes = fig_to_png_bytes(fig)
    st.download_button(
        "⬇️ Download Shot Map PNG",
        data=png_bytes,
        file_name=f"{selected_player}_shot_map.png",
        mime="image/png"
    )

with right:
    st.subheader("Shot Zones")
    st.dataframe(zone_table(player_df), use_container_width=True, height=250)

    st.subheader("By Result")
    st.dataframe(shots_by_result(player_df), use_container_width=True, height=180)

st.subheader("Shots Table")
show_cols = [c for c in [
    "date", "opponent", "minute", "x", "y", "xg", "result", "shot_type", "body_part"
] if c in player_df.columns]

st.dataframe(
    player_df[show_cols].reset_index(drop=True),
    use_container_width=True,
    height=320
)
