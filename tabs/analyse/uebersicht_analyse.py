import streamlit as st


def show():
    st.subheader("Analyseübersicht")

    lap_times = st.session_state.get("lap_times", [])
    tyre_data = st.session_state.get("tyre_wear_data", [])
    fuel_data = st.session_state.get("fuel_data", [])

    valid_laps = [
        lap
        for lap in lap_times
        if lap.get("Gültig", True)
        and lap.get("Sekunden") is not None
    ]

    best_lap = None

    if valid_laps:
        best_lap = min(
            valid_laps,
            key=lambda lap: lap["Sekunden"],
        )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Erfasste Runden",
            len(lap_times),
        )

    with col2:
        st.metric(
            "Gültige Runden",
            len(valid_laps),
        )

    with col3:
        st.metric(
            "Reifenmessungen",
            len(tyre_data),
        )

    with col4:
        st.metric(
            "Spritmessungen",
            len(fuel_data),
        )

    st.divider()

    if best_lap:
        st.metric(
            "Beste Runde",
            best_lap.get("Rundenzeit", "-"),
        )
    else:
        st.info("Noch keine gültige Rundenzeit vorhanden.")

    if not lap_times and not tyre_data and not fuel_data:
        st.warning(
            "Es wurden noch keine Tracking-Daten erfasst."
        )