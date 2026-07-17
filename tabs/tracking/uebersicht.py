import streamlit as st


TRAINING_GOALS = [
    "Quali-Sim",
    "Longrun",
    "Einfahren",
    "Setup bauen",
    "Strategie-Testlauf",
]


def show_current_selection(data):
    st.divider()
    st.subheader("Aktuelle Auswahl")

    session_type = data.get("Session-Art", "-")

    st.write(f"**Session-Art:** {session_type}")
    st.write(
        f"**Session:** "
        f"{data.get('Trainingssession', '-')}"
    )

    if (
        session_type != "Rennen"
        and data.get("Stint") is not None
    ):
        st.write(
            f"**Stint:** {data.get('Stint')}"
        )

    if data.get("Ziel") is not None:
        st.write(
            f"**Ziel:** {data.get('Ziel')}"
        )

    if data.get("Quali Dauer") is not None:
        st.write(
            f"**Quali-Dauer:** "
            f"{data.get('Quali Dauer')} Minuten"
        )

    if data.get("Renndauer") is not None:
        st.write(
            f"**Renndauer:** "
            f"{data.get('Renndauer')} Minuten"
        )

    if data.get("Startplatz") is not None:
        st.write(
            f"**Startplatz:** "
            f"P{data.get('Startplatz')}"
        )

    if data.get("Pflichtboxenstopp") is not None:
        mandatory_stop = (
            "Ja"
            if data.get("Pflichtboxenstopp")
            else "Nein"
        )

        st.write(
            f"**Pflichtboxenstopp:** "
            f"{mandatory_stop}"
        )

    if data.get("Pflichtstopps") is not None:
        st.write(
            f"**Anzahl Pflichtstopps:** "
            f"{data.get('Pflichtstopps')}"
        )

    if data.get("Fahrerwechsel") is not None:
        driver_change = (
            "Ja"
            if data.get("Fahrerwechsel")
            else "Nein"
        )

        st.write(
            f"**Fahrerwechsel nötig:** "
            f"{driver_change}"
        )

    if data.get("Ziel") == "Strategie-Testlauf":
        st.divider()
        st.markdown("#### Strategie-Testlauf")

        st.write(
            f"**Testserie:** "
            f"{data.get('Testserie', '-')}"
        )

        st.write(
            f"**Testlauf:** "
            f"{data.get('Testlaufnummer', '-')}"
        )

        st.write(
            f"**Blockgröße:** "
            f"{data.get('Blockgröße', '-')} Runden"
        )

        st.write(
            f"**Anzahl Blöcke:** "
            f"{data.get('Anzahl Blöcke', '-')}"
        )

        st.write(
            f"**Gesamtdistanz:** "
            f"{data.get('Gesamtrunden', '-')} Runden"
        )

        st.write(
            f"**Starttank:** "
            f"{data.get('Starttank', 0):.1f} l"
        )

        st.write(
            f"**Reifensatz:** "
            f"{data.get('Reifensatz', '-')}"
        )

        new_tyres = (
            "Ja"
            if data.get("Neue Reifen")
            else "Nein"
        )

        st.write(
            f"**Neue Reifen bestätigt:** "
            f"{new_tyres}"
        )


def show_strategy_test_fields():
    st.markdown("### Strategie-Testlauf")

    test_series = st.text_input(
        "Testserie",
        value="Strategie-Test 1",
        placeholder=(
            "z. B. Imola Rennsimulation 01"
        ),
    )

    col1, col2 = st.columns(2)

    with col1:
        test_run_number = st.number_input(
            "Testlaufnummer",
            min_value=1,
            value=1,
            step=1,
        )

    with col2:
        block_size_selection = st.selectbox(
            "Blockgröße",
            [
                "3 Runden",
                "5 Runden",
                "10 Runden",
                "Benutzerdefiniert",
            ],
            index=1,
        )

    if block_size_selection == "Benutzerdefiniert":
        block_size = st.number_input(
            "Benutzerdefinierte Blockgröße",
            min_value=1,
            value=5,
            step=1,
        )
    else:
        block_size = int(
            block_size_selection.split()[0]
        )

    number_of_blocks = st.number_input(
        "Anzahl der Blöcke",
        min_value=1,
        value=int(test_run_number),
        step=1,
        help=(
            "Beispiel: Testlauf 1 fährt einen Block, "
            "Testlauf 2 fährt zwei Blöcke."
        ),
    )

    total_laps = int(block_size) * int(
        number_of_blocks
    )

    st.info(
        f"Geplante Gesamtdistanz: "
        f"{total_laps} Runden"
    )

    col3, col4 = st.columns(2)

    with col3:
        start_fuel = st.number_input(
            "Starttank in Liter",
            min_value=0.0,
            value=80.0,
            step=1.0,
        )

    with col4:
        tyre_set = st.selectbox(
            "Reifensatz",
            [
                "Satz 1",
                "Satz 2",
                "Satz 3",
                "Satz 4",
                "Satz 5",
                "Anderer Satz",
            ],
        )

    new_tyres = st.checkbox(
        "Neue Reifen für diesen Testlauf bestätigt",
        value=True,
    )

    reference_setup = st.text_input(
        "Referenz-Setup",
        placeholder=(
            "z. B. Race Setup V3"
        ),
    )

    return {
        "Testserie": test_series,
        "Testlaufnummer": int(
            test_run_number
        ),
        "Blockgröße": int(block_size),
        "Anzahl Blöcke": int(
            number_of_blocks
        ),
        "Gesamtrunden": int(total_laps),
        "Starttank": float(start_fuel),
        "Reifensatz": tyre_set,
        "Neue Reifen": new_tyres,
        "Referenz-Setup": reference_setup,
    }


def show():
    st.header("Tracking Übersicht")

    session_type = st.session_state.get(
        "tracking_info",
        {},
    ).get(
        "Session-Art",
        "Training",
    )

    if session_type == "Training":
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
                TRAINING_GOALS,
            )

            strategy_test_data = {}

            if stint_goal == "Strategie-Testlauf":
                strategy_test_data = (
                    show_strategy_test_fields()
                )

            submit = st.form_submit_button(
                "Training speichern",
                use_container_width=True,
            )

            if submit:
                if (
                    stint_goal
                    == "Strategie-Testlauf"
                    and not strategy_test_data.get(
                        "Neue Reifen"
                    )
                ):
                    st.error(
                        "Bitte bestätigen, dass für den "
                        "Testlauf neue Reifen verwendet "
                        "werden."
                    )
                    return

                previous_overview = (
                    st.session_state.get(
                        "training_overview",
                        {},
                    )
                )

                previous_stint = (
                    previous_overview.get("Stint")
                )

                overview_data = {
                    "Session-Art": "Training",
                    "Stint": int(stint),
                    "Trainingssession":
                        training_session,
                    "Ziel": stint_goal,
                }

                if stint_goal == "Strategie-Testlauf":
                    overview_data.update(
                        strategy_test_data
                    )

                st.session_state[
                    "training_overview"
                ] = overview_data

                if previous_stint != int(stint):
                    lap_counters = (
                        st.session_state.get(
                            "lap_counters",
                            {},
                        )
                    )

                    counter_key = (
                        f"Training|"
                        f"{training_session}|"
                        f"{int(stint)}"
                    )

                    lap_counters.setdefault(
                        counter_key,
                        1,
                    )

                    st.session_state[
                        "lap_counters"
                    ] = lap_counters

                st.success(
                    "Trainingsübersicht gespeichert."
                )
                st.rerun()

    elif session_type == "Qualifying":
        with st.form(
            "qualifying_overview_form"
        ):
            stint = st.number_input(
                "Stint",
                value=1,
                min_value=1,
                step=1,
            )

            quali_session = st.selectbox(
                "Qualifying-Session",
                [
                    "Q1",
                    "Q2",
                    "Q3",
                ],
            )

            quali_duration = st.number_input(
                "Quali-Dauer in Minuten",
                value=15,
                min_value=1,
                step=5,
            )

            submit = st.form_submit_button(
                "Qualifying speichern",
                use_container_width=True,
            )

            if submit:
                st.session_state[
                    "training_overview"
                ] = {
                    "Session-Art": "Qualifying",
                    "Stint": int(stint),
                    "Trainingssession":
                        quali_session,
                    "Ziel": "Qualifying",
                    "Quali Dauer": int(
                        quali_duration
                    ),
                }

                st.success(
                    "Qualifying-Übersicht gespeichert."
                )
                st.rerun()

    elif session_type == "Rennen":
        with st.form("race_overview_form"):
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

            if mandatory_pitstop:
                pitstop_count = st.number_input(
                    "Anzahl Pflichtstopps",
                    value=1,
                    min_value=1,
                    step=1,
                )
            else:
                pitstop_count = 0

            driver_change = st.checkbox(
                "Fahrerwechsel nötig",
                value=False,
            )

            submit = st.form_submit_button(
                "Renndaten speichern",
                use_container_width=True,
            )

            if submit:
                st.session_state[
                    "training_overview"
                ] = {
                    "Session-Art": "Rennen",
                    "Trainingssession": "Rennen",
                    "Ziel": "Rennen",
                    "Renndauer": int(
                        race_duration
                    ),
                    "Startplatz": int(
                        start_position
                    ),
                    "Pflichtboxenstopp":
                        mandatory_pitstop,
                    "Pflichtstopps": int(
                        pitstop_count
                    ),
                    "Fahrerwechsel":
                        driver_change,
                }

                st.success(
                    "Rennübersicht gespeichert."
                )
                st.rerun()

    if "training_overview" in st.session_state:
        data = st.session_state[
            "training_overview"
        ]

        if (
            data.get("Session-Art")
            == session_type
        ):
            show_current_selection(data)