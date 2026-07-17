from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import pandas as pd
import pytesseract
import streamlit as st

from utils.time_parser import (
    format_seconds,
    parse_time_to_seconds,
)


# =========================================================
# KONFIGURATION
# =========================================================

TESSERACT_DEFAULT_PATH = Path(
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

# Das Modul ist auf das gezeigte ACC-Rundenzeitenlayout optimiert.
#
# Alle Werte sind relative Positionen und funktionieren dadurch
# auch bei einer anderen Screenshot-Auflösung, solange das
# Seitenverhältnis und das ACC-Menülayout gleich bleiben.
CELL_RANGES = {
    "Runde": (0.113, 0.145),
    "Sektor 1": (0.484, 0.534),
    "Sektor 2": (0.530, 0.580),
    "Sektor 3": (0.576, 0.628),
    "Rundenzeit": (0.620, 0.677),
}

FIRST_ROW_CENTER_RATIO = 0.202
ROW_HEIGHT_RATIO = 0.04235
MAX_VISIBLE_ROWS = 18

TIME_PATTERN = re.compile(
    r"(?:(\d{1,2})[:])?(\d{1,2})[.](\d{3})"
)


# =========================================================
# INITIALISIERUNG
# =========================================================

def init_state() -> None:
    if "image_import_rows" not in st.session_state:
        st.session_state["image_import_rows"] = []

    if "image_import_ranges" not in st.session_state:
        st.session_state["image_import_ranges"] = []

    if "image_import_ocr_debug" not in st.session_state:
        st.session_state["image_import_ocr_debug"] = []


def configure_tesseract() -> None:
    """
    Verwendet zuerst den PATH und danach den üblichen
    Windows-Installationspfad.
    """

    detected_path = shutil.which("tesseract")

    if detected_path:
        pytesseract.pytesseract.tesseract_cmd = detected_path
        return

    if TESSERACT_DEFAULT_PATH.exists():
        pytesseract.pytesseract.tesseract_cmd = str(
            TESSERACT_DEFAULT_PATH
        )
        return

    raise FileNotFoundError(
        "Tesseract wurde nicht gefunden. Erwarteter Pfad: "
        f"{TESSERACT_DEFAULT_PATH}"
    )


# =========================================================
# BILDVERARBEITUNG
# =========================================================

def uploaded_file_to_image(
    uploaded_file: Any,
) -> np.ndarray | None:
    file_bytes = np.asarray(
        bytearray(uploaded_file.getvalue()),
        dtype=np.uint8,
    )

    image = cv2.imdecode(
        file_bytes,
        cv2.IMREAD_COLOR,
    )

    return image


def crop_relative(
    image: np.ndarray,
    x_start: float,
    x_end: float,
    y_start: float,
    y_end: float,
) -> np.ndarray:
    height, width = image.shape[:2]

    x1 = max(0, int(width * x_start))
    x2 = min(width, int(width * x_end))
    y1 = max(0, int(height * y_start))
    y2 = min(height, int(height * y_end))

    return image[y1:y2, x1:x2]


def get_row_bounds(
    image_height: int,
    row_index: int,
) -> tuple[int, int]:
    row_height = image_height * ROW_HEIGHT_RATIO

    center = (
        image_height * FIRST_ROW_CENTER_RATIO
        + row_index * row_height
    )

    half_height = row_height * 0.39

    y1 = max(0, int(center - half_height))
    y2 = min(
        image_height,
        int(center + half_height),
    )

    return y1, y2


def get_cell_crop(
    image: np.ndarray,
    row_index: int,
    cell_name: str,
) -> np.ndarray:
    height, width = image.shape[:2]

    y1, y2 = get_row_bounds(
        height,
        row_index,
    )

    x_start, x_end = CELL_RANGES[cell_name]

    x1 = int(width * x_start)
    x2 = int(width * x_end)

    return image[y1:y2, x1:x2]


def enlarge_image(
    image: np.ndarray,
    factor: int = 4,
) -> np.ndarray:
    return cv2.resize(
        image,
        None,
        fx=factor,
        fy=factor,
        interpolation=cv2.INTER_CUBIC,
    )


def create_ocr_variants(
    image: np.ndarray,
) -> list[np.ndarray]:
    """
    Erstellt mehrere Varianten, da ACC sowohl dunkle Schrift
    auf hellen Flächen als auch helle Schrift auf roten oder
    dunklen Flächen verwendet.
    """

    enlarged = enlarge_image(image)

    gray = cv2.cvtColor(
        enlarged,
        cv2.COLOR_BGR2GRAY,
    )

    gray = cv2.GaussianBlur(
        gray,
        (3, 3),
        0,
    )

    _, binary = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU,
    )

    _, binary_inverted = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU,
    )

    adaptive = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        7,
    )

    adaptive_inverted = cv2.bitwise_not(
        adaptive
    )

    return [
        enlarged,
        gray,
        binary,
        binary_inverted,
        adaptive,
        adaptive_inverted,
    ]


# =========================================================
# OCR-HILFSFUNKTIONEN
# =========================================================

def normalize_ocr_text(text: str) -> str:
    replacements = {
        "O": "0",
        "o": "0",
        "Q": "0",
        "D": "0",
        "I": "1",
        "l": "1",
        "|": "1",
        ",": ".",
        ";": ":",
        " ": "",
        "\n": "",
        "\r": "",
    }

    normalized = text.strip()

    for source, target in replacements.items():
        normalized = normalized.replace(
            source,
            target,
        )

    normalized = re.sub(
        r"[^0-9:.]",
        "",
        normalized,
    )

    return normalized


def normalize_time_value(
    text: str,
    is_sector: bool,
) -> str | None:
    normalized = normalize_ocr_text(text)

    match = TIME_PATTERN.search(normalized)

    if not match:
        # Manche OCR-Ergebnisse verlieren den Doppelpunkt,
        # beispielsweise 0139965 statt 01:39.965.
        digits = re.sub(
            r"\D",
            "",
            normalized,
        )

        if is_sector and len(digits) >= 5:
            # Beispiel: 33145 -> 33.145
            digits = digits[-5:]
            normalized = (
                f"{digits[:2]}.{digits[2:]}"
            )

        elif not is_sector and len(digits) >= 6:
            # Beispiel: 139965 -> 1:39.965
            digits = digits[-6:]
            normalized = (
                f"{digits[0]}:"
                f"{digits[1:3]}."
                f"{digits[3:]}"
            )

        match = TIME_PATTERN.search(
            normalized
        )

    if not match:
        return None

    minutes_text = match.group(1)
    seconds_text = match.group(2)
    milliseconds_text = match.group(3)

    try:
        minutes = (
            int(minutes_text)
            if minutes_text is not None
            else 0
        )

        seconds = int(seconds_text)
        milliseconds = int(milliseconds_text)

    except ValueError:
        return None

    if seconds >= 60 or milliseconds >= 1000:
        return None

    if is_sector:
        total_seconds = (
            minutes * 60
            + seconds
            + milliseconds / 1000
        )

        if not 5.0 <= total_seconds <= 180.0:
            return None

        if total_seconds < 60:
            return f"{total_seconds:.3f}"

        return format_seconds(total_seconds)

    total_seconds = (
        minutes * 60
        + seconds
        + milliseconds / 1000
    )

    if not 20.0 <= total_seconds <= 900.0:
        return None

    return format_seconds(total_seconds)


def run_ocr(
    image: np.ndarray,
    is_sector: bool,
) -> tuple[str | None, str]:
    """
    Führt OCR mit mehreren Bildvarianten durch und gibt
    den ersten plausiblen Zeitwert zurück.
    """

    config = (
        "--oem 3 "
        "--psm 7 "
        "-c tessedit_char_whitelist=0123456789:."
    )

    raw_results = []

    for variant in create_ocr_variants(image):
        try:
            raw_text = pytesseract.image_to_string(
                variant,
                config=config,
                timeout=8,
            )

        except RuntimeError:
            continue

        raw_results.append(
            raw_text.strip()
        )

        normalized = normalize_time_value(
            raw_text,
            is_sector=is_sector,
        )

        if normalized is not None:
            return normalized, raw_text.strip()

    return None, " | ".join(raw_results)


def run_lap_number_ocr(
    image: np.ndarray,
) -> tuple[int | None, str]:
    config = (
        "--oem 3 "
        "--psm 7 "
        "-c tessedit_char_whitelist=0123456789"
    )

    raw_results = []

    for variant in create_ocr_variants(image):
        try:
            raw_text = pytesseract.image_to_string(
                variant,
                config=config,
                timeout=8,
            )

        except RuntimeError:
            continue

        raw_results.append(
            raw_text.strip()
        )

        digits = re.sub(
            r"\D",
            "",
            raw_text,
        )

        if not digits:
            continue

        try:
            lap_number = int(digits)

        except ValueError:
            continue

        if 1 <= lap_number <= 9999:
            return lap_number, raw_text.strip()

    return None, " | ".join(raw_results)


# =========================================================
# GÜLTIGKEITSERKENNUNG
# =========================================================

def detect_validity(
    image: np.ndarray,
    row_index: int,
) -> bool:
    """
    Ungültige ACC-Runden besitzen im gezeigten Layout einen
    deutlich roten Zeilenhintergrund.

    Ein hoher Anteil roter Pixel bedeutet daher ungültig.
    Weiße, schwarze, grüne oder violette Felder gelten als
    gültig.
    """

    height, width = image.shape[:2]
    y1, y2 = get_row_bounds(
        height,
        row_index,
    )

    x1 = int(width * 0.475)
    x2 = int(width * 0.700)

    row_crop = image[
        y1:y2,
        x1:x2,
    ]

    if row_crop.size == 0:
        return True

    hsv = cv2.cvtColor(
        row_crop,
        cv2.COLOR_BGR2HSV,
    )

    red_mask_1 = cv2.inRange(
        hsv,
        np.array([0, 70, 55]),
        np.array([14, 255, 255]),
    )

    red_mask_2 = cv2.inRange(
        hsv,
        np.array([165, 70, 55]),
        np.array([180, 255, 255]),
    )

    red_mask = cv2.bitwise_or(
        red_mask_1,
        red_mask_2,
    )

    red_ratio = (
        cv2.countNonZero(red_mask)
        / red_mask.size
    )

    return red_ratio < 0.32


# =========================================================
# PLAUSIBILITÄT
# =========================================================

def validate_sector_sum(
    sector_1: str | None,
    sector_2: str | None,
    sector_3: str | None,
    lap_time: str | None,
) -> tuple[bool, float | None]:
    if not all(
        [
            sector_1,
            sector_2,
            sector_3,
            lap_time,
        ]
    ):
        return False, None

    s1 = parse_time_to_seconds(sector_1)
    s2 = parse_time_to_seconds(sector_2)
    s3 = parse_time_to_seconds(sector_3)
    total = parse_time_to_seconds(lap_time)

    if None in [s1, s2, s3, total]:
        return False, None

    difference = abs(
        (s1 + s2 + s3) - total
    )

    # ACC kann je nach Darstellung Rundungsunterschiede
    # im Millisekundenbereich besitzen.
    return difference <= 0.080, difference


def calculate_row_quality(
    row: dict[str, Any],
) -> int:
    score = 0

    if row.get("Runde") is not None:
        score += 1

    for key in [
        "Sektor 1",
        "Sektor 2",
        "Sektor 3",
        "Rundenzeit",
    ]:
        if row.get(key):
            score += 2

    if row.get("Sektorsumme korrekt"):
        score += 3

    return score


# =========================================================
# SCREENSHOT-AUSWERTUNG
# =========================================================

def analyze_image(
    image: np.ndarray,
    image_name: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = []
    debug_rows = []

    for row_index in range(MAX_VISIBLE_ROWS):
        lap_crop = get_cell_crop(
            image,
            row_index,
            "Runde",
        )

        lap_number, lap_raw = (
            run_lap_number_ocr(lap_crop)
        )

        # Leere Zeilen nach den sichtbaren Tabellenzeilen
        # werden übersprungen.
        if lap_number is None:
            continue

        sector_1, sector_1_raw = run_ocr(
            get_cell_crop(
                image,
                row_index,
                "Sektor 1",
            ),
            is_sector=True,
        )

        sector_2, sector_2_raw = run_ocr(
            get_cell_crop(
                image,
                row_index,
                "Sektor 2",
            ),
            is_sector=True,
        )

        sector_3, sector_3_raw = run_ocr(
            get_cell_crop(
                image,
                row_index,
                "Sektor 3",
            ),
            is_sector=True,
        )

        lap_time, lap_time_raw = run_ocr(
            get_cell_crop(
                image,
                row_index,
                "Rundenzeit",
            ),
            is_sector=False,
        )

        valid = detect_validity(
            image,
            row_index,
        )

        sector_sum_valid, difference = (
            validate_sector_sum(
                sector_1,
                sector_2,
                sector_3,
                lap_time,
            )
        )

        row = {
            "Importieren": True,
            "Bild": image_name,
            "Runde": lap_number,
            "Sektor 1": sector_1 or "",
            "Sektor 2": sector_2 or "",
            "Sektor 3": sector_3 or "",
            "Rundenzeit": lap_time or "",
            "Gültig": valid,
            "Stint": None,
            "Sektorsumme korrekt":
                sector_sum_valid,
            "Abweichung Sektorsumme": (
                round(difference, 3)
                if difference is not None
                else None
            ),
        }

        row["Qualität"] = calculate_row_quality(
            row
        )

        rows.append(row)

        debug_rows.append(
            {
                "Bild": image_name,
                "Tabellenzeile": row_index + 1,
                "Runde erkannt": lap_number,
                "Runde Rohtext": lap_raw,
                "S1 Rohtext": sector_1_raw,
                "S2 Rohtext": sector_2_raw,
                "S3 Rohtext": sector_3_raw,
                "Gesamt Rohtext": lap_time_raw,
            }
        )

    return rows, debug_rows


def merge_duplicate_laps(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Bei überlappenden Screenshots bleibt für jede Runde
    der Datensatz mit der höchsten Erkennungsqualität erhalten.
    """

    best_rows: dict[int, dict[str, Any]] = {}

    for row in rows:
        lap_number = row.get("Runde")

        if lap_number is None:
            continue

        existing = best_rows.get(
            int(lap_number)
        )

        if (
            existing is None
            or row.get("Qualität", 0)
            > existing.get("Qualität", 0)
        ):
            best_rows[int(lap_number)] = row

    return sorted(
        best_rows.values(),
        key=lambda item: int(
            item.get("Runde", 0)
        ),
    )


# =========================================================
# STINT-BEREICHE
# =========================================================

def create_default_ranges(
    rows: list[dict[str, Any]],
) -> list[dict[str, int]]:
    lap_numbers = [
        int(row["Runde"])
        for row in rows
        if row.get("Runde") is not None
    ]

    if not lap_numbers:
        return []

    return [
        {
            "Start-Runde": min(lap_numbers),
            "Ende-Runde": max(lap_numbers),
            "Stint": 1,
        }
    ]


def normalize_ranges(
    dataframe: pd.DataFrame,
) -> list[dict[str, int]]:
    ranges = []

    if dataframe.empty:
        return ranges

    for _, row in dataframe.iterrows():
        try:
            start_lap = int(
                row["Start-Runde"]
            )

            end_lap = int(
                row["Ende-Runde"]
            )

            stint = int(
                row["Stint"]
            )

        except (
            TypeError,
            ValueError,
            KeyError,
        ):
            continue

        ranges.append(
            {
                "Start-Runde": start_lap,
                "Ende-Runde": end_lap,
                "Stint": stint,
            }
        )

    return ranges


def validate_ranges(
    ranges: list[dict[str, int]],
    available_laps: list[int],
) -> tuple[list[str], list[int]]:
    errors = []
    assignments: dict[int, list[int]] = {}

    for index, item in enumerate(
        ranges,
        start=1,
    ):
        start_lap = item["Start-Runde"]
        end_lap = item["Ende-Runde"]
        stint = item["Stint"]

        if start_lap < 1:
            errors.append(
                f"Bereich {index}: Die Start-Runde "
                "muss mindestens 1 sein."
            )

        if end_lap < start_lap:
            errors.append(
                f"Bereich {index}: Die Ende-Runde "
                "liegt vor der Start-Runde."
            )

        if stint < 1:
            errors.append(
                f"Bereich {index}: Der Stint muss "
                "mindestens 1 sein."
            )

        for lap in available_laps:
            if start_lap <= lap <= end_lap:
                assignments.setdefault(
                    lap,
                    [],
                ).append(stint)

    overlapping_laps = [
        lap
        for lap, assigned_stints
        in assignments.items()
        if len(set(assigned_stints)) > 1
    ]

    if overlapping_laps:
        errors.append(
            "Folgende Runden sind mehreren Stints "
            "zugeordnet: "
            + ", ".join(
                str(lap)
                for lap in overlapping_laps
            )
        )

    missing_laps = [
        lap
        for lap in available_laps
        if lap not in assignments
    ]

    return errors, missing_laps


def apply_stint_ranges(
    rows: list[dict[str, Any]],
    ranges: list[dict[str, int]],
) -> list[dict[str, Any]]:
    updated_rows = []

    for source_row in rows:
        row = source_row.copy()
        lap_number = row.get("Runde")
        assigned_stint = None

        if lap_number is not None:
            for item in ranges:
                if (
                    item["Start-Runde"]
                    <= int(lap_number)
                    <= item["Ende-Runde"]
                ):
                    assigned_stint = item["Stint"]
                    break

        row["Stint"] = assigned_stint
        updated_rows.append(row)

    return updated_rows


# =========================================================
# IMPORT IN SESSION STATE
# =========================================================

def build_lap_entries(
    dataframe: pd.DataFrame,
) -> tuple[list[dict[str, Any]], list[str]]:
    overview = st.session_state.get(
        "training_overview",
        {},
    )

    session_type = st.session_state.get(
        "tracking_info",
        {},
    ).get(
        "Session-Art",
        "Training",
    )

    session_name = overview.get(
        "Trainingssession",
        session_type,
    )

    ziel = overview.get(
        "Ziel",
        session_type,
    )

    block_size = int(
        overview.get("Blockgröße", 0) or 0
    )

    strategy_test = (
        ziel == "Strategie-Testlauf"
    )

    errors = []
    entries = []

    selected_rows = dataframe[
        dataframe["Importieren"] == True
    ].copy()

    selected_rows = selected_rows.sort_values(
        [
            "Stint",
            "Runde",
        ]
    )

    stint_position_counter: dict[int, int] = {}

    for _, row in selected_rows.iterrows():
        try:
            lap_number = int(row["Runde"])
            stint = int(row["Stint"])

        except (TypeError, ValueError):
            errors.append(
                "Mindestens eine ausgewählte Runde "
                "hat keine gültige Runde- oder "
                "Stintzuordnung."
            )
            continue

        sector_1 = str(
            row.get("Sektor 1", "")
        ).strip()

        sector_2 = str(
            row.get("Sektor 2", "")
        ).strip()

        sector_3 = str(
            row.get("Sektor 3", "")
        ).strip()

        lap_time = str(
            row.get("Rundenzeit", "")
        ).strip()

        seconds = parse_time_to_seconds(
            lap_time
        )

        if seconds is None:
            errors.append(
                f"Runde {lap_number}: Ungültige "
                "Gesamtzeit."
            )
            continue

        stint_position_counter[stint] = (
            stint_position_counter.get(
                stint,
                0,
            )
            + 1
        )

        stint_lap = stint_position_counter[
            stint
        ]

        entry = {
            "Session-Art": session_type,
            "Stint": stint,
            "Trainingssession": session_name,
            "Ziel": ziel,
            "Runde": lap_number,
            "Stint-Runde": stint_lap,
            "Sektor 1": sector_1,
            "Sektor 2": sector_2,
            "Sektor 3": sector_3,
            "Rundenzeit": lap_time,
            "Sekunden": float(seconds),
            "Rundenart": (
                "Push Lap"
                if ziel in [
                    "Quali-Sim",
                    "Setup bauen",
                    "Qualifying",
                ]
                else "Normale Runde"
            ),
            "Gültig": bool(
                row.get("Gültig", True)
            ),
            "Bemerkung": "Import aus ACC-Screenshot",
            "Importquelle": str(
                row.get("Bild", "")
            ),
        }

        if strategy_test and block_size > 0:
            block_number = (
                (stint_lap - 1)
                // block_size
                + 1
            )

            lap_in_block = (
                (stint_lap - 1)
                % block_size
                + 1
            )

            entry.update(
                {
                    "Testserie": overview.get(
                        "Testserie",
                        "",
                    ),
                    "Testlaufnummer":
                        overview.get(
                            "Testlaufnummer"
                        ),
                    "Blockgröße": block_size,
                    "Block": block_number,
                    "Runde im Block":
                        lap_in_block,
                    "Anzahl Blöcke":
                        overview.get(
                            "Anzahl Blöcke"
                        ),
                    "Referenz-Setup":
                        overview.get(
                            "Referenz-Setup",
                            "",
                        ),
                }
            )

        entries.append(entry)

    return entries, errors


def remove_existing_duplicates(
    new_entries: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], int]:
    existing_laps = st.session_state.get(
        "lap_times",
        [],
    )

    existing_keys = {
        (
            entry.get("Session-Art"),
            entry.get("Trainingssession"),
            entry.get("Stint"),
            entry.get("Runde"),
        )
        for entry in existing_laps
    }

    filtered_entries = []
    duplicate_count = 0

    for entry in new_entries:
        key = (
            entry.get("Session-Art"),
            entry.get("Trainingssession"),
            entry.get("Stint"),
            entry.get("Runde"),
        )

        if key in existing_keys:
            duplicate_count += 1
            continue

        filtered_entries.append(entry)

    return filtered_entries, duplicate_count


# =========================================================
# STREAMLIT-OBERFLÄCHE
# =========================================================

def show_upload_section() -> None:
    st.markdown("### ACC-Screenshots hochladen")

    uploaded_files = st.file_uploader(
        "Ein oder mehrere Bilder auswählen",
        type=[
            "png",
            "jpg",
            "jpeg",
        ],
        accept_multiple_files=True,
        key="lap_image_upload",
        help=(
            "Die Erkennung ist auf die gezeigte "
            "ACC-Rundenzeitentabelle optimiert."
        ),
    )

    if not uploaded_files:
        st.info(
            "Lade mindestens einen Screenshot der "
            "ACC-Rundenzeitentabelle hoch."
        )
        return

    preview_columns = st.columns(
        min(len(uploaded_files), 3)
    )

    for index, uploaded_file in enumerate(
        uploaded_files
    ):
        with preview_columns[
            index % len(preview_columns)
        ]:
            st.image(
                uploaded_file,
                caption=uploaded_file.name,
                use_container_width=True,
            )

    if st.button(
        "Bilder auswerten",
        type="primary",
        use_container_width=True,
        key="analyze_lap_images",
    ):
        try:
            configure_tesseract()

        except FileNotFoundError as error:
            st.error(str(error))
            return

        all_rows = []
        all_debug_rows = []

        progress = st.progress(0)
        status = st.empty()

        for index, uploaded_file in enumerate(
            uploaded_files,
            start=1,
        ):
            status.write(
                f"Bild {index} von "
                f"{len(uploaded_files)} wird ausgewertet …"
            )

            image = uploaded_file_to_image(
                uploaded_file
            )

            if image is None:
                st.warning(
                    f"{uploaded_file.name} konnte "
                    "nicht gelesen werden."
                )
                continue

            rows, debug_rows = analyze_image(
                image,
                uploaded_file.name,
            )

            all_rows.extend(rows)
            all_debug_rows.extend(
                debug_rows
            )

            progress.progress(
                index / len(uploaded_files)
            )

        merged_rows = merge_duplicate_laps(
            all_rows
        )

        st.session_state[
            "image_import_rows"
        ] = merged_rows

        st.session_state[
            "image_import_ocr_debug"
        ] = all_debug_rows

        st.session_state[
            "image_import_ranges"
        ] = create_default_ranges(
            merged_rows
        )

        progress.empty()
        status.empty()

        if merged_rows:
            st.success(
                f"{len(merged_rows)} unterschiedliche "
                "Runden wurden erkannt."
            )
        else:
            st.error(
                "Es konnten keine Runden erkannt werden. "
                "Prüfe, ob der Screenshot dem gezeigten "
                "ACC-Layout entspricht."
            )

        st.rerun()


def show_recognized_table() -> pd.DataFrame | None:
    rows = st.session_state.get(
        "image_import_rows",
        [],
    )

    if not rows:
        return None

    st.divider()
    st.markdown("### Erkannte Runden prüfen")

    dataframe = pd.DataFrame(rows)

    required_columns = [
        "Importieren",
        "Bild",
        "Runde",
        "Sektor 1",
        "Sektor 2",
        "Sektor 3",
        "Rundenzeit",
        "Gültig",
        "Stint",
        "Sektorsumme korrekt",
        "Abweichung Sektorsumme",
        "Qualität",
    ]

    for column in required_columns:
        if column not in dataframe.columns:
            dataframe[column] = None

    edited_dataframe = st.data_editor(
        dataframe[required_columns],
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="image_import_lap_editor",
        column_config={
            "Importieren":
                st.column_config.CheckboxColumn(
                    "Importieren",
                    default=True,
                ),
            "Bild":
                st.column_config.TextColumn(
                    "Bild",
                    disabled=True,
                ),
            "Runde":
                st.column_config.NumberColumn(
                    "Runde",
                    min_value=1,
                    step=1,
                    required=True,
                ),
            "Sektor 1":
                st.column_config.TextColumn(
                    "Sektor 1",
                ),
            "Sektor 2":
                st.column_config.TextColumn(
                    "Sektor 2",
                ),
            "Sektor 3":
                st.column_config.TextColumn(
                    "Sektor 3",
                ),
            "Rundenzeit":
                st.column_config.TextColumn(
                    "Rundenzeit",
                    required=True,
                ),
            "Gültig":
                st.column_config.CheckboxColumn(
                    "Gültig",
                ),
            "Stint":
                st.column_config.NumberColumn(
                    "Stint",
                    min_value=1,
                    step=1,
                ),
            "Sektorsumme korrekt":
                st.column_config.CheckboxColumn(
                    "Sektorsumme",
                    disabled=True,
                ),
            "Abweichung Sektorsumme":
                st.column_config.NumberColumn(
                    "Abweichung",
                    format="%.3f s",
                    disabled=True,
                ),
            "Qualität":
                st.column_config.NumberColumn(
                    "OCR-Qualität",
                    disabled=True,
                ),
        },
    )

    return edited_dataframe


def show_range_assignment(
    lap_dataframe: pd.DataFrame,
) -> pd.DataFrame:
    st.divider()
    st.markdown("### Stints über Rundenbereiche zuordnen")

    st.info(
        "Beispiel: Runde 1–16 = Stint 1 und "
        "Runde 17–22 = Stint 2."
    )

    range_dataframe = pd.DataFrame(
        st.session_state.get(
            "image_import_ranges",
            [],
        )
    )

    if range_dataframe.empty:
        range_dataframe = pd.DataFrame(
            columns=[
                "Start-Runde",
                "Ende-Runde",
                "Stint",
            ]
        )

    edited_ranges = st.data_editor(
        range_dataframe,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key="image_import_range_editor",
        column_config={
            "Start-Runde":
                st.column_config.NumberColumn(
                    "Start-Runde",
                    min_value=1,
                    step=1,
                    required=True,
                ),
            "Ende-Runde":
                st.column_config.NumberColumn(
                    "Ende-Runde",
                    min_value=1,
                    step=1,
                    required=True,
                ),
            "Stint":
                st.column_config.NumberColumn(
                    "Stint",
                    min_value=1,
                    step=1,
                    required=True,
                ),
        },
    )

    ranges = normalize_ranges(
        edited_ranges
    )

    selected_laps = [
        int(value)
        for value in lap_dataframe.loc[
            lap_dataframe["Importieren"] == True,
            "Runde",
        ].dropna()
    ]

    errors, missing_laps = validate_ranges(
        ranges,
        selected_laps,
    )

    for error in errors:
        st.error(error)

    if missing_laps:
        st.warning(
            "Noch keinem Stint zugeordnet: "
            + ", ".join(
                str(lap)
                for lap in missing_laps
            )
        )

    if st.button(
        "Stintzuordnung anwenden",
        use_container_width=True,
        disabled=bool(errors),
        key="apply_image_stint_ranges",
    ):
        updated_rows = apply_stint_ranges(
            lap_dataframe.to_dict(
                orient="records"
            ),
            ranges,
        )

        st.session_state[
            "image_import_rows"
        ] = updated_rows

        st.session_state[
            "image_import_ranges"
        ] = ranges

        st.success(
            "Die Stintzuordnung wurde angewendet."
        )

        st.rerun()

    return edited_ranges


def show_import_button(
    lap_dataframe: pd.DataFrame,
) -> None:
    st.divider()
    st.markdown("### Runden übernehmen")

    selected_dataframe = lap_dataframe[
        lap_dataframe["Importieren"] == True
    ]

    if selected_dataframe.empty:
        st.warning(
            "Es wurden keine Runden zum Import "
            "ausgewählt."
        )
        return

    missing_stints = selected_dataframe[
        selected_dataframe["Stint"].isna()
    ]

    invalid_times = []

    for _, row in selected_dataframe.iterrows():
        lap_time = str(
            row.get("Rundenzeit", "")
        ).strip()

        if (
            parse_time_to_seconds(lap_time)
            is None
        ):
            invalid_times.append(
                row.get("Runde")
            )

    if not missing_stints.empty:
        st.warning(
            "Noch nicht alle ausgewählten Runden "
            "wurden einem Stint zugeordnet."
        )

    if invalid_times:
        st.error(
            "Ungültige Gesamtzeiten bei Runde: "
            + ", ".join(
                str(value)
                for value in invalid_times
            )
        )

    import_disabled = (
        not missing_stints.empty
        or bool(invalid_times)
    )

    if st.button(
        "Ausgewählte Runden importieren",
        type="primary",
        use_container_width=True,
        disabled=import_disabled,
        key="import_recognized_laps",
    ):
        entries, errors = build_lap_entries(
            lap_dataframe
        )

        if errors:
            for error in errors:
                st.error(error)
            return

        entries, duplicate_count = (
            remove_existing_duplicates(
                entries
            )
        )

        if "lap_times" not in st.session_state:
            st.session_state[
                "lap_times"
            ] = []

        st.session_state[
            "lap_times"
        ].extend(entries)

        if duplicate_count:
            st.warning(
                f"{duplicate_count} bereits vorhandene "
                "Runden wurden übersprungen."
            )

        st.success(
            f"{len(entries)} Runden wurden "
            "erfolgreich importiert."
        )

        st.session_state[
            "image_import_rows"
        ] = []

        st.session_state[
            "image_import_ranges"
        ] = []

        st.session_state[
            "image_import_ocr_debug"
        ] = []

        st.rerun()


def show_debug_information() -> None:
    debug_rows = st.session_state.get(
        "image_import_ocr_debug",
        [],
    )

    if not debug_rows:
        return

    with st.expander(
        "OCR-Diagnose anzeigen"
    ):
        st.caption(
            "Diese Tabelle hilft beim Anpassen der "
            "Erkennung, falls einzelne Werte falsch "
            "gelesen werden."
        )

        st.dataframe(
            pd.DataFrame(debug_rows),
            use_container_width=True,
            hide_index=True,
        )


def show() -> None:
    init_state()

    st.subheader("Rundenzeiten aus Bildern importieren")

    st.caption(
        "Die Auswertung erfolgt vollständig lokal "
        "mit Tesseract. Es werden keine Bilder "
        "hochgeladen."
    )

    show_upload_section()

    lap_dataframe = show_recognized_table()

    if lap_dataframe is None:
        return

    show_range_assignment(
        lap_dataframe
    )

    # Nach dem Anwenden einer Bereichszuordnung wird die
    # aktuelle Session-State-Version erneut verwendet.
    current_rows = st.session_state.get(
        "image_import_rows",
        [],
    )

    if current_rows:
        current_dataframe = pd.DataFrame(
            current_rows
        )
    else:
        current_dataframe = lap_dataframe

    show_import_button(
        current_dataframe
    )

    show_debug_information()