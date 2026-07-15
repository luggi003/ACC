import pandas as pd
import streamlit as st

from utils.time_parser import (
    format_seconds,
    parse_time_to_seconds,
)


def init():
    if "lap_counter" not in st.session_state:
        st.session_state["lap_counter"] = 1

    if "lap_times" not in st.session_state:
        st.session_state["lap_times"] = []


def get_current_laps(session_type, stint):
    return [
        lap
        for lap in st.session_state["lap_times"]
        if lap.get("Session-Art") == session_type
        and lap.get("Stint") == stint
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


def get_best_sector(valid_laps, sector_key):
    sector_values = []

    for lap in valid_laps:
        sector_value = parse_time_to_seconds(
            lap.get(sector_key, "")
        )

        if sector_value is not None:
            sector_values.append(sector_value)

    if not sector_values:
        return None

    return min(sector_values)


def show_statistics(laps, use_sectors):
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

        if (
            best_s1 is not None
            and best_s2 is not None
            and best_s3 is not None
        ):
            ideal_lap = best_s1 + best_s2 + best_s3
        else:
            ideal_lap = None

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric(
                "Beste Runde",
                (
                    best_lap["Rundenzeit"]
                    if best_lap
                    else "-"
                ),
            )

        with col2:
            st.metric(
                "Bester Sektor 1",
                (
                    f"{best_s1:.3f}"
                    if best_s1 is not None
                    else "-"
                ),
            )

        with col3:
            st.metric(
                "Bester Sektor 2",
                (
                    f"{best_s2:.3f}"
                    if best_s2 is not None
                    else "-"
                ),
            )

        with col4:
            st.metric(
                "Bester Sektor 3",
                (
                    f"{best_s3:.3f}"
                    if best_s3 is not None
                    else "-"
                ),
            )

        with col5:
            st.metric(
                "Ideale Runde",
                (
                    format_seconds(ideal_lap)
                    if ideal_lap is not None
                    else "-"
                ),
            )

    else:
        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Beste Runde",
                (
                    best_lap["Rundenzeit"]
                    if best_lap
                    else "-"
                ),
            )

        with col2:
            st.metric(
                "Gültige Runden",
                len(valid_laps),
            )


def show_lap_table(laps, use_sectors):
    if not laps:
        return

    table_rows = []

    for lap in laps:
        row = {
            "Runde": lap.get("Runde"),
            "Stint": lap.get("Stint"),
            "Rundenart": lap.get("Rundenart"),
            "Rundenzeit": lap.get("Rundenzeit"),
            "Gültig": "Ja" if lap.get("Gültig") else "Nein",
            "Bemerkung": lap.get("Bemerkung", ""),
        }

        if use_sectors:
            row.update(
                {
                    "Sektor 1": lap.get("Sektor 1", ""),
                    "Sektor 2": lap.get("Sektor 2", ""),
                    "Sektor 3": lap.get("Sektor 3", ""),
                }
            )

        table_rows.append(row)

    dataframe = pd.DataFrame(table_rows)

    if use_sectors:
        column_order = [
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
        column_order = [
            "Runde",
            "Stint",
            "Rundenart",
            "Rundenzeit",
            "Gültig",
            "Bemerkung",
        ]

    dataframe = dataframe[column_order]

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
    )


def show():
    init()

    st.header("Rundenzeiten")

    if "training_overview" not in st.session_state:
        st.warning("Bitte zuerst die Übersicht ausfüllen.")
        return

    overview = st.session_state["training_overview"]
    stint = overview.get("Stint", 1)
    ziel = overview.get("Ziel", "-")
    session_name = overview.get("Trainingssession", "-")

    session_type = st.session_state.get(
        "tracking_info",
        {},
    ).get(
        "Session-Art",
        "Training",
    )

    use_sectors = session_type in [
        "Training",
        "Qualifying",
    ]

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Stint", stint)

    with col2:
        st.metric("Session", session_name)

    with col3:
        st.metric("Ziel", ziel)

    st.divider()

    current_laps = get_current_laps(
        session_type,
        stint,
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
            st.session_state["lap_counter"],
        )

    with col_minus:
        if st.button(
            "➖",
            key="lap_minus",
            use_container_width=True,
        ):
            st.session_state["lap_counter"] = max(
                1,
                st.session_state["lap_counter"] - 1,
            )
            st.rerun()

    with col_plus:
        if st.button(
            "➕",
            key="lap_plus",
            use_container_width=True,
        ):
            st.session_state["lap_counter"] += 1
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

    with st.form("lap_form"):
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

            s1 = parse_time_to_seconds(sector_1)
            s2 = parse_time_to_seconds(sector_2)
            s3 = parse_time_to_seconds(sector_3)

            if (
                s1 is not None
                and s2 is not None
                and s3 is not None
            ):
                total_seconds = s1 + s2 + s3
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

            total_seconds = parse_time_to_seconds(
                lap_time
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

            current_lap = st.session_state[
                "lap_counter"
            ]

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

            st.session_state["lap_times"].append(
                lap_entry
            )

            st.session_state["lap_counter"] += 1

            st.success(
                f"Runde {current_lap} gespeichert."
            )
            st.rerun()

    st.divider()

    current_laps = get_current_laps(
        session_type,
        stint,
    )

    if current_laps:
        st.subheader("Gespeicherte Runden")

        show_lap_table(
            current_laps,
            use_sectors,
        )
    else:
        st.info(
            "Für diesen Stint wurden noch keine "
            "Runden gespeichert."
        )