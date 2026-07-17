import math

import streamlit as st


def calculate_strategy(parameters):
    race_duration_seconds = (
        float(parameters["Renndauer"]) * 60
    )

    average_lap_time = float(
        parameters["Durchschnittliche Rundenzeit"]
    )

    fuel_per_lap = float(
        parameters["Verbrauch pro Runde"]
    )

    tank_capacity = float(
        parameters["Tankvolumen"]
    )

    planned_start_fuel = float(
        parameters["Starttank"]
    )

    safety_laps = int(
        parameters["Sicherheitsrunden"]
    )

    mandatory_stops = int(
        parameters.get("Pflichtstopps", 0)
    )

    # Aufrunden, damit eine eventuell begonnene letzte Runde
    # ebenfalls eingeplant wird.
    expected_race_laps = math.ceil(
        race_duration_seconds / average_lap_time
    )

    planned_laps = (
        expected_race_laps + safety_laps
    )

    total_fuel_required = (
        planned_laps * fuel_per_lap
    )

    maximum_laps_per_full_tank = math.floor(
        tank_capacity / fuel_per_lap
    )

    maximum_laps_start_tank = math.floor(
        planned_start_fuel / fuel_per_lap
    )

    # Minimale Stintanzahl, die sich aus dem Tankvolumen ergibt.
    minimum_stints_by_fuel = math.ceil(
        total_fuel_required / tank_capacity
    )

    minimum_stops_by_fuel = max(
        0,
        minimum_stints_by_fuel - 1,
    )

    required_stops = max(
        mandatory_stops,
        minimum_stops_by_fuel,
    )

    number_of_stints = required_stops + 1

    start_fuel = min(
        planned_start_fuel,
        tank_capacity,
        total_fuel_required,
    )

    remaining_fuel_need = max(
        0.0,
        total_fuel_required - start_fuel,
    )

    fuel_per_remaining_stint = (
        remaining_fuel_need / required_stops
        if required_stops > 0
        else 0.0
    )

    return {
        "Erwartete Rennrunden": expected_race_laps,
        "Geplante Runden inkl. Reserve": planned_laps,
        "Gesamtbedarf": total_fuel_required,
        "Starttank": start_fuel,
        "Restlicher Tankbedarf": remaining_fuel_need,
        "Maximale Runden voller Tank":
            maximum_laps_per_full_tank,
        "Maximale Runden Starttank":
            maximum_laps_start_tank,
        "Minimale Stopps durch Tank":
            minimum_stops_by_fuel,
        "Pflichtstopps": mandatory_stops,
        "Geplante Stopps": required_stops,
        "Anzahl Stints": number_of_stints,
        "Tankmenge je weiterem Stint":
            fuel_per_remaining_stint,
    }


def show():
    st.subheader("Kraftstoffstrategie")

    if "strategy_parameters" not in st.session_state:
        st.warning(
            "Bitte zuerst die Rennparameter speichern."
        )
        return

    parameters = st.session_state[
        "strategy_parameters"
    ]

    strategy = calculate_strategy(parameters)

    st.session_state[
        "strategy_fuel"
    ] = strategy

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Erwartete Rennrunden",
            strategy["Erwartete Rennrunden"],
        )

    with col2:
        st.metric(
            "Runden inkl. Reserve",
            strategy[
                "Geplante Runden inkl. Reserve"
            ],
        )

    with col3:
        st.metric(
            "Gesamtbedarf",
            f"{strategy['Gesamtbedarf']:.1f} l",
        )

    with col4:
        st.metric(
            "Geplante Stopps",
            strategy["Geplante Stopps"],
        )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Starttank",
            f"{strategy['Starttank']:.1f} l",
        )

    with col2:
        st.metric(
            "Reichweite Starttank",
            (
                f"{strategy['Maximale Runden Starttank']} "
                "Runden"
            ),
        )

    with col3:
        st.metric(
            "Reichweite voller Tank",
            (
                f"{strategy['Maximale Runden voller Tank']} "
                "Runden"
            ),
        )

    st.divider()

    if (
        strategy["Minimale Stopps durch Tank"]
        > strategy["Pflichtstopps"]
    ):
        st.warning(
            "Aufgrund des Tankvolumens sind mehr Stopps "
            "notwendig als durch das Reglement vorgeschrieben."
        )

    elif (
        strategy["Pflichtstopps"]
        > strategy["Minimale Stopps durch Tank"]
    ):
        st.info(
            "Die Anzahl der Stopps wird durch das Reglement "
            "und nicht durch die Tankreichweite bestimmt."
        )

    else:
        st.success(
            "Pflichtstopps und notwendige Tankstopps stimmen überein."
        )

    st.subheader("Vorgeschlagene Tankaufteilung")

    number_of_stints = strategy["Anzahl Stints"]

    suggested_fuel = []

    remaining = strategy["Gesamtbedarf"]

    for stint_number in range(
        1,
        number_of_stints + 1,
    ):
        if stint_number == 1:
            fuel_amount = min(
                strategy["Starttank"],
                remaining,
            )
        else:
            remaining_stints = (
                number_of_stints
                - stint_number
                + 1
            )

            fuel_amount = min(
                parameters["Tankvolumen"],
                remaining / remaining_stints,
            )

        suggested_fuel.append(
            {
                "Stint": stint_number,
                "Tankmenge": fuel_amount,
                "Erwartete Reichweite": (
                    fuel_amount
                    / parameters["Verbrauch pro Runde"]
                ),
            }
        )

        remaining = max(
            0.0,
            remaining - fuel_amount,
        )

    st.session_state[
        "strategy_fuel_stints"
    ] = suggested_fuel

    for stint in suggested_fuel:
        with st.container(border=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Stint",
                    stint["Stint"],
                )

            with col2:
                st.metric(
                    "Tankmenge",
                    f"{stint['Tankmenge']:.1f} l",
                )

            with col3:
                st.metric(
                    "Theoretische Reichweite",
                    (
                        f"{stint['Erwartete Reichweite']:.1f} "
                        "Runden"
                    ),
                )

    st.divider()

    reserve_fuel = (
        parameters["Sicherheitsrunden"]
        * parameters["Verbrauch pro Runde"]
    )

    st.write(
        f"**Sicherheitsreserve:** "
        f"{parameters['Sicherheitsrunden']} Runden "
        f"= {reserve_fuel:.1f} Liter"
    )

    st.write(
        f"**Restlicher Tankbedarf nach dem Start:** "
        f"{strategy['Restlicher Tankbedarf']:.1f} Liter"
    )