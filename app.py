import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Super League Shot Helper", layout="wide")

REQUIRED = ["team", "player", "minute", "x", "y", "result"]
RESULTS = ["Goal", "Miss", "Saved", "Blocked"]

def draw_pitch(ax):
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    ax.plot([0, 100, 100, 0, 0], [0, 0, 100, 100, 0], linewidth=2)
    ax.plot([50, 50], [0, 100], linewidth=2)
    ax.add_patch(plt.Circle((50, 50), 8.7, fill=False, linewidth=2))

def shot_map(df, title="Shot Map"):
    fig, ax = plt.subplots(figsize=(10, 6))
    draw_pitch(ax)

    is_goal = df["result"].astype(str).str.lower().eq("goal")
    if "xg" in df.columns and df["xg"].notna().any():
        sizes = (pd.to_numeric(df["xg"], errors="coerce").fillna(0).clip(0, 1) * 900) + 30
    else:
        sizes = 140

    ax.scatter(df.loc[~is_goal, "x"], df.loc[~is_goal, "y"],
               s=sizes if np.isscalar(sizes) else sizes[~is_goal],
               alpha=0.65, marker="o", linewidths=0)
    ax.scatter(df.loc[is_goal, "x"], df.loc[is_goal, "y"],
               s=sizes if np.isscalar(sizes) else sizes[is_goal],
               alpha=0.9, marker="*", linewidths=0)

    ax.set_title(title)
    st.pyplot(fig, clear_figure=True)

def ensure_schema(df: pd.DataFrame) -> pd.DataFrame:
    for c in REQUIRED:
        if c not in df.columns:
            df[c] = np.nan
    for c in ["xg", "match_id", "competition", "season", "date", "home", "away", "shot_type"]:
        if c not in df.columns:
            df[c] = np.nan
    return df

def validate_row(row: dict) -> tuple[bool, str]:
    try:
        minute = float(row["minute"])
        x = float(row["x"])
        y = float(row["y"])
        if not (0 <= x <= 100 and 0 <= y <= 100):
            return False, "x και y πρέπει να είναι 0–100."
        if minute < 0 or minute > 130:
            return False, "minute πρέπει να είναι 0–130."
    except Exception:
        return False, "minute/x/y πρέπει να είναι αριθμοί."
    if str(row["team"]).strip() == "" or str(row["player"]).strip() == "":
        return False, "team και player δεν μπορεί να είναι κενά."
    if row["result"] not in RESULTS:
        return False, f"result πρέπει να είναι ένα από: {RESULTS}"
    if row.get("xg") not in [None, ""] and not pd.isna(row.get("xg")):
        try:
            xg = float(row["xg"])
            if not (0 <= xg <= 1):
                return False, "xg πρέπει να είναι 0–1."
        except Exception:
            return False, "xg πρέπει να είναι αριθμός."
    return True, ""

# ---------- State ----------
if "shots" not in st.session_state:
    st.session_state.shots = ensure_schema(pd.DataFrame(columns=[
        "match_id","competition","season","date","home","away",
        "team","player","minute","x","y","xg","result","shot_type"
    ]))

st.title("⚽ Super League Shot Helper")
st.caption("Καταχώρηση shots με φόρμα → αυτόματο shot map → export σε CSV")

# ---------- Input methods ----------
tabs = st.tabs(["➕ Helper (φόρμα)", "⬆️ Upload CSV", "🧪 Demo"])

with tabs[0]:
    st.subheader("Match info (προαιρετικά αλλά χρήσιμο)")
    c1, c2, c3, c4 = st.columns(4)
    match_id = c1.text_input("match_id", value="1")
    season = c2.text_input("season", value="2025-26")
    date = c3.text_input("date (YYYY-MM-DD)", value="")
    competition = c4.text_input("competition", value="Greece - Super League")

    c5, c6 = st.columns(2)
    home = c5.text_input("home", value="Panathinaikos")
    away = c6.text_input("away", value="Opponent")

    st.divider()
    st.subheader("Πρόσθεσε shot")

    with st.form("add_shot", clear_on_submit=True):
        a1, a2, a3, a4 = st.columns(4)
        team = a1.text_input("team", value=home)
        player = a2.text_input("player")
        minute = a3.number_input("minute", min_value=0, max_value=130, value=1, step=1)
        result = a4.selectbox("result", RESULTS, index=1)

        b1, b2, b3, b4 = st.columns(4)
        x = b1.number_input("x (0-100)", min_value=0.0, max_value=100.0, value=85.0, step=0.5)
        y = b2.number_input("y (0-100)", min_value=0.0, max_value=100.0, value=50.0, step=0.5)
        xg = b3.number_input("xg (0-1)", min_value=0.0, max_value=1.0, value=0.10, step=0.01)
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
            st.session_state.shots = pd.concat([st.session_state.shots, pd.DataFrame([row])], ignore_index=True)
            st.success("✅ Προστέθηκε!")

    st.divider()
    st.subheader("Shots table")
    st.dataframe(st.session_state.shots, use_container_width=True, height=260)

    cA, cB, cC = st.columns(3)
    if cA.button("🗑️ Clear shots"):
        st.session_state.shots = st.session_state.shots.iloc[0:0]
        st.success("Καθαρίστηκαν όλα.")

    if cB.button("↩️ Remove last shot"):
        if len(st.session_state.shots) > 0:
            st.session_state.shots = st.session_state.shots.iloc[:-1]
            st.success("Αφαιρέθηκε το τελευταίο.")
        else:
            st.info("Δεν υπάρχουν shots.")

    csv_bytes = st.session_state.shots.to_csv(index=False).encode("utf-8")
    cC.download_button("⬇️ Download CSV", data=csv_bytes, file_name="superleague_shots.csv", mime="text/csv")

    st.divider()
    if len(st.session_state.shots) > 0:
        shot_map(st.session_state.shots, title=f"Shot Map — {home} vs {away}")
    else:
        st.info("Πρόσθεσε τουλάχιστον 1 shot για να εμφανιστεί το shot map.")

with tabs[1]:
    st.subheader("Upload shots CSV")
    up = st.file_uploader("CSV", type=["csv"])
    if up:
        df = pd.read_csv(up)
        df = ensure_schema(df)
        st.session_state.shots = df
        st.success("✅ Φορτώθηκαν δεδομένα από CSV στο helper.")
        st.dataframe(df, use_container_width=True, height=300)
        if len(df) > 0:
            shot_map(df, title="Shot Map (from upload)")

with tabs[2]:
    st.subheader("Demo")
    if st.button("Load demo Super League match"):
        demo = pd.DataFrame([
            {"match_id": 1,"competition":"Greece - Super League","season":"2025-26","date":"2026-03-05",
             "home":"Panathinaikos","away":"Opponent","team":"Panathinaikos","player":"Player A","minute":12,"x":88,"y":46,"xg":0.24,"result":"Goal","shot_type":"Open Play"},
            {"match_id": 1,"competition":"Greece - Super League","season":"2025-26","date":"2026-03-05",
             "home":"Panathinaikos","away":"Opponent","team":"Panathinaikos","player":"Player B","minute":35,"x":84,"y":62,"xg":0.09,"result":"Saved","shot_type":"Open Play"},
            {"match_id": 1,"competition":"Greece - Super League","season":"2025-26","date":"2026-03-05",
             "home":"Panathinaikos","away":"Opponent","team":"Opponent","player":"Player X","minute":54,"x":81,"y":52,"xg":0.07,"result":"Miss","shot_type":"Open Play"},
        ])
        st.session_state.shots = ensure_schema(demo)
        st.success("✅ Demo loaded. Πήγαινε στο tab Helper.")
