import math

import pandas as pd
import streamlit as st


def create_default_stint_plan(
    parameters,
    fuel_strategy,
    fuel_stints,
):
    number_of_stints = int(
        fuel_strategy.get("Anzahl Stints", 1)
    )

    expected_laps = int(
        fuel_strategy.get(
            "Erwartete Rennrunden",
            1,
        )
    )

    fuel_per_lap = float(
        parameters.get(
            "Verbrauch pro Runde",
            0.0,
        )
    )

    if number_of_stints <= 0:
        number_of_stints = 1

    base_laps = expected_laps // number_of_stints
    remaining_laps = expected_laps % number_of_stints

    plan = []

    start_lap = 1

    for index in range(number_of_stints):
        stint_number = index + 1

        stint_laps = base_laps

        if index < remaining_laps:
            stint_laps += 1

        end_lap = start_lap + stint_laps - 1

        fuel_data = next(
            (
                entry
                for entry in fuel_stints
                if int(entry.get("Stint", 0))
                == stint_number
            ),
            {},
        )

        tank_amount = float(
            fuel_data.get(
                "Tankmenge",
                stint_laps * fuel_per_lap,
            )
        )

        if stint_number == 1:
            refuel_amount = 0.0
        else:
            refuel_amount = tank_amount

        plan.append(
            {
                "Stint": stint_number,
                "Start Runde": start_lap,
                "Ende Runde": end_lap,
                "Runden": stint_laps,
                "Tankmenge Start": tank_amount,
                "Nachtanken": refuel_amount,
                "Reifensatz": f"Satz {stint_number}",
                "Reifenwechsel": (
                    stint_number > 1
                ),
                "Fahrer": "",
                "Bemerkung": "",
            }
        )

        start_lap = end_lap + 1

    return plan


def calculate_plan_summary(
    dataframe,
    fuel_per_lap,
):
    if dataframe.empty:
        return {
            "Gesamtrunden": 0,
            "Gesamtkraftstoff": 0.0,
            "Gesamtnachtanken": 0.0,
            "Stopps": 0,
        }

    total_laps = int(
        dataframe["Runden"].fillna(0).sum()
    )

    total_start_fuel = float(
        dataframe[
            "Tankmenge Start"
        ].fillna(0).sum()
    )

    total_refuel = float(
        dataframe["Nachtanken"].fillna(0).sum()
    )

    stops = max(
        0,
        len(dataframe) - 1,
    )

    calculated_fuel_need = (
        total_laps * fuel_per_lap
    )

    return {
        "Gesamtrunden": total_laps,
        "Gesamtkraftstoff":
            total_start_fuel,
        "Gesamtnachtanken":
            total_refuel,
        "Stopps": stops,
        "Rechnerischer Bedarf":
            calculated_fuel_need,
    }


def validate_plan(
    dataframe,
    parameters,
    fuel_strategy,
):
    errors = []
    warnings = []

    if dataframe.empty:
        errors.append(
            "Die Stintplanung ist leer."
        )
        return errors, warnings

    expected_laps = int(
        fuel_strategy.get(
            "Erwartete Rennrunden",
            0,
        )
    )

    tank_capacity = float(
        parameters.get(
            "Tankvolumen",
            0.0,
        )
    )

    fuel_per_lap = float(
        parameters.get(
            "Verbrauch pro Runde",
            0.0,
        )
    )

    mandatory_stops = int(
        parameters.get(
            "Pflichtstopps",
            0,
        )
    )

    total_laps = int(
        dataframe["Runden"].fillna(0).sum()
    )

    if total_laps < expected_laps:
        errors.append(
            "Die geplanten Stints decken nicht "
            "alle erwarteten Rennrunden ab."
        )

    if total_laps > expected_laps:
        warnings.append(
            "Die geplanten Stints enthalten mehr "
            "Runden als aktuell erwartet."
        )

    planned_stops = max(
        0,
        len(dataframe) - 1,
    )

    if planned_stops < mandatory_stops:
        errors.append(
            "Die geplante Anzahl an Stopps liegt "
            "unter der vorgeschriebenen Anzahl."
        )

    for _, row in dataframe.iterrows():
        stint_number = int(
            row.get("Stint", 0)
        )

        laps = int(
            row.get("Runden", 0)
        )

        tank_amount = float(
            row.get(
                "Tankmenge Start",
                0.0,
            )
        )

        required_fuel = (
            laps * fuel_per_lap
        )

        if tank_amount > tank_capacity:
            errors.append(
                f"Stint {stint_number}: "
                "Tankmenge überschreitet das "
                "Tankvolumen."
            )

        if tank_amount < required_fuel:
            errors.append(
                f"Stint {stint_number}: "
                "Die Tankmenge reicht rechnerisch "
                "nicht für die geplanten Runden."
            )

    return errors, warnings


def show():
    st.subheader("Stintplanung")

    if (
        "strategy_parameters"
        not in st.session_state
    ):
        st.warning(
            "Bitte zuerst die Rennparameter "
            "speichern."
        )
        return

    if (
        "strategy_fuel"
        not in st.session_state
    ):
        st.warning(
            "Bitte zuerst die Kraftstoffstrategie "
            "öffnen und berechnen lassen."
        )
        return

    parameters = st.session_state[
        "strategy_parameters"
    ]

    fuel_strategy = st.session_state[
        "strategy_fuel"
    ]

    fuel_stints = st.session_state.get(
        "strategy_fuel_stints",
        [],
    )

    if (
        "strategy_stints"
        not in st.session_state
    ):
        st.session_state[
            "strategy_stints"
        ] = create_default_stint_plan(
            parameters,
            fuel_strategy,
            fuel_stints,
        )

    if st.button(
        "Stintplanung neu berechnen",
        use_container_width=True,
    ):
        st.session_state[
            "strategy_stints"
        ] = create_default_stint_plan(
            parameters,
            fuel_strategy,
            fuel_stints,
        )

        st.rerun()

    st.info(
        "Die Tabelle kann direkt bearbeitet "
        "werden. Änderungen werden nach dem "
        "Speichern übernommen."
    )

    dataframe = pd.DataFrame(
        st.session_state[
            "strategy_stints"
        ]
    )

    edited_dataframe = st.data_editor(
        dataframe,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Stint":
                st.column_config.NumberColumn(
                    "Stint",
                    min_value=1,
                    step=1,
                    required=True,
                ),
            "Start Runde":
                st.column_config.NumberColumn(
                    "Start Runde",
                    min_value=1,
                    step=1,
                    required=True,
                ),
            "Ende Runde":
                st.column_config.NumberColumn(
                    "Ende Runde",
                    min_value=1,
                    step=1,
                    required=True,
                ),
            "Runden":
                st.column_config.NumberColumn(
                    "Runden",
                    min_value=1,
                    step=1,
                    required=True,
                ),
            "Tankmenge Start":
                st.column_config.NumberColumn(
                    "Tankmenge Start",
                    min_value=0.0,
                    max_value=float(
                        parameters.get(
                            "Tankvolumen",
                            120.0,
                        )
                    ),
                    step=0.5,
                    format="%.1f l",
                    required=True,
                ),
            "Nachtanken":
                st.column_config.NumberColumn(
                    "Nachtanken",
                    min_value=0.0,
                    step=0.5,
                    format="%.1f l",
                ),
            "Reifensatz":
                st.column_config.TextColumn(
                    "Reifensatz",
                ),
            "Reifenwechsel":
                st.column_config.CheckboxColumn(
                    "Reifenwechsel",
                ),
            "Fahrer":
                st.column_config.TextColumn(
                    "Fahrer",
                ),
            "Bemerkung":
                st.column_config.TextColumn(
                    "Bemerkung",
                ),
        },
        key="strategy_stint_editor",
    )

    fuel_per_lap = float(
        parameters.get(
            "Verbrauch pro Runde",
            0.0,
        )
    )

    summary = calculate_plan_summary(
        edited_dataframe,
        fuel_per_lap,
    )

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Geplante Runden",
        summary["Gesamtrunden"],
    )

    col2.metric(
        "Anzahl Stints",
        len(edited_dataframe),
    )

    col3.metric(
        "Boxenstopps",
        summary["Stopps"],
    )

    col4.metric(
        "Rechnerischer Spritbedarf",
        (
            f"{summary['Rechnerischer Bedarf']:.1f} l"
        ),
    )

    errors, warnings = validate_plan(
        edited_dataframe,
        parameters,
        fuel_strategy,
    )

    if errors:
        for error in errors:
            st.error(error)

    if warnings:
        for warning in warnings:
            st.warning(warning)

    save_disabled = bool(errors)

    if st.button(
        "Stintplanung speichern",
        use_container_width=True,
        disabled=save_disabled,
    ):
        saved_plan = (
            edited_dataframe
            .sort_values("Stint")
            .to_dict(
                orient="records"
            )
        )

        st.session_state[
            "strategy_stints"
        ] = saved_plan

        st.session_state.pop(
            "strategy_pitstops",
            None,
        )

        st.success(
            "Stintplanung gespeichert."
        )

        st.rerun()

    st.divider()

    st.subheader("Geplanter Rennverlauf")

    sorted_plan = edited_dataframe.sort_values(
        "Stint"
    )

    for _, stint in sorted_plan.iterrows():
        with st.container(border=True):
            col1, col2, col3, col4 = (
                st.columns(4)
            )

            col1.metric(
                "Stint",
                int(stint["Stint"]),
            )

            col2.metric(
                "Runden",
                (
                    f"{int(stint['Start Runde'])}"
                    "–"
                    f"{int(stint['Ende Runde'])}"
                ),
            )

            col3.metric(
                "Tankmenge",
                (
                    f"{float(stint['Tankmenge Start']):.1f} l"
                ),
            )

            col4.metric(
                "Reifensatz",
                stint.get(
                    "Reifensatz",
                    "-",
                ),
            )

            if stint.get("Fahrer"):
                st.write(
                    f"**Fahrer:** "
                    f"{stint['Fahrer']}"
                )

            if stint.get("Bemerkung"):
                st.info(
                    stint["Bemerkung"]
                )