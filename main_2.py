from pathlib import Path

import streamlit as st
import track_classes

from tabs import event_info

from tabs.tracking import (
    uebersicht,
    rundenzeiten,
    reifenverschleiss,
    spritverbrauch,
    quali_ergebnis,
    training_ergebnis,
    rennen_ergebnis,
)

from tabs.analyse import (
    uebersicht_analyse,
    rundenanalyse,
    reifenanalyse,
    spritanalyse,
    reifen_rundenzeit,
)

st.set_page_config(
    page_title="ACC Analyse",
    layout="wide",
)


# =========================================================
# SESSION STATE INITIALISIEREN
# =========================================================

if "start_info_saved" not in st.session_state:
    st.session_state["start_info_saved"] = False

if "lap_counter" not in st.session_state:
    st.session_state["lap_counter"] = 1

if "lap_times" not in st.session_state:
    st.session_state["lap_times"] = []

if "fuel_data" not in st.session_state:
    st.session_state["fuel_data"] = []

if "tyre_wear_data" not in st.session_state:
    st.session_state["tyre_wear_data"] = []


# =========================================================
# STARTINFORMATIONEN
# =========================================================

if not st.session_state["start_info_saved"]:
    st.title("ACC – Startinformationen")

    with st.form("start_form"):
        selected_track = st.selectbox(
            "Strecke",
            track_classes.ALL_TRACKS,
        )

        weather = st.selectbox(
            "Wetter",
            [
                "Sonnig",
                "Bewölkt",
                "Regen leicht",
                "Regen mittel",
                "Regen stark",
                "Sturm",
            ],
        )

        temp = st.number_input(
            "Temperatur (°C)",
            value=25.0,
            step=1.0,
        )

        track_temp = st.number_input(
            "Streckentemperatur (°C)",
            value=30.0,
            step=1.0,
        )

        submit = st.form_submit_button("Weiter")

        if submit:
            # Daten einer vorherigen Session zurücksetzen
            st.session_state["lap_counter"] = 1
            st.session_state["lap_times"] = []
            st.session_state["fuel_data"] = []
            st.session_state["tyre_wear_data"] = []

            st.session_state.pop("event_info", None)
            st.session_state.pop("tracking_info", None)
            st.session_state.pop("training_overview", None)
            st.session_state.pop("quali_result", None)
            st.session_state.pop("training_result", None)
            st.session_state.pop("race_result", None)

            st.session_state["allgemeine_info"] = {
                "Track": selected_track,
                "Wetter": weather,
                "Temperatur": temp,
                "Streckentemperatur": track_temp,
            }

            st.session_state["start_info_saved"] = True
            st.rerun()

    st.stop()


# =========================================================
# STRECKENÜBERSICHT
# =========================================================

st.title("ACC – Analyse")

info = st.session_state["allgemeine_info"]
track = info["Track"]

st.markdown("---")

col_left, col_right = st.columns([2.2, 1])

with col_left:
    st.markdown(f"## 🏁 {track.name}")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Länge",
            f"{track.length:.3f} km",
        )

        st.metric(
            "Kurven",
            track.num_corners,
        )

        pitlane_time = (
            f"{track.pit_lane_time} s"
            if track.pit_lane_time is not None
            else "-"
        )

        st.metric(
            "Pitlane Time",
            pitlane_time,
        )

    with col2:
        st.metric(
            "Wetter",
            info["Wetter"],
        )

        st.metric(
            "Lufttemperatur",
            f"{info['Temperatur']} °C",
        )

        st.metric(
            "Streckentemperatur",
            f"{info['Streckentemperatur']} °C",
        )

    col3, col4 = st.columns(2)

    with col3:
        pitlane_speed = (
            f"{track.pit_lane_speed} km/h"
            if track.pit_lane_speed is not None
            else "-"
        )

        st.metric(
            "Pitlane Speed",
            pitlane_speed,
        )

    with col4:
        st.metric(
            "Rundenrekord",
            track.lap_record or "-",
        )

with col_right:
    image_path = (
        Path("Sources")
        / "Screenshots"
        / track.image
    )

    if image_path.exists():
        st.image(
            str(image_path),
            use_container_width=True,
        )
    else:
        st.warning(
            f"Bild nicht gefunden: {image_path}"
        )


if st.button("Startinformationen ändern"):
    st.session_state["start_info_saved"] = False
    st.rerun()


st.markdown("---")


# =========================================================
# TEAM UND MODUS
# =========================================================

with st.expander("Team & Modus", expanded=True):
    event_info.show()


if "event_info" not in st.session_state:
    st.info(
        "Bitte zuerst Team, Fahrer und Modus auswählen."
    )
    st.stop()


if "Modus" not in st.session_state["event_info"]:
    st.session_state.pop("event_info", None)

    st.warning(
        "Alte Event-Daten wurden zurückgesetzt. "
        "Bitte Team, Fahrer und Modus erneut auswählen."
    )

    st.rerun()


mode = st.session_state["event_info"]["Modus"]

st.markdown("---")
st.subheader(f"Aktueller Modus: {mode}")


# =========================================================
# SETUP ANLEGEN
# =========================================================

if mode == "Setup anlegen":
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        [
            "Reifen",
            "Elektronik",
            "Kraftstoff & Strategie",
            "Mechanischer Grip",
            "Stoßdämpfer",
            "Spoiler",
        ]
    )

    with tab1:
        st.header("Reifen")
        st.info("Setup-Modul Reifen wird noch erstellt.")

    with tab2:
        st.header("Elektronik")
        st.info("Setup-Modul Elektronik wird noch erstellt.")

    with tab3:
        st.header("Kraftstoff & Strategie")
        st.info(
            "Setup-Modul Kraftstoff & Strategie "
            "wird noch erstellt."
        )

    with tab4:
        st.header("Mechanischer Grip")
        st.info(
            "Setup-Modul Mechanischer Grip "
            "wird noch erstellt."
        )

    with tab5:
        st.header("Stoßdämpfer")
        st.info(
            "Setup-Modul Stoßdämpfer "
            "wird noch erstellt."
        )

    with tab6:
        st.header("Spoiler")
        st.info("Setup-Modul Spoiler wird noch erstellt.")


# =========================================================
# DATEN TRACKEN
# =========================================================

elif mode == "Daten tracken":
    previous_session_type = st.session_state.get(
        "tracking_info",
        {},
    ).get("Session-Art")

    session_type = st.selectbox(
        "Session-Art",
        [
            "Training",
            "Qualifying",
            "Rennen",
        ],
        key="tracking_session_type",
    )

    # Beim Wechsel der Session-Art alte Übersicht entfernen
    if previous_session_type != session_type:
        st.session_state["tracking_info"] = {
            "Session-Art": session_type,
        }

        st.session_state.pop(
            "training_overview",
            None,
        )

        st.session_state["lap_counter"] = 1
        st.session_state["lap_times"] = []
        st.session_state["fuel_data"] = []
        st.session_state["tyre_wear_data"] = []

        st.rerun()

    st.session_state["tracking_info"] = {
        "Session-Art": session_type,
    }

    # -----------------------------------------------------
    # TRAINING
    # -----------------------------------------------------

    if session_type == "Training":
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            [
                "Übersicht",
                "Rundenzeiten",
                "Reifenverschleiß",
                "Spritverbrauch",
                "Ergebnis",
            ]
        )

        with tab1:
            uebersicht.show()

        with tab2:
            rundenzeiten.show()

        with tab3:
            reifenverschleiss.show()

        with tab4:
            spritverbrauch.show()

        with tab5:
            training_ergebnis.show()

    # -----------------------------------------------------
    # QUALIFYING
    # -----------------------------------------------------

    elif session_type == "Qualifying":
        tab1, tab2, tab3, tab4 = st.tabs(
            [
                "Übersicht",
                "Rundenzeiten",
                "Spritverbrauch",
                "Ergebnis",
            ]
        )

        with tab1:
            uebersicht.show()

        with tab2:
            rundenzeiten.show()

        with tab3:
            spritverbrauch.show()

        with tab4:
            quali_ergebnis.show()

    # -----------------------------------------------------
    # RENNEN
    # -----------------------------------------------------

    elif session_type == "Rennen":
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            [
                "Übersicht",
                "Rundenzeiten",
                "Reifenverschleiß",
                "Spritverbrauch",
                "Ergebnis",
            ]
        )

        with tab1:
            uebersicht.show()

        with tab2:
            rundenzeiten.show()

        with tab3:
            reifenverschleiss.show()

        with tab4:
            spritverbrauch.show()

        with tab5:
            rennen_ergebnis.show()


# =========================================================
# DATEN ANALYSIEREN
# =========================================================

elif mode == "Daten analysieren":
    st.header("Daten analysieren")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Übersicht",
            "Rundenanalyse",
            "Reifenanalyse",
            "Spritverbrauch",
            "Reifen vs. Rundenzeit",
        ]
    )

    with tab1:
        uebersicht_analyse.show()

    with tab2:
        rundenanalyse.show()

    with tab3:
        reifenanalyse.show()

    with tab4:
        spritanalyse.show()

    with tab5:
        reifen_rundenzeit.show()

# =========================================================
# STRATEGIE PLANEN
# =========================================================

elif mode == "Strategie planen":
    st.header("Strategie planen")
    st.info("Der Strategie-Planner wird später erstellt.")