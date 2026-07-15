import streamlit as st


def show():
    st.header("Tracking Übersicht")

    session_type = st.session_state.get(
        "tracking_info", {}
    ).get("Session-Art", "Training")

    if session_type == "Training":
        with st.form("training_overview_form"):
            stint = st.number_input("Stint", value=1, min_value=1, step=1)

            training_session = st.selectbox(
                "Trainingssession",
                ["Training 1", "Training 2", "Freies Training", "Privates Training"],
            )

            stint_goal = st.selectbox(
                "Ziel des Stints",
                ["Quali-Sim", "Longrun", "Einfahren", "Setup bauen"],
            )

            submit = st.form_submit_button("Speichern")

            if submit:
                st.session_state["training_overview"] = {
                    "Session-Art": "Training",
                    "Stint": stint,
                    "Trainingssession": training_session,
                    "Ziel": stint_goal,
                }
                st.rerun()

    elif session_type == "Qualifying":
        with st.form("qualifying_overview_form"):
            stint = st.number_input("Stint", value=1, min_value=1, step=1)

            quali_session = st.selectbox(
                "Session",
                ["Q1", "Q2", "Q3"],
            )

            quali_duration = st.number_input(
                "Quali Dauer in Minuten",
                value=15,
                min_value=1,
                step=5,
            )

            submit = st.form_submit_button("Speichern")

            if submit:
                st.session_state["training_overview"] = {
                    "Session-Art": "Qualifying",
                    "Stint": stint,
                    "Trainingssession": quali_session,
                    "Ziel": "Qualifying",
                    "Quali Dauer": quali_duration,
                }
                st.rerun()

    elif session_type == "Rennen":
        with st.form("race_overview_form"):
            stint = st.number_input("Stint", value=1, min_value=1, step=1)

            race_duration = st.number_input(
                "Renndauer in Minuten",
                value=60,
                min_value=1,
                step=5,
            )

            start_position = st.number_input(
                "Startplatz",
                value=1,
                min_value=1,
                step=1,
            )

            mandatory_pitstop = st.checkbox(
                "Pflichtboxenstopp",
                value=True,
            )

            pitstop_count = st.number_input(
                "Anzahl Pflichtstopps",
                value=1,
                min_value=0,
                step=1,
            )

            driver_change = st.checkbox(
                "Fahrerwechsel nötig",
                value=False,
            )

            submit = st.form_submit_button("Speichern")

            if submit:
                st.session_state["training_overview"] = {
                    "Session-Art": "Rennen",
                    "Stint": stint,
                    "Trainingssession": "Rennen",
                    "Ziel": "Rennen",
                    "Renndauer": race_duration,
                    "Startplatz": start_position,
                    "Pflichtboxenstopp": mandatory_pitstop,
                    "Pflichtstopps": pitstop_count,
                    "Fahrerwechsel": driver_change,
                }
                st.rerun()

    if "training_overview" in st.session_state:
        data = st.session_state["training_overview"]

        st.divider()
        st.subheader("Aktuelle Auswahl")

        st.write(f"**Session-Art:** {data.get('Session-Art')}")
        st.write(f"**Stint:** {data.get('Stint')}")
        st.write(f"**Session:** {data.get('Trainingssession')}")
        st.write(f"**Ziel:** {data.get('Ziel')}")

        if data.get("Quali Dauer") is not None:
            st.write(f"**Quali Dauer:** {data.get('Quali Dauer')} Minuten")

        if data.get("Renndauer") is not None:
            st.write(f"**Renndauer:** {data.get('Renndauer')} Minuten")

        if data.get("Startplatz") is not None:
            st.write(f"**Startplatz:** P{data.get('Startplatz')}")

        if data.get("Pflichtboxenstopp") is not None:
            pflicht = "Ja" if data.get("Pflichtboxenstopp") else "Nein"
            st.write(f"**Pflichtboxenstopp:** {pflicht}")

        if data.get("Pflichtstopps") is not None:
            st.write(f"**Pflichtstopps:** {data.get('Pflichtstopps')}")

        if data.get("Fahrerwechsel") is not None:
            wechsel = "Ja" if data.get("Fahrerwechsel") else "Nein"
            st.write(f"**Fahrerwechsel:** {wechsel}")