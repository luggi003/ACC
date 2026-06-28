import streamlit as st


TYRE_POSITIONS = {
    "VL": "Vorne Links",
    "VR": "Vorne Rechts",
    "HL": "Hinten Links",
    "HR": "Hinten Rechts",
}


def get_cold_psi_from_setup(position):
    setup_data = st.session_state.get("setup_data", {})

    default_values = {
        "VL": 26.0,
        "VR": 26.0,
        "HL": 26.0,
        "HR": 26.0,
    }

    return setup_data.get("Cold PSI", {}).get(position, default_values[position])


def tyre_box(position):
    title = TYRE_POSITIONS[position]
    cold_psi = get_cold_psi_from_setup(position)

    with st.container(border=True):
        st.markdown(f"#### {title}")

        col_psi1, col_psi2 = st.columns(2)

        with col_psi1:
            st.metric("Cold", f"{cold_psi:.1f}")

        with col_psi2:
            psi_hot = st.number_input(
                "Hot",
                value=26.8,
                min_value=0.0,
                step=0.1,
                key=f"{position}_psi_hot",
            )

        st.markdown("**Verschleiß mm**")

        wear_col1, wear_col2, wear_col3 = st.columns(3)

        with wear_col1:
            wear_a = st.number_input(
                "A",
                value=3.0,
                min_value=0.0,
                max_value=3.0,
                step=0.1,
                key=f"{position}_wear_a",
            )

        with wear_col2:
            wear_m = st.number_input(
                "M",
                value=3.0,
                min_value=0.0,
                max_value=3.0,
                step=0.1,
                key=f"{position}_wear_m",
            )

        with wear_col3:
            wear_i = st.number_input(
                "I",
                value=3.0,
                min_value=0.0,
                max_value=3.0,
                step=0.1,
                key=f"{position}_wear_i",
            )

        st.caption("Start 3.0 mm | Wechsel ca. 1.5 mm")

        st.markdown("**Temp °C**")

        temp_col1, temp_col2, temp_col3 = st.columns(3)

        with temp_col1:
            temp_a = st.number_input(
                "A ",
                value=0.0,
                step=1.0,
                key=f"{position}_temp_a",
            )

        with temp_col2:
            temp_m = st.number_input(
                "M ",
                value=0.0,
                step=1.0,
                key=f"{position}_temp_m",
            )

        with temp_col3:
            temp_i = st.number_input(
                "I ",
                value=0.0,
                step=1.0,
                key=f"{position}_temp_i",
            )

        damage_col1, damage_col2, damage_col3 = st.columns(3)

        with damage_col1:
            graining = st.selectbox(
                "Grain",
                ["Keine", "Leicht", "Mittel", "Stark"],
                key=f"{position}_graining",
            )

        with damage_col2:
            blistering = st.selectbox(
                "Blasen",
                ["Keine", "Leicht", "Mittel", "Stark"],
                key=f"{position}_blistering",
            )

        with damage_col3:
            flatspot = st.selectbox(
                "Platten",
                ["Keine", "Leicht", "Mittel", "Stark"],
                key=f"{position}_flatspot",
            )

        brake_col1, brake_col2 = st.columns(2)

        with brake_col1:
            brake_pad = st.number_input(
                "Beläge",
                value=0.0,
                min_value=0.0,
                step=0.1,
                key=f"{position}_brake_pad",
            )

        with brake_col2:
            brake_disc = st.number_input(
                "Scheiben",
                value=0.0,
                min_value=0.0,
                step=0.1,
                key=f"{position}_brake_disc",
            )

        return {
            "Position": position,
            "Name": title,
            "Cold PSI": cold_psi,
            "PSI hot": psi_hot,
            "Verschleiß Außen": wear_a,
            "Verschleiß Mitte": wear_m,
            "Verschleiß Innen": wear_i,
            "Temperatur Außen": temp_a,
            "Temperatur Mitte": temp_m,
            "Temperatur Innen": temp_i,
            "Graining": graining,
            "Blasenbildung": blistering,
            "Bremsplatten": flatspot,
            "Bremsbelagabnutzung": brake_pad,
            "Bremsscheibenabnutzung": brake_disc,
        }