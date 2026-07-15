import streamlit as st

from storage.database import (
    create_session,
    get_connection,
)


def init():
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = None

    if "app_screen" not in st.session_state:
        st.session_state["app_screen"] = "hub"


def create_new_session():
    session_id = create_session(
        st.session_state["allgemeine_info"],
        st.session_state["event_info"],
        st.session_state.get("tracking_info", {"Session-Art": ""}),
    )

    st.session_state["session_id"] = session_id
    return session_id


def get_current_session():
    return st.session_state.get("session_id")


def reset_session():
    st.session_state["session_id"] = None
    st.session_state["start_info_saved"] = False
    st.session_state["app_screen"] = "hub"


def load_sessions():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            track,
            weather,
            air_temp,
            track_temp,
            team,
            driver,
            mode,
            session_type,
            created_at
        FROM sessions
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return rows


def select_existing_session(session_id):
    st.session_state["session_id"] = session_id
    st.session_state["app_screen"] = "app"


def delete_session(session_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM lap_times WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM fuel_data WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM tyre_data WHERE session_id = ?", (session_id,))
    cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))

    conn.commit()
    conn.close()