import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.time_parser import (
    format_seconds,
)


TYRE_POSITIONS = [
    "VL",
    "HL",
    "VR",
    "HR",
]


def safe_float(value):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_wear(tyre):
    if not isinstance(tyre, dict):
        tyre = {}

    wear = tyre.get("Wear")

    if not isinstance(wear, dict):
        wear = {}

    wear_a = wear.get("A")
    wear_m = wear.get("M")
    wear_i = wear.get("I")

    if wear_a is None:
        wear_a = tyre.get(
            "Verschleiß Außen"
        )

    if wear_m is None:
        wear_m = tyre.get(
            "Verschleiß Mitte"
        )

    if wear_i is None:
        wear_i = tyre.get(
            "Verschleiß Innen"
        )

    return {
        "A": safe_float(wear_a),
        "M": safe_float(wear_m),
        "I": safe_float(wear_i),
    }


def average(values):
    valid_values = [
        value
        for value in values
        if value is not None
    ]

    if not valid_values:
        return None

    return (
        sum(valid_values)
        / len(valid_values)
    )


def get_available_stints(
    laps,
    tyre_entries,
):
    lap_stints = {
        int(lap["Stint"])
        for lap in laps
        if lap.get("Stint") is not None
    }

    tyre_stints = {
        int(entry["Stint"])
        for entry in tyre_entries
        if entry.get("Stint") is not None
    }

    return sorted(
        lap_stints.intersection(
            tyre_stints
        )
    )


def select_stints_with_checkboxes(
    available_stints,
):
    st.markdown("#### Stints auswählen")

    col_all, col_none = st.columns(2)

    with col_all:
        if st.button(
            "Alle auswählen",
            key="tyre_lap_select_all",
            use_container_width=True,
        ):
            for stint in available_stints:
                st.session_state[
                    f"tyre_lap_stint_{stint}"
                ] = True

            st.rerun()

    with col_none:
        if st.button(
            "Auswahl löschen",
            key="tyre_lap_clear_all",
            use_container_width=True,
        ):
            for stint in available_stints:
                st.session_state[
                    f"tyre_lap_stint_{stint}"
                ] = False

            st.rerun()

    columns = st.columns(
        min(len(available_stints), 4)
    )

    selected_stints = []

    for index, stint in enumerate(
        available_stints
    ):
        key = f"tyre_lap_stint_{stint}"

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


def get_lap_statistics(
    laps,
    stint,
):
    valid_laps = [
        lap
        for lap in laps
        if lap.get("Stint") == stint
        and lap.get("Gültig", True)
        and lap.get("Sekunden") is not None
    ]

    if not valid_laps:
        return None

    seconds = [
        float(lap["Sekunden"])
        for lap in valid_laps
    ]

    return {
        "Runden": len(valid_laps),
        "Beste Runde": min(seconds),
        "Durchschnitt": (
            sum(seconds)
            / len(seconds)
        ),
    }


def get_tyre_statistics(
    tyre_entries,
    stint,
):
    matching_entries = [
        entry
        for entry in tyre_entries
        if entry.get("Stint") == stint
    ]

    if not matching_entries:
        return None

    # Neueste Messung des Stints verwenden
    latest_entry = matching_entries[-1]

    profile_by_position = {}

    for position in TYRE_POSITIONS:
        wear = normalize_wear(
            latest_entry.get(position, {})
        )

        profile_by_position[position] = (
            average(
                [
                    wear.get("A"),
                    wear.get("M"),
                    wear.get("I"),
                ]
            )
        )

    valid_profiles = [
        value
        for value
        in profile_by_position.values()
        if value is not None
    ]

    if not valid_profiles:
        return None

    overall_profile = average(
        valid_profiles
    )

    tyre_consumption = max(
        0.0,
        3.0 - overall_profile,
    )

    return {
        "Profiltiefe VL":
            profile_by_position.get("VL"),
        "Profiltiefe HL":
            profile_by_position.get("HL"),
        "Profiltiefe VR":
            profile_by_position.get("VR"),
        "Profiltiefe HR":
            profile_by_position.get("HR"),
        "Ø Profiltiefe":
            overall_profile,
        "Ø Reifenverbrauch":
            tyre_consumption,
    }


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


def show():
    st.subheader(
        "Reifenverbrauch im Vergleich "
        "zur Rundenzeit"
    )

    laps = st.session_state.get(
        "lap_times",
        [],
    )

    tyre_entries = st.session_state.get(
        "tyre_wear_data",
        [],
    )

    if not laps:
        st.info(
            "Noch keine Rundenzeiten vorhanden."
        )
        return

    if not tyre_entries:
        st.info(
            "Noch keine Reifendaten vorhanden."
        )
        return

    available_stints = get_available_stints(
        laps,
        tyre_entries,
    )

    if not available_stints:
        st.warning(
            "Es gibt keinen Stint, für den "
            "Rundenzeiten und Reifendaten "
            "vorhanden sind."
        )
        return

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

    rows = []

    for stint in selected_stints:
        lap_statistics = (
            get_lap_statistics(
                laps,
                stint,
            )
        )

        tyre_statistics = (
            get_tyre_statistics(
                tyre_entries,
                stint,
            )
        )

        if (
            lap_statistics is None
            or tyre_statistics is None
        ):
            continue

        rows.append(
            {
                "Stint": stint,
                **lap_statistics,
                **tyre_statistics,
            }
        )

    if not rows:
        st.warning(
            "Für die ausgewählten Stints "
            "konnten keine gemeinsamen Daten "
            "berechnet werden."
        )
        return

    dataframe = pd.DataFrame(rows)

    display_dataframe = dataframe.copy()

    display_dataframe["Beste Runde"] = (
        display_dataframe[
            "Beste Runde"
        ].apply(format_seconds)
    )

    display_dataframe["Durchschnitt"] = (
        display_dataframe[
            "Durchschnitt"
        ].apply(format_seconds)
    )

    st.dataframe(
        display_dataframe,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    tick_values, tick_labels = (
        create_time_ticks(
            dataframe[
                "Durchschnitt"
            ].tolist()
        )
    )

    figure = go.Figure()

    figure.add_trace(
        go.Scatter(
            x=dataframe[
                "Ø Reifenverbrauch"
            ],
            y=dataframe[
                "Durchschnitt"
            ],
            mode="markers+text",
            text=[
                f"Stint {stint}"
                for stint
                in dataframe["Stint"]
            ],
            textposition="top center",
            customdata=[
                [
                    row["Stint"],
                    row["Runden"],
                    row["Ø Profiltiefe"],
                    format_seconds(
                        row["Beste Runde"]
                    ),
                    format_seconds(
                        row["Durchschnitt"]
                    ),
                ]
                for _, row
                in dataframe.iterrows()
            ],
            hovertemplate=(
                "Stint %{customdata[0]}<br>"
                "Runden: %{customdata[1]}<br>"
                "Reifenverbrauch: "
                "%{x:.3f} mm<br>"
                "Ø Profiltiefe: "
                "%{customdata[2]:.3f} mm<br>"
                "Beste Runde: "
                "%{customdata[3]}<br>"
                "Ø Rundenzeit: "
                "%{customdata[4]}"
                "<extra></extra>"
            ),
            name="Stints",
        )
    )

    figure.update_layout(
        title=(
            "Rundenzeit im Verhältnis "
            "zum Reifenverbrauch"
        ),
        xaxis_title=(
            "Durchschnittlicher "
            "Reifenverbrauch (mm)"
        ),
        yaxis_title=(
            "Durchschnittliche Rundenzeit"
        ),
        showlegend=False,
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

    st.caption(
        "Für jeden Stint wird die neueste "
        "Reifenmessung verwendet. Der Verbrauch "
        "wird ausgehend von 3,0 mm Profiltiefe "
        "berechnet."
    )