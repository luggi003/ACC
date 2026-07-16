import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.time_parser import (
    format_seconds,
    parse_time_to_seconds,
)


def get_available_stints(laps):
    stints = {
        int(lap["Stint"])
        for lap in laps
        if lap.get("Stint") is not None
    }

    return sorted(stints)


def select_stints_with_checkboxes(
    available_stints,
):
    st.markdown("#### Stints auswählen")

    if not available_stints:
        return []

    col_all, col_none = st.columns(2)

    with col_all:
        if st.button(
            "Alle auswählen",
            key="lap_analysis_select_all",
            use_container_width=True,
        ):
            for stint in available_stints:
                st.session_state[
                    f"lap_analysis_stint_{stint}"
                ] = True

            st.rerun()

    with col_none:
        if st.button(
            "Auswahl löschen",
            key="lap_analysis_clear_all",
            use_container_width=True,
        ):
            for stint in available_stints:
                st.session_state[
                    f"lap_analysis_stint_{stint}"
                ] = False

            st.rerun()

    columns = st.columns(
        min(len(available_stints), 4)
    )

    selected_stints = []

    for index, stint in enumerate(
        available_stints
    ):
        key = f"lap_analysis_stint_{stint}"

        if key not in st.session_state:
            st.session_state[key] = True

        with columns[index % len(columns)]:
            checked = st.checkbox(
                f"Stint {stint}",
                key=key,
            )

        if checked:
            selected_stints.append(stint)

    return selected_stints


def get_valid_laps(laps):
    return [
        lap
        for lap in laps
        if lap.get("Gültig", True)
        and lap.get("Sekunden") is not None
    ]


def get_best_sector(
    laps,
    sector_key,
):
    values = []

    for lap in laps:
        seconds = parse_time_to_seconds(
            lap.get(sector_key, "")
        )

        if seconds is not None:
            values.append(seconds)

    return min(values) if values else None


def create_time_ticks(
    values,
    count=6,
):
    if not values:
        return [], []

    minimum = min(values)
    maximum = max(values)

    if minimum == maximum:
        minimum -= 0.5
        maximum += 0.5

    step = (
        maximum - minimum
    ) / max(count - 1, 1)

    tick_values = [
        minimum + index * step
        for index in range(count)
    ]

    tick_labels = [
        format_seconds(value)
        for value in tick_values
    ]

    return tick_values, tick_labels


def show_lap_chart(laps):
    if not laps:
        return

    values = [
        float(lap["Sekunden"])
        for lap in laps
    ]

    tick_values, tick_labels = (
        create_time_ticks(values)
    )

    figure = go.Figure()

    stints = sorted(
        {
            int(lap["Stint"])
            for lap in laps
            if lap.get("Stint") is not None
        }
    )

    for stint in stints:
        stint_laps = [
            lap
            for lap in laps
            if lap.get("Stint") == stint
        ]

        stint_laps = sorted(
            stint_laps,
            key=lambda lap: lap.get(
                "Runde",
                0,
            ),
        )

        figure.add_trace(
            go.Scatter(
                x=[
                    lap.get("Runde")
                    for lap in stint_laps
                ],
                y=[
                    lap.get("Sekunden")
                    for lap in stint_laps
                ],
                mode="lines+markers",
                name=f"Stint {stint}",
                customdata=[
                    [
                        lap.get(
                            "Rundenzeit",
                            "",
                        ),
                        lap.get(
                            "Rundenart",
                            "",
                        ),
                        lap.get(
                            "Bemerkung",
                            "",
                        ),
                    ]
                    for lap in stint_laps
                ],
                hovertemplate=(
                    "Runde %{x}<br>"
                    "Zeit: %{customdata[0]}<br>"
                    "Art: %{customdata[1]}<br>"
                    "Bemerkung: %{customdata[2]}"
                    "<extra></extra>"
                ),
            )
        )

    figure.update_layout(
        title="Rundenzeiten-Verlauf",
        xaxis_title="Runde",
        yaxis_title="Rundenzeit",
        hovermode="closest",
        legend_title="Stint",
    )

    figure.update_xaxes(
        dtick=1,
    )

    figure.update_yaxes(
        tickmode="array",
        tickvals=tick_values,
        ticktext=tick_labels,
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
    )


def show():
    st.subheader("Rundenanalyse")

    all_laps = st.session_state.get(
        "lap_times",
        [],
    )

    if not all_laps:
        st.info(
            "Noch keine Rundenzeiten vorhanden."
        )
        return

    available_stints = get_available_stints(
        all_laps
    )

    selected_stints = (
        select_stints_with_checkboxes(
            available_stints
        )
    )

    if not selected_stints:
        st.warning(
            "Bitte mindestens einen Stint auswählen."
        )
        return

    filtered_laps = [
        lap
        for lap in all_laps
        if lap.get("Stint") in selected_stints
    ]

    valid_laps = get_valid_laps(
        filtered_laps
    )

    if not valid_laps:
        st.warning(
            "Für die ausgewählten Stints sind "
            "keine gültigen Runden vorhanden."
        )
        return

    best_lap = min(
        valid_laps,
        key=lambda lap: lap["Sekunden"],
    )

    average_seconds = sum(
        lap["Sekunden"]
        for lap in valid_laps
    ) / len(valid_laps)

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

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Beste Runde",
        best_lap.get("Rundenzeit", "-"),
    )

    col2.metric(
        "Durchschnitt",
        format_seconds(average_seconds),
    )

    col3.metric(
        "Ideale Runde",
        (
            format_seconds(ideal_lap)
            if ideal_lap is not None
            else "-"
        ),
    )

    col4.metric(
        "Gültige Runden",
        len(valid_laps),
    )

    if ideal_lap is not None:
        sector_col1, sector_col2, sector_col3 = (
            st.columns(3)
        )

        sector_col1.metric(
            "Bester Sektor 1",
            f"{best_s1:.3f} s",
        )

        sector_col2.metric(
            "Bester Sektor 2",
            f"{best_s2:.3f} s",
        )

        sector_col3.metric(
            "Bester Sektor 3",
            f"{best_s3:.3f} s",
        )

    st.divider()

    rows = []

    for lap in valid_laps:
        delta = (
            lap["Sekunden"]
            - best_lap["Sekunden"]
        )

        rows.append(
            {
                "Stint": lap.get("Stint"),
                "Runde": lap.get("Runde"),
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
                "Rundenzeit": lap.get(
                    "Rundenzeit",
                    "",
                ),
                "Delta": (
                    f"+{delta:.3f} s"
                    if delta > 0
                    else "0.000 s"
                ),
                "Rundenart": lap.get(
                    "Rundenart",
                    "",
                ),
                "Bemerkung": lap.get(
                    "Bemerkung",
                    "",
                ),
            }
        )

    dataframe = pd.DataFrame(rows)

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    show_lap_chart(valid_laps)