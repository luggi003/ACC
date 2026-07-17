import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.time_parser import format_seconds


def get_sorted_stints():
    stints = st.session_state.get(
        "strategy_stints",
        [],
    )

    return sorted(
        stints,
        key=lambda entry: int(
            entry.get("Stint", 0)
        ),
    )


def get_sorted_pitstops():
    pitstops = st.session_state.get(
        "strategy_pitstops",
        [],
    )

    return sorted(
        pitstops,
        key=lambda entry: int(
            entry.get("Stop", 0)
        ),
    )


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


def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def calculate_summary(
    parameters,
    fuel_strategy,
    stints,
    pitstops,
):
    total_laps = sum(
        safe_int(stint.get("Runden"))
        for stint in stints
    )

    total_refuel = sum(
        safe_float(stop.get("Nachtanken"))
        for stop in pitstops
    )

    total_pit_loss = sum(
        safe_float(
            stop.get(
                "Erwarteter Gesamtverlust"
            )
        )
        for stop in pitstops
    )

    race_duration_seconds = (
        safe_float(
            parameters.get("Renndauer")
        )
        * 60
    )

    average_lap_time = safe_float(
        parameters.get(
            "Durchschnittliche Rundenzeit"
        )
    )

    estimated_driving_time = (
        total_laps * average_lap_time
    )

    estimated_total_time = (
        estimated_driving_time
        + total_pit_loss
    )

    return {
        "Geplante Runden": total_laps,
        "Anzahl Stints": len(stints),
        "Anzahl Stopps": len(pitstops),
        "Starttank": safe_float(
            parameters.get("Starttank")
        ),
        "Gesamtbedarf": safe_float(
            fuel_strategy.get("Gesamtbedarf")
        ),
        "Gesamt Nachtanken": total_refuel,
        "Boxenverlust": total_pit_loss,
        "Fahrzeit": estimated_driving_time,
        "Gesamtzeit": estimated_total_time,
        "Renndauer Soll": race_duration_seconds,
    }


def create_strategy_rows(
    stints,
    tyre_strategy,
):
    rows = []

    for stint in stints:
        stint_number = safe_int(
            stint.get("Stint")
        )

        tyre = tyre_strategy.get(
            stint_number,
            {},
        )

        rows.append(
            {
                "Stint": stint_number,
                "Start Runde": safe_int(
                    stint.get("Start Runde")
                ),
                "Ende Runde": safe_int(
                    stint.get("Ende Runde")
                ),
                "Runden": safe_int(
                    stint.get("Runden")
                ),
                "Tankmenge Start": safe_float(
                    stint.get(
                        "Tankmenge Start"
                    )
                ),
                "Nachtanken": safe_float(
                    stint.get("Nachtanken")
                ),
                "Reifensatz": tyre.get(
                    "Reifensatz",
                    stint.get(
                        "Reifensatz",
                        "-",
                    ),
                ),
                "Reifenwechsel": bool(
                    tyre.get(
                        "Reifenwechsel",
                        stint.get(
                            "Reifenwechsel",
                            False,
                        ),
                    )
                ),
                "Doppelstint": bool(
                    tyre.get(
                        "Doppelstint",
                        False,
                    )
                ),
                "Fahrer": stint.get(
                    "Fahrer",
                    "",
                ),
                "Bemerkung": stint.get(
                    "Bemerkung",
                    "",
                ),
            }
        )

    return rows


def create_timeline_figure(
    strategy_rows,
    pitstops,
):
    figure = go.Figure()

    for row in strategy_rows:
        stint_number = row["Stint"]
        start_lap = row["Start Runde"]
        end_lap = row["Ende Runde"]

        figure.add_trace(
            go.Bar(
                x=[
                    end_lap
                    - start_lap
                    + 1
                ],
                y=[
                    f"Stint {stint_number}"
                ],
                base=[start_lap - 1],
                orientation="h",
                name=f"Stint {stint_number}",
                text=[
                    (
                        f"Runde {start_lap}–{end_lap}<br>"
                        f"{row['Reifensatz']}<br>"
                        f"{row['Tankmenge Start']:.1f} l"
                    )
                ],
                textposition="inside",
                hovertemplate=(
                    f"Stint {stint_number}<br>"
                    f"Runden: {start_lap}–{end_lap}<br>"
                    f"Tank: {row['Tankmenge Start']:.1f} l<br>"
                    f"Reifen: {row['Reifensatz']}"
                    "<extra></extra>"
                ),
            )
        )

    for stop in pitstops:
        pit_lap = safe_int(
            stop.get("Boxenrunde")
        )

        figure.add_vline(
            x=pit_lap,
            line_dash="dash",
            annotation_text=(
                f"Stop {safe_int(stop.get('Stop'))}"
            ),
            annotation_position="top",
        )

    figure.update_layout(
        title="Strategie-Zeitachse",
        xaxis_title="Runde",
        yaxis_title="Stint",
        barmode="overlay",
        showlegend=False,
        height=max(
            320,
            90 * len(strategy_rows),
        ),
    )

    figure.update_xaxes(
        dtick=1,
    )

    return figure


def show_strategy_cards(
    strategy_rows,
    pitstops,
):
    pitstop_by_stint = {
        safe_int(
            stop.get("Nach Stint")
        ): stop
        for stop in pitstops
    }

    for row in strategy_rows:
        stint_number = row["Stint"]

        with st.container(border=True):
            st.markdown(
                f"### Stint {stint_number}"
            )

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Runden",
                (
                    f"{row['Start Runde']}–"
                    f"{row['Ende Runde']}"
                ),
            )

            col2.metric(
                "Anzahl Runden",
                row["Runden"],
            )

            col3.metric(
                "Tankmenge",
                f"{row['Tankmenge Start']:.1f} l",
            )

            col4.metric(
                "Reifensatz",
                row["Reifensatz"],
            )

            if row.get("Fahrer"):
                st.write(
                    f"**Fahrer:** {row['Fahrer']}"
                )

            st.write(
                "**Reifenwechsel vor diesem Stint:** "
                + (
                    "Ja"
                    if row["Reifenwechsel"]
                    else "Nein"
                )
            )

            st.write(
                "**Doppelstint:** "
                + (
                    "Ja"
                    if row["Doppelstint"]
                    else "Nein"
                )
            )

            if row.get("Bemerkung"):
                st.info(
                    row["Bemerkung"]
                )

            stop = pitstop_by_stint.get(
                stint_number
            )

            if stop is not None:
                st.divider()
                st.markdown(
                    f"#### Boxenstopp nach Stint {stint_number}"
                )

                stop_col1, stop_col2, stop_col3 = (
                    st.columns(3)
                )

                stop_col1.metric(
                    "Boxenrunde",
                    safe_int(
                        stop.get("Boxenrunde")
                    ),
                )

                stop_col2.metric(
                    "Nachtanken",
                    (
                        f"{safe_float(stop.get('Nachtanken')):.1f} l"
                    ),
                )

                stop_col3.metric(
                    "Zeitverlust",
                    (
                        f"{safe_float(stop.get('Erwarteter Gesamtverlust')):.1f} s"
                    ),
                )

                st.write(
                    "**Reifenwechsel:** "
                    + (
                        "Ja"
                        if bool(
                            stop.get(
                                "Reifenwechsel"
                            )
                        )
                        else "Nein"
                    )
                )

                if bool(
                    stop.get("Fahrerwechsel")
                ):
                    st.write(
                        "**Fahrerwechsel:** Ja"
                    )

                    st.write(
                        f"**Neuer Fahrer:** "
                        f"{stop.get('Neuer Fahrer', '-')}"
                    )


def show():
    st.subheader("Strategieübersicht")

    required_states = {
        "strategy_parameters":
            "Rennparameter",
        "strategy_fuel":
            "Kraftstoffstrategie",
        "strategy_stints":
            "Stintplanung",
        "strategy_tyres":
            "Reifenstrategie",
        "strategy_pitstops":
            "Boxenstrategie",
    }

    missing = [
        label
        for key, label
        in required_states.items()
        if key not in st.session_state
    ]

    if missing:
        st.warning(
            "Folgende Bereiche müssen zuerst "
            "erstellt und gespeichert werden: "
            + ", ".join(missing)
        )
        return

    parameters = st.session_state[
        "strategy_parameters"
    ]

    fuel_strategy = st.session_state[
        "strategy_fuel"
    ]

    stints = get_sorted_stints()
    pitstops = get_sorted_pitstops()
    tyre_strategy = (
        get_tyre_strategy_by_stint()
    )

    if not stints:
        st.warning(
            "Die Stintplanung enthält keine Daten."
        )
        return

    summary = calculate_summary(
        parameters,
        fuel_strategy,
        stints,
        pitstops,
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Geplante Runden",
        summary["Geplante Runden"],
    )

    col2.metric(
        "Stints",
        summary["Anzahl Stints"],
    )

    col3.metric(
        "Stopps",
        summary["Anzahl Stopps"],
    )

    col4.metric(
        "Gesamtbedarf",
        f"{summary['Gesamtbedarf']:.1f} l",
    )

    col5, col6, col7, col8 = st.columns(4)

    col5.metric(
        "Starttank",
        f"{summary['Starttank']:.1f} l",
    )

    col6.metric(
        "Gesamt Nachtanken",
        f"{summary['Gesamt Nachtanken']:.1f} l",
    )

    col7.metric(
        "Boxenverlust",
        f"{summary['Boxenverlust']:.1f} s",
    )

    col8.metric(
        "Geschätzte Gesamtzeit",
        format_seconds(
            summary["Gesamtzeit"]
        ),
    )

    st.divider()

    strategy_rows = create_strategy_rows(
        stints,
        tyre_strategy,
    )

    strategy_dataframe = pd.DataFrame(
        strategy_rows
    )

    st.subheader("Gesamtplan")

    st.dataframe(
        strategy_dataframe,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Tankmenge Start":
                st.column_config.NumberColumn(
                    "Tankmenge Start",
                    format="%.1f l",
                ),
            "Nachtanken":
                st.column_config.NumberColumn(
                    "Nachtanken",
                    format="%.1f l",
                ),
        },
    )

    st.divider()

    timeline_figure = create_timeline_figure(
        strategy_rows,
        pitstops,
    )

    st.plotly_chart(
        timeline_figure,
        use_container_width=True,
    )

    st.divider()

    st.subheader("Strategie im Detail")

    show_strategy_cards(
        strategy_rows,
        pitstops,
    )

    st.divider()

    st.subheader("Boxenstoppübersicht")

    if pitstops:
        pitstop_dataframe = pd.DataFrame(
            pitstops
        )

        st.dataframe(
            pitstop_dataframe,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Nachtanken":
                    st.column_config.NumberColumn(
                        "Nachtanken",
                        format="%.1f l",
                    ),
                "Mindeststandzeit":
                    st.column_config.NumberColumn(
                        "Mindeststandzeit",
                        format="%.1f s",
                    ),
                "Pitlane-Verlust":
                    st.column_config.NumberColumn(
                        "Pitlane-Verlust",
                        format="%.1f s",
                    ),
                "Erwarteter Gesamtverlust":
                    st.column_config.NumberColumn(
                        "Gesamtverlust",
                        format="%.1f s",
                    ),
            },
        )
    else:
        st.info(
            "Es sind keine Boxenstopps geplant."
        )

    st.divider()

    fuel_difference = (
        summary["Starttank"]
        + summary["Gesamt Nachtanken"]
        - summary["Gesamtbedarf"]
    )

    if fuel_difference >= 0:
        st.success(
            f"Die Strategie enthält eine rechnerische "
            f"Kraftstoffreserve von "
            f"{fuel_difference:.1f} Litern."
        )
    else:
        st.error(
            f"Die Strategie weist ein rechnerisches "
            f"Kraftstoffdefizit von "
            f"{abs(fuel_difference):.1f} Litern auf."
        )

    required_stops = safe_int(
        parameters.get("Pflichtstopps")
    )

    if len(pitstops) < required_stops:
        st.error(
            "Die Anzahl der geplanten Stopps liegt "
            "unter den vorgeschriebenen Pflichtstopps."
        )

    elif len(pitstops) == required_stops:
        st.success(
            "Die vorgeschriebene Anzahl an "
            "Pflichtstopps wird eingehalten."
        )

    else:
        st.info(
            "Es sind mehr Stopps eingeplant als "
            "durch das Reglement vorgeschrieben."
        )