import pandas as pd
import plotly.graph_objects as go
import streamlit as st


def get_available_stints(entries):
    stints = {
        int(entry["Stint"])
        for entry in entries
        if entry.get("Stint") is not None
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
            key="fuel_analysis_select_all",
            use_container_width=True,
        ):
            for stint in available_stints:
                st.session_state[
                    f"fuel_analysis_stint_{stint}"
                ] = True

            st.rerun()

    with col_none:
        if st.button(
            "Auswahl löschen",
            key="fuel_analysis_clear_all",
            use_container_width=True,
        ):
            for stint in available_stints:
                st.session_state[
                    f"fuel_analysis_stint_{stint}"
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
            f"fuel_analysis_stint_{stint}"
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


def show():
    st.subheader("Spritverbrauchsanalyse")

    fuel_data = st.session_state.get(
        "fuel_data",
        [],
    )

    if not fuel_data:
        st.info(
            "Noch keine Spritdaten vorhanden."
        )
        return

    available_stints = get_available_stints(
        fuel_data
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

    filtered_data = [
        entry
        for entry in fuel_data
        if entry.get("Stint")
        in selected_stints
    ]

    consumptions = [
        float(
            entry["ConsumptionPerLap"]
        )
        for entry in filtered_data
        if entry.get(
            "ConsumptionPerLap"
        ) is not None
    ]

    if not consumptions:
        st.warning(
            "Für die ausgewählten Stints sind "
            "keine Verbrauchswerte vorhanden."
        )
        return

    average = (
        sum(consumptions)
        / len(consumptions)
    )

    minimum = min(consumptions)
    maximum = max(consumptions)

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Ø Verbrauch",
        f"{average:.2f} l/Runde",
    )

    col2.metric(
        "Niedrigster Verbrauch",
        f"{minimum:.2f} l/Runde",
    )

    col3.metric(
        "Höchster Verbrauch",
        f"{maximum:.2f} l/Runde",
    )

    rows = []

    for index, entry in enumerate(
        filtered_data,
        start=1,
    ):
        rows.append(
            {
                "Messung": index,
                "Stint": entry.get("Stint"),
                "Runden": entry.get("Laps"),
                "Starttank": entry.get(
                    "StartFuel"
                ),
                "Endtank": entry.get(
                    "EndFuel"
                ),
                "Verbrauch gesamt":
                    entry.get(
                        "Consumption"
                    ),
                "Verbrauch/Runde":
                    entry.get(
                        "ConsumptionPerLap"
                    ),
                "Restreichweite":
                    entry.get(
                        "RemainingLaps"
                    ),
            }
        )

    dataframe = pd.DataFrame(rows)

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True,
    )

    figure = go.Figure()

    for stint in selected_stints:
        stint_data = dataframe[
            dataframe["Stint"] == stint
        ]

        figure.add_trace(
            go.Bar(
                x=[
                    f"Messung {value}"
                    for value
                    in stint_data["Messung"]
                ],
                y=stint_data[
                    "Verbrauch/Runde"
                ],
                name=f"Stint {stint}",
                text=[
                    f"{value:.2f} l"
                    for value
                    in stint_data[
                        "Verbrauch/Runde"
                    ]
                ],
                textposition="outside",
            )
        )

    figure.update_layout(
        title="Verbrauch pro Runde",
        xaxis_title="Messung",
        yaxis_title="Liter pro Runde",
        barmode="group",
        legend_title="Stint",
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
    )