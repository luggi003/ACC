import streamlit as st

from tabs.tracking.components.tyre_box import (
    tyre_box,
)
from tabs.tracking.components.car_image import (
    show_car_image,
)


def init_session_state():
    if "tyre_wear_data" not in st.session_state:
        st.session_state["tyre_wear_data"] = []

    if "race_tyre_stint" not in st.session_state:
        st.session_state["race_tyre_stint"] = 1


def show_header(
    stint,
    session_name,
    ziel,
):
    col1, col2, col3 = st.columns(3)

    col1.metric("Stint", stint)
    col2.metric("Session", session_name)
    col3.metric("Ziel", ziel)


def get_current_entries(
    session_type,
    stint,
    session_name,
):
    return [
        entry
        for entry in st.session_state[
            "tyre_wear_data"
        ]
        if entry.get("Session-Art") == session_type
        and entry.get("Stint") == stint
        and entry.get("Trainingssession")
        == session_name
    ]


def show_saved_entries(entries):
    if not entries:
        return

    st.divider()
    st.subheader("Gespeicherte Reifendaten")

    for index, entry in enumerate(
        entries,
        start=1,
    ):
        with st.expander(
            f"Eintrag {index} | "
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

            for tab, position in zip(
                tyre_tabs,
                ["VL", "VR", "HL", "HR"],
            ):
                tyre = entry[position]

                with tab:
                    left, right = st.columns(2)

                    with left:
                        st.markdown("##### Druck")

                        st.write(
                            f"Cold PSI: "
                            f"**{tyre['Cold PSI']:.1f}**"
                        )

                        st.write(
                            f"Hot PSI: "
                            f"**{tyre['Hot PSI']:.1f}**"
                        )

                        st.markdown(
                            "##### Verschleiß"
                        )

                        wear = tyre["Wear"]

                        st.write(
                            f"Außen: "
                            f"{wear['A']:.1f} mm"
                        )

                        st.write(
                            f"Mitte: "
                            f"{wear['M']:.1f} mm"
                        )

                        st.write(
                            f"Innen: "
                            f"{wear['I']:.1f} mm"
                        )

                    with right:
                        st.markdown(
                            "##### Temperatur"
                        )

                        temperature = tyre[
                            "Temperature"
                        ]

                        st.write(
                            f"Außen: "
                            f"{temperature['A']} °C"
                        )

                        st.write(
                            f"Mitte: "
                            f"{temperature['M']} °C"
                        )

                        st.write(
                            f"Innen: "
                            f"{temperature['I']} °C"
                        )

                        st.markdown("##### Schäden")

                        damage = tyre["Damage"]

                        st.write(
                            f"Graining: "
                            f"{damage['Graining']}"
                        )

                        st.write(
                            f"Blasenbildung: "
                            f"{damage['Blasenbildung']}"
                        )

                        st.write(
                            f"Bremsplatten: "
                            f"{damage['Bremsplatten']}"
                        )

                        st.markdown("##### Bremsen")

                        brakes = tyre["Brakes"]

                        st.write(
                            f"Beläge: "
                            f"{brakes['Beläge']}"
                        )

                        st.write(
                            f"Scheiben: "
                            f"{brakes['Scheiben']}"
                        )

            if entry.get("Bemerkungen"):
                st.divider()
                st.info(entry["Bemerkungen"])


def show():
    init_session_state()

    st.header("Reifenverschleiß")

    if "training_overview" not in st.session_state:
        st.warning(
            "Bitte zuerst die Übersicht ausfüllen."
        )
        return

    overview = st.session_state["training_overview"]

    session_type = st.session_state.get(
        "tracking_info",
        {},
    ).get(
        "Session-Art",
        "Training",
    )

    if overview.get("Session-Art") != session_type:
        st.warning(
            "Bitte zuerst die Übersicht für die "
            "aktuelle Session-Art speichern."
        )
        return

    session_name = overview.get(
        "Trainingssession",
        session_type,
    )

    ziel = overview.get(
        "Ziel",
        session_type,
    )

    # Rennen: Stint direkt im Reifen-Tab auswählen
    if session_type == "Rennen":
        stint = st.number_input(
            "Stint",
            min_value=1,
            value=int(
                st.session_state["race_tyre_stint"]
            ),
            step=1,
            key="race_tyre_stint_input",
        )

        stint = int(stint)
        st.session_state["race_tyre_stint"] = stint

    else:
        stint = int(
            overview.get("Stint", 1)
        )

    show_header(
        stint,
        session_name,
        ziel,
    )

    st.divider()

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
            key=(
                f"tyre_set_"
                f"{session_type}_{stint}"
            ),
        )

    with col2:
        tyre_status = st.selectbox(
            "Reifenstatus",
            [
                "Neu",
                "Eingefahren",
                "Gebraucht",
            ],
            key=(
                f"tyre_status_"
                f"{session_type}_{stint}"
            ),
        )

    st.divider()

    form_key = (
        f"reifen_tracking_"
        f"{session_type}_{stint}"
    )

    with st.form(form_key):
        st.subheader("Reifenübersicht")

        # Vorderachse
        top_left, top_center, top_right = st.columns(
            [1.15, 0.7, 1.15]
        )

        with top_left:
            vl_data = tyre_box("VL")

        with top_center:
            st.empty()

        with top_right:
            vr_data = tyre_box("VR")

        st.write("")

        # Fahrzeug
        car_left, car_center, car_right = st.columns(
            [1.15, 0.7, 1.15]
        )

        with car_left:
            st.empty()

        with car_center:
            show_car_image()

        with car_right:
            st.empty()

        st.write("")

        # Hinterachse
        bottom_left, bottom_center, bottom_right = (
            st.columns([1.15, 0.7, 1.15])
        )

        with bottom_left:
            hl_data = tyre_box("HL")

        with bottom_center:
            st.empty()

        with bottom_right:
            hr_data = tyre_box("HR")

        st.divider()

        notes = st.text_area(
            "Bemerkungen",
            placeholder=(
                "z. B. Untersteuern, Überhitzen, "
                "Druck steigt zu schnell ..."
            ),
            height=90,
        )

        submit = st.form_submit_button(
            "Reifendaten speichern",
            use_container_width=True,
        )

        if submit:
            tyre_entry = {
                "Session-Art": session_type,
                "Stint": stint,
                "Trainingssession": session_name,
                "Ziel": ziel,
                "Reifensatz": tyre_set,
                "Reifenstatus": tyre_status,
                "Bemerkungen": notes,
                "VL": vl_data,
                "VR": vr_data,
                "HL": hl_data,
                "HR": hr_data,
            }

            st.session_state[
                "tyre_wear_data"
            ].append(tyre_entry)

            st.success(
                "Reifendaten gespeichert."
            )
            st.rerun()

    current_entries = get_current_entries(
        session_type,
        stint,
        session_name,
    )

    if current_entries:
        show_saved_entries(current_entries)
    else:
        st.info(
            f"Für Stint {stint} wurden noch "
            "keine Reifendaten gespeichert."
        )