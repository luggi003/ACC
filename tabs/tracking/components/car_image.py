from pathlib import Path

import streamlit as st
from PIL import Image


CAR_IMAGE_PATH = Path("Sources") / "Auto_Setup" / "Porsche911.png"


def show_car_image():
    if not CAR_IMAGE_PATH.exists():
        st.warning(f"Bild nicht gefunden: {CAR_IMAGE_PATH}")
        return

    image = Image.open(CAR_IMAGE_PATH)
    image = image.rotate(-90, expand=True)

    st.image(
        image,
        width=260,
    )