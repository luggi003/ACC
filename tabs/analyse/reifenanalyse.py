import pandas as pd
import plotly.graph_objects as go
import streamlit as st


TYRE_POSITIONS = [
    "VL",
    "HL",
    "VR",
    "HR",
]


CATEGORY_ORDER = [
    ("VL", "A"),
    ("VL", "M"),
    ("VL", "I"),
    ("HL", "A"),
    ("HL", "M"),
    ("HL", "I"),
    ("VR", "I"),
    ("VR", "M"),
    ("VR", "A"),
    ("HR", "I"),
    ("HR", "M"),
    ("HR", "A"),
]


def safe_float(value):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_tyre_data(tyre):
    if not isinstance(tyre, dict):
        tyre = {}

    wear = tyre.get("Wear")

    if not isinstance(wear, dict):
        wear = {}

    temperature = tyre.get(
        "Temperature"
    )

    if not isinstance(
        temperature,
        dict,
    ):
        temperature = {}

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

    temp_a = temperature.get("A")
    temp_m = temperature.get("M")
    temp_i = temperature.get("I")

    if temp_a is None:
        temp_a = tyre.get(
            "Temperatur Außen"
        )

    if temp_m is None:
        temp_m = tyre.get(
            "Temperatur Mitte"
        )

    if temp_i is None:
        temp_i = tyre.get(
            "Temperatur Innen"
        )

    cold_psi = tyre.get("Cold PSI")

    if cold_psi is None:
        cold_psi = tyre.get("PSI cold")

    hot_psi = tyre.get("Hot PSI")

    if hot_psi is None:
        hot_psi = tyre.get("PSI hot")

    return {
        "Cold PSI": safe_float(cold_psi),
        "Hot PSI": safe_float(hot_psi),
        "Wear": {
            "A": safe_float(wear_a),
            "M": safe_float(wear_m),
            "I": safe_float(wear_i),
        },
        "Temperature": {
            "A": safe_float(temp_a),
            "M": safe_float(temp_m),
            "I": safe_float(temp_i),
        },
    }


def get_available_stints(entries):
    stints = {
        int(entry["Stint"])
        for entry in entries
        if isinstance(entry, dict)
        and entry.get("Stint") is not None
    }

    return sorted(stints)


def select_stints_with_checkboxes(
    available_stints,
):
    st.markdown("#### Stints auswählen")

    col_all, col_none = st.columns(2)

    with col_all:
        if st.button(
            "Alle auswählen",
            key="tyre_analysis_select_all",
            use_container_width=True,
        ):
            for stint in available_stints:
                st.session_state[
                    f"tyre_analysis_stint_{stint}"
                ] = True

            st.rerun()

    with col_none:
        if st.button(
            "Auswahl löschen",
            key="tyre_analysis_clear_all",
            use_container_width=True,
        ):
            for stint in available_stints:
                st.session_state[
                    f"tyre_analysis_stint_{stint}"
                ] = False

            st.rerun()

    columns = st.columns(
        min(len(available_stints), 4)
    )

    selected_stints = []

    for index, stint in enumerate(
        available_stints
    ):
        key = (
            f"tyre_analysis_stint_{stint}"
        )

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


def create_tyre_dataframe(entries):
    rows = []

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        for position in TYRE_POSITIONS:
            tyre = normalize_tyre_data(
                entry.get(position, {})
            )

            wear = tyre["Wear"]

            temperature = tyre[
                "Temperature"
            ]

            rows.append(
                {
                    "Stint": entry.get(
                        "Stint"
                    ),
                    "Reifensatz": entry.get(
                        "Reifensatz",
                        "-",
                    ),
                    "Position": position,
                    "Profiltiefe A": wear.get(
                        "A"
                    ),
                    "Profiltiefe M": wear.get(
                        "M"
                    ),
                    "Profiltiefe I": wear.get(
                        "I"
                    ),
                    "Temperatur A":
                        temperature.get("A"),
                    "Temperatur M":
                        temperature.get("M"),
                    "Temperatur I":
                        temperature.get("I"),
                    "Cold PSI": tyre.get(
                        "Cold PSI"
                    ),
                    "Hot PSI": tyre.get(
                        "Hot PSI"
                    ),
                }
            )

    return pd.DataFrame(rows)


def aggregate_tyre_data(dataframe):
    value_columns = [
        "Profiltiefe A",
        "Profiltiefe M",
        "Profiltiefe I",
        "Temperatur A",
        "Temperatur M",
        "Temperatur I",
        "Cold PSI",
        "Hot PSI",
    ]

    return (
        dataframe
        .groupby(
            [
                "Stint",
                "Position",
            ],
            as_index=False,
        )[value_columns]
        .mean(numeric_only=True)
    )


def get_chart_values(
    dataframe,
    stint,
    value_prefix,
):
    stint_data = dataframe[
        dataframe["Stint"] == stint
    ]

    values = []

    for position, zone in CATEGORY_ORDER:
        row = stint_data[
            stint_data["Position"]
            == position
        ]

        if row.empty:
            values.append(None)
            continue

        value = row.iloc[0].get(
            f"{value_prefix} {zone}"
        )

        if pd.isna(value):
            value = None

        values.append(value)

    return values


def show_tyre_chart(
    dataframe,
    selected_stints,
    value_prefix,
    title,
    y_axis_title,
    unit,
):
    labels = [
        f"{position}-{zone}"
        for position, zone
        in CATEGORY_ORDER
    ]

    figure = go.Figure()

    for stint in selected_stints:
        values = get_chart_values(
            dataframe,
            stint,
            value_prefix,
        )

        figure.add_trace(
            go.Bar(
                x=labels,
                y=values,
                name=f"Stint {stint}",
                text=[
                    (
                        f"{value:.1f}{unit}"
                        if value is not None
                        else ""
                    )
                    for value in values
                ],
                textposition="outside",
                hovertemplate=(
                    "Position: %{x}<br>"
                    f"{y_axis_title}: "
                    f"%{{y:.2f}}{unit}"
                    "<extra></extra>"
                ),
            )
        )

    figure.update_layout(
        title=title,
        xaxis_title=(
            "Links: A–M–I | "
            "Rechts: I–M–A"
        ),
        yaxis_title=y_axis_title,
        barmode="group",
        legend_title="Stint",
    )

    figure.update_xaxes(
        categoryorder="array",
        categoryarray=labels,
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
    )


def show():
    st.subheader("Reifenanalyse")

    tyre_entries = st.session_state.get(
        "tyre_wear_data",
        [],
    )

    if not tyre_entries:
        st.info(
            "Noch keine Reifendaten vorhanden."
        )
        return

    available_stints = get_available_stints(
        tyre_entries
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

    filtered_entries = [
        entry
        for entry in tyre_entries
        if entry.get("Stint")
        in selected_stints
    ]

    dataframe = create_tyre_dataframe(
        filtered_entries
    )

    if dataframe.empty:
        st.warning(
            "Für die ausgewählten Stints sind "
            "keine Reifendaten vorhanden."
        )
        return

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
    )

    aggregated_data = aggregate_tyre_data(
        dataframe
    )

    st.divider()

    show_tyre_chart(
        dataframe=aggregated_data,
        selected_stints=selected_stints,
        value_prefix="Profiltiefe",
        title="Profiltiefe pro Reifen",
        y_axis_title="Profiltiefe",
        unit=" mm",
    )

    st.divider()

    show_tyre_chart(
        dataframe=aggregated_data,
        selected_stints=selected_stints,
        value_prefix="Temperatur",
        title="Reifentemperatur pro Reifen",
        y_axis_title="Temperatur",
        unit=" °C",
    )

    st.divider()

    st.subheader("Druckübersicht")

    pressure_table = aggregated_data[
        [
            "Stint",
            "Position",
            "Cold PSI",
            "Hot PSI",
        ]
    ]

    st.dataframe(
        pressure_table,
        use_container_width=True,
        hide_index=True,
    )