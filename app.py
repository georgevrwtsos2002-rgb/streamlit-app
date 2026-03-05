import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import StringIO

st.set_page_config(page_title="Football Shot Map Dashboard", layout="wide")

REQUIRED = ["team", "player", "minute", "x", "y", "result"]
OPTIONAL = ["xg", "shot_type", "match_id", "competition", "season", "date", "home", "away"]

def make_template_df():
    return pd.DataFrame([
        {
            "match_id": 1,
            "competition": "Greece - Super League",
            "season": "2025-26",
            "date": "2026-03-05",
            "home": "Panathinaikos",
            "away": "Opponent",
            "team": "Panathinaikos",
            "player": "Player A",
            "minute": 12,
            "x": 88,
            "y": 46,
            "xg": 0.24,
            "result": "Goal",
            "shot_type": "Open Play",
        },
        {
            "match_id": 1,
            "competition": "Greece - Super League",
            "season": "2025-26",
            "date": "2026-03-05",
            "home": "Panathinaikos",
            "away": "Opponent",
            "team": "Opponent",
            "player": "Player X",
            "minute": 35,
            "x": 82,
            "y": 61,
            "xg": 0.08,
            "result": "Saved",
            "shot_type": "Open Play",
        },
    ])

def validate(df: pd.DataFrame):
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        return False, f"Λείπουν columns: {missing}. Απαιτούνται: {REQUIRED}"
    try:
        df["minute"] = pd.to_numeric(df["minute"])
        df["x"] = pd.to_numeric(df["x"])
        df["y"] = pd.to_numeric(df["y"])
        if "xg" in df.columns:
            df["xg"] = pd.to_numeric(df["xg"])
    except Exception:
        return False, "minute/x/y (και xg αν υπάρχει) πρέπει να είναι αριθμοί."
    # bounds
    if ((df["x"] < 0) | (df["x"] > 100) | (df["y"] < 0) | (df["y"] > 100)).any():
        return False, "Οι συντεταγμένες x,y πρέπει να είναι στο εύρος 0–100."
    return True, ""

def draw_pitch(ax):
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    ax.plot([0, 100, 100, 0, 0], [0, 0, 100, 100, 0], linewidth=2)
    ax.plot([50, 50], [0, 100], linewidth=2)
    cc = plt.Circle((50, 50), 8.7, fill=False, linewidth=2)
    ax.add_patch(cc)

def shot_map(df, title="Shot Map"):
    fig, ax = plt.subplots(figsize=(10, 6))
    draw_pitch(ax)

    is_goal = df["result"].astype(str).str.lower().eq("goal")

    if "xg" in df.columns:
        sizes = (df["xg"].clip(0, 1) * 900) + 30
    else:
        sizes = 120

    ax.scatter(df.loc[~is_goal, "x"], df.loc[~is_goal, "y"], s=sizes if np.isscalar(sizes) else sizes[~is_goal],
               alpha=0.65, marker="o", linewidths=0)
    ax.scatter(df.loc[is_goal, "x"], df.loc[is_goal, "y"], s=sizes if np.isscalar(sizes) else sizes[is_goal],
               alpha=0.9, marker="*", linewidths=0)

    ax.set_title(title)
    st.pyplot(fig, clear_figure=True)

def player_stats(df):
    d = df.copy()
    d["is_goal"] = d["result"].astype(str).str.lower().eq("goal")
    d["is_sot"] = d["result"].astype(str).str.lower().isin(["goal", "saved"])
    agg = d.groupby(["team", "player"], as_index=False).agg(
        shots=("player", "size"),
        goals=("is_goal", "sum"),
        sot=("is_sot", "sum"),
        xg=("xg", "sum") if "xg" in d.columns else ("is_goal", "sum"),
    )
    if "xg" in d.columns:
        agg["xg_per_shot"] = (agg["xg"] / agg["shots"]).round(3)
    agg["sot_pct"] = (100 * agg["sot"] / agg["shots"]).round(1)
    return agg.sort_values(["shots", "goals"], ascending=False)

st.title("⚽ Football Shot Map Dashboard (Super League-ready)")

# Template download
tmpl = make_template_df()
csv_bytes = tmpl.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Κατέβασε CSV template", data=csv_bytes, file_name="shots_template.csv", mime="text/csv")

with st.sidebar:
    st.header("Input")
    uploaded = st.file_uploader("Upload shots CSV", type=["csv"])
    paste_mode = st.checkbox("Ή κάνε Paste δεδομένα (CSV text)", value=False)

df = None

if paste_mode:
    st.info("Κάνε paste CSV text εδώ (με header). Π.χ. team,player,minute,x,y,result,xg")
    raw = st.text_area("Paste CSV", height=180)
    if raw.strip():
        df = pd.read_csv(StringIO(raw))
elif uploaded:
    df = pd.read_csv(uploaded)
else:
    st.caption("Ανέβασε CSV ή κάνε paste. Μπορείς να ξεκινήσεις με το template.")

if df is None:
    st.stop()

ok, msg = validate(df)
if not ok:
    st.error(msg)
    st.stop()

# Ensure optional columns exist
for c in OPTIONAL:
    if c not in df.columns:
        df[c] = np.nan

# Filters (incl. Super League)
with st.sidebar:
    st.header("Filters")
    comp_values = sorted(df["competition"].dropna().astype(str).unique().tolist())
    if comp_values:
        default_comp = [c for c in comp_values if "super league" in c.lower() or "greece" in c.lower()] or comp_values
        comp_sel = st.multiselect("Competition", comp_values, default=default_comp)
        df = df[df["competition"].astype(str).isin(comp_sel)]
    teams = sorted(df["team"].astype(str).unique().tolist())
    team_sel = st.multiselect("Team", teams, default=teams)

df_f = df[df["team"].astype(str).isin(team_sel)].copy()

# KPIs
shots = len(df_f)
goals = (df_f["result"].astype(str).str.lower() == "goal").sum()
sot = df_f["result"].astype(str).str.lower().isin(["goal", "saved"]).sum()
xg_sum = float(df_f["xg"].sum()) if "xg" in df_f.columns and df_f["xg"].notna().any() else None

c1, c2, c3, c4 = st.columns(4)
c1.metric("Shots", int(shots))
c2.metric("Goals", int(goals))
c3.metric("SoT%", round((100 * sot / shots), 1) if shots else 0.0)
c4.metric("xG", round(xg_sum, 2) if xg_sum is not None else "—")

st.divider()
left, right = st.columns([1.2, 0.8])
with left:
    title = "Shot Map"
    shot_map(df_f, title=title)
    st.caption("★=Goal, ●=Other. Αν έχεις xG, το μέγεθος του marker μεγαλώνει.")
with right:
    st.subheader("Player stats")
    st.dataframe(player_stats(df_f), use_container_width=True, height=420)

st.subheader("Raw data (filtered)")
st.dataframe(df_f.reset_index(drop=True), use_container_width=True, height=320)
