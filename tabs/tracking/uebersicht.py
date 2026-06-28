import streamlit as st


def show():
    st.header("Tracking Übersicht")

    session_type = st.session_state.get(
        "tracking_info",
        {}
    ).get("Session-Art", "Training")

    if session_type == "Training":
        st.subheader("Training")

        with st.form("training_overview_form"):
            stint = st.number_input(
                "Stint",
                value=1,
                min_value=1,
                step=1,
            )

            training_session = st.selectbox(
                "Trainingssession",
                [
                    "Training 1",
                    "Training 2",
                    "Freies Training",
                    "Privates Training",
                ],
            )

            stint_goal = st.selectbox(
                "Ziel des Stints",
                [
                    "Quali-Sim",
                    "Longrun",
                    "Einfahren",
                    "Setup bauen",
                ],
            )

            submit = st.form_submit_button("Speichern")

            if submit:
                st.session_state["training_overview"] = {
                    "Stint": stint,
                    "Trainingssession": training_session,
                    "Ziel": stint_goal,
                }

                if "lap_counter" not in st.session_state:
                    st.session_state["lap_counter"] = 1

                st.success("Trainingsübersicht gespeichert.")

    else:
        st.subheader(session_type)
        st.info("Qualy- und Rennübersicht werden später erweitert.")

    if "training_overview" in st.session_state:
        data = st.session_state["training_overview"]

        st.divider()
        st.subheader("Aktueller Stint")

        st.write(f"**Stint:** {data['Stint']}")
        st.write(f"**Trainingssession:** {data['Trainingssession']}")
        st.write(f"**Ziel:** {data['Ziel']}")