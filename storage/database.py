import sqlite3
from pathlib import Path

DB_PATH = Path("data") / "acc_data.db"


# ---------------------------------------------------------
# Verbindung
# ---------------------------------------------------------

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)


# ---------------------------------------------------------
# Datenbank erstellen
# ---------------------------------------------------------

def init_database():

    conn = get_connection()
    cursor = conn.cursor()

    # -----------------------------------------------------
    # Sessions
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            track TEXT,
            weather TEXT,
            air_temp REAL,
            track_temp REAL,
            team TEXT,
            driver TEXT,
            mode TEXT,
            session_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # -----------------------------------------------------
    # Rundenzeiten
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lap_times(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,

            stint INTEGER,
            lap INTEGER,

            lap_type TEXT,

            sector_1 TEXT,
            sector_2 TEXT,
            sector_3 TEXT,

            lap_time TEXT,
            seconds REAL,

            valid INTEGER,

            notes TEXT,

            FOREIGN KEY(session_id)
                REFERENCES sessions(id)
        )
    """)

    # -----------------------------------------------------
    # Reifen
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tyre_data(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,

            stint INTEGER,

            tyre_set TEXT,
            tyre_status TEXT,

            position TEXT,

            cold_psi REAL,
            hot_psi REAL,

            wear_outer REAL,
            wear_middle REAL,
            wear_inner REAL,

            temp_outer REAL,
            temp_middle REAL,
            temp_inner REAL,

            graining TEXT,
            blistering TEXT,
            flatspot TEXT,

            brake_pad REAL,
            brake_disc REAL,

            notes TEXT,

            FOREIGN KEY(session_id)
                REFERENCES sessions(id)
        )
    """)

    # -----------------------------------------------------
    # Sprit
    # -----------------------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fuel_data(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,

            stint INTEGER,

            start_fuel REAL,
            end_fuel REAL,

            consumption REAL,
            consumption_per_lap REAL,

            remaining_laps REAL,

            laps INTEGER,

            notes TEXT,

            FOREIGN KEY(session_id)
                REFERENCES sessions(id)
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# Session anlegen
# ---------------------------------------------------------

def create_session(
    general_info,
    event_info,
    tracking_info,
):

    conn = get_connection()
    cursor = conn.cursor()

    track = general_info["Track"]

    cursor.execute("""
        INSERT INTO sessions(
            track,
            weather,
            air_temp,
            track_temp,
            team,
            driver,
            mode,
            session_type
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        track.name,
        general_info.get("Wetter"),
        general_info.get("Temperatur"),
        general_info.get("Streckentemperatur"),
        event_info.get("Team"),
        event_info.get("Fahrer"),
        event_info.get("Modus"),
        tracking_info.get("Session-Art"),
    ))

    session_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return session_id


# ---------------------------------------------------------
# Runde speichern
# ---------------------------------------------------------

def save_lap_time(
    session_id,
    lap,
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO lap_times(
            session_id,
            stint,
            lap,
            lap_type,
            sector_1,
            sector_2,
            sector_3,
            lap_time,
            seconds,
            valid,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        lap.get("Stint"),
        lap.get("Runde"),
        lap.get("Rundenart"),
        lap.get("Sektor 1"),
        lap.get("Sektor 2"),
        lap.get("Sektor 3"),
        lap.get("Rundenzeit"),
        lap.get("Sekunden"),
        1 if lap.get("Gültig") else 0,
        lap.get("Bemerkung"),
    ))

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# Sprit speichern
# ---------------------------------------------------------

def save_fuel_data(
    session_id,
    fuel,
):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO fuel_data(
            session_id,
            stint,
            start_fuel,
            end_fuel,
            consumption,
            consumption_per_lap,
            remaining_laps,
            laps,
            notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_id,
        fuel.get("Stint"),
        fuel.get("StartFuel"),
        fuel.get("EndFuel"),
        fuel.get("Consumption"),
        fuel.get("ConsumptionPerLap"),
        fuel.get("RemainingLaps"),
        fuel.get("Laps"),
        fuel.get("Notes"),
    ))

    conn.commit()
    conn.close()
    