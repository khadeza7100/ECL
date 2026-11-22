import flet as ft
from components.dropdown_configuration import get_configured_dropdown_options
from datetime import date

from components.ev_validation_ui import get_recalculate_button
from components.pd_regression import EV_PREDICTORS, build_pd_regression_models
from components.regression import predict_multiple_regression
from database import (
    get_all_economic_variables,
    get_all_stage_migration_rates,
    save_adjusted_pd_results,
)


def _build_adjusted_pd_data(economic_data, migration_data):
    matched_years, regressions = build_pd_regression_models(
        economic_data,
        migration_data,
    )
    data_rows = []
    for regression in regressions:
        model = regression["model"]
        for observation in regression["observations"]:
            raw_prediction = (
                predict_multiple_regression(model, observation["predictors"])
                if model is not None else None
            )
            adjusted_pd = (
                min(1.0, max(0.0, raw_prediction))
                if raw_prediction is not None else None
            )
            historical_pd = observation["historical_pd"]
            data_rows.append({
                "facility_type": regression["facility_type"],
                "pd_stage": regression["pd_stage"],
                "year": observation["year"],
                "historical_pd": historical_pd,
                "adjusted_pd_value": adjusted_pd,
                "adjusted_pd": (
                    f"{adjusted_pd * 100:.2f}%"
                    if adjusted_pd is not None else "N/A"
                ),
                "change": (
                    f"{(adjusted_pd - historical_pd) * 100:+.2f}%"
                    if adjusted_pd is not None else "N/A"
                ),
                "model_n": len(regression["years"]),
            })
    return matched_years, regressions, data_rows


def get_adjusted_pd_form(page: ft.Page, on_recalculate=None, recalculation_state=None):
    economic_data = get_all_economic_variables() or {}
    migration_data = get_all_stage_migration_rates() or []
    matched_years, regressions, data_rows = _build_adjusted_pd_data(
        economic_data,
        migration_data,
    )

    current_year = str(date.today().year)
    available_year_label = "none"
    if matched_years:
        numeric_years = [
            int(year) for year in matched_years if year.isdigit()
        ]
        if (
            len(numeric_years) == len(matched_years)
            and numeric_years == list(range(numeric_years[0], numeric_years[-1] + 1))
        ):
            available_year_label = f"{numeric_years[0]}-{numeric_years[-1]}"
        else:
            available_year_label = ", ".join(matched_years)
        if current_year in matched_years:
            coverage_text = (
                "Matched historical PD and economic-variable data is available "
                f"for {available_year_label}."
            )
        else:
            coverage_text = (
                "Matched historical PD and economic-variable data is available "
                f"for {available_year_label}. No matched data is available for "
                f"{current_year}."
            )
    else:
        coverage_text = (
            "No matched historical PD and economic-variable data is available, "
            f"including {current_year}."
        )

    year_values = set(matched_years)
    year_values.update(get_configured_dropdown_options("year"))
    year_values.add(current_year)
    sorted_years = sorted(
        year_values,
        key=lambda year: (
            not year.isdigit(),
            int(year) if year.isdigit() else year,
        ),
        reverse=True,
    )
    year_filter = ft.Dropdown(
        label="Year",
        options=[
            ft.dropdown.Option("All"),
            *[ft.dropdown.Option(year) for year in sorted_years],
        ],
        value=current_year,
        width=160,
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
    )
    facility_types = sorted({
        regression["facility_type"] for regression in regressions
    })
    facility_filter = ft.Dropdown(
        label="Facility Type",
        options=[
            ft.dropdown.Option("All"),
            *[ft.dropdown.Option(value) for value in facility_types],
        ],
        value="All",
        width=220,
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
    )
    pd_stages = sorted({
        regression["pd_stage"] for regression in regressions
    })
    pd_stage_filter = ft.Dropdown(
        label="PD Stage",
        options=[
            ft.dropdown.Option("All"),
            *[ft.dropdown.Option(value) for value in pd_stages],
        ],
        value="All",
        width=180,
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
    )

    table_holder = ft.Container(expand=True)

    def render_table(e=None):
        filtered_rows = [
            row for row in data_rows
            if (year_filter.value == "All" or row["year"] == year_filter.value)
            and (
                facility_filter.value == "All"
                or row["facility_type"] == facility_filter.value
            )
            and (
                pd_stage_filter.value == "All"
                or row["pd_stage"] == pd_stage_filter.value
            )
        ]
        rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(row["facility_type"], color="white", size=11)),
                ft.DataCell(ft.Text(row["pd_stage"], color="white", size=11)),
                ft.DataCell(ft.Text(row["year"], color="white", size=11)),
                ft.DataCell(ft.Text(
                    f"{row['historical_pd'] * 100:.2f}%",
                    color="white",
                    size=11,
                )),
                ft.DataCell(ft.Text(row["adjusted_pd"], color="#78eb64", weight="bold", size=11)),
                ft.DataCell(ft.Text(row["change"], color="white", size=11)),
                ft.DataCell(ft.Text(str(row["model_n"]), color="white", size=11)),
            ])
            for row in filtered_rows
        ]
        if not rows:
            if year_filter.value != "All" and year_filter.value not in matched_years:
                if matched_years:
                    empty_message = (
                        f"No matched data is available for {year_filter.value}. "
                        f"Available years: {available_year_label}."
                    )
                else:
                    empty_message = (
                        f"No matched data is available for {year_filter.value}; "
                        "there are no matched years."
                    )
            else:
                empty_message = "No Adjusted PD records match the selected filters."
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(
                    empty_message,
                    color="white70",
                    italic=True,
                    size=12,
                )),
                *[ft.DataCell(ft.Text("", size=11)) for _ in range(6)],
            ]))

        table_holder.content = ft.Row([
            ft.DataTable(
                width=1000,
                columns=[
                    ft.DataColumn(ft.Text("Facility Type", color="white", weight="bold", size=11)),
                    ft.DataColumn(ft.Text("PD Stage", color="white", weight="bold", size=11)),
                    ft.DataColumn(ft.Text("Year", color="white", weight="bold", size=11)),
                    ft.DataColumn(ft.Text("Historical PD", color="white", weight="bold", size=11)),
                    ft.DataColumn(ft.Text("Adjusted PD", color="white", weight="bold", size=11)),
                    ft.DataColumn(ft.Text("Change", color="white", weight="bold", size=11)),
                    ft.DataColumn(ft.Text("Model N", color="white", weight="bold", size=11)),
                ],
                rows=rows,
                border=ft.Border.all(0.5, "#1e534b"),
                heading_row_color="#0c3832",
                heading_row_height=40,
                data_row_min_height=36,
                column_spacing=14,
            )
        ], scroll=ft.ScrollMode.AUTO)
        if e is not None:
            table_holder.update()

    year_filter.on_select = render_table
    facility_filter.on_select = render_table
    pd_stage_filter.on_select = render_table
    render_table()

    note = (
        "Adjusted PD is the multiple-regression estimate of historical PD for each "
        "matched year and facility type, using "
        f"{', '.join(EV_PREDICTORS)}. Estimates are constrained to 0%-100%. "
        f"Matched years: {', '.join(matched_years) if matched_years else 'none'}. "
        "A model needs enough non-collinear observations; unavailable models are marked accordingly. "
        "These fitted historical estimates are not forward forecasts."
    )

    def recalculate_and_save(e):
        latest_economic_data = get_all_economic_variables() or {}
        latest_migration_data = get_all_stage_migration_rates() or []
        _, _, recalculated_rows = _build_adjusted_pd_data(
            latest_economic_data,
            latest_migration_data,
        )
        saved_count = save_adjusted_pd_results([
            {
                "year": row["year"],
                "facility_type": row["facility_type"],
                "pd_stage": row["pd_stage"],
                "historical_pd": row["historical_pd"],
                "adjusted_pd": row["adjusted_pd_value"],
                "model_n": row["model_n"],
            }
            for row in recalculated_rows
            if row["adjusted_pd_value"] is not None
        ])
        if on_recalculate is not None:
            on_recalculate(e)
        return f"Recalculated and saved {saved_count} Adjusted PD result(s)."

    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text("Adjusted PD", size=20, weight="bold", color="#00e676"),
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding(0, 0, 0, 10),
            ),
            ft.Container(
                content=ft.Column([
                    get_recalculate_button(
                        page,
                        recalculate_and_save,
                        recalculation_state,
                        button_label="Recalculate & Save",
                        button_width=180,
                    ),
                    ft.Row(
                        [year_filter, facility_filter, pd_stage_filter],
                        spacing=12,
                        wrap=True,
                    ),
                    ft.Container(
                        content=ft.Text(
                            coverage_text,
                            color="#ffcc80" if current_year not in matched_years else "#78eb64",
                            size=12,
                            weight="bold",
                        ),
                        bgcolor="#2b271b" if current_year not in matched_years else "#0c3832",
                        border=ft.Border.all(
                            1,
                            "#ffcc80" if current_year not in matched_years else "#1e534b",
                        ),
                        border_radius=6,
                        padding=10,
                    ),
                    ft.Text(note, color="white70", size=12),
                    ft.Container(height=8),
                    table_holder,
                ]),
                padding=15,
                border=ft.Border.all(width=1, color="#00e676"),
                border_radius=8,
                bgcolor="#061d19",
            ),
        ], scroll=ft.ScrollMode.AUTO, expand=True),
        expand=True,
    )
