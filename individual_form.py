import flet as ft
from database import (
    save_individual_profile,
    get_all_individual_profiles,
    delete_individual_profile_by_id,
    is_customer_exists_in_table,
    get_customer_name_by_number
)
from components.custom_datepicker import CustomDatePicker
from components.dropdown_configuration import get_configured_dropdown_options

def get_individual_profile_form(page: ft.Page):
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

    raw_cache = get_all_individual_profiles() or {}
    full_db_cache = {str(k).strip(): v for k, v in raw_cache.items()}

    dropdown_options = {
        "Legal Entity Type": get_configured_dropdown_options("individual.legal_entity_type"),
        "District": get_configured_dropdown_options("individual.district"),
        "Gender": get_configured_dropdown_options("individual.gender"),
        "Religion": get_configured_dropdown_options("individual.religion"),
        "Marital Status": get_configured_dropdown_options("individual.marital_status"),
        "Education": get_configured_dropdown_options("individual.education"),
        "Occupation": get_configured_dropdown_options("individual.occupation"),
        "Default History": get_configured_dropdown_options("individual.default_history"),
        "Repayment Behavior": get_configured_dropdown_options("individual.repayment_behavior"),
        "Latest CIB Status": get_configured_dropdown_options("individual.cib_status"),
        "Major Audit Objections": get_configured_dropdown_options("individual.audit_objections"),
    }

    numeric_fields = [
        "Salary Income", "Other Income", "Monthly Installment", 
        "Monthly Family Expense", "Total Asset", "Total Liability"
    ]

    dob_datepicker = CustomDatePicker(page, "DOB", width=None, height=45)
    
    def calculate_individual_metrics(e=None):
        try:
            asset_val = float(input_fields["Total Asset"].value or 0)
            liab_val = float(input_fields["Total Liability"].value or 0)
            input_fields["Net-Worth"].value = f"{(asset_val - liab_val):.2f}"
        except ValueError:
            input_fields["Net-Worth"].value = "0.00"

        try:
            salary = float(input_fields["Salary Income"].value or 0)
            other = float(input_fields["Other Income"].value or 0)
            install = float(input_fields["Monthly Installment"].value or 0)
            expense = float(input_fields["Monthly Family Expense"].value or 0)
            
            total_inc = salary + other
            total_exp = install + expense
            
            if total_exp > 0:
                input_fields["Income Expense Ratio"].value = f"{(total_inc / total_exp):.2f}"
            else:
                input_fields["Income Expense Ratio"].value = "0.00"
        except ValueError:
            input_fields["Income Expense Ratio"].value = "0.00"

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
        "District", "Gender", "Religion",
        "Marital Status", "DOB", "Education",
        "Occupation", "Salary Income", "Other Income",
        "Monthly Installment", "Monthly Family Expense", "Income Expense Ratio",
        "Total Asset", "Total Liability", "Net-Worth",
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
        elif label_name in ["Income Expense Ratio", "Net-Worth"]:
            tf = ft.TextField(
                label=label_name,
                read_only=True,
                value="0.00",
                **base_field_style
            )
        elif label_name == "DOB":
            tf = dob_datepicker.input_field
            tf.label = "DOB"
            tf.height = 45
            tf.content_padding = ft.Padding(12, 10, 12, 10)
            tf.border_color = "#00e676"
            tf.focused_border_color = "#00e676"
            tf.border_radius = 6
            tf.label_style = ft.TextStyle(color="white70", size=14)
            tf.text_style = ft.TextStyle(color="white", size=13)
            tf.expand = True
        else:
            is_num = label_name in numeric_fields or label_name == "Customer Number"
            on_chg = calculate_individual_metrics if label_name in numeric_fields else None
            if label_name == "Customer Number":
                on_chg = on_customer_number_change

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
        input_fields["District"].value = str(data.get("district") or "")
        input_fields["Gender"].value = str(data.get("gender") or "")
        input_fields["Religion"].value = str(data.get("religion") or "")
        input_fields["Marital Status"].value = str(data.get("marital_status") or "")
        
        dob_val = str(data.get("dob") or "")
        dob_datepicker.input_field.value = dob_val
        
        input_fields["Education"].value = str(data.get("education") or "")
        input_fields["Occupation"].value = str(data.get("occupation") or "")
        
        input_fields["Salary Income"].value = str(data.get("salary_income") or "0.00")
        input_fields["Other Income"].value = str(data.get("other_income") or "0.00")
        input_fields["Monthly Installment"].value = str(data.get("monthly_installment") or "0.00")
        input_fields["Monthly Family Expense"].value = str(data.get("family_expense") or "0.00")
        input_fields["Income Expense Ratio"].value = str(data.get("income_expense_ratio") or "0.00")
        
        input_fields["Total Asset"].value = str(data.get("total_asset") or "0.00")
        input_fields["Total Liability"].value = str(data.get("total_liability") or "0.00")
        input_fields["Net-Worth"].value = str(data.get("net_worth") or "0.00")
        
        input_fields["Default History"].value = str(data.get("default_history") or "")
        input_fields["Repayment Behavior"].value = str(data.get("repayment_behavior") or "")
        input_fields["Latest CIB Status"].value = str(data.get("cib_status") or "")
        input_fields["Major Audit Objections"].value = str(data.get("audit_objection") or "")

        calculate_individual_metrics()
        page.update()

    def clear_form_fields():
        for k, tf in input_fields.items():
            if k in ["Income Expense Ratio", "Net-Worth"]:
                tf.value = "0.00"
            else:
                tf.value = ""
        dob_datepicker.input_field.value = ""
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
                ft.DataCell(ft.Text(str(c_data.get("district", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("occupation", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("salary_income", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("income_expense_ratio", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("total_asset", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("net_worth", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("cib_status", "")), color="white", size=11)),
                ft.DataCell(action_cell)
            ]

            rows.append(ft.DataRow(cells=data_cells))

        return ft.DataTable(
            width=800,
            columns=[
                ft.DataColumn(ft.Text("Cust No", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Name", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("District", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Occupation", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Salary", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Inc/Exp Ratio", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Asset", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Net Worth", color="white", weight="bold", size=11)),
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
        fetched = get_all_individual_profiles() or {}
        full_db_cache = {str(k).strip(): v for k, v in fetched.items()}

    def parse_flt(val):
        try:
            return float(val) if val else 0.00
        except ValueError:
            return 0.00

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
        if is_customer_exists_in_table(cust_num, "corporate_profiles"):
            page.overlay.append(ft.SnackBar(
                content=ft.Text(f"Customer Number '{cust_num}' already exists in Corporate Profiles!"),
                bgcolor="#ff5252", open=True
            ))
            page.update()
            return

        calculate_individual_metrics()

        payload = {
            "customer_number": cust_num,
            "customer_name": input_fields["Customer Name"].value.strip() if input_fields["Customer Name"].value else "",
            "legal_entity": input_fields["Legal Entity Type"].value or "",
            "district": input_fields["District"].value or "",
            "gender": input_fields["Gender"].value or "",
            "religion": input_fields["Religion"].value or "",
            "marital_status": input_fields["Marital Status"].value or "",
            "dob": dob_datepicker.input_field.value or "",
            "education": input_fields["Education"].value or "",
            "occupation": input_fields["Occupation"].value or "",
            "salary_income": parse_flt(input_fields["Salary Income"].value),
            "other_income": parse_flt(input_fields["Other Income"].value),
            "monthly_installment": parse_flt(input_fields["Monthly Installment"].value),
            "family_expense": parse_flt(input_fields["Monthly Family Expense"].value),
            "income_expense_ratio": parse_flt(input_fields["Income Expense Ratio"].value),
            "total_asset": parse_flt(input_fields["Total Asset"].value),
            "total_liability": parse_flt(input_fields["Total Liability"].value),
            "net_worth": parse_flt(input_fields["Net-Worth"].value),
            "default_history": input_fields["Default History"].value or "",
            "repayment_behavior": input_fields["Repayment Behavior"].value or "",
            "cib_status": input_fields["Latest CIB Status"].value or "",
            "audit_objection": input_fields["Major Audit Objections"].value or ""
        }

        try:
            save_individual_profile(payload)
            refresh_cache()
            clear_form_fields()
            render_history_table(grid_search_tf.value or "")

            page.overlay.append(ft.SnackBar(
                content=ft.Text(f"Profile for Customer {cust_num} saved successfully!"),
                bgcolor="#00e676", open=True
            ))
        except Exception as err:
            page.overlay.append(ft.SnackBar(
                content=ft.Text(f"Error saving profile: {str(err)}"),
                bgcolor="red", open=True
            ))
        page.update()

    def execute_delete(cust_num):
        if not cust_num:
            return
        try:
            delete_individual_profile_by_id(cust_num)
            refresh_cache()
            clear_form_fields()
            render_history_table(grid_search_tf.value or "")

            page.overlay.append(ft.SnackBar(
                content=ft.Text(f"Profile for Customer {cust_num} deleted successfully!"),
                bgcolor="#ff5252", open=True
            ))
        except Exception as err:
            page.overlay.append(ft.SnackBar(
                content=ft.Text(f"Error deleting profile: {str(err)}"),
                bgcolor="red", open=True
            ))
        page.update()

    add_btn = ft.ElevatedButton(
        content=ft.Text("Add / Edit Individual", color="black", weight="bold", size=14),
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
                content=ft.Text("Individual Customer Profile Entry", size=20, weight="bold", color="#00e676"),
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