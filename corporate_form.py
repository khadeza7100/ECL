import flet as ft
from database import (
    save_corporate_profile,
    get_all_corporate_profiles,
    delete_corporate_profile_by_id,
    is_customer_exists_in_table,
    get_customer_name_by_number
)
from components.dropdown_configuration import get_configured_dropdown_options

def get_corporate_profile_form(page: ft.Page):
    input_fields = {}
    
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

    raw_cache = get_all_corporate_profiles() or {}
    full_db_cache = {str(k).strip(): v for k, v in raw_cache.items()}

    dropdown_options = {
        "Legal Entity Type": get_configured_dropdown_options("corporate.legal_entity_type"),
        "Business Type": get_configured_dropdown_options("corporate.business_type"),
        "Size of Business": get_configured_dropdown_options("corporate.size_of_business"),
        "Location District": get_configured_dropdown_options("corporate.location_district"),
        "Default History": get_configured_dropdown_options("corporate.default_history"),
        "Repayment Behavior": get_configured_dropdown_options("corporate.repayment_behavior"),
        "Latest CIB Status": get_configured_dropdown_options("corporate.cib_status"),
        "Major Audit Objections": get_configured_dropdown_options("corporate.audit_objections"),
    }

    numeric_fields = ["Fixed Asset Value", "Business Turnover", "Manpower Count"]

    def update_corporate_category(e=None):
        bsize = input_fields["Size of Business"].value or ""
        btype = input_fields["Business Type"].value or ""
        if bsize or btype:
            input_fields["Category [Type & Size]"].value = f"{bsize} {btype}".strip()
        else:
            input_fields["Category [Type & Size]"].value = ""
        page.update()

    def on_customer_number_change(e):
        cust_num = (input_fields["Customer Number"].value or "").strip()
        if cust_num:
            name = get_customer_name_by_number(cust_num)
            input_fields["Customer Name"].value = name if name else ""
        else:
            input_fields["Customer Name"].value = ""
        
        page.update()
        
    all_field_names = [
        "Customer Number", "Customer Name", "Legal Entity Type",
        "Business Type", "Fixed Asset Value", "Manpower Count",
        "Business Turnover", "Size of Business", "Category [Type & Size]",
        "Business Sector", "Product / Service Name", "Location District",
        "Default History", "Repayment Behavior", "Latest CIB Status",
        "Major Audit Objections"
    ]

    for label_name in all_field_names:
        if label_name in dropdown_options:
            tf = ft.Dropdown(
                label=label_name,
                options=[ft.dropdown.Option(opt) for opt in dropdown_options[label_name]],
                **base_field_style
            )
            if label_name in ["Business Type", "Size of Business"]:
                tf.on_select = update_corporate_category
        elif label_name == "Category [Type & Size]":
            tf = ft.TextField(
                label=label_name,
                read_only=True,
                value="",
                **base_field_style
            )
        else:
            is_num = label_name in numeric_fields or label_name == "Customer Number"
            on_chg = on_customer_number_change if label_name == "Customer Number" else None

            tf = ft.TextField(
                label=label_name,
                keyboard_type=ft.KeyboardType.NUMBER if is_num else ft.KeyboardType.TEXT,
                on_change=on_chg,
                **base_field_style
            )
        input_fields[label_name] = tf

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
        if not data:
            return

        input_fields["Customer Number"].value = search_key
        input_fields["Customer Name"].value = str(data.get("customer_name") or "")
        input_fields["Legal Entity Type"].value = str(data.get("legal_entity") or "")
        input_fields["Business Type"].value = str(data.get("business_type") or "")
        input_fields["Fixed Asset Value"].value = str(data.get("fixed_asset") or "0.00")
        input_fields["Manpower Count"].value = str(data.get("manpower_count") or "0")
        input_fields["Business Turnover"].value = str(data.get("business_turnover") or "0.00")
        input_fields["Size of Business"].value = str(data.get("business_size") or "")
        input_fields["Category [Type & Size]"].value = str(data.get("category") or "")
        input_fields["Business Sector"].value = str(data.get("business_sector") or "")
        input_fields["Product / Service Name"].value = str(data.get("product_service_name") or "")
        input_fields["Location District"].value = str(data.get("location_district") or "")
        input_fields["Default History"].value = str(data.get("default_history") or "")
        input_fields["Repayment Behavior"].value = str(data.get("repayment_behavior") or "")
        input_fields["Latest CIB Status"].value = str(data.get("cib_status") or "")
        input_fields["Major Audit Objections"].value = str(data.get("audit_objection") or "")

        page.update()

    def clear_form_fields():
        for k, tf in input_fields.items():
            if k == "Category [Type & Size]":
                tf.value = ""
            else:
                tf.value = ""
        page.update()

    grid_search_tf = ft.TextField(
        hint_text="Cust No.",
        hint_style=ft.TextStyle(color="white38", size=13),
        width=130,
        height=40,
        content_padding=ft.Padding(12, 8, 12, 8),
        border_color="#00e676",
        focused_border_color="#00e676",
        border_radius=6,
        text_style=ft.TextStyle(color="white", size=13, weight="bold")
    )

    history_table_holder = ft.Container(expand=True)

    def get_table_control(search_query=""):
        sorted_keys = sorted(full_db_cache.keys(), reverse=True)

        if search_query.strip():
            sorted_keys = [k for k in sorted_keys if search_query.strip().lower() in k.lower()]

        sorted_keys = sorted_keys[:5]

        if not sorted_keys:
            return ft.Container(
                content=ft.Text("No records found.", color="white54", italic=True, size=13),
                padding=15
            )

        rows = []
        for key in sorted_keys:
            c_data = full_db_cache[key]

            def make_edit_handler(c_num):
                return lambda e: populate_fields(c_num)

            def make_delete_handler(c_num):
                return lambda e: execute_delete(c_num)

            edit_btn = ft.IconButton(
                icon=ft.Icons.EDIT,
                icon_color="#00e676",
                icon_size=18,
                tooltip="Edit",
                on_click=make_edit_handler(key)
            )

            del_btn = ft.IconButton(
                icon=ft.Icons.DELETE,
                icon_color="#ff5252",
                icon_size=18,
                tooltip="Delete",
                on_click=make_delete_handler(key)
            )

            action_cell = ft.Row([edit_btn, del_btn], spacing=0, alignment="center")

            data_cells = [
                ft.DataCell(ft.Text(key, weight="bold", color="#00e676", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("customer_name", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("legal_entity", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("business_type", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("business_turnover", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("category", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("location_district", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("cib_status", "")), color="white", size=11)),
                ft.DataCell(action_cell)
            ]

            rows.append(ft.DataRow(cells=data_cells))

        return ft.DataTable(
            width=800,
            columns=[
                ft.DataColumn(ft.Text("Cust No", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Name", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Entity", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Type", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Turnover", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Category", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("District", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("CIB", color="white", weight="bold", size=11)),
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

    def on_grid_search_change(e):
        render_history_table(grid_search_tf.value or "")
        history_table_holder.update()

    grid_search_tf.on_change = on_grid_search_change

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
        padding=15,
        border=ft.Border.all(width=1, color="#00e676"),
        border_radius=8,
        bgcolor="#061d19"
    )

    def refresh_cache():
        nonlocal full_db_cache
        fetched = get_all_corporate_profiles() or {}
        full_db_cache = {str(k).strip(): v for k, v in fetched.items()}

    def parse_flt(val):
        try:
            return float(val) if val else 0.00
        except ValueError:
            return 0.00

    def parse_int(val):
        try:
            return int(val) if val else 0
        except ValueError:
            return 0

    def on_save_click(e):
        cust_num = input_fields["Customer Number"].value.strip() if input_fields["Customer Number"].value else ""
        if not cust_num:
            page.overlay.append(ft.SnackBar(
                content=ft.Text("Please enter a valid Customer Number first!"),
                bgcolor="#ff9800", open=True
            ))
            page.update()
            return

        # Cross-Table Duplicate Validation Check
        if is_customer_exists_in_table(cust_num, "individual_profiles"):
            page.overlay.append(ft.SnackBar(
                content=ft.Text(f"Customer Number '{cust_num}' already exists in Individual Profiles!"),
                bgcolor="#ff5252", open=True
            ))
            page.update()
            return

        update_corporate_category()

        payload = {
            "customer_number": cust_num,
            "customer_name": input_fields["Customer Name"].value.strip() if input_fields["Customer Name"].value else "",
            "legal_entity": input_fields["Legal Entity Type"].value or "",
            "business_type": input_fields["Business Type"].value or "",
            "fixed_asset": parse_flt(input_fields["Fixed Asset Value"].value),
            "manpower_count": parse_int(input_fields["Manpower Count"].value),
            "business_turnover": parse_flt(input_fields["Business Turnover"].value),
            "business_size": input_fields["Size of Business"].value or "",
            "category": input_fields["Category [Type & Size]"].value or "",
            "business_sector": input_fields["Business Sector"].value.strip() if input_fields["Business Sector"].value else "",
            "product_service_name": input_fields["Product / Service Name"].value.strip() if input_fields["Product / Service Name"].value else "",
            "location_district": input_fields["Location District"].value or "",
            "default_history": input_fields["Default History"].value or "",
            "repayment_behavior": input_fields["Repayment Behavior"].value or "",
            "cib_status": input_fields["Latest CIB Status"].value or "",
            "audit_objection": input_fields["Major Audit Objections"].value or ""
        }

        try:
            save_corporate_profile(payload)
            refresh_cache()
            clear_form_fields()
            render_history_table(grid_search_tf.value or "")

            page.overlay.append(ft.SnackBar(
                content=ft.Text(f"Corporate Profile for {cust_num} saved successfully!"),
                bgcolor="#00e676", open=True
            ))
        except Exception as err:
            page.overlay.append(ft.SnackBar(
                content=ft.Text(f"Error saving corporate profile: {str(err)}"),
                bgcolor="red", open=True
            ))
        page.update()

    def execute_delete(cust_num):
        if not cust_num:
            return
        try:
            delete_corporate_profile_by_id(cust_num)
            refresh_cache()
            clear_form_fields()
            render_history_table(grid_search_tf.value or "")

            page.overlay.append(ft.SnackBar(
                content=ft.Text(f"Corporate Profile for {cust_num} deleted successfully!"),
                bgcolor="#ff5252", open=True
            ))
        except Exception as err:
            page.overlay.append(ft.SnackBar(
                content=ft.Text(f"Error deleting profile: {str(err)}"),
                bgcolor="red", open=True
            ))
        page.update()

    add_btn = ft.ElevatedButton(
        content=ft.Text("Add / Edit Corporate", color="black", weight="bold", size=14),
        on_click=on_save_click,
        style=ft.ButtonStyle(
            bgcolor="#78eb64",
            shape=ft.RoundedRectangleBorder(radius=20)
        ),
        height=42,
        width=210
    )

    input_form_card = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text("Corporate Customer Profile Entry", size=20, weight="bold", color="#00e676"),
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