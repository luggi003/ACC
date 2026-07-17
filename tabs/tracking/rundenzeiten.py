from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from tabs.tracking import rundenzeiten_bildimport
from utils.time_parser import (
    format_seconds,
    parse_time_to_seconds,
)


# =========================================================
# INITIALISIERUNG
# =========================================================

def init() -> None:
    if "lap_times" not in st.session_state:
        st.session_state["lap_times"] = []

    # Eigener Rundenzähler für jede Kombination aus:
    # Session-Art, Sessionname und Stint
    if "lap_counters" not in st.session_state:
        st.session_state["lap_counters"] = {}

    if "race_lap_stint" not in st.session_state:
        st.session_state["race_lap_stint"] = 1


# =========================================================
# ALLGEMEINE HILFSFUNKTIONEN
# =========================================================

def get_session_type() -> str:
    return st.session_state.get(
        "tracking_info",
        {},
    ).get(
        "Session-Art",
        "Training",
    )


def get_overview() -> dict[str, Any]:
    return st.session_state.get(
        "training_overview",
        {},
    )


def get_lap_counter_key(
    session_type: str,
    session_name: str,
    stint: int,
) -> str:
    return (
        f"{session_type}|"
        f"{session_name}|"
        f"{int(stint)}"
    )


def get_lap_counter(
    session_type: str,
    session_name: str,
    stint: int,
) -> int:
    key = get_lap_counter_key(
        session_type,
        session_name,
        stint,
    )

    if key not in st.session_state["lap_counters"]:
        existing_laps = get_current_laps(
            session_type=session_type,
            stint=stint,
            session_name=session_name,
        )

        existing_numbers = [
            int(lap.get("Runde", 0))
            for lap in existing_laps
            if lap.get("Runde") is not None
        ]

        if existing_numbers:
            next_lap = max(existing_numbers) + 1
        else:
            next_lap = 1

        st.session_state["lap_counters"][key] = next_lap

    return int(
        st.session_state["lap_counters"][key]
    )


def set_lap_counter(
    session_type: str,
    session_name: str,
    stint: int,
    value: int,
) -> None:
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
    session_type: str,
    stint: int,
    session_name: str,
) -> list[dict[str, Any]]:
    return [
        lap
        for lap in st.session_state.get(
            "lap_times",
            [],
        )
        if lap.get("Session-Art") == session_type
        and int(lap.get("Stint", 0)) == int(stint)
        and lap.get("Trainingssession") == session_name
    ]


def get_valid_laps(
    laps: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        lap
        for lap in laps
        if lap.get("Gültig", True)
        and lap.get("Sekunden") is not None
    ]


def get_best_lap(
    valid_laps: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not valid_laps:
        return None

    return min(
        valid_laps,
        key=lambda lap: float(
            lap["Sekunden"]
        ),
    )


def get_best_sector(
    valid_laps: list[dict[str, Any]],
    sector_key: str,
) -> float | None:
    values = []

    for lap in valid_laps:
        value = parse_time_to_seconds(
            str(
                lap.get(
                    sector_key,
                    "",
                )
            )
        )

        if value is not None:
            values.append(float(value))

    return min(values) if values else None


def is_strategy_test(
    overview: dict[str, Any],
) -> bool:
    return (
        overview.get("Session-Art") == "Training"
        and overview.get("Ziel")
        == "Strategie-Testlauf"
    )


# =========================================================
# STRATEGIE-TESTLAUF / BLOCKSYSTEM
# =========================================================

def get_stint_lap_number(
    session_type: str,
    stint: int,
    session_name: str,
) -> int:
    """
    Gibt die nächste fortlaufende Runde innerhalb
    des ausgewählten Stints zurück.

    Anders als die angezeigte ACC-Rundennummer beginnt
    dieser Wert in jedem Stint wieder bei 1.
    """

    current_laps = get_current_laps(
        session_type=session_type,
        stint=stint,
        session_name=session_name,
    )

    stint_lap_numbers = [
        int(lap.get("Stint-Runde", 0))
        for lap in current_laps
        if lap.get("Stint-Runde") is not None
    ]

    if stint_lap_numbers:
        return max(stint_lap_numbers) + 1

    return len(current_laps) + 1


def get_block_information(
    stint_lap: int,
    overview: dict[str, Any],
) -> dict[str, int]:
    block_size = max(
        1,
        int(
            overview.get(
                "Blockgröße",
                5,
            )
        ),
    )

    number_of_blocks = max(
        1,
        int(
            overview.get(
                "Anzahl Blöcke",
                1,
            )
        ),
    )

    total_laps = (
        block_size
        * number_of_blocks
    )

    block_number = (
        (stint_lap - 1)
        // block_size
        + 1
    )

    lap_in_block = (
        (stint_lap - 1)
        % block_size
        + 1
    )

    return {
        "Blockgröße": block_size,
        "Anzahl Blöcke": number_of_blocks,
        "Gesamtrunden": total_laps,
        "Block": block_number,
        "Runde im Block": lap_in_block,
        "Stint-Runde": stint_lap,
    }


def show_strategy_test_progress(
    session_type: str,
    session_name: str,
    stint: int,
    overview: dict[str, Any],
) -> None:
    current_laps = get_current_laps(
        session_type=session_type,
        stint=stint,
        session_name=session_name,
    )

    completed_laps = len(current_laps)
    next_stint_lap = completed_laps + 1

    block_info = get_block_information(
        next_stint_lap,
        overview,
    )

    block_size = block_info["Blockgröße"]
    number_of_blocks = block_info[
        "Anzahl Blöcke"
    ]
    total_laps = block_info["Gesamtrunden"]

    completed_blocks = min(
        completed_laps // block_size,
        number_of_blocks,
    )

    current_block = min(
        block_info["Block"],
        number_of_blocks,
    )

    if completed_laps >= total_laps:
        st.success(
            "Der geplante Strategie-Testlauf "
            "ist vollständig abgeschlossen."
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Gefahrene Runden",
            completed_laps,
        )

        col2.metric(
            "Abgeschlossene Blöcke",
            number_of_blocks,
        )

        col3.metric(
            "Geplante Distanz",
            total_laps,
        )

        return

    st.markdown("### Strategie-Testlauf")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Aktueller Block",
        f"{current_block} / {number_of_blocks}",
    )

    col2.metric(
        "Runde im Block",
        (
            f"{block_info['Runde im Block']} "
            f"/ {block_size}"
        ),
    )

    col3.metric(
        "Gesamtrunde",
        (
            f"{next_stint_lap} "
            f"/ {total_laps}"
        ),
    )

    col4.metric(
        "Blöcke abgeschlossen",
        completed_blocks,
    )

    progress_value = min(
        completed_laps / total_laps,
        1.0,
    )

    st.progress(progress_value)

    st.caption(
        f"Testserie: "
        f"{overview.get('Testserie', '-')} | "
        f"Testlauf: "
        f"{overview.get('Testlaufnummer', '-')} | "
        f"Reifensatz: "
        f"{overview.get('Reifensatz', '-')}"
    )


# =========================================================
# STATISTIK
# =========================================================

def show_statistics(
    laps: list[dict[str, Any]],
    use_sectors: bool,
) -> None:
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
                float(best_s1)
                + float(best_s2)
                + float(best_s3)
            )
        else:
            ideal_lap = None

        col1, col2, col3, col4, col5 = (
            st.columns(5)
        )

        col1.metric(
            "Beste Runde",
            (
                best_lap.get(
                    "Rundenzeit",
                    "-",
                )
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
                best_lap.get(
                    "Rundenzeit",
                    "-",
                )
                if best_lap
                else "-"
            ),
        )

        col2.metric(
            "Gültige Runden",
            len(valid_laps),
        )


# =========================================================
# TABELLENANZEIGE
# =========================================================

def show_lap_table(
    laps: list[dict[str, Any]],
    use_sectors: bool,
    strategy_test: bool,
) -> None:
    if not laps:
        return

    rows = []

    sorted_laps = sorted(
        laps,
        key=lambda lap: (
            int(lap.get("Stint", 0)),
            int(
                lap.get(
                    "Stint-Runde",
                    lap.get("Runde", 0),
                )
            ),
        ),
    )

    for lap in sorted_laps:
        row = {
            "Runde": lap.get("Runde"),
            "Stint-Runde": lap.get(
                "Stint-Runde",
                lap.get("Runde"),
            ),
            "Stint": lap.get("Stint"),
            "Rundenart": lap.get(
                "Rundenart",
                "",
            ),
            "Rundenzeit": lap.get(
                "Rundenzeit",
                "",
            ),
            "Gültig": (
                "Ja"
                if lap.get("Gültig", True)
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

        if strategy_test:
            row.update(
                {
                    "Block": lap.get(
                        "Block",
                        "",
                    ),
                    "Runde im Block": lap.get(
                        "Runde im Block",
                        "",
                    ),
                    "Testlauf": lap.get(
                        "Testlaufnummer",
                        "",
                    ),
                }
            )

        rows.append(row)

    dataframe = pd.DataFrame(rows)

    columns = [
        "Runde",
        "Stint-Runde",
        "Stint",
    ]

    if strategy_test:
        columns.extend(
            [
                "Testlauf",
                "Block",
                "Runde im Block",
            ]
        )

    columns.append("Rundenart")

    if use_sectors:
        columns.extend(
            [
                "Sektor 1",
                "Sektor 2",
                "Sektor 3",
            ]
        )

    columns.extend(
        [
            "Rundenzeit",
            "Gültig",
            "Bemerkung",
        ]
    )

    available_columns = [
        column
        for column in columns
        if column in dataframe.columns
    ]

    st.dataframe(
        dataframe[available_columns],
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# MANUELLE EINGABE
# =========================================================

def get_lap_type_options(
    ziel: str,
) -> list[str]:
    if ziel in [
        "Quali-Sim",
        "Setup bauen",
        "Qualifying",
    ]:
        return [
            "Push Lap",
            "Cool Down",
            "Out Lap",
            "In Lap",
        ]

    return [
        "Normale Runde",
        "Cool Down",
        "Out Lap",
        "In Lap",
    ]


def show_manual_input(
    session_type: str,
    session_name: str,
    ziel: str,
    stint: int,
    overview: dict[str, Any],
    use_sectors: bool,
) -> None:
    current_counter = get_lap_counter(
        session_type,
        session_name,
        stint,
    )

    strategy_test = is_strategy_test(
        overview
    )

    if strategy_test:
        show_strategy_test_progress(
            session_type=session_type,
            session_name=session_name,
            stint=stint,
            overview=overview,
        )

        st.divider()

    col_lap, col_minus, col_plus = st.columns(
        [6, 1, 1]
    )

    with col_lap:
        st.metric(
            "Aktuelle ACC-Runde",
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

    lap_type_options = get_lap_type_options(
        ziel
    )

    form_key = (
        f"lap_form_"
        f"{session_type}_"
        f"{session_name}_"
        f"{stint}"
    )

    with st.form(form_key):
        if use_sectors:
            st.subheader("Sektorzeiten")

            col_s1, col_s2, col_s3 = (
                st.columns(3)
            )

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
                for value in [
                    s1,
                    s2,
                    s3,
                ]
            ):
                total_seconds = (
                    float(s1)
                    + float(s2)
                    + float(s3)
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

            stint_lap = get_stint_lap_number(
                session_type,
                stint,
                session_name,
            )

            lap_entry = {
                "Session-Art": session_type,
                "Stint": int(stint),
                "Trainingssession":
                    session_name,
                "Ziel": ziel,
                "Runde": int(current_lap),
                "Stint-Runde": int(
                    stint_lap
                ),
                "Sektor 1": sector_1,
                "Sektor 2": sector_2,
                "Sektor 3": sector_3,
                "Rundenzeit": lap_time,
                "Sekunden": float(
                    total_seconds
                ),
                "Rundenart": lap_type,
                "Gültig": bool(valid),
                "Bemerkung": notes,
                "Importquelle": "Manuell",
            }

            if strategy_test:
                block_info = (
                    get_block_information(
                        stint_lap,
                        overview,
                    )
                )

                lap_entry.update(
                    {
                        "Testserie":
                            overview.get(
                                "Testserie",
                                "",
                            ),
                        "Testlaufnummer":
                            overview.get(
                                "Testlaufnummer"
                            ),
                        "Blockgröße":
                            block_info[
                                "Blockgröße"
                            ],
                        "Anzahl Blöcke":
                            block_info[
                                "Anzahl Blöcke"
                            ],
                        "Block":
                            block_info[
                                "Block"
                            ],
                        "Runde im Block":
                            block_info[
                                "Runde im Block"
                            ],
                        "Referenz-Setup":
                            overview.get(
                                "Referenz-Setup",
                                "",
                            ),
                        "Test-Starttank":
                            overview.get(
                                "Starttank"
                            ),
                        "Test-Reifensatz":
                            overview.get(
                                "Reifensatz"
                            ),
                    }
                )

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
                f"Runde {current_lap} "
                "wurde gespeichert."
            )

            st.rerun()


# =========================================================
# HAUPTFUNKTION
# =========================================================

def show() -> None:
    st.write("Geladene Datei:", __file__)
    st.write("Neue Rundenzeiten-Version aktiv")
    st.stop()
    init()

    st.header("Rundenzeiten")

    overview = get_overview()

    if not overview:
        st.warning(
            "Bitte zuerst die Übersicht ausfüllen."
        )
        return

    session_type = get_session_type()

    if (
        overview.get("Session-Art")
        != session_type
    ):
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

    # Beim Rennen wird der Stint direkt im Tab gewählt.
    if session_type == "Rennen":
        stint = st.number_input(
            "Stint",
            min_value=1,
            value=int(
                st.session_state.get(
                    "race_lap_stint",
                    1,
                )
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
            overview.get(
                "Stint",
                1,
            )
        )

    use_sectors = session_type in [
        "Training",
        "Qualifying",
    ]

    strategy_test = is_strategy_test(
        overview
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Stint",
        stint,
    )

    col2.metric(
        "Session",
        session_name,
    )

    col3.metric(
        "Ziel",
        ziel,
    )

    st.divider()

    current_laps = get_current_laps(
        session_type=session_type,
        stint=stint,
        session_name=session_name,
    )

    show_statistics(
        current_laps,
        use_sectors,
    )

    st.divider()

    input_mode = st.radio(
        "Eingabemethode",
        [
            "Manuelle Eingabe",
            "Bildimport",
        ],
        horizontal=True,
        key=(
            f"lap_input_mode_"
            f"{session_type}_"
            f"{session_name}_"
            f"{stint}"
        ),
    )

    st.divider()

    if input_mode == "Manuelle Eingabe":
        show_manual_input(
            session_type=session_type,
            session_name=session_name,
            ziel=ziel,
            stint=stint,
            overview=overview,
            use_sectors=use_sectors,
        )

    else:
        rundenzeiten_bildimport.show()

    st.divider()

    current_laps = get_current_laps(
        session_type=session_type,
        stint=stint,
        session_name=session_name,
    )

    if current_laps:
        st.subheader(
            "Gespeicherte Runden des "
            f"aktuellen Stints"
        )

        show_lap_table(
            current_laps,
            use_sectors,
            strategy_test,
        )

    else:
        st.info(
            f"Für Stint {stint} wurden noch "
            "keine Runden gespeichert."
        )