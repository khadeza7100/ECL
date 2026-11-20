import flet as ft
from datetime import date
from components.custom_datepicker import CustomDatePicker
from database import (
    save_credit_ratings_profile,
    get_all_credit_ratings_profiles,
    delete_credit_ratings_profile_by_id,
    get_customer_name_by_number,
    is_customer_exists_in_table
)

def get_credit_ratings_form(page: ft.Page):
    input_fields = {}
    
    # 1. Base input field style
    base_field_style = {
        "height": 45,
        "content_padding": ft.Padding(12, 10, 12, 10),
        "border_color": "#00e676",
        "focused_border_color": "#00e676",
        "border_radius": 6,
        "label_style": ft.TextStyle(color="white70", size=14),
        "text_style": ft.TextStyle(color="white", size=13),
        "expand": True
    }

    raw_cache = get_all_credit_ratings_profiles() or {}
    full_db_cache = {str(k).strip(): v for k, v in raw_cache.items()}

    # 2. Options Definitions
    current_year = str(date.today().year)
    year_options = [str(y) for y in range(2020, int(current_year) + 1)]
    rating_options = ["Excellent", "Good", "Marginal", "Unacceptable"]
    credit_rating_datepicker = CustomDatePicker(
        page, "Credit Rating Date", width=None, height=45
    )
    credit_rating_datepicker.input_field.content_padding = ft.Padding(12, 10, 12, 10)
    credit_rating_datepicker.input_field.border_color = "#00e676"
    credit_rating_datepicker.input_field.focused_border_color = "#00e676"
    credit_rating_datepicker.input_field.border_radius = 6
    credit_rating_datepicker.input_field.label_style = ft.TextStyle(color="white70", size=14)
    credit_rating_datepicker.input_field.text_style = ft.TextStyle(color="white", size=13)
    credit_rating_datepicker.input_field.expand = True
    credit_rating_expiry_datepicker = CustomDatePicker(
        page, "Credit Rating Expiry Date", width=None, height=45
    )
    credit_rating_expiry_datepicker.input_field.content_padding = ft.Padding(12, 10, 12, 10)
    credit_rating_expiry_datepicker.input_field.border_color = "#00e676"
    credit_rating_expiry_datepicker.input_field.focused_border_color = "#00e676"
    credit_rating_expiry_datepicker.input_field.border_radius = 6
    credit_rating_expiry_datepicker.input_field.label_style = ft.TextStyle(color="white70", size=14)
    credit_rating_expiry_datepicker.input_field.text_style = ft.TextStyle(color="white", size=13)
    credit_rating_expiry_datepicker.input_field.expand = True

    dropdown_options = {
        "Year of Financials": year_options,
        "ICRRS Rating": rating_options,
        "ICRRS Rating Year": year_options,
        "Credit Rating Company": ["Alpha Rating", "CRAB", "CRISL", "Mega"],
        "Credit Scoring": rating_options,
        "Credit Scoring Year": year_options
    }

    numeric_fields = [
        "Current Ratio", "Net Profit Margin %", "Interest Coverage Ratio",
        "Debt Service Coverage Ratio", "Debt Equity Ratio", "Financial Debt to Tangible NW"
    ]

    # Auto-fill Customer Name handler
    def on_customer_number_change(e):
        cust_num = (input_fields["Customer Number"].value or "").strip()
        if cust_num:
            name = get_customer_name_by_number(cust_num)
            input_fields["Customer Name"].value = name if name else ""
        else:
            input_fields["Customer Name"].value = ""
        
        page.update()

    # 3. Input Field Names
    all_field_names = [
        "Customer Number", "Customer Name", "Year of Financials",
        "Current Ratio", "Net Profit Margin %", "Interest Coverage Ratio",
        "Debt Service Coverage Ratio", "Debt Equity Ratio", "Financial Debt to Tangible NW",
        "ICRRS Rating", "ICRRS Rating Year", "Credit Rating Company", "Credit Rating (Short Term)",
        "Credit Rating (Long Term)", "Credit Rating Date", "Credit Rating Expiry Date", "Credit Scoring",
        "Credit Scoring Year"
    ]

    for label_name in all_field_names:
        if label_name in dropdown_options:
            tf = ft.Dropdown(
                label=label_name,
                options=[ft.dropdown.Option(opt) for opt in dropdown_options[label_name]],
                value=current_year if "Year" in label_name else None,
                **base_field_style
            )
        elif label_name == "Credit Rating Date":
            tf = credit_rating_datepicker.input_field
        elif label_name == "Credit Rating Expiry Date":
            tf = credit_rating_expiry_datepicker.input_field
        else:
            is_num = label_name in numeric_fields
            tf = ft.TextField(
                label=label_name,
                keyboard_type=ft.KeyboardType.NUMBER if is_num else ft.KeyboardType.TEXT,
                on_change=on_customer_number_change if label_name == "Customer Number" else None,
                **base_field_style
            )
        input_fields[label_name] = tf

    # 4. Build 3-Column Uniform Grid Layout
    grid_rows = []
    for i in range(0, len(all_field_names), 3):
        row_controls = []
        for j in range(3):
            if i + j < len(all_field_names):
                f_name = all_field_names[i + j]
                row_controls.append(ft.Container(content=input_fields[f_name], expand=1))
            else:
                row_controls.append(ft.Container(expand=1))
        grid_rows.append(ft.Row(controls=row_controls, spacing=15))

    grid_column = ft.Column(controls=grid_rows, spacing=15)

    def populate_fields(cust_num):
        search_key = str(cust_num).strip()
        data = full_db_cache.get(search_key, {})
        if not data: return

        input_fields["Customer Number"].value = search_key
        input_fields["Customer Name"].value = str(data.get("customer_name") or "")
        input_fields["Year of Financials"].value = str(data.get("year_financials") or "")
        input_fields["Current Ratio"].value = str(data.get("current_ratio") or "0.00")
        input_fields["Net Profit Margin %"].value = str(data.get("net_profit_margin") or "0.00")
        input_fields["Interest Coverage Ratio"].value = str(data.get("icr") or "0.00")
        input_fields["Debt Service Coverage Ratio"].value = str(data.get("dscr") or "0.00")
        input_fields["Debt Equity Ratio"].value = str(data.get("debt_equity") or "0.00")
        input_fields["Financial Debt to Tangible NW"].value = str(data.get("fin_debt_nw") or "0.00")
        input_fields["ICRRS Rating"].value = str(data.get("icrrs_rating") or "")
        input_fields["ICRRS Rating Year"].value = str(data.get("icrrs_year") or "")
        input_fields["Credit Rating Company"].value = str(data.get("rating_company") or "")
        input_fields["Credit Rating (Short Term)"].value = str(data.get("short_term_rating") or "")
        input_fields["Credit Rating (Long Term)"].value = str(data.get("long_term_rating") or "")
        rating_date = str(data.get("rating_year") or "")
        if len(rating_date) == 4 and rating_date.isdigit():
            credit_rating_datepicker.input_field.value = rating_date
        else:
            credit_rating_datepicker.set_date_from_string(rating_date)
        credit_rating_expiry_datepicker.set_date_from_string(
            str(data.get("rating_expiry_date") or "")
        )
        input_fields["Credit Scoring"].value = str(data.get("scoring") or "")
        input_fields["Credit Scoring Year"].value = str(data.get("scoring_year") or "")

        page.update()

    def clear_form_fields():
        for label_name, tf in input_fields.items():
            tf.value = current_year if "Year" in label_name else ""
        credit_rating_datepicker.clear()
        credit_rating_expiry_datepicker.clear()
        page.update()

    # Search Bar
    grid_search_tf = ft.TextField(
        hint_text="Cust No.", hint_style=ft.TextStyle(color="white38", size=13),
        width=130, height=40, content_padding=ft.Padding(12, 8, 12, 8),
        border_color="#00e676", focused_border_color="#00e676", border_radius=6,
        text_style=ft.TextStyle(color="white", size=13, weight="bold")
    )

    history_table_holder = ft.Container(expand=True)

    def get_table_control(search_query=""):
        sorted_keys = sorted(full_db_cache.keys(), reverse=True)
        if search_query.strip():
            sorted_keys = [k for k in sorted_keys if search_query.strip().lower() in k.lower()]
        sorted_keys = sorted_keys[:5]

        if not sorted_keys:
            return ft.Container(content=ft.Text("No records found.", color="white54", italic=True, size=13), padding=15)

        rows = []
        for key in sorted_keys:
            c_data = full_db_cache[key]

            edit_btn = ft.IconButton(
                icon=ft.Icons.EDIT, icon_color="#00e676", icon_size=18, tooltip="Edit",
                on_click=lambda e, k=key: populate_fields(k)
            )
            del_btn = ft.IconButton(
                icon=ft.Icons.DELETE, icon_color="#ff5252", icon_size=18, tooltip="Delete",
                on_click=lambda e, k=key: execute_delete(k)
            )

            action_cell = ft.Row([edit_btn, del_btn], spacing=0, alignment="center")

            data_cells = [
                ft.DataCell(ft.Text(key, weight="bold", color="#00e676", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("customer_name", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("year_financials", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("current_ratio", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("icrrs_rating", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("scoring", "")), color="white", size=11)),
                ft.DataCell(action_cell)
            ]
            rows.append(ft.DataRow(cells=data_cells))

        return ft.DataTable(
            width=800,
            columns=[
                ft.DataColumn(ft.Text("Cust No", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Name", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Fin Year", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Curr Ratio", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("ICRRS", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Scoring", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Actions", color="white", weight="bold", size=11)),
            ],
            rows=rows, border=ft.Border.all(0.5, "#1e534b"),
            heading_row_color="#0c3832", heading_row_height=36, data_row_min_height=34, column_spacing=12
        )

    def render_history_table(search_query=""):
        history_table_holder.content = get_table_control(search_query)

    grid_search_tf.on_change = lambda e: (render_history_table(grid_search_tf.value or ""), history_table_holder.update())

    search_header_row = ft.Row([
        ft.Text("Search by Cust No :", size=15, weight="bold", color="#00e676"),
        grid_search_tf
    ], vertical_alignment="center", spacing=12)

    history_section_container = ft.Container(
        content=ft.Column([
            search_header_row,
            ft.Container(height=10),
            ft.Row([history_table_holder], scroll=ft.ScrollMode.AUTO, expand=True)
        ], horizontal_alignment="stretch"),
        padding=15, border=ft.Border.all(width=1, color="#00e676"), border_radius=8, bgcolor="#061d19"
    )

    def refresh_cache():
        nonlocal full_db_cache
        fetched = get_all_credit_ratings_profiles() or {}
        full_db_cache = {str(k).strip(): v for k, v in fetched.items()}

    def parse_flt(val):
        try:
            return float(val) if val else 0.00
        except ValueError:
            return 0.00

    def on_save_click(e):
        cust_num = input_fields["Customer Number"].value.strip() if input_fields["Customer Number"].value else ""
        if not cust_num:
            page.overlay.append(ft.SnackBar(ft.Text("Please enter a valid Customer Number first!"), bgcolor="#ff9800", open=True))
            page.update()
            return

        future_year_fields = [
            label_name
            for label_name in ("Year of Financials", "ICRRS Rating Year", "Credit Scoring Year")
            if input_fields[label_name].value
            and input_fields[label_name].value.isdigit()
            and int(input_fields[label_name].value) > int(current_year)
        ]
        if future_year_fields:
            page.overlay.append(ft.SnackBar(ft.Text("Year cannot be greater than the current year."), bgcolor="#ff9800", open=True))
            page.update()
            return

        # Check existence in Corporate or Individual profile tables
        exists_corp = is_customer_exists_in_table(cust_num, "corporate_profiles")
        exists_ind = is_customer_exists_in_table(cust_num, "individual_profiles")

        if not (exists_corp or exists_ind):
            page.overlay.append(ft.SnackBar(
                ft.Text(f"Customer Number '{cust_num}' does not exist in Corporate or Individual profiles!"),
                bgcolor="#ff9800", open=True
            ))
            page.update()
            return

        payload = {
            "customer_number": cust_num,
            "customer_name": input_fields["Customer Name"].value.strip() if input_fields["Customer Name"].value else "",
            "year_financials": input_fields["Year of Financials"].value or "",
            "current_ratio": parse_flt(input_fields["Current Ratio"].value),
            "net_profit_margin": parse_flt(input_fields["Net Profit Margin %"].value),
            "icr": parse_flt(input_fields["Interest Coverage Ratio"].value),
            "dscr": parse_flt(input_fields["Debt Service Coverage Ratio"].value),
            "debt_equity": parse_flt(input_fields["Debt Equity Ratio"].value),
            "fin_debt_nw": parse_flt(input_fields["Financial Debt to Tangible NW"].value),
            "icrrs_rating": input_fields["ICRRS Rating"].value or "",
            "icrrs_year": input_fields["ICRRS Rating Year"].value or "",
            "rating_company": input_fields["Credit Rating Company"].value or "",
            "short_term_rating": input_fields["Credit Rating (Short Term)"].value.strip() if input_fields["Credit Rating (Short Term)"].value else "",
            "long_term_rating": input_fields["Credit Rating (Long Term)"].value.strip() if input_fields["Credit Rating (Long Term)"].value else "",
            "rating_year": input_fields["Credit Rating Date"].value or "",
            "rating_expiry_date": input_fields["Credit Rating Expiry Date"].value or "",
            "scoring": input_fields["Credit Scoring"].value or "",
            "scoring_year": input_fields["Credit Scoring Year"].value or ""
        }

        try:
            save_credit_ratings_profile(payload)
            refresh_cache()
            clear_form_fields()
            render_history_table(grid_search_tf.value or "")
            page.overlay.append(ft.SnackBar(ft.Text(f"Credit Ratings for {cust_num} saved successfully!"), bgcolor="#00e676", open=True))
        except Exception as err:
            page.overlay.append(ft.SnackBar(ft.Text(f"Error saving ratings: {str(err)}"), bgcolor="red", open=True))
        page.update()

    def execute_delete(cust_num):
        if not cust_num: return
        try:
            delete_credit_ratings_profile_by_id(cust_num)
            refresh_cache()
            clear_form_fields()
            render_history_table(grid_search_tf.value or "")
            page.overlay.append(ft.SnackBar(ft.Text(f"Credit Ratings for {cust_num} deleted successfully!"), bgcolor="#ff5252", open=True))
        except Exception as err:
            page.overlay.append(ft.SnackBar(ft.Text(f"Error deleting record: {str(err)}"), bgcolor="red", open=True))
        page.update()

    add_btn = ft.ElevatedButton(
        content=ft.Text("Save Credit Ratings", color="black", weight="bold", size=14),
        on_click=on_save_click,
        style=ft.ButtonStyle(bgcolor="#78eb64", shape=ft.RoundedRectangleBorder(radius=20)),
        height=42, width=210
    )

    input_form_card = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text("Credit Ratings & Ratios Entry", size=20, weight="bold", color="#00e676"),
                alignment=ft.Alignment(0, 0), padding=ft.Padding(0, 0, 0, 15)
            ),
            grid_column,
            ft.Container(height=20),
            ft.Row([add_btn], alignment="center")
        ]),
        padding=20, border=ft.Border.all(width=1, color="#00e676"), border_radius=8, bgcolor="#061d19"
    )

    main_layout = ft.Column(
        controls=[input_form_card, history_section_container],
        scroll=ft.ScrollMode.AUTO, spacing=15
    )

    render_history_table()

    return ft.Container(
        content=main_layout, width=820, alignment=ft.Alignment(0, -1), padding=ft.Padding(0, 0, 0, 20)
    )