import streamlit as st


def init():
    if "fuel_data" not in st.session_state:
        st.session_state["fuel_data"] = []


def get_completed_laps(stint):
    laps = st.session_state.get("lap_times", [])

    return len(
        [
            lap
            for lap in laps
            if lap.get("Stint") == stint
        ]
    )


def show():
    init()

    st.header("Spritverbrauch")

    if "training_overview" not in st.session_state:
        st.warning("Bitte zuerst die Übersicht ausfüllen.")
        return

    overview = st.session_state["training_overview"]

    stint = overview.get("Stint", 1)
    session_name = overview.get("Trainingssession", "-")
    ziel = overview.get("Ziel", "-")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Stint", stint)

    with col2:
        st.metric("Session", session_name)

    with col3:
        st.metric("Ziel", ziel)

    st.divider()

    completed_laps = get_completed_laps(stint)

    with st.form("fuel_tracking_form"):
        col_start, col_end = st.columns(2)

        with col_start:
            start_fuel = st.number_input(
                "Tankfüllung Start (Liter)",
                min_value=0.0,
                value=65.0,
                step=0.1,
            )

        with col_end:
            end_fuel = st.number_input(
                "Tankfüllung Ende (Liter)",
                min_value=0.0,
                value=30.0,
                step=0.1,
            )

        use_tracked_laps = st.checkbox(
            "Rundenzahl aus Rundenzeiten übernehmen",
            value=True,
        )

        if use_tracked_laps:
            laps = completed_laps
            st.info(f"Erfasste Runden für Stint {stint}: {laps}")
        else:
            laps = st.number_input(
                "Gefahrene Runden",
                min_value=1,
                value=max(completed_laps, 1),
                step=1,
            )

        consumption = max(start_fuel - end_fuel, 0.0)

        if laps > 0:
            consumption_per_lap = consumption / laps
        else:
            consumption_per_lap = 0.0

        if consumption_per_lap > 0:
            remaining_laps = end_fuel / consumption_per_lap
        else:
            remaining_laps = 0.0

        st.divider()
        st.subheader("Berechnete Werte")

        col_a, col_b, col_c, col_d = st.columns(4)

        with col_a:
            st.metric(
                "Runden",
                laps,
            )

        with col_b:
            st.metric(
                "Verbrauch gesamt",
                f"{consumption:.2f} l",
            )

        with col_c:
            st.metric(
                "Verbrauch pro Runde",
                f"{consumption_per_lap:.2f} l",
            )

        with col_d:
            st.metric(
                "Restreichweite",
                f"{remaining_laps:.1f} Runden",
            )

        notes = st.text_area(
            "Bemerkungen",
            height=80,
            placeholder="z. B. viel Lift and Coast, Verkehr, Safety Car ...",
        )

        submit = st.form_submit_button(
            "Spritdaten speichern",
            use_container_width=True,
        )

        if submit:
            if end_fuel > start_fuel:
                st.error(
                    "Die Tankfüllung am Ende kann nicht größer "
                    "als die Tankfüllung am Anfang sein."
                )
                return

            if laps <= 0:
                st.error(
                    "Es wurden noch keine Runden erfasst. "
                    "Bitte Rundenzahl manuell eingeben."
                )
                return

            fuel_entry = {
                "Session-Art": overview.get("Session-Art"),
                "Stint": stint,
                "Trainingssession": session_name,
                "Ziel": ziel,
                "StartFuel": start_fuel,
                "EndFuel": end_fuel,
                "Consumption": consumption,
                "ConsumptionPerLap": consumption_per_lap,
                "RemainingLaps": remaining_laps,
                "Laps": int(laps),
                "Notes": notes,
            }

            st.session_state["fuel_data"].append(fuel_entry)

            st.success("Spritdaten gespeichert.")
            st.rerun()

    if st.session_state["fuel_data"]:
        st.divider()
        st.subheader("Gespeicherte Spritdaten")

        for index, fuel in enumerate(
            st.session_state["fuel_data"],
            start=1,
        ):
            with st.expander(
                f"Eintrag {index} | "
                f"Stint {fuel['Stint']} | "
                f"{fuel['ConsumptionPerLap']:.2f} l/Runde"
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(
                        f"**Session:** {fuel['Trainingssession']}"
                    )
                    st.write(
                        f"**Ziel:** {fuel['Ziel']}"
                    )
                    st.write(
                        f"**Gefahrene Runden:** {fuel['Laps']}"
                    )
                    st.write(
                        f"**Starttank:** {fuel['StartFuel']:.1f} l"
                    )
                    st.write(
                        f"**Endtank:** {fuel['EndFuel']:.1f} l"
                    )

                with col2:
                    st.write(
                        f"**Verbrauch gesamt:** "
                        f"{fuel['Consumption']:.2f} l"
                    )
                    st.write(
                        f"**Verbrauch pro Runde:** "
                        f"{fuel['ConsumptionPerLap']:.2f} l"
                    )
                    st.write(
                        f"**Restreichweite:** "
                        f"{fuel['RemainingLaps']:.1f} Runden"
                    )

                if fuel["Notes"]:
                    st.info(fuel["Notes"])