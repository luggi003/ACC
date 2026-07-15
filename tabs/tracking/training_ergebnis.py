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
    st.header("Training Ergebnis / Auswertung")

    best_lap = get_best_lap_from_lap_times()

    if best_lap:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Beste Runde", best_lap["Rundenzeit"])

        with col2:
            st.metric("Runde", best_lap["Runde"])

        with col3:
            st.metric("Rundenart", best_lap["Rundenart"])
    else:
        st.info("Noch keine gültigen Rundenzeiten vorhanden.")

    st.divider()

    if "training_table" not in st.session_state:
        st.session_state["training_table"] = pd.DataFrame(
            {
                "Fahrer": [""] * 10,
                "Beste Zeit": [""] * 10,
                "Stint": [""] * 10,
                "Ziel": [""] * 10,
                "Ich": [False] * 10,
            }
        )

    st.subheader("Training Vergleichstabelle")

    edited_table = st.data_editor(
        st.session_state["training_table"],
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        column_config={
            "Fahrer": st.column_config.TextColumn("Fahrer"),
            "Beste Zeit": st.column_config.TextColumn(
                "Beste Zeit",
                help="Format z.B. 1:47.263",
            ),
            "Stint": st.column_config.TextColumn("Stint"),
            "Ziel": st.column_config.TextColumn("Ziel"),
            "Ich": st.column_config.CheckboxColumn("Ich"),
        },
    )

    st.session_state["training_table"] = edited_table

    own_rows = edited_table[edited_table["Ich"] == True]

    own_time = None
    own_seconds = None

    if not own_rows.empty:
        own_row = own_rows.iloc[0]
        own_time = own_row["Beste Zeit"]
        own_seconds = parse_time_to_seconds(own_time)

    all_times = []

    for _, row in edited_table.iterrows():
        seconds = parse_time_to_seconds(row["Beste Zeit"])

        if seconds is not None:
            all_times.append(
                {
                    "Fahrer": row["Fahrer"],
                    "Beste Zeit": row["Beste Zeit"],
                    "Sekunden": seconds,
                    "Stint": row["Stint"],
                    "Ziel": row["Ziel"],
                }
            )

    fastest = min(all_times, key=lambda x: x["Sekunden"]) if all_times else None

    st.divider()
    st.subheader("Auswertung")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Eigene Trainingszeit",
            own_time if own_time else "-",
        )

    with col2:
        if fastest:
            st.metric("Schnellste Trainingszeit", fastest["Beste Zeit"])
        else:
            st.metric("Schnellste Trainingszeit", "-")

    with col3:
        if fastest and own_seconds:
            gap = own_seconds - fastest["Sekunden"]
            st.metric("Abstand", f"+{gap:.3f}" if gap > 0 else "+0.000")
        else:
            st.metric("Abstand", "-")

    if fastest:
        st.write(
            f"**Schnellster:** {fastest['Fahrer']} | "
            f"{fastest['Beste Zeit']} | "
            f"Stint {fastest['Stint']} | "
            f"{fastest['Ziel']}"
        )

    notes = st.text_area("Bemerkungen", height=80)

    if st.button("Training Ergebnis speichern", use_container_width=True):
        st.session_state["training_result"] = {
            "Tabelle": edited_table.to_dict(orient="records"),
            "Eigene Zeit": own_time,
            "Schnellste Zeit": fastest,
            "Bemerkungen": notes,
        }

        st.success("Training-Ergebnis gespeichert.")