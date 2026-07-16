import streamlit as st

from tabs.tracking.components.tyre_box import tyre_box
from tabs.tracking.components.car_image import show_car_image


TYRE_POSITIONS = ["VL", "VR", "HL", "HR"]


def init_session_state():
    """Benötigte Session-State-Werte initialisieren."""

    if "tyre_wear_data" not in st.session_state:
        st.session_state["tyre_wear_data"] = []

    if "race_tyre_stint" not in st.session_state:
        st.session_state["race_tyre_stint"] = 1


def get_session_type():
    """Aktuell ausgewählte Session-Art zurückgeben."""

    return st.session_state.get(
        "tracking_info",
        {},
    ).get(
        "Session-Art",
        "Training",
    )


def get_safe_float(value):
    """Wert sicher in float umwandeln."""

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def format_number(value, decimals=1, suffix=""):
    """Zahlen robust für die Anzeige formatieren."""

    number = get_safe_float(value)

    if number is None:
        return "-"

    return f"{number:.{decimals}f}{suffix}"


def normalize_tyre_data(tyre):
    """
    Vereinheitlicht neue und alte Reifendaten.

    Neue Struktur:
    {
        "Cold PSI": ...,
        "Hot PSI": ...,
        "Wear": {"A": ..., "M": ..., "I": ...},
        "Temperature": {"A": ..., "M": ..., "I": ...},
        "Damage": {...},
        "Brakes": {...}
    }

    Alte Struktur:
    {
        "Cold PSI": ...,
        "PSI hot": ...,
        "Verschleiß Außen": ...,
        "Temperatur Außen": ...,
        "Graining": ...,
        "Bremsbelagabnutzung": ...
    }
    """

    if not isinstance(tyre, dict):
        tyre = {}

    # Druck
    cold_psi = tyre.get("Cold PSI")

    if cold_psi is None:
        cold_psi = tyre.get("PSI cold")

    if cold_psi is None:
        cold_psi = tyre.get("Cold")

    hot_psi = tyre.get("Hot PSI")

    if hot_psi is None:
        hot_psi = tyre.get("PSI hot")

    if hot_psi is None:
        hot_psi = tyre.get("Hot")

    # Verschleiß
    wear = tyre.get("Wear")

    if not isinstance(wear, dict):
        wear = {}

    wear_a = wear.get("A")

    if wear_a is None:
        wear_a = tyre.get("Verschleiß Außen")

    if wear_a is None:
        wear_a = tyre.get("wear_a")

    wear_m = wear.get("M")

    if wear_m is None:
        wear_m = tyre.get("Verschleiß Mitte")

    if wear_m is None:
        wear_m = tyre.get("wear_m")

    wear_i = wear.get("I")

    if wear_i is None:
        wear_i = tyre.get("Verschleiß Innen")

    if wear_i is None:
        wear_i = tyre.get("wear_i")

    # Temperatur
    temperature = tyre.get("Temperature")

    if not isinstance(temperature, dict):
        temperature = {}

    temp_a = temperature.get("A")

    if temp_a is None:
        temp_a = tyre.get("Temperatur Außen")

    if temp_a is None:
        temp_a = tyre.get("temp_a")

    temp_m = temperature.get("M")

    if temp_m is None:
        temp_m = tyre.get("Temperatur Mitte")

    if temp_m is None:
        temp_m = tyre.get("temp_m")

    temp_i = temperature.get("I")

    if temp_i is None:
        temp_i = tyre.get("Temperatur Innen")

    if temp_i is None:
        temp_i = tyre.get("temp_i")

    # Schäden
    damage = tyre.get("Damage")

    if not isinstance(damage, dict):
        damage = {}

    graining = damage.get("Graining")

    if graining is None:
        graining = tyre.get("Graining", "-")

    blistering = damage.get("Blasenbildung")

    if blistering is None:
        blistering = tyre.get("Blasenbildung")

    if blistering is None:
        blistering = tyre.get("Blasen", "-")

    flatspot = damage.get("Bremsplatten")

    if flatspot is None:
        flatspot = tyre.get("Bremsplatten")

    if flatspot is None:
        flatspot = tyre.get("Platten", "-")

    # Bremsen
    brakes = tyre.get("Brakes")

    if not isinstance(brakes, dict):
        brakes = {}

    brake_pad = brakes.get("Beläge")

    if brake_pad is None:
        brake_pad = tyre.get("Bremsbelagabnutzung")

    if brake_pad is None:
        brake_pad = tyre.get("Beläge")

    if brake_pad is None:
        brake_pad = tyre.get("brake_pad")

    brake_disc = brakes.get("Scheiben")

    if brake_disc is None:
        brake_disc = tyre.get("Bremsscheibenabnutzung")

    if brake_disc is None:
        brake_disc = tyre.get("Scheiben")

    if brake_disc is None:
        brake_disc = tyre.get("brake_disc")

    return {
        "Cold PSI": cold_psi,
        "Hot PSI": hot_psi,
        "Wear": {
            "A": wear_a,
            "M": wear_m,
            "I": wear_i,
        },
        "Temperature": {
            "A": temp_a,
            "M": temp_m,
            "I": temp_i,
        },
        "Damage": {
            "Graining": graining or "-",
            "Blasenbildung": blistering or "-",
            "Bremsplatten": flatspot or "-",
        },
        "Brakes": {
            "Beläge": brake_pad,
            "Scheiben": brake_disc,
        },
    }


def show_header(stint, session_name, ziel):
    """Kopfbereich mit Stint, Session und Ziel."""

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Stint", stint)

    with col2:
        st.metric("Session", session_name)

    with col3:
        st.metric("Ziel", ziel)


def get_current_entries(
    session_type,
    stint,
    session_name,
):
    """Gespeicherte Einträge für die aktuelle Auswahl filtern."""

    entries = st.session_state.get(
        "tyre_wear_data",
        [],
    )

    return [
        entry
        for entry in entries
        if isinstance(entry, dict)
        and entry.get("Session-Art") == session_type
        and entry.get("Stint") == stint
        and entry.get("Trainingssession") == session_name
    ]


def show_tyre_details(tyre):
    """Daten eines einzelnen Reifens robust anzeigen."""

    normalized = normalize_tyre_data(tyre)

    pressure = {
        "Cold PSI": normalized.get("Cold PSI"),
        "Hot PSI": normalized.get("Hot PSI"),
    }

    wear = normalized.get("Wear", {})
    temperature = normalized.get("Temperature", {})
    damage = normalized.get("Damage", {})
    brakes = normalized.get("Brakes", {})

    left, right = st.columns(2)

    with left:
        st.markdown("##### Druck")

        st.write(
            "Cold PSI: "
            f"**{format_number(pressure.get('Cold PSI'), 1)}**"
        )

        st.write(
            "Hot PSI: "
            f"**{format_number(pressure.get('Hot PSI'), 1)}**"
        )

        st.markdown("##### Verschleiß")

        st.write(
            "Außen: "
            f"**{format_number(wear.get('A'), 1, ' mm')}**"
        )

        st.write(
            "Mitte: "
            f"**{format_number(wear.get('M'), 1, ' mm')}**"
        )

        st.write(
            "Innen: "
            f"**{format_number(wear.get('I'), 1, ' mm')}**"
        )

    with right:
        st.markdown("##### Temperatur")

        st.write(
            "Außen: "
            f"**{format_number(temperature.get('A'), 1, ' °C')}**"
        )

        st.write(
            "Mitte: "
            f"**{format_number(temperature.get('M'), 1, ' °C')}**"
        )

        st.write(
            "Innen: "
            f"**{format_number(temperature.get('I'), 1, ' °C')}**"
        )

        st.markdown("##### Schäden")

        st.write(
            f"Graining: **{damage.get('Graining', '-')}**"
        )

        st.write(
            "Blasenbildung: "
            f"**{damage.get('Blasenbildung', '-')}**"
        )

        st.write(
            "Bremsplatten: "
            f"**{damage.get('Bremsplatten', '-')}**"
        )

        st.markdown("##### Bremsen")

        st.write(
            "Beläge: "
            f"**{format_number(brakes.get('Beläge'), 1)}**"
        )

        st.write(
            "Scheiben: "
            f"**{format_number(brakes.get('Scheiben'), 1)}**"
        )


def show_saved_entries(entries):
    """Bereits gespeicherte Reifendaten anzeigen."""

    if not entries:
        return

    st.divider()
    st.subheader("Gespeicherte Reifendaten")

    for index, entry in enumerate(
        entries,
        start=1,
    ):
        if not isinstance(entry, dict):
            continue

        stint = entry.get("Stint", "-")
        tyre_set = entry.get("Reifensatz", "-")
        tyre_status = entry.get("Reifenstatus", "-")

        expander_title = (
            f"Eintrag {index} | "
            f"Stint {stint} | "
            f"{tyre_set} | "
            f"{tyre_status}"
        )

        with st.expander(expander_title):
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    "Stint",
                    entry.get("Stint", "-"),
                )

            with col2:
                st.metric(
                    "Session",
                    entry.get(
                        "Trainingssession",
                        "-",
                    ),
                )

            with col3:
                st.metric(
                    "Ziel",
                    entry.get("Ziel", "-"),
                )

            tyre_tabs = st.tabs(TYRE_POSITIONS)

            for tab, position in zip(
                tyre_tabs,
                TYRE_POSITIONS,
            ):
                with tab:
                    tyre = entry.get(position, {})

                    if not isinstance(tyre, dict):
                        st.warning(
                            f"Für {position} wurden keine "
                            "gültigen Reifendaten gefunden."
                        )
                        continue

                    show_tyre_details(tyre)

            notes = entry.get("Bemerkungen")

            if notes:
                st.divider()
                st.markdown("##### Bemerkungen")
                st.info(notes)


def show():
    """Hauptfunktion des Reifenverschleiß-Tabs."""

    init_session_state()

    st.header("Reifenverschleiß")

    if "training_overview" not in st.session_state:
        st.warning(
            "Bitte zuerst die Übersicht ausfüllen."
        )
        return

    overview = st.session_state.get(
        "training_overview",
        {},
    )

    session_type = get_session_type()

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

    # Beim Rennen wird der Stint direkt im Reifen-Tab gewählt.
    if session_type == "Rennen":
        stint = st.number_input(
            "Stint",
            min_value=1,
            value=int(
                st.session_state.get(
                    "race_tyre_stint",
                    1,
                )
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

    col_set, col_status = st.columns(2)

    with col_set:
        tyre_set = st.selectbox(
            "Reifensatz",
            [
                "Satz 1",
                "Satz 2",
                "Satz 3",
                "Satz 4",
                "Satz 5",
            ],
            key=f"tyre_set_{session_type}_{stint}",
        )

    with col_status:
        tyre_status = st.selectbox(
            "Reifenstatus",
            [
                "Neu",
                "Eingefahren",
                "Gebraucht",
            ],
            key=f"tyre_status_{session_type}_{stint}",
        )

    st.divider()

    form_key = (
        f"reifen_tracking_"
        f"{session_type}_{session_name}_{stint}"
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

        # Fahrzeug mittig
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
        bottom_left, bottom_center, bottom_right = st.columns(
            [1.15, 0.7, 1.15]
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
            # Daten schon beim Speichern auf eine einheitliche
            # Struktur bringen.
            tyre_entry = {
                "Session-Art": session_type,
                "Stint": stint,
                "Trainingssession": session_name,
                "Ziel": ziel,
                "Reifensatz": tyre_set,
                "Reifenstatus": tyre_status,
                "Bemerkungen": notes,
                "VL": normalize_tyre_data(vl_data),
                "VR": normalize_tyre_data(vr_data),
                "HL": normalize_tyre_data(hl_data),
                "HR": normalize_tyre_data(hr_data),
            }

            st.session_state["tyre_wear_data"].append(
                tyre_entry
            )

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