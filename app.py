import io
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go

st.set_page_config(page_title="Super League Shot Map Tool", layout="wide")

SUPER_LEAGUE_TEAMS = [
    "Panathinaikos",
    "Olympiacos",
    "AEK",
    "PAOK",
    "Aris",
    "Asteras Tripolis",
    "Atromitos",
    "OFI",
    "Panetolikos",
    "Kifisia",
    "Volos",
    "Panseraikos",
    "Levadiakos",
    "AEL",
]

RESULTS = ["Goal", "Miss", "Saved", "Blocked"]
SHOT_TYPES = ["Open Play", "Set Piece", "Penalty", "Counter", "Header", "Other"]


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
        xg = float(row["xg"])
    except Exception:
        return False, "minute / x / y / xg πρέπει να είναι αριθμοί."

    if not (50 <= x <= 100):
        return False, "Το x πρέπει να είναι 50–100."
    if not (0 <= y <= 100):
        return False, "Το y πρέπει να είναι 0–100."
    if not (0 <= minute <= 130):
        return False, "Το minute πρέπει να είναι 0–130."
    if not (0 <= xg <= 1):
        return False, "Το xg πρέπει να είναι 0–1."

    if str(row["team"]).strip() == "":
        return False, "Το team δεν μπορεί να είναι κενό."
    if str(row["player"]).strip() == "":
        return False, "Το player δεν μπορεί να είναι κενό."
    if row["result"] not in RESULTS:
        return False, "Μη έγκυρο result."

    return True, ""


def get_zone(x: float, y: float) -> str:
    # Small box
    if x >= 94 and 37 <= y <= 63:
        return "Small Box"
    # Penalty box center
    if x >= 84 and 37 <= y <= 63:
        return "Central Box"
    # Penalty box left/right
    if x >= 84 and y < 37:
        return "Right Side Box"
    if x >= 84 and y > 63:
        return "Left Side Box"
    # Outside box
    if x < 84 and 30 <= y <= 70:
        return "Central Outside Box"
    if x < 84 and y < 30:
        return "Right Outside Box"
    return "Left Outside Box"


def enrich_df(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) == 0:
        return df.copy()

    out = df.copy()
    out["minute"] = pd.to_numeric(out["minute"], errors="coerce")
    out["x"] = pd.to_numeric(out["x"], errors="coerce")
    out["y"] = pd.to_numeric(out["y"], errors="coerce")
    out["xg"] = pd.to_numeric(out["xg"], errors="coerce").fillna(0)
    out["is_goal"] = out["result"].astype(str).str.lower().eq("goal")
    out["zone"] = out.apply(lambda r: get_zone(r["x"], r["y"]), axis=1)
    return out


def draw_half_pitch_matplotlib(ax):
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
    ax.scatter([89], [50], s=22, color="black")

    # Penalty arc
    theta = np.linspace(-0.95, 0.95, 200)
    r = 8.7
    x_arc = 89 - r * np.cos(theta)
    y_arc = 50 + r * np.sin(theta)
    mask = x_arc <= 84
    ax.plot(x_arc[mask], y_arc[mask], linewidth=2, color="black")


def shot_color(result: str) -> str:
    result = str(result).lower()
    if result == "goal":
        return "green"
    if result == "saved":
        return "orange"
    if result == "blocked":
        return "red"
    return "gray"


def build_shot_map_figure(df: pd.DataFrame, title: str = "Shot Map"):
    fig, ax = plt.subplots(figsize=(8, 10))
    draw_half_pitch_matplotlib(ax)
    ax.set_title(title, fontsize=16)

    if len(df) > 0:
        d = enrich_df(df)
        for _, row in d.iterrows():
            marker = "*" if row["is_goal"] else "o"
            size = (row["xg"] * 900) + 50
            ax.scatter(
                row["x"], row["y"],
                s=size,
                marker=marker,
                color=shot_color(row["result"]),
                alpha=0.8,
                edgecolors="black",
                linewidths=0.5
            )

    return fig


def make_half_pitch_figure():
    fig = go.Figure()

    # Outer boundary
    fig.add_trace(go.Scatter(
        x=[50, 100, 100, 50, 50],
        y=[0, 0, 100, 100, 0],
        mode="lines",
        hoverinfo="skip",
        showlegend=False
    ))

    # Penalty area
    fig.add_trace(go.Scatter(
        x=[100, 84, 84, 100],
        y=[21, 21, 79, 79],
        mode="lines",
        hoverinfo="skip",
        showlegend=False
    ))

    # Small box
    fig.add_trace(go.Scatter(
        x=[100, 94, 94, 100],
        y=[37, 37, 63, 63],
        mode="lines",
        hoverinfo="skip",
        showlegend=False
    ))

    # Goal
    fig.add_trace(go.Scatter(
        x=[100, 102, 102, 100],
        y=[45, 45, 55, 55],
        mode="lines",
        hoverinfo="skip",
        showlegend=False
    ))

    # Penalty spot
    fig.add_trace(go.Scatter(
        x=[89], y=[50],
        mode="markers",
        marker=dict(size=6),
        hoverinfo="skip",
        showlegend=False
    ))

    # Penalty arc
    theta = np.linspace(-0.95, 0.95, 200)
    r = 8.7
    x_arc = 89 - r * np.cos(theta)
    y_arc = 50 + r * np.sin(theta)
    mask = x_arc <= 84
    fig.add_trace(go.Scatter(
        x=x_arc[mask],
        y=y_arc[mask],
        mode="lines",
        hoverinfo="skip",
        showlegend=False
    ))

    # Invisible grid for selection
    xs = np.arange(50, 101, 1)
    ys = np.arange(0, 101, 1)
    grid_x, grid_y = np.meshgrid(xs, ys)
    fig.add_trace(go.Scatter(
        x=grid_x.ravel(),
        y=grid_y.ravel(),
        mode="markers",
        marker=dict(size=10, opacity=0.01),
        hovertemplate="x=%{x}<br>y=%{y}<extra></extra>",
        showlegend=False
    ))

    # Selected point
    fig.add_trace(go.Scatter(
        x=[st.session_state.selected_x],
        y=[st.session_state.selected_y],
        mode="markers",
        marker=dict(size=14, symbol="x"),
        hovertemplate="Selected: x=%{x}, y=%{y}<extra></extra>",
        showlegend=False
    ))

    fig.update_layout(
        height=700,
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(range=[50, 103], visible=False),
        yaxis=dict(range=[0, 100], visible=False, scaleanchor="x", scaleratio=1),
        dragmode="select"
    )
    return fig


def player_stats_table(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) == 0:
        return pd.DataFrame(columns=["team", "player", "shots", "goals", "xg", "sot", "sot_pct"])

    d = enrich_df(df)
    d["is_sot"] = d["result"].astype(str).str.lower().isin(["goal", "saved"])

    out = d.groupby(["team", "player"], as_index=False).agg(
        shots=("player", "size"),
        goals=("is_goal", "sum"),
        xg=("xg", "sum"),
        sot=("is_sot", "sum"),
    )
    out["sot_pct"] = (100 * out["sot"] / out["shots"]).round(1)
    out["xg"] = out["xg"].round(2)
    return out.sort_values(["xg", "shots"], ascending=False)


def zone_stats_table(df: pd.DataFrame) -> pd.DataFrame:
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


def xg_by_team(df: pd.DataFrame) -> pd.DataFrame:
    if len(df) == 0:
        return pd.DataFrame(columns=["team", "shots", "goals", "xg"])

    d = enrich_df(df)
    out = d.groupby("team", as_index=False).agg(
        shots=("team", "size"),
        goals=("is_goal", "sum"),
        xg=("xg", "sum")
    )
    out["xg"] = out["xg"].round(2)
    return out.sort_values("xg", ascending=False)


def fig_to_png_bytes(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=200, bbox_inches="tight")
    buf.seek(0)
    return buf.getvalue()


init_state()

st.title("⚽ Super League Shot Map Tool")
st.caption("Public-ready εργαλείο για καταχώρηση και ανάλυση σουτ.")

with st.sidebar:
    st.header("Match Setup")

    match_id = st.text_input("match_id", value="1")
    season = st.text_input("season", value="2025-26")
    date = st.text_input("date", value="")

    home = st.selectbox("Home", SUPER_LEAGUE_TEAMS, index=0)
    away_options = [t for t in SUPER_LEAGUE_TEAMS if t != home]
    away = st.selectbox("Away", away_options, index=1 if len(away_options) > 1 else 0)

    competition = st.text_input("competition", value="Greece - Super League")

    st.divider()
    st.header("Save / Load")

    uploaded_saved_file = st.file_uploader("Load previous CSV", type=["csv"])
    if uploaded_saved_file is not None:
        loaded_df = pd.read_csv(uploaded_saved_file)
        st.session_state.shots = loaded_df
        st.success("✅ Η προηγούμενη δουλειά φορτώθηκε.")

    csv_bytes = st.session_state.shots.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download all shots as CSV",
        data=csv_bytes,
        file_name="superleague_shots.csv",
        mime="text/csv"
    )

    if st.button("🗑️ Reset all data"):
        st.session_state.shots = st.session_state.shots.iloc[0:0]
        st.success("Καθαρίστηκαν όλα τα δεδομένα.")

left, right = st.columns([1.15, 0.85])

with left:
    st.subheader("Pitch Selector")

    pitch_fig = make_half_pitch_figure()
    event = st.plotly_chart(
        pitch_fig,
        key="pitch_selector",
        on_select="rerun",
        use_container_width=True
    )

    if event and "selection" in event and event["selection"].get("points"):
        p = event["selection"]["points"][0]
        x_val = float(p["x"])
        y_val = float(p["y"])
        if 50 <= x_val <= 100 and 0 <= y_val <= 100:
            st.session_state.selected_x = round(x_val, 1)
            st.session_state.selected_y = round(y_val, 1)

    st.info(f"Selected point: x={st.session_state.selected_x}, y={st.session_state.selected_y}")

with right:
    st.subheader("Add Shot")

    with st.form("add_shot_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        team = c1.selectbox("Team", [home, away])
        player = c2.text_input("Player")

        c3, c4 = st.columns(2)
        minute = c3.number_input("Minute", min_value=0, max_value=130, value=1, step=1)
        result = c4.selectbox("Result", RESULTS)

        c5, c6 = st.columns(2)
        x = c5.number_input("x", min_value=50.0, max_value=100.0, value=float(st.session_state.selected_x), step=0.5)
        y = c6.number_input("y", min_value=0.0, max_value=100.0, value=float(st.session_state.selected_y), step=0.5)

        c7, c8 = st.columns(2)
        xg = c7.number_input("xG", min_value=0.0, max_value=1.0, value=0.10, step=0.01)
        shot_type = c8.selectbox("Shot Type", SHOT_TYPES)

        submitted = st.form_submit_button("Add Shot")

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

    st.subheader("Quick Actions")
    a1, a2 = st.columns(2)
    if a1.button("↩️ Remove last shot"):
        if len(st.session_state.shots) > 0:
            st.session_state.shots = st.session_state.shots.iloc[:-1]
            st.success("Αφαιρέθηκε το τελευταίο σουτ.")
    if a2.button("Load demo match"):
        demo = pd.DataFrame([
            {"match_id": 1, "competition": "Greece - Super League", "season": "2025-26", "date": "2026-03-06",
             "home": home, "away": away, "team": home, "player": "Player A", "minute": 12, "x": 95, "y": 50, "xg": 0.42, "result": "Goal", "shot_type": "Open Play"},
            {"match_id": 1, "competition": "Greece - Super League", "season": "2025-26", "date": "2026-03-06",
             "home": home, "away": away, "team": home, "player": "Player B", "minute": 33, "x": 87, "y": 60, "xg": 0.12, "result": "Saved", "shot_type": "Open Play"},
            {"match_id": 1, "competition": "Greece - Super League", "season": "2025-26", "date": "2026-03-06",
             "home": home, "away": away, "team": away, "player": "Player X", "minute": 55, "x": 82, "y": 46, "xg": 0.08, "result": "Miss", "shot_type": "Set Piece"},
        ])
        st.session_state.shots = demo
        st.success("✅ Demo loaded.")

st.divider()

shots_df = st.session_state.shots.copy()

st.subheader("Filters")
f1, f2, f3 = st.columns(3)

team_filter = f1.multiselect(
    "Filter by Team",
    sorted(shots_df["team"].dropna().astype(str).unique().tolist()) if len(shots_df) > 0 else [],
    default=sorted(shots_df["team"].dropna().astype(str).unique().tolist()) if len(shots_df) > 0 else []
)

player_filter = f2.multiselect(
    "Filter by Player",
    sorted(shots_df["player"].dropna().astype(str).unique().tolist()) if len(shots_df) > 0 else [],
    default=sorted(shots_df["player"].dropna().astype(str).unique().tolist()) if len(shots_df) > 0 else []
)

result_filter = f3.multiselect(
    "Filter by Result",
    RESULTS,
    default=RESULTS
)

filtered = shots_df.copy()
if len(filtered) > 0:
    if team_filter:
        filtered = filtered[filtered["team"].astype(str).isin(team_filter)]
    if player_filter:
        filtered = filtered[filtered["player"].astype(str).isin(player_filter)]
    if result_filter:
        filtered = filtered[filtered["result"].astype(str).isin(result_filter)]

d = enrich_df(filtered)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Shots", int(len(d)))
k2.metric("Goals", int(d["is_goal"].sum()) if len(d) > 0 else 0)
k3.metric("xG", round(float(d["xg"].sum()), 2) if len(d) > 0 else 0.0)
k4.metric("Teams", int(d["team"].nunique()) if len(d) > 0 else 0)

st.divider()

c1, c2 = st.columns([1.1, 0.9])

with c1:
    st.subheader("Shot Map")
    map_fig = build_shot_map_figure(d, title=f"{home} vs {away} — Shot Map")
    st.pyplot(map_fig, clear_figure=False)

    png_bytes = fig_to_png_bytes(map_fig)
    st.download_button(
        "⬇️ Export Shot Map PNG",
        data=png_bytes,
        file_name="shot_map.png",
        mime="image/png"
    )

with c2:
    st.subheader("xG by Team")
    st.dataframe(xg_by_team(d), use_container_width=True, height=180)

    st.subheader("Shot Zones")
    st.dataframe(zone_stats_table(d), use_container_width=True, height=220)

st.subheader("Player Stats")
st.dataframe(player_stats_table(d), use_container_width=True, height=250)

st.subheader("Shots Table")
st.dataframe(d.drop(columns=["is_goal", "zone"], errors="ignore"), use_container_width=True, height=300)
