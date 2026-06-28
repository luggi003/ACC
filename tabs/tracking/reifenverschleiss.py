import streamlit as st

from tabs.tracking.components.tyre_box import tyre_box
from tabs.tracking.components.car_image import show_car_image


def init_session_state():
    if "tyre_wear_data" not in st.session_state:
        st.session_state["tyre_wear_data"] = []


def show_header(overview):

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Stint",
            overview["Stint"],
        )

    with col2:
        st.metric(
            "Session",
            overview["Trainingssession"],
        )

    with col3:
        st.metric(
            "Ziel",
            overview["Ziel"],
        )


def show():

    st.header("Reifenverschleiß")

    if "training_overview" not in st.session_state:
        st.warning(
            "Bitte zuerst die Trainingsübersicht ausfüllen."
        )
        return

    init_session_state()

    overview = st.session_state["training_overview"]

    show_header(overview)

    st.divider()

    # ---------------------------------------------------
    # Allgemeine Informationen
    # ---------------------------------------------------

    col1, col2 = st.columns(2)

    with col1:

        tyre_set = st.selectbox(
            "Reifensatz",
            [
                "Satz 1",
                "Satz 2",
                "Satz 3",
                "Satz 4",
                "Satz 5",
            ],
        )

    with col2:

        tyre_status = st.selectbox(
            "Reifenstatus",
            [
                "Neu",
                "Eingefahren",
                "Gebraucht",
            ],
        )

    st.divider()

    # ---------------------------------------------------
    # Formular
    # ---------------------------------------------------

    with st.form("reifen_tracking"):

        st.subheader("Reifenübersicht")

        # ---------------- Vorderachse ----------------

        col_left, col_car, col_right = st.columns(
            [1.15, 0.7, 1.15]
        )

        with col_left:
            vl_data = tyre_box("VL")

        with col_car:
            st.empty()

        with col_right:
            vr_data = tyre_box("VR")

        st.write("")

        # ---------------- Fahrzeug ----------------

        left, center, right = st.columns(
            [1.15, 0.7, 1.15]
        )

        with left:
            st.empty()

        with center:
            show_car_image()

        with right:
            st.empty()

        st.write("")

        # ---------------- Hinterachse ----------------

        col_left, col_car, col_right = st.columns(
            [1.15, 0.7, 1.15]
        )

        with col_left:
            hl_data = tyre_box("HL")

        with col_car:
            st.empty()

        with col_right:
            hr_data = tyre_box("HR")

        st.divider()

        notes = st.text_area(
            "Bemerkungen",
            placeholder="z.B. Untersteuern, Überhitzen der Vorderreifen, Druck steigt zu schnell...",
            height=90,
        )

        submit = st.form_submit_button(
            "💾 Reifendaten speichern",
            use_container_width=True,
        )
                # ---------------------------------------------------
        # Speichern
        # ---------------------------------------------------

        if submit:

            tyre_entry = {
                "Stint": overview["Stint"],
                "Trainingssession": overview["Trainingssession"],
                "Ziel": overview["Ziel"],
                "Reifensatz": tyre_set,
                "Reifenstatus": tyre_status,
                "Bemerkungen": notes,
                "VL": vl_data,
                "VR": vr_data,
                "HL": hl_data,
                "HR": hr_data,
            }

            st.session_state["tyre_wear_data"].append(
                tyre_entry
            )

            st.success("Reifendaten gespeichert.")

            st.rerun()

    # =======================================================
    # Gespeicherte Reifendaten
    # =======================================================

    if not st.session_state["tyre_wear_data"]:
        return

    st.divider()

    st.subheader("Gespeicherte Reifendaten")

    for index, entry in enumerate(
        st.session_state["tyre_wear_data"],
        start=1,
    ):

        with st.expander(
            f"Stint {entry['Stint']} | "
            f"{entry['Reifensatz']} | "
            f"{entry['Reifenstatus']}"
        ):

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Stint",
                entry["Stint"],
            )

            col2.metric(
                "Session",
                entry["Trainingssession"],
            )

            col3.metric(
                "Ziel",
                entry["Ziel"],
            )

            tyre_tabs = st.tabs(
                [
                    "VL",
                    "VR",
                    "HL",
                    "HR",
                ]
            )

            positions = ["VL", "VR", "HL", "HR"]

            for tab, position in zip(
                tyre_tabs,
                positions,
            ):

                tyre = entry[position]

                with tab:

                    left, right = st.columns(2)

                    with left:

                        st.markdown("##### Druck")

                        st.write(
                            f"Cold PSI: **{tyre['Cold PSI']:.1f}**"
                        )

                        st.write(
                            f"Hot PSI: **{tyre['Hot PSI']:.1f}**"
                        )

                        st.markdown("##### Verschleiß")

                        wear = tyre["Wear"]

                        st.write(
                            f"Außen: {wear['A']:.1f} mm"
                        )

                        st.write(
                            f"Mitte: {wear['M']:.1f} mm"
                        )

                        st.write(
                            f"Innen: {wear['I']:.1f} mm"
                        )

                    with right:

                        st.markdown("##### Temperatur")

                        temp = tyre["Temperature"]

                        st.write(
                            f"Außen: {temp['A']} °C"
                        )

                        st.write(
                            f"Mitte: {temp['M']} °C"
                        )

                        st.write(
                            f"Innen: {temp['I']} °C"
                        )

                        st.markdown("##### Schäden")

                        damage = tyre["Damage"]

                        st.write(
                            f"Graining: {damage['Graining']}"
                        )

                        st.write(
                            f"Blasenbildung: {damage['Blasenbildung']}"
                        )

                        st.write(
                            f"Bremsplatten: {damage['Bremsplatten']}"
                        )

                        st.markdown("##### Bremsen")

                        brakes = tyre["Brakes"]

                        st.write(
                            f"Beläge: {brakes['Beläge']}"
                        )

                        st.write(
                            f"Scheiben: {brakes['Scheiben']}"
                        )

            if entry["Bemerkungen"]:

                st.divider()

                st.info(
                    entry["Bemerkungen"]
                )