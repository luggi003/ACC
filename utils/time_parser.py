def parse_time_to_seconds(time_str):
    if time_str is None:
        return None

    text = str(time_str).strip().replace(",", ".")

    if text == "":
        return None

    parts = text.split(":")

    try:
        if len(parts) == 1:
            return float(parts[0])

        if len(parts) == 2:
            return float(parts[0]) * 60 + float(parts[1])

        if len(parts) == 3:
            return (
                float(parts[0]) * 3600
                + float(parts[1]) * 60
                + float(parts[2])
            )

    except ValueError:
        return None

    return None