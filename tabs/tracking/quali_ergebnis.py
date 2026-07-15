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


def format_gap(seconds):
    if seconds is None:
        return "-"

    if seconds <= 0:
        return "+0.000"

    return f"+{seconds:.3f}"


def show():
    st.header("Qualifying Ergebnis")

    best_lap = get_best_lap_from_lap_times()

    if "quali_table" not in st.session_state:
        st.session_state["quali_table"] = pd.DataFrame(
            {
                "Pos": list(range(1, 11)),
                "Fahrer": [""] * 10,
                "Zeit": [""] * 10,
                "Ich": [False] * 10,
            }
        )

    st.subheader("Ergebnisliste")

    edited_table = st.data_editor(
        st.session_state["quali_table"],
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Pos": st.column_config.NumberColumn(
                "Pos",
                min_value=1,
                step=1,
            ),
            "Fahrer": st.column_config.TextColumn("Fahrer"),
            "Zeit": st.column_config.TextColumn(
                "Zeit",
                help="Format z.B. 1:47.263",
            ),
            "Ich": st.column_config.CheckboxColumn("Ich"),
        },
    )

    st.session_state["quali_table"] = edited_table

    own_rows = edited_table[edited_table["Ich"] == True]

    own_position = None
    own_time = None
    own_seconds = None

    if not own_rows.empty:
        own_row = own_rows.iloc[0]
        own_position = int(own_row["Pos"])
        own_time = own_row["Zeit"]
        own_seconds = parse_time_to_seconds(own_time)

    all_times = []

    for _, row in edited_table.iterrows():
        seconds = parse_time_to_seconds(row["Zeit"])

        if seconds is not None:
            all_times.append(
                {
                    "Pos": row["Pos"],
                    "Fahrer": row["Fahrer"],
                    "Zeit": row["Zeit"],
                    "Sekunden": seconds,
                }
            )

    pole = min(all_times, key=lambda x: x["Sekunden"]) if all_times else None

    st.divider()
    st.subheader("Auswertung")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Eigene Position",
            f"P{own_position}" if own_position else "-",
        )

    with col2:
        if own_time:
            st.metric("Eigene Quali-Zeit", own_time)
        elif best_lap:
            st.metric("Beste Runde aus Tracking", best_lap["Rundenzeit"])
        else:
            st.metric("Beste Runde", "-")

    with col3:
        if pole and own_seconds:
            st.metric(
                "Abstand zur Pole",
                format_gap(own_seconds - pole["Sekunden"]),
            )
        else:
            st.metric("Abstand zur Pole", "-")

    if pole:
        st.write(f"**Pole:** P{int(pole['Pos'])} | {pole['Fahrer']} | {pole['Zeit']}")

    notes = st.text_area(
        "Bemerkungen",
        height=80,
    )

    if st.button("Qualifying Ergebnis speichern", use_container_width=True):
        st.session_state["quali_result"] = {
            "Tabelle": edited_table.to_dict(orient="records"),
            "Eigene Position": own_position,
            "Eigene Zeit": own_time,
            "Pole": pole,
            "Bemerkungen": notes,
        }

        st.success("Qualifying-Ergebnis gespeichert.")