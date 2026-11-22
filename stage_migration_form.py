import flet as ft
from datetime import date
from database import (
    save_stage_migration_rate,
    get_all_stage_migration_rates,
    delete_stage_migration_rate
)
from components.dropdown_configuration import (
    get_configured_dropdown_options,
    get_configured_year_options,
)

def get_stage_migration_form(page: ft.Page):
    raw_cache = get_all_stage_migration_rates() or []
    editing_record_id = None
    today = date.today()
    default_year = str(today.year)
    year_options = get_configured_year_options(
        record.get("year") for record in raw_cache
    )
    default_year = (
        default_year
        if default_year in year_options
        else (year_options[-1] if year_options else None)
    )

    facility_type_options = get_configured_dropdown_options("facility.all")
    facility_filter_options = ["All"] + facility_type_options
    migrated_options = ["Stage-1", "Stage-2", "Stage-3"]
    migrated_to_options = ["Stage-1", "Stage-2", "Stage-3"]

    # Form input fields
    year_dd = ft.Dropdown(
        label="Year",
        options=[ft.dropdown.Option(year) for year in year_options],
        value=default_year,
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
        expand=True
    )

    facility_type_dd = ft.Dropdown(
        label="Facility Type",
        options=[ft.dropdown.Option(opt) for opt in facility_type_options],
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
        expand=True
    )

    migrated_from_dd = ft.Dropdown(
        label="Migrated from",
        options=[ft.dropdown.Option(opt) for opt in migrated_options],
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
        expand=True
    )

    migrated_to_dd = ft.Dropdown(
        label="Migrated To",
        options=[ft.dropdown.Option(opt) for opt in migrated_to_options],
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
        expand=True
    )

    num_migrated_tf = ft.TextField(
        label="Number of A/C Migrated",
        hint_text="0",
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
        keyboard_type=ft.KeyboardType.NUMBER,
        expand=True
    )

    total_ac_tf = ft.TextField(
        label="Total A/C of that Stage",
        hint_text="0",
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
        keyboard_type=ft.KeyboardType.NUMBER,
        expand=True
    )

    migration_rate_tf = ft.TextField(
        label="Migration Rate",
        value="0.0000",
        read_only=True,
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
        expand=True
    )

    def parse_int(val):
        try: return int(val) if val else 0
        except ValueError: return 0

    def calculate_migration_rate(e=None):
        num_migrated = parse_int(num_migrated_tf.value)
        total_ac = parse_int(total_ac_tf.value)
        if total_ac > 0:
            rate = num_migrated / total_ac
            migration_rate_tf.value = f"{rate:.4f}"
        else:
            migration_rate_tf.value = "0.0000"
        page.update()

    num_migrated_tf.on_change = calculate_migration_rate
    total_ac_tf.on_change = calculate_migration_rate

    # Form Layout Grid
    row1 = ft.Row([
        ft.Container(content=year_dd, expand=1),
        ft.Container(content=facility_type_dd, expand=1),
        ft.Container(content=migrated_from_dd, expand=1),
    ], spacing=15)

    row2 = ft.Row([
        ft.Container(content=migrated_to_dd, expand=1),
        ft.Container(content=num_migrated_tf, expand=1),
        ft.Container(content=total_ac_tf, expand=1),
    ], spacing=15)

    row3 = ft.Row([
        ft.Container(content=migration_rate_tf, expand=1),
        ft.Container(expand=1),
        ft.Container(expand=1),
    ], spacing=15)

    def clear_form_fields():
        nonlocal editing_record_id
        editing_record_id = None
        year_dd.value = default_year
        facility_type_dd.value = None
        migrated_from_dd.value = None
        migrated_to_dd.value = None
        num_migrated_tf.value = ""
        total_ac_tf.value = ""
        migration_rate_tf.value = "0.0000"
        page.update()

    def populate_fields(data_item):
        nonlocal editing_record_id
        editing_record_id = data_item.get("id")
        year_dd.value = str(data_item.get("year", ""))
        facility_type_dd.value = str(data_item.get("facility_type") or "") or None
        migrated_from_dd.value = str(data_item.get("migrated_from", ""))
        migrated_to_dd.value = str(data_item.get("migrated_to", ""))
        num_migrated_tf.value = str(data_item.get("num_migrated", 0))
        total_ac_tf.value = str(data_item.get("total_ac_stage", 0))
        calculate_migration_rate()

    # Search fields (Search Year, Migrated from)
    search_year_tf = ft.TextField(
        value=str(today.year),
        hint_text="YYYY",
        hint_style=ft.TextStyle(color="white38", size=13),
        width=75,
        height=40,
        content_padding=ft.Padding(10, 8, 10, 8),
        border_color="#00e676",
        focused_border_color="#00e676",
        text_style=ft.TextStyle(color="white", size=13, weight="bold"),
        keyboard_type=ft.KeyboardType.NUMBER
    )

    search_migrated_dd = ft.Dropdown(
        hint_text="All Stages",
        options=[ft.dropdown.Option("All")] + [ft.dropdown.Option(opt) for opt in migrated_options],
        width=110,
        height=40,
        content_padding=ft.Padding(10, 0, 10, 0),
        border_color="#00e676",
        focused_border_color="#00e676",
        text_style=ft.TextStyle(color="white", size=13),
        value="All"
    )

    search_migrated_to_dd = ft.Dropdown(
        hint_text="All Stages",
        options=[ft.dropdown.Option("All")] + [ft.dropdown.Option(opt) for opt in migrated_to_options],
        width=110,
        height=40,
        content_padding=ft.Padding(10, 0, 10, 0),
        border_color="#00e676",
        focused_border_color="#00e676",
        text_style=ft.TextStyle(color="white", size=13),
        value="All"
    )

    search_facility_dd = ft.Dropdown(
        hint_text="All Facility Types",
        options=[ft.dropdown.Option(opt) for opt in facility_filter_options],
        width=130,
        height=40,
        content_padding=ft.Padding(10, 0, 10, 0),
        border_color="#00e676",
        focused_border_color="#00e676",
        text_style=ft.TextStyle(color="white", size=13),
        value="All"
    )

    category_filters = {}
    for category in ("upward", "downward", "net"):
        category_filters[category] = {
            "year": ft.TextField(
                value=str(today.year),
                hint_text="YYYY",
                hint_style=ft.TextStyle(color="white38", size=13),
                width=75,
                height=40,
                content_padding=ft.Padding(10, 8, 10, 8),
                border_color="#00e676",
                focused_border_color="#00e676",
                text_style=ft.TextStyle(color="white", size=13, weight="bold"),
                keyboard_type=ft.KeyboardType.NUMBER
            ),
            "stage": ft.Dropdown(
                hint_text="All Stages",
                options=[ft.dropdown.Option("All")] + [ft.dropdown.Option(opt) for opt in migrated_options],
                width=110,
                height=40,
                content_padding=ft.Padding(10, 0, 10, 0),
                border_color="#00e676",
                focused_border_color="#00e676",
                text_style=ft.TextStyle(color="white", size=13),
                value="All"
            ),
            "to": ft.Dropdown(
                hint_text="All Stages",
                options=[ft.dropdown.Option("All")] + [ft.dropdown.Option(opt) for opt in migrated_to_options],
                width=110,
                height=40,
                content_padding=ft.Padding(10, 0, 10, 0),
                border_color="#00e676",
                focused_border_color="#00e676",
                text_style=ft.TextStyle(color="white", size=13),
                value="All"
            ),
            "facility": ft.Dropdown(
                hint_text="All Facility Types",
                options=[ft.dropdown.Option(opt) for opt in facility_filter_options],
                width=130,
                height=40,
                content_padding=ft.Padding(10, 0, 10, 0),
                border_color="#00e676",
                focused_border_color="#00e676",
                text_style=ft.TextStyle(color="white", size=13),
                value="All"
            ),
        }

    def create_category_search_row(category):
        controls = category_filters[category]
        if category == "net":
            return ft.Row([
                ft.Text("Year:", size=11, weight="bold", color="#00e676"),
                controls["year"],
                ft.Text("Type:", size=11, weight="bold", color="#00e676"),
                controls["facility"],
                ft.Text("Stage:", size=11, weight="bold", color="#00e676"),
                controls["stage"],
            ], vertical_alignment="center", spacing=6)

        return ft.Row([
            ft.Text("Year:", size=11, weight="bold", color="#00e676"),
            controls["year"],
            ft.Text("Type:", size=11, weight="bold", color="#00e676"),
            controls["facility"],
            ft.Text("From:", size=11, weight="bold", color="#00e676"),
            controls["stage"],
            ft.Text("To:", size=11, weight="bold", color="#00e676"),
            controls["to"],
        ], vertical_alignment="center", spacing=6)

    history_table_holder = ft.Container(expand=True)
    upward_table_holder = ft.Container(expand=True)
    downward_table_holder = ft.Container(expand=True)
    net_table_holder = ft.Container(expand=True)

    def filter_records(records, yr_search="", stage_search="All", to_search="All", facility_search="All"):
        filtered = list(records)
        if yr_search.strip():
            filtered = [r for r in filtered if yr_search.strip().lower() in str(r.get("year", "")).lower()]
        if stage_search and stage_search != "All":
            filtered = [r for r in filtered if str(r.get("migrated_from", "")).lower() == stage_search.lower()]
        if to_search and to_search != "All":
            filtered = [r for r in filtered if str(r.get("migrated_to", "")).lower() == to_search.lower()]
        if facility_search and facility_search != "All":
            if facility_search == "Unspecified":
                filtered = [r for r in filtered if not str(r.get("facility_type") or "").strip()]
            else:
                filtered = [
                    r for r in filtered
                    if str(r.get("facility_type") or "").strip().lower() == facility_search.lower()
                ]
        return filtered

    def get_table_control(yr_search="", stage_search="All", to_search="All", facility_search="All"):
        filtered = filter_records(raw_cache, yr_search, stage_search, to_search, facility_search)
        filtered = filtered[:10]

        if not filtered:
            return ft.Container(content=ft.Text("No records found.", color="white54", italic=True, size=13), padding=15)

        rows = []
        for item in filtered:
            yr = str(item.get("year", ""))
            facility_type_value = str(item.get("facility_type") or "").strip()
            facility_type = facility_type_value or "Unspecified"
            stage = str(item.get("migrated_from", ""))
            migrated_to = str(item.get("migrated_to", ""))

            action_cell = ft.Row([
                ft.IconButton(icon=ft.Icons.EDIT, icon_color="#00e676", icon_size=18, tooltip="Edit", on_click=lambda e, d=item: populate_fields(d)),
                ft.IconButton(icon=ft.Icons.DELETE, icon_color="#ff5252", icon_size=18, tooltip="Delete", on_click=lambda e, y=yr, f=facility_type_value, s=stage, t=migrated_to: execute_delete(y, f, s, t))
            ], spacing=0, alignment="center")

            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(yr, weight="bold", color="#00e676", size=11)),
                ft.DataCell(ft.Text(facility_type, color="white", size=11)),
                ft.DataCell(ft.Text(stage, color="white", size=11)),
                ft.DataCell(ft.Text(migrated_to, color="white", size=11)),
                ft.DataCell(ft.Text(str(item.get('num_migrated', 0)), color="white", size=11)),
                ft.DataCell(ft.Text(str(item.get('total_ac_stage', 0)), color="white", size=11)),
                ft.DataCell(ft.Text(f"{float(item.get('migration_rate', 0)):.4f}", color="white", weight="bold", size=11)),
                ft.DataCell(action_cell)
            ]))

        return ft.DataTable(
            width=780,
            columns=[
                ft.DataColumn(ft.Text("Year", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Facility Type", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Migrated From", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Migrated To", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Migrated A/C", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Total A/C", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Migration Rate", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Actions", color="white", weight="bold", size=11)),
            ],
            rows=rows,
            border=ft.Border.all(0.5, "#1e534b"),
            heading_row_color="#0c3832",
            heading_row_height=36,
            data_row_min_height=34,
            column_spacing=8
        )

    def get_category_summary(category, yr_search="", stage_search="All", to_search="All", facility_search="All"):
        if category == "net":
            records = filter_records(raw_cache, yr_search, facility_search=facility_search)
        else:
            records = filter_records(raw_cache, yr_search, stage_search, to_search, facility_search)
        if not records:
            return ft.Container(content=ft.Text("No summary data available.", color="white54", italic=True, size=13), padding=15)

        if category == "net":
            yearly_net = {}
            for item in records:
                year = str(item.get("year", "")).strip()
                facility_type = str(item.get("facility_type") or "").strip() or "Unspecified"
                migrated_from = str(item.get("migrated_from", "")).strip()
                migrated_to = str(item.get("migrated_to", "")).strip()
                if not year or not migrated_from or not migrated_to:
                    continue

                try:
                    from_stage = int(migrated_from.split("-")[-1])
                    to_stage = int(migrated_to.split("-")[-1])
                except (TypeError, ValueError):
                    continue

                rate = float(item.get("migration_rate", 0) or 0)
                from_key = (year, facility_type, migrated_from)
                to_key = (year, facility_type, migrated_to)
                yearly_net.setdefault(from_key, 0.0)
                yearly_net.setdefault(to_key, 0.0)
                yearly_net[from_key] -= rate
                yearly_net[to_key] += rate

            grouped_by_stage = {}
            for (year, facility_type, stage), net_rate in yearly_net.items():
                grouped_by_stage.setdefault((facility_type, stage), []).append(net_rate)

            average_by_stage = {
                stage: sum(rates) / len(rates) if rates else 0.0
                for stage, rates in grouped_by_stage.items()
            }

            rows = []
            for year, facility_type, stage in sorted(
                yearly_net.keys(), key=lambda key: (key[2], key[1], key[0]), reverse=True
            ):
                if stage_search and stage_search != "All" and stage.lower() != stage_search.lower():
                    continue
                facility_average = average_by_stage[(facility_type, stage)]
                rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(year, weight="bold", color="#00e676", size=11)),
                    ft.DataCell(ft.Text(facility_type, color="white", size=11)),
                    ft.DataCell(ft.Text(stage, color="white", size=11)),
                    ft.DataCell(ft.Text(f"{yearly_net[(year, facility_type, stage)]:.4f}", color="white", weight="bold", size=11)),
                    ft.DataCell(ft.Text(f"{facility_average:.4f}", color="#78eb64", weight="bold", size=11)),
                ]))

            if not rows:
                return ft.Container(content=ft.Text("No records found.", color="white54", italic=True, size=13), padding=15)

            return ft.DataTable(
                width=920,
                columns=[
                    ft.DataColumn(ft.Text("Year", color="white", weight="bold", size=11)),
                    ft.DataColumn(ft.Text("Facility Type", color="white", weight="bold", size=11)),
                    ft.DataColumn(ft.Text("Stage", color="white", weight="bold", size=11)),
                    ft.DataColumn(ft.Text("Net Migration Rate", color="white", weight="bold", size=11)),
                    ft.DataColumn(ft.Text("Average Net Migration Rate", color="white", weight="bold", size=11)),
                ],
                rows=rows,
                border=ft.Border.all(0.5, "#1e534b"),
                heading_row_color="#0c3832",
                heading_row_height=36,
                data_row_min_height=34,
                column_spacing=30
            )

        grouped = {}
        for item in records:
            migrated_from = str(item.get("migrated_from", "")).strip()
            migrated_to = str(item.get("migrated_to", "")).strip()
            year = str(item.get("year", "")).strip()
            facility_type = str(item.get("facility_type") or "").strip() or "Unspecified"
            if not migrated_from:
                continue

            try:
                from_stage = int(str(migrated_from).strip().split("-")[-1])
                to_stage = int(str(migrated_to).strip().split("-")[-1])
            except (TypeError, ValueError):
                continue

            rate = float(item.get("migration_rate", 0) or 0)
            if to_stage > from_stage:
                direction = "upward"
            elif to_stage < from_stage:
                direction = "downward"
            else:
                continue

            if category != "net" and direction != category:
                continue

            key = (year, facility_type, migrated_from, migrated_to)
            if key not in grouped:
                grouped[key] = {"rates": [], "num_migrated": 0, "total_ac_stage": 0}

            if category == "net":
                grouped[key]["rates"].append(rate if direction == "upward" else -rate)
            else:
                grouped[key]["rates"].append(rate)
            grouped[key]["num_migrated"] += parse_int(item.get("num_migrated", 0))
            grouped[key]["total_ac_stage"] += parse_int(item.get("total_ac_stage", 0))

        rows = []
        for year, facility_type, migrated_from, migrated_to in sorted(grouped.keys(), reverse=True):
            data = grouped[(year, facility_type, migrated_from, migrated_to)]
            average_rate = sum(data["rates"]) / len(data["rates"]) if data["rates"] else 0.0

            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(year, color="white", size=11)),
                ft.DataCell(ft.Text(facility_type, color="white", size=11)),
                ft.DataCell(ft.Text(migrated_from, weight="bold", color="#00e676", size=11)),
                ft.DataCell(ft.Text(migrated_to, color="white", size=11)),
                ft.DataCell(ft.Text(str(data["num_migrated"]), color="white", size=11)),
                ft.DataCell(ft.Text(str(data["total_ac_stage"]), color="white", size=11)),
                ft.DataCell(ft.Text(f"{average_rate:.4f}", color="white", weight="bold", size=11)),
            ]))

        if not rows:
            return ft.Container(content=ft.Text("No records found.", color="white54", italic=True, size=13), padding=15)

        return ft.DataTable(
            width=920,
            columns=[
                ft.DataColumn(ft.Text("Year", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Facility Type", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Migrated From", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Migrated To", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("No. of A/C Migrated", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Total A/C of that Stage", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Average Migration Rate", color="white", weight="bold", size=11)),
            ],
            rows=rows,
            border=ft.Border.all(0.5, "#1e534b"),
            heading_row_color="#0c3832",
            heading_row_height=36,
            data_row_min_height=34,
            column_spacing=20
        )

    def render_all_tables():
        history_table_holder.content = get_table_control(
            search_year_tf.value or "",
            search_migrated_dd.value or "All",
            search_migrated_to_dd.value or "All",
            search_facility_dd.value or "All"
        )
        for category, holder in (
            ("upward", upward_table_holder),
            ("downward", downward_table_holder),
            ("net", net_table_holder),
        ):
            controls = category_filters[category]
            holder.content = get_category_summary(
                category,
                controls["year"].value or "",
                controls["stage"].value or "All",
                controls["to"].value or "All",
                controls["facility"].value or "All"
            )

    def update_search_filter(e):
        history_table_holder.content = get_table_control(
            search_year_tf.value or "",
            search_migrated_dd.value or "All",
            search_migrated_to_dd.value or "All",
            search_facility_dd.value or "All"
        )
        history_table_holder.update()

    search_year_tf.on_change = update_search_filter
    search_migrated_dd.on_select = update_search_filter
    search_migrated_to_dd.on_select = update_search_filter
    search_facility_dd.on_select = update_search_filter

    def update_category_filter(category, holder):
        controls = category_filters[category]
        holder.content = get_category_summary(
            category,
            controls["year"].value or "",
            controls["stage"].value or "All",
            controls["to"].value or "All",
            controls["facility"].value or "All"
        )
        holder.update()

    for category, holder in (
        ("upward", upward_table_holder),
        ("downward", downward_table_holder),
        ("net", net_table_holder),
    ):
        controls = category_filters[category]
        controls["year"].on_change = lambda e, c=category, h=holder: update_category_filter(c, h)
        controls["stage"].on_select = lambda e, c=category, h=holder: update_category_filter(c, h)
        controls["to"].on_select = lambda e, c=category, h=holder: update_category_filter(c, h)
        controls["facility"].on_select = lambda e, c=category, h=holder: update_category_filter(c, h)

    search_header_row = ft.Row([
        ft.Text("Year:", size=11, weight="bold", color="#00e676"),
        search_year_tf,
        ft.Text("Type:", size=11, weight="bold", color="#00e676"),
        search_facility_dd,
        ft.Text("From:", size=11, weight="bold", color="#00e676"),
        search_migrated_dd,
        ft.Text("To:", size=11, weight="bold", color="#00e676"),
        search_migrated_to_dd
    ], vertical_alignment="center", spacing=6)

    # Detailed Records & Search Table
    history_section_container = ft.Container(
        content=ft.Column([
            search_header_row,
            ft.Container(height=10),
            ft.Row([history_table_holder], scroll=ft.ScrollMode.AUTO, expand=True)
        ], horizontal_alignment="stretch"),
        padding=15,
        border=ft.Border.all(width=1, color="#00e676"),
        border_radius=8,
        bgcolor="#061d19"
    )

    upward_section_container = ft.Container(
        content=ft.Column([
            ft.Text("Upward Migration Rate (Role Rate)", size=16, weight="bold", color="#00e676"),
            create_category_search_row("upward"),
            ft.Container(height=8),
            ft.Row([upward_table_holder], scroll=ft.ScrollMode.AUTO, expand=True),
        ], horizontal_alignment="stretch"),
        padding=15,
        border=ft.Border.all(width=1, color="#00e676"),
        border_radius=8,
        bgcolor="#061d19"
    )

    downward_section_container = ft.Container(
        content=ft.Column([
            ft.Text("Downward Migration Rate (Cure/Improvement Rate)", size=16, weight="bold", color="#00e676"),
            create_category_search_row("downward"),
            ft.Container(height=8),
            ft.Row([downward_table_holder], scroll=ft.ScrollMode.AUTO, expand=True),
        ], horizontal_alignment="stretch"),
        padding=15,
        border=ft.Border.all(width=1, color="#00e676"),
        border_radius=8,
        bgcolor="#061d19"
    )

    net_section_container = ft.Container(
        content=ft.Column([
            ft.Text("Net Migration Rate", size=16, weight="bold", color="#00e676"),
            create_category_search_row("net"),
            ft.Container(height=8),
            ft.Row([net_table_holder], scroll=ft.ScrollMode.AUTO, expand=True),
        ], horizontal_alignment="stretch"),
        padding=15,
        border=ft.Border.all(width=1, color="#00e676"),
        border_radius=8,
        bgcolor="#061d19"
    )

    def refresh_cache():
        nonlocal raw_cache
        raw_cache = get_all_stage_migration_rates() or []

    def update_all_containers():
        refresh_cache()
        clear_form_fields()
        render_all_tables()

    def on_save_click(e):
        yr = year_dd.value or ""
        facility_type = facility_type_dd.value or ""
        migrated_from = migrated_from_dd.value or ""
        migrated_to = migrated_to_dd.value or ""

        if not yr or not facility_type or not migrated_from or not migrated_to:
            page.overlay.append(ft.SnackBar(content=ft.Text("Please select Year, Facility Type, Migrated From, and Migrated To stages!"), bgcolor="#ff9800", open=True))
            page.update()
            return

        if yr not in year_options:
            page.overlay.append(ft.SnackBar(content=ft.Text("Select a configured Year."), bgcolor="#ff9800", open=True))
            page.update()
            return

        if migrated_from == migrated_to:
            page.overlay.append(ft.SnackBar(content=ft.Text("Migrated From and Migrated To stages must be different."), bgcolor="#ff9800", open=True))
            page.update()
            return

        calculate_migration_rate()

        payload = {
            "year": yr,
            "facility_type": facility_type,
            "migrated_from": migrated_from,
            "migrated_to": migrated_to,
            "num_migrated": parse_int(num_migrated_tf.value),
            "total_ac_stage": parse_int(total_ac_tf.value),
            "migration_rate": float(migration_rate_tf.value or 0.0)
        }
        if editing_record_id is not None:
            payload["id"] = editing_record_id

        try:
            save_stage_migration_rate(payload)
            update_all_containers()
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Stage Migration Rate for {yr} ({facility_type}, {migrated_from} to {migrated_to}) saved successfully!"), bgcolor="#00e676", open=True))
        except Exception as err:
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Error saving Migration Rate: {str(err)}"), bgcolor="red", open=True))
        page.update()

    def execute_delete(yr, facility_type, migrated_from, migrated_to):
        try:
            delete_stage_migration_rate(yr, facility_type, migrated_from, migrated_to)
            update_all_containers()
            display_facility_type = facility_type or "Unspecified"
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Stage Migration Rate for {yr} ({display_facility_type}, {migrated_from} to {migrated_to}) deleted successfully!"), bgcolor="#ff5252", open=True))
        except Exception as err:
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Error deleting: {str(err)}"), bgcolor="red", open=True))
        page.update()

    add_btn = ft.ElevatedButton(
        content=ft.Text("Save Migration Rate", color="black", weight="bold", size=14),
        on_click=on_save_click,
        style=ft.ButtonStyle(bgcolor="#78eb64", shape=ft.RoundedRectangleBorder(radius=20)),
        height=42, width=190
    )

    # Input Form Container
    input_form_card = ft.Container(
        content=ft.Column([
            ft.Container(content=ft.Text("Stage Migration Rate", size=20, weight="bold", color="#00e676"), alignment=ft.Alignment(0, 0), padding=ft.Padding(0, 0, 0, 15)),
            row1,
            ft.Container(height=5),
            row2,
            ft.Container(height=5),
            row3,
            ft.Container(height=20),
            ft.Row([add_btn], alignment="center")
        ]),
        padding=20, border=ft.Border.all(width=1, color="#00e676"), border_radius=8, bgcolor="#061d19"
    )

    render_all_tables()

    return ft.Container(
        content=ft.Column([
            input_form_card,
            history_section_container,
            upward_section_container,
            downward_section_container,
            net_section_container
        ], scroll=ft.ScrollMode.AUTO, spacing=15),
        width=820, alignment=ft.Alignment(0, -1), padding=ft.Padding(0, 0, 0, 20)
    )