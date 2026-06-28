import streamlit as st
import track_classes
from pathlib import Path

from tabs import event_info

from tabs.tracking import (
    uebersicht,
    rundenzeiten,
    reifenverschleiss,
    spritverbrauch,
)

from tabs.tracking import (
    uebersicht,
    rundenzeiten,
    reifenverschleiss,
    spritverbrauch,
)


st.set_page_config(
    page_title="ACC Analyse",
    layout="wide",
)


if "start_info_saved" not in st.session_state:
    st.session_state["start_info_saved"] = False


if not st.session_state["start_info_saved"]:
    st.title("ACC - Startinformationen")

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
            st.session_state["allgemeine_info"] = {
                "Track": selected_track,
                "Wetter": weather,
                "Temperatur": temp,
                "Streckentemperatur": track_temp,
            }

            st.session_state["start_info_saved"] = True
            st.rerun()

    st.stop()


st.title("ACC - Analyse")

info = st.session_state["allgemeine_info"]
track = info["Track"]

st.markdown("---")

col_left, col_right = st.columns([2.2, 1])

with col_left:
    st.markdown(f"## 🏁 {track.name}")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Länge", f"{track.length:.3f} km")
        st.metric("Kurven", track.num_corners)
        st.metric("Pitlane Time", f"{track.pit_lane_time} s")

    with col2:
        st.metric("Wetter", info["Wetter"])
        st.metric("Lufttemperatur", f"{info['Temperatur']} °C")
        st.metric("Streckentemperatur", f"{info['Streckentemperatur']} °C")

    col3, col4 = st.columns(2)

    with col3:
        st.metric("Pitlane Speed", f"{track.pit_lane_speed} km/h")

    with col4:
        st.metric("Rundenrekord", track.lap_record)

with col_right:
    image_path = Path("Sources") / "Screenshots" / track.image

    if image_path.exists():
        st.image(
            str(image_path),
            use_container_width=True,
        )
    else:
        st.warning(f"Bild nicht gefunden: {image_path}")

st.markdown("---")


tab_event = st.tabs(["Team & Modus"])[0]

with tab_event:
    event_info.show()


if "event_info" not in st.session_state:
    st.info("Bitte zuerst Team, Fahrer und Modus auswählen.")
    st.stop()


if "Modus" not in st.session_state["event_info"]:
    del st.session_state["event_info"]
    st.warning("Alte Event-Daten wurden zurückgesetzt. Bitte Modus neu auswählen.")
    st.rerun()


mode = st.session_state["event_info"]["Modus"]

st.markdown("---")
st.subheader(f"Aktueller Modus: {mode}")


if mode == "Setup anlegen":
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "Reifen",
            "Elektronik",
            "Kraftstoff & Strategie",
            "Mechanischer Grip",
            "Stoßdämpfer & Spoiler",
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
        st.info("Dieses Modul wird als nächstes erstellt.")

    with tab4:
        st.header("Mechanischer Grip")
        st.info("Dieses Modul wird als nächstes erstellt.")

    with tab5:
        st.header("Stoßdämpfer & Spoiler")
        st.info("Dieses Modul wird als nächstes erstellt.")


elif mode == "Daten tracken":
    session_type = st.selectbox(
        "Session-Art",
        [
            "Training",
            "Qualifying",
            "Rennen",
        ],
        key="tracking_session_type",
    )

    st.session_state["tracking_info"] = {
        "Session-Art": session_type
    }

    tab1, tab2, tab3, tab4 = st.tabs(
        [
            "Übersicht",
            "Rundenzeiten",
            "Reifenverschleiß",
            "Spritverbrauch",
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


elif mode == "Daten analysieren":
    st.header("Daten analysieren")
    st.info("Analysebereich wird später erstellt.")


elif mode == "Strategie planen":
    st.header("Strategie planen")
    st.info("Strategie-Planner wird später erstellt.")