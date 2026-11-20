import flet as ft
from datetime import date, timedelta
from database import (
    save_funded_ac_profile,
    get_all_funded_ac_profiles,
    delete_funded_ac_profile_by_id,
    get_customer_name_by_number,
    is_account_exists_in_table,
    get_all_credit_conversion_factors
)
from components.custom_datepicker import CustomDatePicker
from components.facility_types import FUNDED_FACILITY_TYPES

def get_average_credit_conversion_rate(facility_type: str) -> float:
    """Returns the average credit conversion rate for a facility type."""
    requested_type = str(facility_type or "").strip().lower()
    ccf_records = get_all_credit_conversion_factors() or []
    matching_rates = [
        float(record.get("cc_rate", 0.0))
        for record in ccf_records
        if str(record.get("facility_type", "")).strip().lower() == requested_type
    ]
    if not matching_rates and requested_type in ("continuous", "continuous loan"):
        matching_rates = [
            float(record.get("cc_rate", 0.0))
            for record in ccf_records
            if str(record.get("facility_type", "")).strip().lower() == "ccod"
        ]
    return sum(matching_rates) / len(matching_rates) if matching_rates else 0.0

def get_last_month_end_date() -> date:
    today = date.today()
    first_day_of_current_month = date(today.year, today.month, 1)
    return first_day_of_current_month - timedelta(days=1)

def get_funded_ac_profile_form(page: ft.Page):
    input_fields = {}
    term_loan_only_fields = {
        "Due Installment (Months)",
        "Installment Size",
        "Amount Recovered",
        "Installment Recovered",
        "Overdue Installment",
    }

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

    raw_cache = get_all_funded_ac_profiles() or {}
    full_db_cache = {str(k).strip(): v for k, v in raw_cache.items()}

    last_month_end = get_last_month_end_date()
    fn_reporting_date_str = last_month_end.strftime("%d/%m/%Y")

    dropdown_options = {
        "Nature of Loan": list(FUNDED_FACILITY_TYPES),
        "Last Approval Type": ["New", "Renewal", "Enhancement", "RSDL", "Restructure"],
        "SICR/Impairment": ["None", "SICR", "Impairment"]
    }

    all_field_names = [
        "Reporting Date", "Customer Number", "Customer Name",
        "Account Number", "Nature of Loan", "Last Approval Type",
        "Approval Date", "Loan Limit", "Loan Outstanding",
        "Accrued Interest", "Calculated Interest", "Available Limit", "Expiry Date",
        "1st Installment Due", "Due Installment (Months)", "Installment Size",
        "Amount Recovered", "Installment Recovered", "Overdue Installment",
        "Overdue Period in Days", "Overdue Amount", "Credit Conversion Factor (CCF)", "EAD",
        "Staging by DPD", "SICR/Impairment", "QJ Stage", "Final Stage",
        "SICR/Impairment Reason"
    ]

    def display_facility_type(value):
        stored_value = str(value or "").strip()
        return {
            "demand": "Demand Loan",
            "continuous": "Continuous Loan",
            "term": "Term Loan",
        }.get(stored_value.lower(), stored_value)

    # Handle Customer Name Autofill
    def autofill_customer_name(e=None):
        raw_val = input_fields["Customer Number"].value
        cust_num = str(raw_val).strip() if raw_val else ""
        
        if cust_num:
            matched_name = get_customer_name_by_number(cust_num)
            if matched_name:
                input_fields["Customer Name"].value = matched_name
                page.overlay.append(
                    ft.SnackBar(
                        content=ft.Text(f"Customer Name Found: {matched_name}"), 
                        bgcolor="#00e676", 
                        open=True
                    )
                )
            else:
                input_fields["Customer Name"].value = ""
        else:
            input_fields["Customer Name"].value = ""
            
        page.update()

    # Handle Duplicate Account Check on Account Number change
    def check_duplicate_ac(e=None):
        ac_num = input_fields["Account Number"].value.strip() if input_fields["Account Number"].value else ""
        if not ac_num:
            return

        if ac_num in full_db_cache:
            populate_fields(ac_num)
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Existing Funded A/C {ac_num} loaded for update."), bgcolor="#0288d1", open=True))
        elif is_account_exists_in_table(ac_num, "non_funded_ac_profiles"):
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Warning: Account {ac_num} exists in Non-Funded A/C Profiles!"), bgcolor="#ff9800", open=True))
        page.update()

    def update_final_stage():
        stage_ranks = {"Stage-1": 1, "Stage-2": 2, "Stage-3": 3}
        qj_stage = str(input_fields["QJ Stage"].value or "").strip()
        dpd_stage = str(input_fields["Staging by DPD"].value or "").strip()
        final_rank = max(stage_ranks.get(qj_stage, 1), stage_ranks.get(dpd_stage, 1))
        input_fields["Final Stage"].value = f"Stage-{final_rank}"

    # Update QJ Stage based on SICR/Impairment dropdown
    def update_qj_stage(e=None):
        sicr_control = input_fields.get("SICR/Impairment")
        sicr_val = str(sicr_control.value or "").strip() if sicr_control else ""

        if sicr_val == "SICR":
            target_stage = "Stage-2"
        elif sicr_val == "Impairment":
            target_stage = "Stage-3"
        else:
            target_stage = "Stage-1"

        if "QJ Stage" in input_fields:
            input_fields["QJ Stage"].value = target_stage
            update_final_stage()
            input_fields["QJ Stage"].update()
            input_fields["Final Stage"].update()

    # Calculate Funded AC Metrics
    def calculate_funded_ac(e=None):
        rep_d = last_month_end
        exp_d = fn_exp_datepicker.value.date() if getattr(fn_exp_datepicker, "value", None) else None
        rep1_d = fn_rep1_datepicker.value.date() if getattr(fn_rep1_datepicker, "value", None) else None
        nature_val = input_fields["Nature of Loan"].value
        is_term_loan = str(nature_val or "").strip().lower() in ("term", "term loan")
        for field_name in term_loan_only_fields:
            field = input_fields[field_name]
            field.disabled = False
            if field_name in ("Installment Size", "Amount Recovered"):
                field.read_only = not is_term_loan
            field.text_style = ft.TextStyle(
                color="white" if is_term_loan else "white54", size=13
            )

        loan_out_val = 0.0
        accrued_int_val = 0.0
        calc_int_val = 0.0
        loan_limit_val = 0.0

        try: loan_out_val = float(input_fields["Loan Outstanding"].value or 0)
        except ValueError: pass

        try: accrued_int_val = float(input_fields["Accrued Interest"].value or 0)
        except ValueError: pass

        try: calc_int_val = float(input_fields["Calculated Interest"].value or 0)
        except ValueError: pass

        try: loan_limit_val = float(input_fields["Loan Limit"].value or 0)
        except ValueError: pass

        available_limit = max(0.0, loan_limit_val - loan_out_val - accrued_int_val - calc_int_val)
        input_fields["Available Limit"].value = f"{available_limit:.2f}"

        inst_size = 0.0
        rec_amt = 0.0
        try:
            inst_size = float(input_fields["Installment Size"].value or 0)
            rec_amt = float(input_fields["Amount Recovered"].value or 0)
        except ValueError: pass

        # Calculate Paid Installments
        inst_rec_val = 0.0
        if inst_size > 0:
            inst_rec_val = rec_amt / inst_size
            input_fields["Installment Recovered"].value = f"{inst_rec_val:.2f}"
        else:
            input_fields["Installment Recovered"].value = "0.00"

        due_inst_count = 0.0
        overdue_days = 0
        overdue_amt = 0.0

        if str(nature_val or "").strip().lower() in ("term", "term loan"):
            if rep_d and rep1_d:
                diff_days = (rep_d - rep1_d).days
                due_inst_count = max(0.0, diff_days / 30.0)
            
            input_fields["Due Installment (Months)"].value = f"{due_inst_count:.2f}"

            # Calculate Overdue Installment
            overdue_inst_val = max(0.0, due_inst_count - inst_rec_val)
            input_fields["Overdue Installment"].value = f"{overdue_inst_val:.2f}"

            if inst_rec_val < due_inst_count:
                overdue_months = due_inst_count - inst_rec_val
                overdue_days = int(overdue_months * 30)
                overdue_amt = min(loan_out_val, overdue_months * inst_size)
            else:
                overdue_days = 0
                overdue_amt = 0.0
        else:
            input_fields["Due Installment (Months)"].value = "0.00"
            input_fields["Overdue Installment"].value = "0.00"
            if exp_d and rep_d and exp_d < rep_d:
                overdue_days = (rep_d - exp_d).days
                overdue_amt = loan_out_val
            else:
                overdue_days = 0
                overdue_amt = 0.0

        input_fields["Overdue Period in Days"].value = str(overdue_days)
        input_fields["Overdue Amount"].value = f"{overdue_amt:.2f}"
        ccf_rate = get_average_credit_conversion_rate(nature_val)
        input_fields["Credit Conversion Factor (CCF)"].value = f"{ccf_rate:.4f}"

        # Calculate Staging by DPD
        if overdue_days <= 30:
            input_fields["Staging by DPD"].value = "Stage-1"
        elif 30 < overdue_days <= 90:
            input_fields["Staging by DPD"].value = "Stage-2"
        else:
            input_fields["Staging by DPD"].value = "Stage-3"
        update_final_stage()

        # Calculate Dynamic EAD
        base_ead = loan_out_val + accrued_int_val + calc_int_val

        if str(nature_val or "").strip().lower() in (
            "continuous", "continuous loan", "ccod", "credit card"
        ):
            ccf_rate = float(input_fields["Credit Conversion Factor (CCF)"].value or 0)
            ead_val = base_ead + ccf_rate * available_limit
        else:
            ead_val = base_ead

        input_fields["EAD"].value = f"{ead_val:.2f}"

        input_fields["Overdue Period in Days"].update()
        input_fields["Overdue Amount"].update()
        input_fields["Staging by DPD"].update()
        input_fields["EAD"].update()
        page.update()

    fn_app_datepicker = CustomDatePicker(page, "Approval Date", width=260, on_change_callback=calculate_funded_ac)
    fn_exp_datepicker = CustomDatePicker(page, "Expiry Date", width=260, on_change_callback=calculate_funded_ac)
    fn_rep1_datepicker = CustomDatePicker(page, "1st Installment Due", width=260, on_change_callback=calculate_funded_ac)

    for label_name in all_field_names:
        if label_name == "Approval Date":
            input_fields[label_name] = fn_app_datepicker
        elif label_name == "Expiry Date":
            input_fields[label_name] = fn_exp_datepicker
        elif label_name == "1st Installment Due":
            input_fields[label_name] = fn_rep1_datepicker
        elif label_name == "Reporting Date":
            input_fields[label_name] = ft.TextField(label=label_name, value=fn_reporting_date_str, read_only=True, **base_field_style)
        elif label_name == "QJ Stage":
            input_fields[label_name] = ft.TextField(label=label_name, value="Stage-1", read_only=True, **base_field_style)
        elif label_name == "Final Stage":
            input_fields[label_name] = ft.TextField(label=label_name, value="Stage-1", read_only=True, **base_field_style)
        elif label_name == "Available Limit":
            input_fields[label_name] = ft.TextField(
                label=label_name, value="0.00", read_only=True, **base_field_style
            )
        elif label_name == "Credit Conversion Factor (CCF)":
            input_fields[label_name] = ft.TextField(
                label=label_name, value="0.0000", read_only=True, **base_field_style
            )
        elif label_name in ["Due Installment (Months)", "Installment Recovered", "Overdue Installment", "Overdue Period in Days", "Overdue Amount", "EAD", "Staging by DPD"]:
            default_val = "0" if label_name == "Overdue Period in Days" else ("Stage-1" if label_name == "Staging by DPD" else "0.00")
            display_label = "Exposure At Default (EAD)" if label_name == "EAD" else label_name
            input_fields[label_name] = ft.TextField(
                label=display_label,
                value=default_val,
                read_only=True,
                **base_field_style
            )
            if label_name in term_loan_only_fields:
                input_fields[label_name].text_style = ft.TextStyle(color="white54", size=13)
        elif label_name in dropdown_options:
            tf = ft.Dropdown(
                label="Facility Type" if label_name == "Nature of Loan" else label_name,
                options=[ft.dropdown.Option(opt) for opt in dropdown_options[label_name]],
                value="None" if label_name == "SICR/Impairment" else None,
                **base_field_style
            )
            if label_name == "Nature of Loan":
                tf.on_select = calculate_funded_ac
            input_fields[label_name] = tf
        else:
            tf = ft.TextField(
                label=label_name,
                keyboard_type=ft.KeyboardType.NUMBER if label_name not in ["Customer Name", "Account Number", "Customer Number", "SICR/Impairment Reason"] else ft.KeyboardType.TEXT,
                read_only=label_name in term_loan_only_fields,
                **base_field_style
            )
            if label_name in term_loan_only_fields:
                tf.text_style = ft.TextStyle(color="white54", size=13)
            if label_name in ["Installment Size", "Amount Recovered", "Loan Outstanding", "Loan Limit", "Accrued Interest", "Calculated Interest"]:
                tf.on_change = calculate_funded_ac
            elif label_name == "Customer Number":
                tf.on_change = autofill_customer_name
            elif label_name == "Account Number":
                tf.on_change = check_duplicate_ac
            input_fields[label_name] = tf

    input_fields["SICR/Impairment"].on_select = update_qj_stage
    input_fields["SICR/Impairment Reason"].on_change = update_qj_stage

    grid_rows = []
    for i in range(0, len(all_field_names), 3):
        row_controls = []
        for j in range(3):
            if i + j < len(all_field_names):
                f_name = all_field_names[i + j]
                ctrl = input_fields[f_name].input_field if isinstance(input_fields[f_name], CustomDatePicker) else input_fields[f_name]
                row_controls.append(ft.Container(content=ctrl, expand=1))
            else:
                row_controls.append(ft.Container(expand=1))
        grid_rows.append(ft.Row(controls=row_controls, spacing=15))

    grid_column = ft.Column(controls=grid_rows, spacing=15)

    def populate_fields(ac_num):
        search_key = str(ac_num).strip()
        data = full_db_cache.get(search_key, {})
        if not data:
            return

        input_fields["Account Number"].value = search_key
        input_fields["Customer Number"].value = str(data.get("cust_num") or "")
        input_fields["Customer Name"].value = str(data.get("cust_name") or "")
        input_fields["Nature of Loan"].value = display_facility_type(data.get("nature"))
        input_fields["Last Approval Type"].value = str(data.get("approval_type") or "")
        input_fields["Loan Limit"].value = f"{float(data.get('loan_limit', 0)):.2f}"
        input_fields["Loan Outstanding"].value = f"{float(data.get('loan_out', 0)):.2f}"
        input_fields["Accrued Interest"].value = f"{float(data.get('accrued_int', 0)):.2f}"
        input_fields["Calculated Interest"].value = f"{float(data.get('calc_int', 0)):.2f}"
        input_fields["Due Installment (Months)"].value = f"{float(data.get('due_install', 0)):.2f}"
        input_fields["Installment Size"].value = f"{float(data.get('install_size', 0)):.2f}"
        input_fields["Amount Recovered"].value = f"{float(data.get('amt_recovered', 0)):.2f}"
        input_fields["Installment Recovered"].value = f"{float(data.get('install_recovered', 0)):.2f}"
        input_fields["Overdue Installment"].value = f"{float(data.get('overdue_install', 0)):.2f}"
        input_fields["Overdue Period in Days"].value = str(data.get("overdue_in_days", 0))
        input_fields["Overdue Amount"].value = f"{float(data.get('overdue_amt', 0)):.2f}"
        input_fields["EAD"].value = f"{float(data.get('ead', 0)):.2f}"
        input_fields["Staging by DPD"].value = str(data.get("staging_by_dpd") or "Stage-1")
        input_fields["SICR/Impairment"].value = str(data.get("sicr_impairment") or "None")
        input_fields["SICR/Impairment Reason"].value = str(data.get("qj_reason") or "")

        if data.get("approval_date"):
            fn_app_datepicker.set_date_from_string(data["approval_date"])
        else:
            fn_app_datepicker.clear()

        if data.get("exp_date"):
            fn_exp_datepicker.set_date_from_string(data["exp_date"])
        else:
            fn_exp_datepicker.clear()

        if data.get("first_inst_due"):
            fn_rep1_datepicker.set_date_from_string(data["first_inst_due"])
        else:
            fn_rep1_datepicker.clear()

        calculate_funded_ac()
        update_qj_stage()
        page.update()

    def clear_form_fields():
        for k, tf in input_fields.items():
            if k == "Reporting Date":
                continue
            elif isinstance(tf, CustomDatePicker):
                tf.clear()
            elif k == "Credit Conversion Factor (CCF)":
                tf.value = "0.0000"
            elif k in ["Due Installment (Months)", "Installment Recovered", "Overdue Installment", "Overdue Period in Days", "Overdue Amount", "Available Limit", "EAD"]:
                tf.value = "0.00" if "Days" not in k else "0"
            elif k == "Staging by DPD":
                tf.value = "Stage-1"
            elif k in ["QJ Stage", "SICR/Impairment Reason"]:
                tf.value = ""
            elif k == "SICR/Impairment":
                tf.value = "None"
            else:
                tf.value = ""
        calculate_funded_ac()
        update_qj_stage()
        page.update()

    grid_search_tf = ft.TextField(
        hint_text="A/C No.",
        hint_style=ft.TextStyle(color="white38", size=13),
        width=140,
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
            return ft.Container(content=ft.Text("No records found.", color="white54", italic=True, size=13), padding=15)

        rows = []
        for key in sorted_keys:
            c_data = full_db_cache[key]
            action_cell = ft.Row([
                ft.IconButton(icon=ft.Icons.EDIT, icon_color="#00e676", icon_size=18, tooltip="Edit", on_click=lambda e, k=key: populate_fields(k)),
                ft.IconButton(icon=ft.Icons.DELETE, icon_color="#ff5252", icon_size=18, tooltip="Delete", on_click=lambda e, k=key: execute_delete(k))
            ], spacing=0, alignment="center")

            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(key, weight="bold", color="#00e676", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("cust_name", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("nature", "")), color="white", size=11)),
                ft.DataCell(ft.Text(f"{float(c_data.get('loan_out', 0)):.2f}", color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("staging_by_dpd", "Stage-1")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("qj_stage", "") or "-"), color="white", size=11)),
                ft.DataCell(action_cell)
            ]))

        return ft.DataTable(
            width=800,
            columns=[
                ft.DataColumn(ft.Text("A/C No", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Name", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Facility Type", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Outstanding", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("DPD Stage", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("QJ Stage", color="white", weight="bold", size=11)),
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

    grid_search_tf.on_change = lambda e: (render_history_table(grid_search_tf.value or ""), history_table_holder.update())

    history_section_container = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Text("Search by A/C No :", size=15, weight="bold", color="#00e676"),
                grid_search_tf
            ], vertical_alignment="center", spacing=12),
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
        fetched = get_all_funded_ac_profiles() or {}
        full_db_cache = {str(k).strip(): v for k, v in fetched.items()}

    def parse_flt(val):
        try: return float(val) if val else 0.00
        except ValueError: return 0.00

    def parse_int(val):
        try: return int(val) if val else 0
        except ValueError: return 0

    def on_save_click(e):
        ac_num = input_fields["Account Number"].value.strip() if input_fields["Account Number"].value else ""
        if not ac_num:
            page.overlay.append(ft.SnackBar(content=ft.Text("Please enter a valid Account Number!"), bgcolor="#ff9800", open=True))
            page.update()
            return

        calculate_funded_ac()
        update_qj_stage()

        payload = {
            "ac_num": ac_num,
            "reporting_date": last_month_end.strftime("%Y-%m-%d"),
            "cust_num": input_fields["Customer Number"].value.strip() if input_fields["Customer Number"].value else "",
            "cust_name": input_fields["Customer Name"].value.strip() if input_fields["Customer Name"].value else "",
            "nature": input_fields["Nature of Loan"].value or "",
            "approval_type": input_fields["Last Approval Type"].value or "",
            "approval_date": fn_app_datepicker.value.strftime("%Y-%m-%d") if getattr(fn_app_datepicker, "value", None) else None,
            "loan_limit": parse_flt(input_fields["Loan Limit"].value),
            "loan_out": parse_flt(input_fields["Loan Outstanding"].value),
            "accrued_int": parse_flt(input_fields["Accrued Interest"].value),
            "calc_int": parse_flt(input_fields["Calculated Interest"].value),
            "exp_date": fn_exp_datepicker.value.strftime("%Y-%m-%d") if getattr(fn_exp_datepicker, "value", None) else None,
            "first_inst_due": fn_rep1_datepicker.value.strftime("%Y-%m-%d") if getattr(fn_rep1_datepicker, "value", None) else None,
            "due_install": parse_flt(input_fields["Due Installment (Months)"].value),
            "install_size": parse_flt(input_fields["Installment Size"].value),
            "amt_recovered": parse_flt(input_fields["Amount Recovered"].value),
            "install_recovered": parse_flt(input_fields["Installment Recovered"].value),
            "overdue_install": parse_flt(input_fields["Overdue Installment"].value),
            "overdue_in_days": parse_int(input_fields["Overdue Period in Days"].value),
            "overdue_amt": parse_flt(input_fields["Overdue Amount"].value),
            "ecl_category": "",
            "ead": parse_flt(input_fields["EAD"].value),
            "staging_by_dpd": input_fields["Staging by DPD"].value or "Stage-1",
            "sicr_impairment": input_fields["SICR/Impairment"].value or "None",
            "qj_stage": input_fields["QJ Stage"].value or "",
            "qj_reason": input_fields["SICR/Impairment Reason"].value.strip() if input_fields["SICR/Impairment Reason"].value else ""
        }

        try:
            save_funded_ac_profile(payload)
            refresh_cache()
            clear_form_fields()
            render_history_table(grid_search_tf.value or "")
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Funded A/C {ac_num} saved successfully!"), bgcolor="#00e676", open=True))
        except Exception as err:
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Error saving record: {str(err)}"), bgcolor="red", open=True))
        page.update()

    def execute_delete(ac_num):
        if not ac_num: return
        try:
            delete_funded_ac_profile_by_id(ac_num)
            refresh_cache()
            clear_form_fields()
            render_history_table(grid_search_tf.value or "")
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Funded A/C {ac_num} deleted successfully!"), bgcolor="#ff5252", open=True))
        except Exception as err:
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Error deleting: {str(err)}"), bgcolor="red", open=True))
        page.update()

    add_btn = ft.ElevatedButton(
        content=ft.Text("Add / Edit Funded A/C", color="black", weight="bold", size=14),
        on_click=on_save_click,
        style=ft.ButtonStyle(bgcolor="#78eb64", shape=ft.RoundedRectangleBorder(radius=20)),
        height=42, width=220
    )

    input_form_card = ft.Container(
        content=ft.Column([
            ft.Container(content=ft.Text("Funded Account Profile Entry", size=20, weight="bold", color="#00e676"), alignment=ft.Alignment(0, 0), padding=ft.Padding(0, 0, 0, 15)),
            grid_column,
            ft.Container(height=20),
            ft.Row([add_btn], alignment="center")
        ]),
        padding=20, border=ft.Border.all(width=1, color="#00e676"), border_radius=8, bgcolor="#061d19"
    )

    render_history_table()

    return ft.Container(
        content=ft.Column([input_form_card, history_section_container], scroll=ft.ScrollMode.AUTO, spacing=15),
        width=820, alignment=ft.Alignment(0, -1), padding=ft.Padding(0, 0, 0, 20)
    )