import flet as ft
from datetime import date

from components.ev_validation_ui import get_recalculate_button
from database import get_all_stage_migration_rates, save_historical_pd_results
from components.dropdown_configuration import (
    get_configured_dropdown_options,
    get_configured_year_options,
)
from components.pd_calculations import get_yearly_net_migration_rates


def _build_historical_pd_records(raw_cache, from_year, to_year, facility_filter):
    yearly_net_rates = get_yearly_net_migration_rates(raw_cache)

    def get_average_net_migration_rates(year, facility_type):
        return {
            stage: rate
            for (item_year, item_facility_type, stage), rate in yearly_net_rates.items()
            if item_year == year and item_facility_type == facility_type
        }

    if facility_filter == "All":
        selected_facilities = sorted({
            str(item.get("facility_type") or "").strip() or "Unspecified"
            for item in raw_cache
            if str(from_year) <= str(item.get("year", "")).strip() <= str(to_year)
        })
    else:
        selected_facilities = [facility_filter]

    yearly_records = []
    stage_1_values = {}
    stage_2_values = {}
    for year in range(from_year, to_year + 1):
        for facility_type in selected_facilities:
            averages = get_average_net_migration_rates(str(year), facility_type)
            stage_1_pd = averages.get("Stage-2")
            stage_2_pd = averages.get("Stage-3")

            if stage_1_pd is not None:
                stage_1_values.setdefault(facility_type, []).append(stage_1_pd)
                yearly_records.append({
                    "year_label": str(year),
                    "facility_type": facility_type,
                    "stage": "Stage-1",
                    "pd_source": "Average Net Migration Rate of Stage-2",
                    "pd_value": stage_1_pd,
                })
            if stage_2_pd is not None:
                stage_2_values.setdefault(facility_type, []).append(stage_2_pd)
                yearly_records.append({
                    "year_label": str(year),
                    "facility_type": facility_type,
                    "stage": "Stage-2",
                    "pd_source": "Average Net Migration Rate of Stage-3",
                    "pd_value": stage_2_pd,
                })

    average_records = []
    for facility_type in selected_facilities:
        facility_stage_1_values = stage_1_values.get(facility_type, [])
        facility_stage_2_values = stage_2_values.get(facility_type, [])
        if not facility_stage_1_values and not facility_stage_2_values:
            continue
        average_stage_1 = (
            sum(facility_stage_1_values) / len(facility_stage_1_values)
            if facility_stage_1_values else 0.0
        )
        average_stage_2 = (
            sum(facility_stage_2_values) / len(facility_stage_2_values)
            if facility_stage_2_values else 0.0
        )
        average_records.extend([
            {
                "year_label": f"{from_year}-{to_year}",
                "facility_type": facility_type,
                "stage": "Stage-1",
                "pd_source": "Average PD",
                "pd_value": average_stage_1,
            },
            {
                "year_label": f"{from_year}-{to_year}",
                "facility_type": facility_type,
                "stage": "Stage-2",
                "pd_source": "Average PD",
                "pd_value": average_stage_2,
            },
        ])

    return average_records + yearly_records


def get_pd_calculation_form(page: ft.Page, recalculation_state=None):
    today = date.today()
    raw_cache = get_all_stage_migration_rates() or []

    base_field_style = {
        "height": 45,
        "content_padding": ft.Padding(12, 10, 12, 10),
        "border_color": "#00e676",
        "focused_border_color": "#00e676",
        "label_style": ft.TextStyle(color="white70", size=14),
        "text_style": ft.TextStyle(color="white", size=13),
    }

    year_options = get_configured_year_options(
        record.get("year") for record in raw_cache
    )
    from_year_default = (
        "2020" if "2020" in year_options else (year_options[0] if year_options else None)
    )
    to_year_default = (
        str(today.year)
        if str(today.year) in year_options
        else (year_options[-1] if year_options else None)
    )
    from_year_dd = ft.Dropdown(
        label="From Year",
        options=[ft.dropdown.Option(year) for year in year_options],
        value=from_year_default,
        width=160,
        **base_field_style,
    )
    to_year_dd = ft.Dropdown(
        label="To Year",
        options=[ft.dropdown.Option(year) for year in year_options],
        value=to_year_default,
        width=160,
        **base_field_style,
    )
    stored_facility_types = {
        str(item.get("facility_type") or "").strip() or "Unspecified"
        for item in raw_cache
    }
    configured_facility_types = get_configured_dropdown_options("facility.all")
    facility_type_options = ["All"] + configured_facility_types
    facility_type_options.extend(sorted(
        stored_facility_types.difference(facility_type_options, {"Unspecified"})
    ))
    facility_type_dd = ft.Dropdown(
        label="Facility Type",
        options=[ft.dropdown.Option(value) for value in facility_type_options],
        value="All",
        width=220,
        **base_field_style,
    )
    table_holder = ft.Container(expand=True)

    def render_table(e=None):
        from_year = int(from_year_dd.value or "2020")
        to_year = int(to_year_dd.value or str(today.year))

        if from_year > to_year:
            if e is not None and e.control is from_year_dd:
                to_year_dd.value = str(from_year)
            else:
                from_year_dd.value = str(to_year)
            from_year, to_year = sorted((from_year, to_year))

        records = _build_historical_pd_records(
            raw_cache,
            from_year,
            to_year,
            facility_type_dd.value or "All",
        )
        pd_rows = [
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(record["year_label"], weight="bold", color="#00e676", size=12)),
                ft.DataCell(ft.Text(record["facility_type"], color="white", size=12)),
                ft.DataCell(ft.Text(record["stage"], weight="bold", color="white", size=12)),
                ft.DataCell(ft.Text(record["pd_source"], color="white", weight="bold", size=12)),
                ft.DataCell(ft.Text(
                    f"{record['pd_value'] * 100:.2f}%",
                    color="#78eb64",
                    weight="bold",
                    size=12,
                )),
            ])
            for record in records
        ]

        table_holder.content = ft.Row([
            ft.DataTable(
                width=980,
                columns=[
                    ft.DataColumn(ft.Text("Year", color="white", weight="bold", size=12)),
                    ft.DataColumn(ft.Text("Facility Type", color="white", weight="bold", size=12)),
                    ft.DataColumn(ft.Text("Stage", color="white", weight="bold", size=12)),
                    ft.DataColumn(ft.Text("PD Source", color="white", weight="bold", size=12)),
                    ft.DataColumn(ft.Text("PD (%)", color="white", weight="bold", size=12)),
                ],
                rows=pd_rows,
                border=ft.Border.all(0.5, "#1e534b"),
                heading_row_color="#0c3832",
                heading_row_height=40,
                data_row_min_height=38,
                column_spacing=20,
            )
        ], scroll=ft.ScrollMode.AUTO)
        if e is not None:
            table_holder.update()

    from_year_dd.on_select = render_table
    to_year_dd.on_select = render_table
    facility_type_dd.on_select = render_table
    render_table()

    def recalculate_and_save(e):
        nonlocal raw_cache
        latest_records = get_all_stage_migration_rates() or []
        from_year = int(from_year_dd.value or "2020")
        to_year = int(to_year_dd.value or str(today.year))
        range_start, range_end = sorted((from_year, to_year))
        from_year_dd.value = str(range_start)
        to_year_dd.value = str(range_end)
        facility_filter = facility_type_dd.value or "All"
        calculated_records = _build_historical_pd_records(
            latest_records,
            range_start,
            range_end,
            facility_filter,
        )
        saved_count = save_historical_pd_results(
            calculated_records,
            range_start,
            range_end,
            facility_filter,
        )
        raw_cache = latest_records
        stored_facilities = {
            str(item.get("facility_type") or "").strip() or "Unspecified"
            for item in raw_cache
        }
        available_facilities = (
            ["All"]
            + configured_facility_types
            + sorted(stored_facilities.difference(configured_facility_types, {"Unspecified"}))
        )
        facility_type_dd.options = [
            ft.dropdown.Option(value)
            for value in available_facilities
        ]
        if facility_filter not in available_facilities:
            facility_type_dd.value = "All"
        render_table(e)
        return f"Recalculated and saved {saved_count} Historical PD result(s)."

    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text("Historical PD", size=20, weight="bold", color="#00e676"),
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding(0, 0, 0, 10),
            ),
            ft.Container(
                content=ft.Column([
                    get_recalculate_button(
                        page,
                        recalculate_and_save,
                        recalculation_state,
                        button_label="Recalculate and Save",
                        button_width=190,
                        show_completed_label=True,
                    ),
                    ft.Row([
                        ft.Text("Year Range:", size=14, weight="bold", color="#00e676"),
                        from_year_dd,
                        ft.Text("to", size=13, color="white70"),
                        to_year_dd,
                        facility_type_dd,
                    ], vertical_alignment="center"),
                    ft.Container(height=10),
                    table_holder,
                ]),
                padding=15,
                border=ft.Border.all(width=1, color="#00e676"),
                border_radius=8,
                bgcolor="#061d19",
            ),
        ], scroll=ft.ScrollMode.ALWAYS, expand=True),
        expand=True,
    )
