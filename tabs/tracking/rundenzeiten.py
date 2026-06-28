# tabs/tracking/rundenzeiten.py

import streamlit as st
from utils.time_parser import parse_time_to_seconds


def init():
    if "lap_counter" not in st.session_state:
        st.session_state["lap_counter"] = 1

    if "lap_times" not in st.session_state:
        st.session_state["lap_times"] = []


def show():
    init()

    st.header("Rundenzeiten")

    if "training_overview" not in st.session_state:
        st.warning("Bitte zuerst die Übersicht ausfüllen.")
        return

    overview = st.session_state["training_overview"]
    ziel = overview["Ziel"]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Stint", overview["Stint"])

    with col2:
        st.metric("Session", overview["Trainingssession"])

    with col3:
        st.metric("Ziel", ziel)

    st.divider()

    col_lap, col_minus, col_plus = st.columns([6, 1, 1])

    with col_lap:
        st.metric("Aktuelle Runde", st.session_state["lap_counter"])

    with col_minus:
        if st.button("➖", key="lap_minus"):
            st.session_state["lap_counter"] = max(
                1,
                st.session_state["lap_counter"] - 1,
            )
            st.rerun()

    with col_plus:
        if st.button("➕", key="lap_plus"):
            st.session_state["lap_counter"] += 1
            st.rerun()

    if ziel in ["Quali-Sim", "Setup bauen"]:
        lap_type_options = [
            "Push Lap",
            "Cool Down",
            "Out Lap",
            "In Lap",
        ]
    else:
        lap_type_options = [
            "Normale Runde",
            "Cool Down",
            "Out Lap",
            "In Lap",
        ]

    with st.form("lap_form"):
        lap_time = st.text_input(
            "Rundenzeit",
            placeholder="z.B. 1:47.263",
        )

        lap_type = st.selectbox(
            "Rundenart",
            lap_type_options,
        )

        valid = st.checkbox(
            "Gültige Runde",
            value=True,
        )

        notes = st.text_area(
            "Bemerkungen",
            height=80,
        )

        submit = st.form_submit_button("Runde speichern")

        if submit:
            current_lap = st.session_state["lap_counter"]

            st.session_state["lap_times"].append({
                "Stint": overview["Stint"],
                "Trainingssession": overview["Trainingssession"],
                "Ziel": ziel,
                "Runde": current_lap,
                "Rundenzeit": lap_time,
                "Sekunden": parse_time_to_seconds(lap_time),
                "Rundenart": lap_type,
                "Gültig": valid,
                "Bemerkung": notes,
            })

            st.session_state["lap_counter"] += 1

            st.success(f"Runde {current_lap} gespeichert.")
            st.rerun()

    st.divider()

    if st.session_state["lap_times"]:
        st.subheader("Gespeicherte Runden")

        for lap in st.session_state["lap_times"]:
            marker = "✅" if lap["Gültig"] else "❌"

            st.write(
                f"{marker} **Runde {lap['Runde']}** | "
                f"Stint {lap['Stint']} | "
                f"{lap['Ziel']} | "
                f"{lap['Rundenart']} | "
                f"{lap['Rundenzeit']} | "
                f"{lap['Bemerkung']}"
            )