import streamlit as st


app_modes = [
    "Setup anlegen",
    "Daten tracken",
    "Daten analysieren",
    "Strategie planen",
]


def init_teams():
    if "teams" not in st.session_state:
        st.session_state["teams"] = {
            "Tyrol Racing": ["Lukas"]
        }


def show():
    init_teams()

    st.header("Team & Modus")

    col_team, col_add_team = st.columns([3, 1])

    with col_team:
        team = st.selectbox(
            "Team",
            list(st.session_state["teams"].keys())
        )

    with col_add_team:
        with st.popover("➕ Team"):
            new_team = st.text_input("Neuer Teamname")

            if st.button("Team hinzufügen"):
                if not new_team.strip():
                    st.warning("Bitte Teamname eingeben.")
                elif new_team in st.session_state["teams"]:
                    st.warning("Team existiert bereits.")
                else:
                    st.session_state["teams"][new_team] = []
                    st.rerun()

    col_driver, col_add_driver = st.columns([3, 1])

    with col_driver:
        drivers = st.session_state["teams"][team]

        if drivers:
            driver = st.selectbox(
                "Fahrer des Teams",
                drivers
            )
        else:
            driver = None
            st.warning("Für dieses Team gibt es noch keinen Fahrer.")

    with col_add_driver:
        with st.popover("➕ Fahrer"):
            new_driver = st.text_input("Neuer Fahrername")

            if st.button("Fahrer hinzufügen"):
                if not new_driver.strip():
                    st.warning("Bitte Fahrername eingeben.")
                elif new_driver in st.session_state["teams"][team]:
                    st.warning("Fahrer existiert bereits.")
                else:
                    st.session_state["teams"][team].append(new_driver)
                    st.rerun()

    mode = st.selectbox(
        "Was möchtest du machen?",
        app_modes
    )

    if st.button("Auswahl speichern"):
        if driver is None:
            st.error("Bitte zuerst einen Fahrer hinzufügen.")
            return

        st.session_state["event_info"] = {
            "Team": team,
            "Fahrer": driver,
            "Modus": mode,
        }

        st.success("Auswahl gespeichert.")
        st.rerun()

    if "event_info" in st.session_state:
        data = st.session_state["event_info"]

        st.divider()
        st.subheader("Aktuelle Auswahl")

        st.write(f"**Team:** {data['Team']}")
        st.write(f"**Fahrer:** {data['Fahrer']}")
        st.write(f"**Modus:** {data['Modus']}")