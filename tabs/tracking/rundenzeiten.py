import pandas as pd
import streamlit as st

from utils.time_parser import (
    format_seconds,
    parse_time_to_seconds,
)


def init():
    if "lap_times" not in st.session_state:
        st.session_state["lap_times"] = []

    # Eigener Rundenzähler je Session-Art, Session und Stint
    if "lap_counters" not in st.session_state:
        st.session_state["lap_counters"] = {}

    if "race_lap_stint" not in st.session_state:
        st.session_state["race_lap_stint"] = 1


def get_lap_counter_key(
    session_type,
    session_name,
    stint,
):
    return (
        f"{session_type}|"
        f"{session_name}|"
        f"{int(stint)}"
    )


def get_lap_counter(
    session_type,
    session_name,
    stint,
):
    key = get_lap_counter_key(
        session_type,
        session_name,
        stint,
    )

    if key not in st.session_state["lap_counters"]:
        st.session_state["lap_counters"][key] = 1

    return st.session_state["lap_counters"][key]


def set_lap_counter(
    session_type,
    session_name,
    stint,
    value,
):
    key = get_lap_counter_key(
        session_type,
        session_name,
        stint,
    )

    st.session_state["lap_counters"][key] = max(
        1,
        int(value),
    )


def get_current_laps(
    session_type,
    stint,
    session_name,
):
    return [
        lap
        for lap in st.session_state["lap_times"]
        if lap.get("Session-Art") == session_type
        and lap.get("Stint") == stint
        and lap.get("Trainingssession") == session_name
    ]


def get_valid_laps(laps):
    return [
        lap
        for lap in laps
        if lap.get("Gültig", True)
        and lap.get("Sekunden") is not None
    ]


def get_best_lap(valid_laps):
    if not valid_laps:
        return None

    return min(
        valid_laps,
        key=lambda lap: lap["Sekunden"],
    )


def get_best_sector(
    valid_laps,
    sector_key,
):
    values = []

    for lap in valid_laps:
        value = parse_time_to_seconds(
            lap.get(sector_key, "")
        )

        if value is not None:
            values.append(value)

    return min(values) if values else None


def show_statistics(
    laps,
    use_sectors,
):
    valid_laps = get_valid_laps(laps)
    best_lap = get_best_lap(valid_laps)

    if use_sectors:
        best_s1 = get_best_sector(
            valid_laps,
            "Sektor 1",
        )

        best_s2 = get_best_sector(
            valid_laps,
            "Sektor 2",
        )

        best_s3 = get_best_sector(
            valid_laps,
            "Sektor 3",
        )

        if all(
            value is not None
            for value in [
                best_s1,
                best_s2,
                best_s3,
            ]
        ):
            ideal_lap = (
                best_s1
                + best_s2
                + best_s3
            )
        else:
            ideal_lap = None

        col1, col2, col3, col4, col5 = st.columns(5)

        col1.metric(
            "Beste Runde",
            (
                best_lap["Rundenzeit"]
                if best_lap
                else "-"
            ),
        )

        col2.metric(
            "Bester Sektor 1",
            (
                f"{best_s1:.3f} s"
                if best_s1 is not None
                else "-"
            ),
        )

        col3.metric(
            "Bester Sektor 2",
            (
                f"{best_s2:.3f} s"
                if best_s2 is not None
                else "-"
            ),
        )

        col4.metric(
            "Bester Sektor 3",
            (
                f"{best_s3:.3f} s"
                if best_s3 is not None
                else "-"
            ),
        )

        col5.metric(
            "Ideale Runde",
            (
                format_seconds(ideal_lap)
                if ideal_lap is not None
                else "-"
            ),
        )

    else:
        col1, col2 = st.columns(2)

        col1.metric(
            "Beste Runde",
            (
                best_lap["Rundenzeit"]
                if best_lap
                else "-"
            ),
        )

        col2.metric(
            "Gültige Runden",
            len(valid_laps),
        )


def show_lap_table(
    laps,
    use_sectors,
):
    if not laps:
        return

    rows = []

    for lap in laps:
        row = {
            "Runde": lap.get("Runde"),
            "Stint": lap.get("Stint"),
            "Rundenart": lap.get("Rundenart"),
            "Rundenzeit": lap.get("Rundenzeit"),
            "Gültig": (
                "Ja"
                if lap.get("Gültig")
                else "Nein"
            ),
            "Bemerkung": lap.get(
                "Bemerkung",
                "",
            ),
        }

        if use_sectors:
            row.update(
                {
                    "Sektor 1": lap.get(
                        "Sektor 1",
                        "",
                    ),
                    "Sektor 2": lap.get(
                        "Sektor 2",
                        "",
                    ),
                    "Sektor 3": lap.get(
                        "Sektor 3",
                        "",
                    ),
                }
            )

        rows.append(row)

    dataframe = pd.DataFrame(rows)

    if use_sectors:
        columns = [
            "Runde",
            "Stint",
            "Rundenart",
            "Sektor 1",
            "Sektor 2",
            "Sektor 3",
            "Rundenzeit",
            "Gültig",
            "Bemerkung",
        ]
    else:
        columns = [
            "Runde",
            "Stint",
            "Rundenart",
            "Rundenzeit",
            "Gültig",
            "Bemerkung",
        ]

    st.dataframe(
        dataframe[columns],
        use_container_width=True,
        hide_index=True,
    )


def show():
    init()

    st.header("Rundenzeiten")

    if "training_overview" not in st.session_state:
        st.warning(
            "Bitte zuerst die Übersicht ausfüllen."
        )
        return

    overview = st.session_state[
        "training_overview"
    ]

    session_type = st.session_state.get(
        "tracking_info",
        {},
    ).get(
        "Session-Art",
        "Training",
    )

    if overview.get("Session-Art") != session_type:
        st.warning(
            "Bitte zuerst die Übersicht für die "
            "aktuelle Session-Art speichern."
        )
        return

    session_name = overview.get(
        "Trainingssession",
        session_type,
    )

    ziel = overview.get(
        "Ziel",
        session_type,
    )

    # Beim Rennen wird der Stint direkt hier gewählt.
    if session_type == "Rennen":
        stint = st.number_input(
            "Stint",
            min_value=1,
            value=int(
                st.session_state[
                    "race_lap_stint"
                ]
            ),
            step=1,
            key="race_lap_stint_input",
        )

        stint = int(stint)

        st.session_state[
            "race_lap_stint"
        ] = stint

    else:
        stint = int(
            overview.get("Stint", 1)
        )

    current_counter = get_lap_counter(
        session_type,
        session_name,
        stint,
    )

    use_sectors = session_type in [
        "Training",
        "Qualifying",
    ]

    col1, col2, col3 = st.columns(3)

    col1.metric("Stint", stint)
    col2.metric("Session", session_name)
    col3.metric("Ziel", ziel)

    st.divider()

    current_laps = get_current_laps(
        session_type,
        stint,
        session_name,
    )

    show_statistics(
        current_laps,
        use_sectors,
    )

    st.divider()

    col_lap, col_minus, col_plus = st.columns(
        [6, 1, 1]
    )

    with col_lap:
        st.metric(
            "Aktuelle Runde",
            current_counter,
        )

    with col_minus:
        if st.button(
            "➖",
            key=(
                f"lap_minus_"
                f"{session_type}_"
                f"{session_name}_"
                f"{stint}"
            ),
            use_container_width=True,
        ):
            set_lap_counter(
                session_type,
                session_name,
                stint,
                current_counter - 1,
            )

            st.rerun()

    with col_plus:
        if st.button(
            "➕",
            key=(
                f"lap_plus_"
                f"{session_type}_"
                f"{session_name}_"
                f"{stint}"
            ),
            use_container_width=True,
        ):
            set_lap_counter(
                session_type,
                session_name,
                stint,
                current_counter + 1,
            )

            st.rerun()

    if ziel in [
        "Quali-Sim",
        "Setup bauen",
        "Qualifying",
    ]:
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

    form_key = (
        f"lap_form_"
        f"{session_type}_"
        f"{session_name}_"
        f"{stint}"
    )

    with st.form(form_key):
        if use_sectors:
            st.subheader("Sektorzeiten")

            col_s1, col_s2, col_s3 = st.columns(3)

            with col_s1:
                sector_1 = st.text_input(
                    "Sektor 1",
                    placeholder="32.421",
                )

            with col_s2:
                sector_2 = st.text_input(
                    "Sektor 2",
                    placeholder="39.817",
                )

            with col_s3:
                sector_3 = st.text_input(
                    "Sektor 3",
                    placeholder="35.025",
                )

            s1 = parse_time_to_seconds(
                sector_1
            )

            s2 = parse_time_to_seconds(
                sector_2
            )

            s3 = parse_time_to_seconds(
                sector_3
            )

            if all(
                value is not None
                for value in [s1, s2, s3]
            ):
                total_seconds = (
                    s1 + s2 + s3
                )

                lap_time = format_seconds(
                    total_seconds
                )

                st.metric(
                    "Automatische Rundenzeit",
                    lap_time,
                )
            else:
                total_seconds = None
                lap_time = ""

        else:
            lap_time = st.text_input(
                "Rundenzeit",
                placeholder="1:47.263",
            )

            total_seconds = (
                parse_time_to_seconds(
                    lap_time
                )
            )

            sector_1 = ""
            sector_2 = ""
            sector_3 = ""

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

        submit = st.form_submit_button(
            "Runde speichern",
            use_container_width=True,
        )

        if submit:
            if total_seconds is None:
                st.error(
                    "Bitte gültige Zeiten eingeben."
                )
                return

            current_lap = get_lap_counter(
                session_type,
                session_name,
                stint,
            )

            lap_entry = {
                "Session-Art": session_type,
                "Stint": stint,
                "Trainingssession": session_name,
                "Ziel": ziel,
                "Runde": current_lap,
                "Sektor 1": sector_1,
                "Sektor 2": sector_2,
                "Sektor 3": sector_3,
                "Rundenzeit": lap_time,
                "Sekunden": total_seconds,
                "Rundenart": lap_type,
                "Gültig": valid,
                "Bemerkung": notes,
            }

            st.session_state[
                "lap_times"
            ].append(lap_entry)

            set_lap_counter(
                session_type,
                session_name,
                stint,
                current_lap + 1,
            )

            st.success(
                f"Runde {current_lap} gespeichert."
            )

            st.rerun()

    st.divider()

    current_laps = get_current_laps(
        session_type,
        stint,
        session_name,
    )

    if current_laps:
        st.subheader("Gespeicherte Runden")

        show_lap_table(
            current_laps,
            use_sectors,
        )
    else:
        st.info(
            f"Für Stint {stint} wurden noch "
            "keine Runden gespeichert."
        )