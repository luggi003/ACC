import streamlit as st

from utils.time_parser import (
    format_seconds,
)


def get_average_lap_time():
    laps = st.session_state.get(
        "lap_times",
        [],
    )

    valid_laps = [
        lap
        for lap in laps
        if lap.get("Gültig", True)
        and lap.get("Sekunden") is not None
        and lap.get("Rundenart")
        not in ["Out Lap", "In Lap", "Cool Down"]
    ]

    if not valid_laps:
        return None

    return sum(
        float(lap["Sekunden"])
        for lap in valid_laps
    ) / len(valid_laps)


def get_average_fuel_consumption():
    fuel_data = st.session_state.get(
        "fuel_data",
        [],
    )

    values = [
        float(entry["ConsumptionPerLap"])
        for entry in fuel_data
        if entry.get("ConsumptionPerLap") is not None
        and float(entry["ConsumptionPerLap"]) > 0
    ]

    if not values:
        return None

    return sum(values) / len(values)


def get_race_overview():
    overview = st.session_state.get(
        "training_overview",
        {},
    )

    if overview.get("Session-Art") != "Rennen":
        return {}

    return overview


def get_track_pitlane_time():
    general_info = st.session_state.get(
        "allgemeine_info",
        {},
    )

    track = general_info.get("Track")

    if track is None:
        return 0.0

    value = getattr(
        track,
        "pit_lane_time",
        0.0,
    )

    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def init_strategy_parameters():
    if "strategy_parameters" not in st.session_state:
        race_overview = get_race_overview()

        average_lap = get_average_lap_time()
        average_fuel = get_average_fuel_consumption()

        st.session_state["strategy_parameters"] = {
            "Renndauer": int(
                race_overview.get(
                    "Renndauer",
                    60,
                )
            ),
            "Durchschnittliche Rundenzeit":
                average_lap or 105.0,
            "Verbrauch pro Runde":
                average_fuel or 3.0,
            "Tankvolumen": 120.0,
            "Starttank": 70.0,
            "Sicherheitsrunden": 2,
            "Pflichtstopps": int(
                race_overview.get(
                    "Pflichtstopps",
                    1,
                )
            ),
            "Pflichtboxenstopp": bool(
                race_overview.get(
                    "Pflichtboxenstopp",
                    True,
                )
            ),
            "Fahrerwechsel": bool(
                race_overview.get(
                    "Fahrerwechsel",
                    False,
                )
            ),
            "Mindeststandzeit": 0.0,
            "Pitlane Time": get_track_pitlane_time(),
            "Reifenwechsel erlaubt": True,
            "Reifenwechsel verpflichtend": False,
        }


def show():
    st.subheader("Rennparameter")

    init_strategy_parameters()

    parameters = st.session_state[
        "strategy_parameters"
    ]

    detected_lap_time = get_average_lap_time()
    detected_fuel = get_average_fuel_consumption()

    if (
        detected_lap_time is not None
        or detected_fuel is not None
    ):
        st.info(
            "Vorhandene Tracking-Daten wurden als "
            "Vorschlagswerte übernommen."
        )

    with st.form("strategy_parameters_form"):
        col1, col2 = st.columns(2)

        with col1:
            race_duration = st.number_input(
                "Renndauer in Minuten",
                min_value=1,
                value=int(
                    parameters.get(
                        "Renndauer",
                        60,
                    )
                ),
                step=5,
            )

            average_lap_time = st.number_input(
                "Durchschnittliche Rundenzeit in Sekunden",
                min_value=1.0,
                value=float(
                    parameters.get(
                        "Durchschnittliche Rundenzeit",
                        105.0,
                    )
                ),
                step=0.1,
                format="%.3f",
            )

            st.caption(
                "Entspricht ungefähr "
                f"{format_seconds(average_lap_time)}"
            )

            fuel_per_lap = st.number_input(
                "Verbrauch pro Runde in Liter",
                min_value=0.01,
                value=float(
                    parameters.get(
                        "Verbrauch pro Runde",
                        3.0,
                    )
                ),
                step=0.01,
                format="%.2f",
            )

            tank_capacity = st.number_input(
                "Tankvolumen in Liter",
                min_value=1.0,
                value=float(
                    parameters.get(
                        "Tankvolumen",
                        120.0,
                    )
                ),
                step=1.0,
            )

            start_fuel = st.number_input(
                "Geplanter Starttank in Liter",
                min_value=0.0,
                max_value=float(tank_capacity),
                value=min(
                    float(
                        parameters.get(
                            "Starttank",
                            70.0,
                        )
                    ),
                    float(tank_capacity),
                ),
                step=1.0,
            )

        with col2:
            safety_laps = st.number_input(
                "Sicherheitsreserve in Runden",
                min_value=0,
                value=int(
                    parameters.get(
                        "Sicherheitsrunden",
                        2,
                    )
                ),
                step=1,
            )

            mandatory_stop = st.checkbox(
                "Pflichtboxenstopp",
                value=bool(
                    parameters.get(
                        "Pflichtboxenstopp",
                        True,
                    )
                ),
            )

            mandatory_stops = st.number_input(
                "Anzahl Pflichtstopps",
                min_value=0,
                value=int(
                    parameters.get(
                        "Pflichtstopps",
                        1,
                    )
                    if mandatory_stop
                    else 0
                ),
                step=1,
                disabled=not mandatory_stop,
            )

            driver_change = st.checkbox(
                "Fahrerwechsel notwendig",
                value=bool(
                    parameters.get(
                        "Fahrerwechsel",
                        False,
                    )
                ),
            )

            minimum_stop_time = st.number_input(
                "Mindeststandzeit in Sekunden",
                min_value=0.0,
                value=float(
                    parameters.get(
                        "Mindeststandzeit",
                        0.0,
                    )
                ),
                step=1.0,
            )

            pitlane_time = st.number_input(
                "Pitlane-Verlustzeit in Sekunden",
                min_value=0.0,
                value=float(
                    parameters.get(
                        "Pitlane Time",
                        0.0,
                    )
                ),
                step=0.1,
            )

            tyre_change_allowed = st.checkbox(
                "Reifenwechsel erlaubt",
                value=bool(
                    parameters.get(
                        "Reifenwechsel erlaubt",
                        True,
                    )
                ),
            )

            tyre_change_required = st.checkbox(
                "Reifenwechsel verpflichtend",
                value=bool(
                    parameters.get(
                        "Reifenwechsel verpflichtend",
                        False,
                    )
                ),
                disabled=not tyre_change_allowed,
            )

        submit = st.form_submit_button(
            "Rennparameter speichern",
            use_container_width=True,
        )

        if submit:
            st.session_state[
                "strategy_parameters"
            ] = {
                "Renndauer": int(race_duration),
                "Durchschnittliche Rundenzeit":
                    float(average_lap_time),
                "Verbrauch pro Runde":
                    float(fuel_per_lap),
                "Tankvolumen":
                    float(tank_capacity),
                "Starttank":
                    float(start_fuel),
                "Sicherheitsrunden":
                    int(safety_laps),
                "Pflichtstopps": (
                    int(mandatory_stops)
                    if mandatory_stop
                    else 0
                ),
                "Pflichtboxenstopp":
                    mandatory_stop,
                "Fahrerwechsel":
                    driver_change,
                "Mindeststandzeit":
                    float(minimum_stop_time),
                "Pitlane Time":
                    float(pitlane_time),
                "Reifenwechsel erlaubt":
                    tyre_change_allowed,
                "Reifenwechsel verpflichtend": (
                    tyre_change_required
                    if tyre_change_allowed
                    else False
                ),
            }

            st.session_state.pop(
                "strategy_stints",
                None,
            )

            st.session_state.pop(
                "strategy_pitstops",
                None,
            )

            st.success(
                "Rennparameter gespeichert."
            )

            st.rerun()

    st.divider()

    saved = st.session_state[
        "strategy_parameters"
    ]

    expected_laps = (
        saved["Renndauer"] * 60
        / saved["Durchschnittliche Rundenzeit"]
    )

    expected_laps_rounded = int(
        expected_laps
    )

    fuel_need = (
        expected_laps_rounded
        + saved["Sicherheitsrunden"]
    ) * saved["Verbrauch pro Runde"]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Erwartete Rennrunden",
        expected_laps_rounded,
    )

    col2.metric(
        "Gesamtbedarf mit Reserve",
        f"{fuel_need:.1f} l",
    )

    col3.metric(
        "Pitlane-Verlust",
        f"{saved['Pitlane Time']:.1f} s",
    )