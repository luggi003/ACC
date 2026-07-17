import pandas as pd
import streamlit as st


TYRE_POSITIONS = [
    "VL",
    "VR",
    "HL",
    "HR",
]


def safe_float(value):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def average(values):
    valid_values = [
        value
        for value in values
        if value is not None
    ]

    if not valid_values:
        return None

    return sum(valid_values) / len(valid_values)


def normalize_wear(tyre):
    if not isinstance(tyre, dict):
        tyre = {}

    wear = tyre.get("Wear")

    if not isinstance(wear, dict):
        wear = {}

    wear_a = wear.get("A")
    wear_m = wear.get("M")
    wear_i = wear.get("I")

    if wear_a is None:
        wear_a = tyre.get("Verschleiß Außen")

    if wear_m is None:
        wear_m = tyre.get("Verschleiß Mitte")

    if wear_i is None:
        wear_i = tyre.get("Verschleiß Innen")

    return {
        "A": safe_float(wear_a),
        "M": safe_float(wear_m),
        "I": safe_float(wear_i),
    }


def get_average_profile_depth(entry):
    profile_values = []

    for position in TYRE_POSITIONS:
        tyre = entry.get(position, {})
        wear = normalize_wear(tyre)

        position_average = average(
            [
                wear.get("A"),
                wear.get("M"),
                wear.get("I"),
            ]
        )

        if position_average is not None:
            profile_values.append(position_average)

    return average(profile_values)


def get_available_tyre_sets():
    tyre_entries = st.session_state.get(
        "tyre_wear_data",
        [],
    )

    tyre_sets = {}

    for entry in tyre_entries:
        if not isinstance(entry, dict):
            continue

        tyre_set = entry.get(
            "Reifensatz",
            "Unbekannter Satz",
        )

        profile_depth = get_average_profile_depth(
            entry
        )

        tyre_sets.setdefault(
            tyre_set,
            {
                "Reifensatz": tyre_set,
                "Status": entry.get(
                    "Reifenstatus",
                    "Unbekannt",
                ),
                "Messungen": 0,
                "Profiltiefen": [],
                "Letzter Stint": entry.get(
                    "Stint",
                ),
            },
        )

        tyre_sets[tyre_set]["Messungen"] += 1

        if profile_depth is not None:
            tyre_sets[tyre_set][
                "Profiltiefen"
            ].append(profile_depth)

        tyre_sets[tyre_set][
            "Letzter Stint"
        ] = entry.get(
            "Stint",
            tyre_sets[tyre_set][
                "Letzter Stint"
            ],
        )

    result = []

    for tyre_set, data in tyre_sets.items():
        profile_depth = average(
            data["Profiltiefen"]
        )

        result.append(
            {
                "Reifensatz": tyre_set,
                "Status": data["Status"],
                "Messungen": data["Messungen"],
                "Ø Profiltiefe":
                    profile_depth,
                "Letzter Stint":
                    data["Letzter Stint"],
            }
        )

    return sorted(
        result,
        key=lambda item: item[
            "Reifensatz"
        ],
    )


def create_default_tyre_sets():
    return [
        {
            "Reifensatz": f"Satz {index}",
            "Status": "Neu",
            "Messungen": 0,
            "Ø Profiltiefe": 3.0,
            "Letzter Stint": None,
        }
        for index in range(1, 6)
    ]


def get_tyre_sets():
    tracked_sets = get_available_tyre_sets()

    if tracked_sets:
        return tracked_sets

    return create_default_tyre_sets()


def calculate_recommendation(
    profile_depth,
    status,
):
    if profile_depth is None:
        return "Keine Messdaten"

    if profile_depth <= 1.5:
        return "Nicht verwenden"

    if profile_depth <= 1.8:
        return "Nur kurzer Stint"

    if profile_depth <= 2.2:
        return "Eingeschränkt verwendbar"

    if status == "Gebraucht":
        return "Für mittleren Stint geeignet"

    if status == "Eingefahren":
        return "Gut einsetzbar"

    return "Sehr gut einsetzbar"


def create_default_strategy(
    stint_plan,
    tyre_sets,
):
    available_names = [
        tyre["Reifensatz"]
        for tyre in tyre_sets
    ]

    if not available_names:
        available_names = [
            "Satz 1",
        ]

    rows = []

    for index, stint in enumerate(
        stint_plan
    ):
        stint_number = int(
            stint.get(
                "Stint",
                index + 1,
            )
        )

        if index < len(
            available_names
        ):
            selected_set = available_names[index]
        else:
            selected_set = available_names[
                index % len(available_names)
            ]

        rows.append(
            {
                "Stint": stint_number,
                "Runden": int(
                    stint.get(
                        "Runden",
                        0,
                    )
                ),
                "Reifensatz":
                    selected_set,
                "Reifenwechsel": (
                    stint_number > 1
                ),
                "Doppelstint":
                    False,
                "Bemerkung": "",
            }
        )

    return rows


def get_set_information(
    tyre_sets,
    tyre_set_name,
):
    return next(
        (
            tyre
            for tyre in tyre_sets
            if tyre.get(
                "Reifensatz"
            ) == tyre_set_name
        ),
        None,
    )


def validate_strategy(
    dataframe,
    tyre_sets,
    tyre_change_allowed,
    tyre_change_required,
):
    errors = []
    warnings = []

    if dataframe.empty:
        errors.append(
            "Die Reifenstrategie ist leer."
        )

        return errors, warnings

    for index, row in dataframe.iterrows():
        stint = int(
            row.get(
                "Stint",
                index + 1,
            )
        )

        tyre_set_name = row.get(
            "Reifensatz",
            "",
        )

        tyre_info = get_set_information(
            tyre_sets,
            tyre_set_name,
        )

        if tyre_info is None:
            errors.append(
                f"Stint {stint}: "
                "Der gewählte Reifensatz "
                "existiert nicht."
            )

            continue

        profile_depth = tyre_info.get(
            "Ø Profiltiefe"
        )

        if (
            profile_depth is not None
            and profile_depth <= 1.5
        ):
            errors.append(
                f"Stint {stint}: "
                f"{tyre_set_name} hat nur noch "
                f"{profile_depth:.2f} mm Profil."
            )

        elif (
            profile_depth is not None
            and profile_depth <= 1.8
        ):
            warnings.append(
                f"Stint {stint}: "
                f"{tyre_set_name} ist mit "
                f"{profile_depth:.2f} mm stark "
                "abgenutzt."
            )

    if not tyre_change_allowed:
        changed_rows = dataframe[
            dataframe[
                "Reifenwechsel"
            ] == True
        ]

        if not changed_rows.empty:
            errors.append(
                "Reifenwechsel sind laut "
                "Rennparametern nicht erlaubt."
            )

    if tyre_change_required:
        changed_rows = dataframe[
            dataframe[
                "Reifenwechsel"
            ] == True
        ]

        if changed_rows.empty:
            errors.append(
                "Mindestens ein Reifenwechsel "
                "ist verpflichtend."
            )

    return errors, warnings


def show():
    st.subheader("Reifenstrategie")

    if (
        "strategy_parameters"
        not in st.session_state
    ):
        st.warning(
            "Bitte zuerst die Rennparameter "
            "speichern."
        )
        return

    if (
        "strategy_stints"
        not in st.session_state
    ):
        st.warning(
            "Bitte zuerst die Stintplanung "
            "erstellen und speichern."
        )
        return

    parameters = st.session_state[
        "strategy_parameters"
    ]

    stint_plan = st.session_state[
        "strategy_stints"
    ]

    tyre_sets = get_tyre_sets()

    tyre_set_names = [
        tyre["Reifensatz"]
        for tyre in tyre_sets
    ]

    if (
        "strategy_tyres"
        not in st.session_state
    ):
        st.session_state[
            "strategy_tyres"
        ] = create_default_strategy(
            stint_plan,
            tyre_sets,
        )

    st.subheader("Verfügbare Reifensätze")

    tyre_table_rows = []

    for tyre in tyre_sets:
        profile_depth = tyre.get(
            "Ø Profiltiefe"
        )

        recommendation = (
            calculate_recommendation(
                profile_depth,
                tyre.get("Status"),
            )
        )

        tyre_table_rows.append(
            {
                "Reifensatz":
                    tyre["Reifensatz"],
                "Status":
                    tyre["Status"],
                "Messungen":
                    tyre["Messungen"],
                "Ø Profiltiefe":
                    profile_depth,
                "Letzter Stint":
                    tyre["Letzter Stint"],
                "Empfehlung":
                    recommendation,
            }
        )

    tyre_dataframe = pd.DataFrame(
        tyre_table_rows
    )

    st.dataframe(
        tyre_dataframe,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Ø Profiltiefe":
                st.column_config.NumberColumn(
                    "Ø Profiltiefe",
                    format="%.2f mm",
                ),
        },
    )

    st.divider()

    if st.button(
        "Reifenstrategie neu erstellen",
        use_container_width=True,
    ):
        st.session_state[
            "strategy_tyres"
        ] = create_default_strategy(
            stint_plan,
            tyre_sets,
        )

        st.rerun()

    strategy_dataframe = pd.DataFrame(
        st.session_state[
            "strategy_tyres"
        ]
    )

    edited_dataframe = st.data_editor(
        strategy_dataframe,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "Stint":
                st.column_config.NumberColumn(
                    "Stint",
                    disabled=True,
                ),
            "Runden":
                st.column_config.NumberColumn(
                    "Runden",
                    disabled=True,
                ),
            "Reifensatz":
                st.column_config.SelectboxColumn(
                    "Reifensatz",
                    options=tyre_set_names,
                    required=True,
                ),
            "Reifenwechsel":
                st.column_config.CheckboxColumn(
                    "Reifenwechsel",
                ),
            "Doppelstint":
                st.column_config.CheckboxColumn(
                    "Doppelstint",
                    help=(
                        "Reifensatz wird in einem "
                        "weiteren Stint erneut "
                        "verwendet."
                    ),
                ),
            "Bemerkung":
                st.column_config.TextColumn(
                    "Bemerkung",
                ),
        },
        key="strategy_tyre_editor",
    )

    errors, warnings = validate_strategy(
        edited_dataframe,
        tyre_sets,
        parameters.get(
            "Reifenwechsel erlaubt",
            True,
        ),
        parameters.get(
            "Reifenwechsel verpflichtend",
            False,
        ),
    )

    if errors:
        for error in errors:
            st.error(error)

    if warnings:
        for warning in warnings:
            st.warning(warning)

    if st.button(
        "Reifenstrategie speichern",
        use_container_width=True,
        disabled=bool(errors),
    ):
        st.session_state[
            "strategy_tyres"
        ] = edited_dataframe.to_dict(
            orient="records"
        )

        st.session_state.pop(
            "strategy_pitstops",
            None,
        )

        st.success(
            "Reifenstrategie gespeichert."
        )

        st.rerun()

    st.divider()
    st.subheader("Geplante Reifenverwendung")

    for _, row in edited_dataframe.iterrows():
        tyre_info = get_set_information(
            tyre_sets,
            row["Reifensatz"],
        )

        profile_depth = (
            tyre_info.get(
                "Ø Profiltiefe"
            )
            if tyre_info
            else None
        )

        recommendation = (
            calculate_recommendation(
                profile_depth,
                tyre_info.get(
                    "Status",
                    "Unbekannt",
                ),
            )
            if tyre_info
            else "Keine Daten"
        )

        with st.container(border=True):
            col1, col2, col3, col4 = (
                st.columns(4)
            )

            col1.metric(
                "Stint",
                int(row["Stint"]),
            )

            col2.metric(
                "Reifensatz",
                row["Reifensatz"],
            )

            col3.metric(
                "Runden",
                int(row["Runden"]),
            )

            col4.metric(
                "Profiltiefe",
                (
                    f"{profile_depth:.2f} mm"
                    if profile_depth is not None
                    else "-"
                ),
            )

            st.write(
                f"**Empfehlung:** "
                f"{recommendation}"
            )

            st.write(
                "**Reifenwechsel:** "
                + (
                    "Ja"
                    if row["Reifenwechsel"]
                    else "Nein"
                )
            )

            st.write(
                "**Doppelstint:** "
                + (
                    "Ja"
                    if row["Doppelstint"]
                    else "Nein"
                )
            )

            if row.get("Bemerkung"):
                st.info(
                    row["Bemerkung"]
                )