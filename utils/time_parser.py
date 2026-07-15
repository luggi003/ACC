def parse_time_to_seconds(time_str):
    """
    Wandelt eine Zeit im Format:
    1:47.263
    oder
    32.421

    in Sekunden um.
    """

    if not time_str:
        return None

    try:
        time_str = str(time_str).strip()

        if ":" in time_str:
            minutes, seconds = time_str.split(":")
            return int(minutes) * 60 + float(seconds)

        return float(time_str)

    except (ValueError, TypeError):
        return None


def format_seconds(seconds):
    """
    Wandelt Sekunden zurück in das Format:
    1:47.263
    """

    if seconds is None:
        return ""

    minutes = int(seconds // 60)
    rest = seconds - (minutes * 60)

    return f"{minutes}:{rest:06.3f}"