import flet as ft
from datetime import date
from database import (
    save_stage_migration_rate,
    get_all_stage_migration_rates,
    delete_stage_migration_rate
)

def get_stage_migration_form(page: ft.Page):
    raw_cache = get_all_stage_migration_rates() or []
    editing_record_id = None
    today = date.today()
    latest_completed_year = today.year
    latest_completed_month = today.month - 1
    if latest_completed_month == 0:
        latest_completed_year -= 1
        latest_completed_month = 12
    default_year = str(latest_completed_year)
    month_names = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    previous_month_value = f"{latest_completed_month:02d}"
    
    migrated_options = ["Stage-1", "Stage-2", "Stage-3"]
    migrated_to_options = ["Stage-1", "Stage-2", "Stage-3"]

    # Form input fields
    year_dd = ft.Dropdown(
        label="Year",
        options=[ft.dropdown.Option(str(year)) for year in range(2020, today.year + 1)],
        value=default_year,
        height=45,
        content_padding=ft.Padding(12, 10, 12, 10),
        border_color="#00e676",
        focused_border_color="#00e676",
        label_style=ft.TextStyle(color="white70", size=14),
        text_style=ft.TextStyle(color="white", size=13),
        expand=True
    )

    month_dd = ft.Dropdown(
        label="Month",
        options=[
            ft.dropdown.Option(key=f"{month:02d}", text=name)
            for month, name in enumerate(month_names, start=1)
        ],
        value=previous_month_value,
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
        ft.Container(content=month_dd, expand=1),
        ft.Container(content=migrated_from_dd, expand=1),
    ], spacing=15)

    row2 = ft.Row([
        ft.Container(content=migrated_to_dd, expand=1),
        ft.Container(content=num_migrated_tf, expand=1),
        ft.Container(content=total_ac_tf, expand=1)
    ], spacing=15)

    row3 = ft.Row([
        ft.Container(content=migration_rate_tf, expand=1),
        ft.Container(expand=1),
        ft.Container(expand=1)
    ], spacing=15)

    def clear_form_fields():
        nonlocal editing_record_id
        editing_record_id = None
        year_dd.value = default_year
        month_dd.value = previous_month_value
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
        stored_month = str(data_item.get("month") or "").strip()
        if stored_month.isdigit() and 1 <= int(stored_month) <= 12:
            month_dd.value = f"{int(stored_month):02d}"
        else:
            month_dd.value = None
        migrated_from_dd.value = str(data_item.get("migrated_from", ""))
        migrated_to_dd.value = str(data_item.get("migrated_to", ""))
        num_migrated_tf.value = str(data_item.get("num_migrated", 0))
        total_ac_tf.value = str(data_item.get("total_ac_stage", 0))
        calculate_migration_rate()

    # Search fields (Search Year, Migrated from)
    search_year_tf = ft.TextField(
        hint_text="YYYY",
        hint_style=ft.TextStyle(color="white38", size=13),
        width=100,
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
        width=150,
        height=40,
        content_padding=ft.Padding(10, 0, 10, 0),
        border_color="#00e676",
        focused_border_color="#00e676",
        text_style=ft.TextStyle(color="white", size=13),
        value="All"
    )

    history_table_holder = ft.Container(expand=True)
    summary_table_holder = ft.Container(expand=True)

    def get_table_control(yr_search="", stage_search="All"):
        filtered = list(raw_cache)

        if yr_search.strip():
            filtered = [r for r in filtered if yr_search.strip().lower() in str(r.get("year", "")).lower()]

        if stage_search and stage_search != "All":
            filtered = [r for r in filtered if str(r.get("migrated_from", "")).lower() == stage_search.lower()]

        filtered = filtered[:10]

        if not filtered:
            return ft.Container(content=ft.Text("No records found.", color="white54", italic=True, size=13), padding=15)

        rows = []
        for item in filtered:
            yr = str(item.get("year", ""))
            month = str(item.get("month", ""))
            stage = str(item.get("migrated_from", ""))
            migrated_to = str(item.get("migrated_to", ""))

            action_cell = ft.Row([
                ft.IconButton(icon=ft.Icons.EDIT, icon_color="#00e676", icon_size=18, tooltip="Edit", on_click=lambda e, d=item: populate_fields(d)),
                ft.IconButton(icon=ft.Icons.DELETE, icon_color="#ff5252", icon_size=18, tooltip="Delete", on_click=lambda e, y=yr, m=month, s=stage, t=migrated_to: execute_delete(y, m, s, t))
            ], spacing=0, alignment="center")

            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(yr, weight="bold", color="#00e676", size=11)),
                ft.DataCell(ft.Text(month, color="white", size=11)),
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
                ft.DataColumn(ft.Text("Month", color="white", weight="bold", size=11)),
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
            column_spacing=25
        )

    # Average of Migration Rate on each change/type of 'Migrated from'
    def get_summary_table_control():
        if not raw_cache:
            return ft.Container(content=ft.Text("No summary data available.", color="white54", italic=True, size=13), padding=15)

        grouped = {}
        for item in raw_cache:
            migrated_from = str(item.get("migrated_from", "")).strip()
            migrated_to = str(item.get("migrated_to", "")).strip()
            if not migrated_from:
                continue
            transition = (migrated_from, migrated_to)
            if transition not in grouped:
                grouped[transition] = {"count": 0, "sum_rate": 0.0}
            grouped[transition]["count"] += 1
            grouped[transition]["sum_rate"] += float(item.get("migration_rate", 0))

        rows = []
        for migrated_from, migrated_to in sorted(grouped.keys()):
            count = grouped[(migrated_from, migrated_to)]["count"]
            avg_rate = grouped[(migrated_from, migrated_to)]["sum_rate"] / count if count > 0 else 0.0

            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(migrated_from, weight="bold", color="#00e676", size=11)),
                ft.DataCell(ft.Text(migrated_to, color="white", size=11)),
                ft.DataCell(ft.Text(str(count), color="white", size=11)),
                ft.DataCell(ft.Text(f"{avg_rate:.4f}", color="white", weight="bold", size=11)),
            ]))

        return ft.DataTable(
            width=780,
            columns=[
                ft.DataColumn(ft.Text("Migrated From", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Migrated To", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Total Records", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Average Migration Rate", color="white", weight="bold", size=11)),
            ],
            rows=rows,
            border=ft.Border.all(0.5, "#1e534b"),
            heading_row_color="#0c3832",
            heading_row_height=36,
            data_row_min_height=34,
            column_spacing=60
        )

    def render_all_tables():
        history_table_holder.content = get_table_control(search_year_tf.value or "", search_migrated_dd.value or "All")
        summary_table_holder.content = get_summary_table_control()

    def update_search_filter(e):
        history_table_holder.content = get_table_control(
            search_year_tf.value or "",
            search_migrated_dd.value or "All"
        )
        history_table_holder.update()

    search_year_tf.on_change = update_search_filter
    search_migrated_dd.on_select = update_search_filter

    search_header_row = ft.Row([
        ft.Text("Search Year:", size=14, weight="bold", color="#00e676"),
        search_year_tf,
        ft.Container(width=10),
        ft.Text("Migrated From:", size=14, weight="bold", color="#00e676"),
        search_migrated_dd
    ], vertical_alignment="center", spacing=10)

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

    # Average Summary Table grouped by Migrated From Stage
    summary_section_container = ft.Container(
        content=ft.Column([
            ft.Text("Stage Migration Rate / Role Rate", size=16, weight="bold", color="#00e676"),
            ft.Container(height=8),
            ft.Row([summary_table_holder], scroll=ft.ScrollMode.AUTO, expand=True)
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
        month_value = month_dd.value or ""
        month_num = parse_int(month_value)
        migrated_from = migrated_from_dd.value or ""
        migrated_to = migrated_to_dd.value or ""

        if not yr or not month_value or not migrated_from or not migrated_to:
            page.overlay.append(ft.SnackBar(content=ft.Text("Please select Year and Month, and select Migrated From and Migrated To stages!"), bgcolor="#ff9800", open=True))
            page.update()
            return

        if int(yr) > today.year:
            page.overlay.append(ft.SnackBar(content=ft.Text("Year cannot be greater than the current year."), bgcolor="#ff9800", open=True))
            page.update()
            return

        if migrated_from == migrated_to:
            page.overlay.append(ft.SnackBar(content=ft.Text("Migrated From and Migrated To stages must be different."), bgcolor="#ff9800", open=True))
            page.update()
            return

        if month_num < 1 or month_num > 12:
            page.overlay.append(ft.SnackBar(content=ft.Text("Please select a valid Month."), bgcolor="#ff9800", open=True))
            page.update()
            return

        if (int(yr), month_num) > (latest_completed_year, latest_completed_month):
            latest_month = month_names[latest_completed_month - 1]
            page.overlay.append(ft.SnackBar(
                content=ft.Text(f"Year and Month cannot be later than {latest_month} {latest_completed_year}."),
                bgcolor="#ff9800",
                open=True
            ))
            page.update()
            return

        calculate_migration_rate()

        payload = {
            "year": yr,
            "month": f"{month_num:02d}",
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
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Stage Migration Rate / Role Rate for {yr}-{month_num:02d} ({migrated_from} to {migrated_to}) saved successfully!"), bgcolor="#00e676", open=True))
        except Exception as err:
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Error saving Migration Rate: {str(err)}"), bgcolor="red", open=True))
        page.update()

    def execute_delete(yr, month, migrated_from, migrated_to):
        try:
            delete_stage_migration_rate(yr, month, migrated_from, migrated_to)
            update_all_containers()
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Stage Migration Rate / Role Rate for {yr}-{month} ({migrated_from} to {migrated_to}) deleted successfully!"), bgcolor="#ff5252", open=True))
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
            ft.Container(content=ft.Text("Stage Migration Rate / Role Rate", size=20, weight="bold", color="#00e676"), alignment=ft.Alignment(0, 0), padding=ft.Padding(0, 0, 0, 15)),
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
            summary_section_container
        ], scroll=ft.ScrollMode.AUTO, spacing=15),
        width=820, alignment=ft.Alignment(0, -1), padding=ft.Padding(0, 0, 0, 20)
    )