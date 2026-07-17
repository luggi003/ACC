import pandas as pd
import streamlit as st


def get_tyre_strategy_by_stint():
    tyre_strategy = st.session_state.get(
        "strategy_tyres",
        [],
    )

    return {
        int(entry.get("Stint", 0)): entry
        for entry in tyre_strategy
        if entry.get("Stint") is not None
    }


def create_default_pitstop_plan(
    parameters,
    stint_plan,
    tyre_strategy,
):
    pitstops = []

    pitlane_time = float(
        parameters.get(
            "Pitlane Time",
            0.0,
        )
    )

    minimum_stop_time = float(
        parameters.get(
            "Mindeststandzeit",
            0.0,
        )
    )

    driver_change_required = bool(
        parameters.get(
            "Fahrerwechsel",
            False,
        )
    )

    sorted_stints = sorted(
        stint_plan,
        key=lambda entry: int(
            entry.get("Stint", 0)
        ),
    )

    for index in range(
        len(sorted_stints) - 1
    ):
        current_stint = sorted_stints[index]
        next_stint = sorted_stints[index + 1]

        stop_number = index + 1

        current_stint_number = int(
            current_stint.get(
                "Stint",
                stop_number,
            )
        )

        next_stint_number = int(
            next_stint.get(
                "Stint",
                stop_number + 1,
            )
        )

        pit_lap = int(
            current_stint.get(
                "Ende Runde",
                0,
            )
        )

        refuel_amount = float(
            next_stint.get(
                "Nachtanken",
                next_stint.get(
                    "Tankmenge Start",
                    0.0,
                ),
            )
        )

        tyre_info = tyre_strategy.get(
            next_stint_number,
            {},
        )

        tyre_change = bool(
            tyre_info.get(
                "Reifenwechsel",
                next_stint.get(
                    "Reifenwechsel",
                    False,
                ),
            )
        )

        tyre_set = tyre_info.get(
            "Reifensatz",
            next_stint.get(
                "Reifensatz",
                "-",
            ),
        )

        # Fahrerwechsel zunächst beim letzten Stop einplanen.
        driver_change = (
            driver_change_required
            and stop_number
            == len(sorted_stints) - 1
        )

        estimated_loss = (
            pitlane_time
            + minimum_stop_time
        )

        pitstops.append(
            {
                "Stop": stop_number,
                "Nach Stint": current_stint_number,
                "Boxenrunde": pit_lap,
                "Nachtanken": refuel_amount,
                "Reifenwechsel": tyre_change,
                "Neuer Reifensatz": tyre_set,
                "Fahrerwechsel": driver_change,
                "Neuer Fahrer": next_stint.get(
                    "Fahrer",
                    "",
                ),
                "Mindeststandzeit": minimum_stop_time,
                "Pitlane-Verlust": pitlane_time,
                "Erwarteter Gesamtverlust":
                    estimated_loss,
                "Bemerkung": "",
            }
        )

    return pitstops


def calculate_stop_loss(
    pitlane_loss,
    minimum_stop_time,
):
    try:
        pitlane_loss = float(pitlane_loss)
    except (TypeError, ValueError):
        pitlane_loss = 0.0

    try:
        minimum_stop_time = float(
            minimum_stop_time
        )
    except (TypeError, ValueError):
        minimum_stop_time = 0.0

    return (
        pitlane_loss
        + minimum_stop_time
    )


def update_calculated_losses(dataframe):
    dataframe = dataframe.copy()

    if dataframe.empty:
        return dataframe

    dataframe[
        "Erwarteter Gesamtverlust"
    ] = dataframe.apply(
        lambda row: calculate_stop_loss(
            row.get(
                "Pitlane-Verlust",
                0.0,
            ),
            row.get(
                "Mindeststandzeit",
                0.0,
            ),
        ),
        axis=1,
    )

    return dataframe


def validate_pitstop_plan(
    dataframe,
    parameters,
    stint_plan,
):
    errors = []
    warnings = []

    if dataframe.empty:
        mandatory_stops = int(
            parameters.get(
                "Pflichtstopps",
                0,
            )
        )

        if mandatory_stops > 0:
            errors.append(
                "Es sind Pflichtstopps vorgeschrieben, "
                "aber es wurde kein Boxenstopp geplant."
            )

        return errors, warnings

    mandatory_stops = int(
        parameters.get(
            "Pflichtstopps",
            0,
        )
    )

    if len(dataframe) < mandatory_stops:
        errors.append(
            "Die geplante Anzahl an Boxenstopps "
            "liegt unter der vorgeschriebenen Anzahl."
        )

    race_laps = 0

    for stint in stint_plan:
        race_laps = max(
            race_laps,
            int(
                stint.get(
                    "Ende Runde",
                    0,
                )
            ),
        )

    used_pit_laps = set()

    for _, row in dataframe.iterrows():
        stop_number = int(
            row.get(
                "Stop",
                0,
            )
        )

        pit_lap = int(
            row.get(
                "Boxenrunde",
                0,
            )
        )

        refuel = float(
            row.get(
                "Nachtanken",
                0.0,
            )
        )

        if pit_lap <= 0:
            errors.append(
                f"Stop {stop_number}: "
                "Die Boxenrunde muss größer als 0 sein."
            )

        if race_laps > 0 and pit_lap >= race_laps:
            warnings.append(
                f"Stop {stop_number}: "
                "Der Stopp liegt in oder nach der "
                "voraussichtlich letzten Rennrunde."
            )

        if pit_lap in used_pit_laps:
            errors.append(
                f"Stop {stop_number}: "
                "Mehrere Stopps sind in derselben "
                "Runde geplant."
            )

        used_pit_laps.add(pit_lap)

        if refuel < 0:
            errors.append(
                f"Stop {stop_number}: "
                "Die Nachtankmenge darf nicht "
                "negativ sein."
            )

    driver_change_required = bool(
        parameters.get(
            "Fahrerwechsel",
            False,
        )
    )

    if driver_change_required:
        driver_change_rows = dataframe[
            dataframe["Fahrerwechsel"] == True
        ]

        if driver_change_rows.empty:
            errors.append(
                "Ein Fahrerwechsel ist vorgeschrieben, "
                "aber bei keinem Stopp eingeplant."
            )

    tyre_change_required = bool(
        parameters.get(
            "Reifenwechsel verpflichtend",
            False,
        )
    )

    if tyre_change_required:
        tyre_change_rows = dataframe[
            dataframe["Reifenwechsel"] == True
        ]

        if tyre_change_rows.empty:
            errors.append(
                "Ein Reifenwechsel ist verpflichtend, "
                "aber bei keinem Stopp eingeplant."
            )

    return errors, warnings


def show():
    st.subheader("Boxenstrategie")

    if (
        "strategy_parameters"
        not in st.session_state
    ):
        st.warning(
            "Bitte zuerst die Rennparameter speichern."
        )
        return

    if (
        "strategy_stints"
        not in st.session_state
    ):
        st.warning(
            "Bitte zuerst die Stintplanung erstellen "
            "und speichern."
        )
        return

    parameters = st.session_state[
        "strategy_parameters"
    ]

    stint_plan = st.session_state[
        "strategy_stints"
    ]

    tyre_strategy = (
        get_tyre_strategy_by_stint()
    )

    if (
        "strategy_pitstops"
        not in st.session_state
    ):
        st.session_state[
            "strategy_pitstops"
        ] = create_default_pitstop_plan(
            parameters,
            stint_plan,
            tyre_strategy,
        )

    if st.button(
        "Boxenstrategie neu erstellen",
        use_container_width=True,
    ):
        st.session_state[
            "strategy_pitstops"
        ] = create_default_pitstop_plan(
            parameters,
            stint_plan,
            tyre_strategy,
        )

        st.rerun()

    st.info(
        "Die Stopps werden zunächst automatisch aus "
        "der Stintplanung erzeugt und können danach "
        "manuell angepasst werden."
    )

    dataframe = pd.DataFrame(
        st.session_state[
            "strategy_pitstops"
        ]
    )

    if dataframe.empty:
        dataframe = pd.DataFrame(
            columns=[
                "Stop",
                "Nach Stint",
                "Boxenrunde",
                "Nachtanken",
                "Reifenwechsel",
                "Neuer Reifensatz",
                "Fahrerwechsel",
                "Neuer Fahrer",
                "Mindeststandzeit",
                "Pitlane-Verlust",
                "Erwarteter Gesamtverlust",
                "Bemerkung",
            ]
        )

    edited_dataframe = st.data_editor(
        dataframe,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Stop":
                st.column_config.NumberColumn(
                    "Stop",
                    min_value=1,
                    step=1,
                    required=True,
                ),
            "Nach Stint":
                st.column_config.NumberColumn(
                    "Nach Stint",
                    min_value=1,
                    step=1,
                    required=True,
                ),
            "Boxenrunde":
                st.column_config.NumberColumn(
                    "Boxenrunde",
                    min_value=1,
                    step=1,
                    required=True,
                ),
            "Nachtanken":
                st.column_config.NumberColumn(
                    "Nachtanken",
                    min_value=0.0,
                    step=0.5,
                    format="%.1f l",
                ),
            "Reifenwechsel":
                st.column_config.CheckboxColumn(
                    "Reifenwechsel",
                ),
            "Neuer Reifensatz":
                st.column_config.TextColumn(
                    "Neuer Reifensatz",
                ),
            "Fahrerwechsel":
                st.column_config.CheckboxColumn(
                    "Fahrerwechsel",
                ),
            "Neuer Fahrer":
                st.column_config.TextColumn(
                    "Neuer Fahrer",
                ),
            "Mindeststandzeit":
                st.column_config.NumberColumn(
                    "Mindeststandzeit",
                    min_value=0.0,
                    step=1.0,
                    format="%.1f s",
                ),
            "Pitlane-Verlust":
                st.column_config.NumberColumn(
                    "Pitlane-Verlust",
                    min_value=0.0,
                    step=0.1,
                    format="%.1f s",
                ),
            "Erwarteter Gesamtverlust":
                st.column_config.NumberColumn(
                    "Gesamtverlust",
                    disabled=True,
                    format="%.1f s",
                ),
            "Bemerkung":
                st.column_config.TextColumn(
                    "Bemerkung",
                ),
        },
        key="strategy_pitstop_editor",
    )

    edited_dataframe = (
        update_calculated_losses(
            edited_dataframe
        )
    )

    st.divider()

    total_refuel = float(
        edited_dataframe[
            "Nachtanken"
        ].fillna(0).sum()
    ) if not edited_dataframe.empty else 0.0

    total_loss = float(
        edited_dataframe[
            "Erwarteter Gesamtverlust"
        ].fillna(0).sum()
    ) if not edited_dataframe.empty else 0.0

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Geplante Stopps",
        len(edited_dataframe),
    )

    col2.metric(
        "Gesamt Nachtanken",
        f"{total_refuel:.1f} l",
    )

    col3.metric(
        "Erwarteter Boxenverlust",
        f"{total_loss:.1f} s",
    )

    errors, warnings = validate_pitstop_plan(
        edited_dataframe,
        parameters,
        stint_plan,
    )

    for error in errors:
        st.error(error)

    for warning in warnings:
        st.warning(warning)

    if st.button(
        "Boxenstrategie speichern",
        use_container_width=True,
        disabled=bool(errors),
    ):
        saved_dataframe = (
            update_calculated_losses(
                edited_dataframe
            )
        )

        st.session_state[
            "strategy_pitstops"
        ] = (
            saved_dataframe
            .sort_values("Stop")
            .to_dict(
                orient="records"
            )
        )

        st.success(
            "Boxenstrategie gespeichert."
        )

        st.rerun()

    st.divider()
    st.subheader("Geplanter Ablauf der Stopps")

    if edited_dataframe.empty:
        st.info(
            "Aktuell sind keine Boxenstopps geplant."
        )
        return

    sorted_stops = (
        edited_dataframe
        .sort_values("Stop")
    )

    for _, stop in sorted_stops.iterrows():
        with st.container(border=True):
            col1, col2, col3, col4 = (
                st.columns(4)
            )

            col1.metric(
                "Stop",
                int(stop["Stop"]),
            )

            col2.metric(
                "Boxenrunde",
                int(stop["Boxenrunde"]),
            )

            col3.metric(
                "Nachtanken",
                f"{float(stop['Nachtanken']):.1f} l",
            )

            col4.metric(
                "Zeitverlust",
                (
                    f"{float(stop['Erwarteter Gesamtverlust']):.1f} s"
                ),
            )

            st.write(
                "**Reifenwechsel:** "
                + (
                    "Ja"
                    if bool(
                        stop["Reifenwechsel"]
                    )
                    else "Nein"
                )
            )

            if bool(
                stop["Reifenwechsel"]
            ):
                st.write(
                    f"**Neuer Reifensatz:** "
                    f"{stop.get('Neuer Reifensatz', '-')}"
                )

            st.write(
                "**Fahrerwechsel:** "
                + (
                    "Ja"
                    if bool(
                        stop["Fahrerwechsel"]
                    )
                    else "Nein"
                )
            )

            if bool(
                stop["Fahrerwechsel"]
            ):
                st.write(
                    f"**Neuer Fahrer:** "
                    f"{stop.get('Neuer Fahrer', '-')}"
                )

            if stop.get("Bemerkung"):
                st.info(
                    stop["Bemerkung"]
                )