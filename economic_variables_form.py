import flet as ft
from datetime import date
from database import (
    save_economic_variables, 
    get_all_economic_variables, 
    delete_economic_variables_by_year
)

def get_economic_variables_form(page: ft.Page):
    field_labels = [
        "Year",
        "Exchange Rate",
        "Inflation",
        "GDP Growth",
        "Un Employment Rate",
        "Deposit Rate",
        "Loan Rate",
        "Bank Rate",
        "Call Money Rate"
    ]

    input_fields = {}

    raw_cache = get_all_economic_variables() or {}
    full_db_cache = {str(k).strip(): v for k, v in raw_cache.items()}
    current_year = str(date.today().year)

    # ৩ কলাম ইনপুট গ্রীড
    grid_rows = []
    for i in range(0, len(field_labels), 3):
        row_controls = []
        for j in range(3):
            if i + j < len(field_labels):
                label_name = field_labels[i + j]
                if label_name == "Year":
                    tf = ft.Dropdown(
                        label=label_name,
                        options=[ft.dropdown.Option(str(year)) for year in range(2020, int(current_year) + 1)],
                        value=current_year,
                        height=45,
                        content_padding=ft.Padding(12, 10, 12, 10),
                        border_color="#00e676",
                        focused_border_color="#00e676",
                        label_style=ft.TextStyle(color="white70", size=15),
                        text_style=ft.TextStyle(color="white", size=13),
                        expand=True
                    )
                else:
                    tf = ft.TextField(
                        label=label_name,
                        hint_text="0.00",
                        height=45,
                        content_padding=ft.Padding(12, 10, 12, 10),
                        border_color="#00e676",
                        focused_border_color="#00e676",
                        label_style=ft.TextStyle(color="white70", size=15),
                        text_style=ft.TextStyle(color="white", size=13),
                        keyboard_type=ft.KeyboardType.NUMBER
                    )
                input_fields[label_name] = tf
                row_controls.append(ft.Container(content=tf, expand=True))
            else:
                row_controls.append(ft.Container(expand=True))

        grid_rows.append(ft.Row(controls=row_controls, spacing=15))

    grid_column = ft.Column(controls=grid_rows, spacing=15)

    def populate_fields(selected_year):
        search_key = str(selected_year).strip()
        year_data = full_db_cache.get(search_key, {})
        
        if "Year" in input_fields:
            input_fields["Year"].value = search_key

        for var_name, tf_control in input_fields.items():
            if var_name != "Year":
                raw_value = year_data.get(var_name, "")
                tf_control.value = str(raw_value) if raw_value is not None else ""
            
        page.update()

    def clear_form_fields():
        for label_name, tf in input_fields.items():
            tf.value = current_year if label_name == "Year" else ""
        page.update()

    # সার্চ ফিল্ড (চ্যাপ্টা হওয়া রোধ করতে নির্দিষ্ট height সহ ক্লিন আউটলাইন)
    grid_search_tf = ft.TextField(
        hint_text="YYYY",
        hint_style=ft.TextStyle(color="white38", size=13),
        width=110,
        height=40,
        content_padding=ft.Padding(12, 8, 12, 8),
        border_color="#00e676",
        focused_border_color="#00e676",
        text_style=ft.TextStyle(color="white", size=13, weight="bold"),
        keyboard_type=ft.KeyboardType.NUMBER
    )

    history_table_holder = ft.Container(expand=True)

    def get_table_control(search_query=""):
        sorted_years = sorted(full_db_cache.keys(), key=lambda x: str(x), reverse=True)

        if search_query.strip():
            sorted_years = [y for y in sorted_years if search_query.strip().lower() in y.lower()]

        # সর্বোচ্চ ৫টি সারি লিমিট
        sorted_years = sorted_years[:10]

        if not sorted_years:
            return ft.Container(
                content=ft.Text("No records found.", color="white54", italic=True, size=13),
                padding=15
            )

        rows = []
        for yr in sorted_years:
            yr_data = full_db_cache[yr]
            
            def make_edit_handler(year_val):
                return lambda e: populate_fields(year_val)

            def make_delete_handler(year_val):
                return lambda e: execute_delete(year_val)

            edit_btn = ft.IconButton(
                icon=ft.Icons.EDIT,
                icon_color="#00e676",
                icon_size=18,
                tooltip="Edit",
                on_click=make_edit_handler(yr)
            )

            del_btn = ft.IconButton(
                icon=ft.Icons.DELETE,
                icon_color="#ff5252",
                icon_size=18,
                tooltip="Delete",
                on_click=make_delete_handler(yr)
            )

            action_cell = ft.Row([edit_btn, del_btn], spacing=0, alignment="center")

            data_cells = [
                ft.DataCell(ft.Text(yr, weight="bold", color="#00e676", size=11)),
                ft.DataCell(ft.Text(str(yr_data.get("Exchange Rate", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(yr_data.get("Inflation", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(yr_data.get("GDP Growth", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(yr_data.get("Un Employment Rate", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(yr_data.get("Deposit Rate", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(yr_data.get("Loan Rate", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(yr_data.get("Bank Rate", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(yr_data.get("Call Money Rate", "")), color="white", size=11)),
                ft.DataCell(action_cell)
            ]

            rows.append(ft.DataRow(cells=data_cells))

        return ft.DataTable(
            width=760,
            columns=[
                ft.DataColumn(ft.Text("Year", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Exchange", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Inflation", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("GDP", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Unemp.", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Deposit", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Loan", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Bank", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Call Money", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Actions", color="white", weight="bold", size=11)),
            ],
            rows=rows,
            border=ft.Border.all(0.5, "#1e534b"),
            heading_row_color="#0c3832",
            heading_row_height=36,
            data_row_min_height=34,
            column_spacing=12
        )

    def render_history_table(search_query=""):
        history_table_holder.content = get_table_control(search_query)

    # সার্চ হ্যান্ডলার: সর্বোচ্চ ৪ ডিজিট নিশ্চিতকরণ + টেবিল রিফ্রেশ
    def on_grid_search_change(e):
        val = grid_search_tf.value or ""
        if len(val) > 4:
            grid_search_tf.value = val[:4]
            grid_search_tf.update()
        render_history_table(grid_search_tf.value)
        history_table_holder.update()

    grid_search_tf.on_change = on_grid_search_change

    search_header_row = ft.Row([
        ft.Text("Search by Year :", size=15, weight="bold", color="#00e676"),
        grid_search_tf
    ], vertical_alignment="center", spacing=12)

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

    def refresh_cache():
        nonlocal full_db_cache
        fetched = get_all_economic_variables() or {}
        full_db_cache = {str(k).strip(): v for k, v in fetched.items()}

    def on_save_click(e):
        selected_year = input_fields["Year"].value.strip() if input_fields["Year"].value else ""
        if not selected_year:
            page.overlay.append(ft.SnackBar(
                content=ft.Text("Please enter a valid Year first!"),
                bgcolor="#ff9800", open=True
            ))
            page.update()
            return

        if selected_year.isdigit() and int(selected_year) > int(current_year):
            page.overlay.append(ft.SnackBar(
                content=ft.Text("Year cannot be greater than the current year."),
                bgcolor="#ff9800", open=True
            ))
            page.update()
            return

        data_to_save = {
            var: tf.value.strip() if tf.value else "" 
            for var, tf in input_fields.items() 
            if var != "Year"
        }
        
        try:
            save_economic_variables(selected_year, data_to_save)
            refresh_cache()
            clear_form_fields()
            render_history_table(grid_search_tf.value or "")

            page.overlay.append(ft.SnackBar(
                content=ft.Text(f"Data for year {selected_year} saved successfully!"),
                bgcolor="#00e676", open=True
            ))
        except Exception as err:
            page.overlay.append(ft.SnackBar(
                content=ft.Text(f"Error saving data: {str(err)}"),
                bgcolor="red", open=True
            ))
        page.update()

    def execute_delete(selected_year):
        if not selected_year:
            return
        try:
            delete_economic_variables_by_year(selected_year)
            refresh_cache()
            clear_form_fields()
            render_history_table(grid_search_tf.value or "")

            page.overlay.append(ft.SnackBar(
                content=ft.Text(f"Data for year {selected_year} deleted successfully!"),
                bgcolor="#ff5252", open=True
            ))
        except Exception as err:
            page.overlay.append(ft.SnackBar(
                content=ft.Text(f"Error deleting data: {str(err)}"),
                bgcolor="red", open=True
            ))
        page.update()

    add_btn = ft.ElevatedButton(
        content=ft.Text("Add / Edit EV", color="black", weight="bold", size=14),
        on_click=on_save_click,
        style=ft.ButtonStyle(
            bgcolor="#78eb64", 
            shape=ft.RoundedRectangleBorder(radius=20)
        ),
        height=42,
        width=170
    )

    input_form_card = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text("Economic Variables", size=20, weight="bold", color="#00e676"),
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding(0, 0, 0, 15)
            ),
            grid_column,
            ft.Container(height=20),
            ft.Row([add_btn], alignment="center")
        ]),
        padding=20,
        border=ft.Border.all(width=1, color="#00e676"),
        border_radius=8,
        bgcolor="#061d19"
    )

    main_layout = ft.Column(
        controls=[
            input_form_card,
            history_section_container
        ],
        scroll=ft.ScrollMode.AUTO,
        spacing=15
    )

    render_history_table()

    return ft.Container(
        content=main_layout,
        width=820,
        alignment=ft.Alignment(0, -1),
        padding=ft.Padding(0, 0, 0, 20)
    )