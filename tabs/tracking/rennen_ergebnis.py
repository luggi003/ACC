import streamlit as st
import pandas as pd
from utils.time_parser import parse_time_to_seconds


def get_best_lap_from_lap_times():
    laps = st.session_state.get("lap_times", [])

    valid_laps = [
        lap for lap in laps
        if lap.get("Sekunden") is not None and lap.get("Gültig", True)
    ]

    if not valid_laps:
        return None

    return min(valid_laps, key=lambda lap: lap["Sekunden"])


def show():
    st.header("Rennen Ergebnis")

    best_lap = get_best_lap_from_lap_times()

    if "race_table" not in st.session_state:
        st.session_state["race_table"] = pd.DataFrame(
            {
                "Pos": list(range(1, 11)),
                "Fahrer": [""] * 10,
                "Runden": [0] * 10,
                "Gesamtzeit": [""] * 10,
                "Beste Runde": [""] * 10,
                "Ich": [False] * 10,
            }
        )

    st.subheader("Rennergebnis")

    edited_table = st.data_editor(
        st.session_state["race_table"],
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Pos": st.column_config.NumberColumn("Pos", min_value=1, step=1),
            "Fahrer": st.column_config.TextColumn("Fahrer"),
            "Runden": st.column_config.NumberColumn("Runden", min_value=0, step=1),
            "Gesamtzeit": st.column_config.TextColumn("Gesamtzeit"),
            "Beste Runde": st.column_config.TextColumn("Beste Runde"),
            "Ich": st.column_config.CheckboxColumn("Ich"),
        },
    )

    st.session_state["race_table"] = edited_table

    own_rows = edited_table[edited_table["Ich"] == True]

    own_position = None
    own_best_lap = None

    if not own_rows.empty:
        own_row = own_rows.iloc[0]
        own_position = int(own_row["Pos"])
        own_best_lap = own_row["Beste Runde"]

    st.divider()
    st.subheader("Auswertung")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Eigene Position",
        f"P{own_position}" if own_position else "-",
    )

    col2.metric(
        "Beste Rennrunde",
        own_best_lap if own_best_lap else (
            best_lap["Rundenzeit"] if best_lap else "-"
        ),
    )

    col3.metric(
        "Teilnehmer",
        len(edited_table[edited_table["Fahrer"] != ""]),
    )

    notes = st.text_area("Bemerkungen", height=80)

    if st.button("Rennergebnis speichern", use_container_width=True):
        st.session_state["race_result"] = {
            "Tabelle": edited_table.to_dict(orient="records"),
            "Eigene Position": own_position,
            "Eigene beste Runde": own_best_lap,
            "Bemerkungen": notes,
        }

        st.success("Rennergebnis gespeichert.")