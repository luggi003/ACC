from pathlib import Path
import shutil

import cv2
import pytesseract


TESSERACT_PATH = Path(
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def configure_tesseract() -> str:
    detected_path = shutil.which("tesseract")

    if detected_path:
        pytesseract.pytesseract.tesseract_cmd = detected_path
        return detected_path

    if TESSERACT_PATH.exists():
        pytesseract.pytesseract.tesseract_cmd = str(
            TESSERACT_PATH
        )
        return str(TESSERACT_PATH)

    raise FileNotFoundError(
        "Tesseract wurde nicht gefunden.\n"
        "Erwarteter Pfad:\n"
        f"{TESSERACT_PATH}\n\n"
        "Prüfe zuerst mit:\n"
        'Get-ChildItem "C:\\Program Files\\Tesseract-OCR"'
    )


def main() -> None:
    tesseract_path = configure_tesseract()

    print(
        "Tesseract gefunden:",
        tesseract_path,
    )

    print(
        "Tesseract-Version:",
        pytesseract.get_tesseract_version(),
    )

    print(
        "OpenCV-Version:",
        cv2.__version__,
    )

    print("Tesseract-Test erfolgreich.")


if __name__ == "__main__":
    main()