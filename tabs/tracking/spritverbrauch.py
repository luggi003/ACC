import streamlit as st


def init():

    if "fuel_data" not in st.session_state:
        st.session_state["fuel_data"] = []


def get_completed_laps():

    if "lap_times" not in st.session_state:
        return 0

    return len(st.session_state["lap_times"])


def show():

    st.header("Spritverbrauch")

    if "training_overview" not in st.session_state:
        st.warning("Bitte zuerst die Trainingsübersicht ausfüllen.")
        return

    init()

    overview = st.session_state["training_overview"]

    col1, col2, col3 = st.columns(3)

    col1.metric("Stint", overview["Stint"])
    col2.metric("Session", overview["Trainingssession"])
    col3.metric("Ziel", overview["Ziel"])

    st.divider()

    laps = get_completed_laps()

    with st.form("fuel_form"):

        start_fuel = st.number_input(
            "Tankfüllung Start (Liter)",
            value=65.0,
            min_value=0.0,
            step=0.1,
        )

        end_fuel = st.number_input(
            "Tankfüllung Ende (Liter)",
            value=30.0,
            min_value=0.0,
            step=0.1,
        )

        consumption = max(
            0,
            start_fuel - end_fuel,
        )

        if laps > 0:
            consumption_per_lap = consumption / laps
        else:
            consumption_per_lap = 0

        if consumption_per_lap > 0:
            remaining_laps = end_fuel / consumption_per_lap
        else:
            remaining_laps = 0

        st.divider()

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Gefahrene Runden",
                laps,
            )

            st.metric(
                "Verbrauch gesamt",
                f"{consumption:.2f} l",
            )

        with col2:
            st.metric(
                "Verbrauch / Runde",
                f"{consumption_per_lap:.2f} l",
            )

            st.metric(
                "Restreichweite",
                f"{remaining_laps:.1f} Runden",
            )

        notes = st.text_area(
            "Bemerkungen",
            height=80,
        )

        submit = st.form_submit_button(
            "💾 Spritdaten speichern",
            use_container_width=True,
        )

        if submit:

            st.session_state["fuel_data"].append({

                "Stint": overview["Stint"],

                "Trainingssession": overview["Trainingssession"],

                "Ziel": overview["Ziel"],

                "StartFuel": start_fuel,

                "EndFuel": end_fuel,

                "Consumption": consumption,

                "ConsumptionPerLap": consumption_per_lap,

                "RemainingLaps": remaining_laps,

                "Laps": laps,

                "Notes": notes,
            })

            st.success("Spritdaten gespeichert.")

            st.rerun()

    if st.session_state["fuel_data"]:

        st.divider()

        st.subheader("Gespeicherte Spritdaten")

        for i, fuel in enumerate(
            st.session_state["fuel_data"],
            start=1,
        ):

            with st.expander(f"Stint {fuel['Stint']}"):

                col1, col2 = st.columns(2)

                with col1:

                    st.write(
                        f"Starttank: **{fuel['StartFuel']:.1f} l**"
                    )

                    st.write(
                        f"Endtank: **{fuel['EndFuel']:.1f} l**"
                    )

                    st.write(
                        f"Verbrauch: **{fuel['Consumption']:.2f} l**"
                    )

                with col2:

                    st.write(
                        f"Runden: **{fuel['Laps']}**"
                    )

                    st.write(
                        f"Ø Verbrauch: **{fuel['ConsumptionPerLap']:.2f} l**"
                    )

                    st.write(
                        f"Restreichweite: **{fuel['RemainingLaps']:.1f} Runden**"
                    )

                if fuel["Notes"]:
                    st.info(fuel["Notes"])