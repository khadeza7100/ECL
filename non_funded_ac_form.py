import flet as ft
from datetime import date, timedelta
from database import (
    save_non_funded_ac_profile,
    get_all_non_funded_ac_profiles,
    delete_non_funded_ac_profile_by_id,
    get_customer_name_by_number,
    is_account_exists_in_table,
    get_all_credit_conversion_factors
)
from components.custom_datepicker import CustomDatePicker
from components.facility_types import NON_FUNDED_FACILITY_TYPES

def get_non_funded_ccf_rate(facility_type: str) -> float:
    """Fetches CCF rate from the database based on facility type."""
    if not facility_type:
        return 0.0
    ccf_records = get_all_credit_conversion_factors() or []
    for record in ccf_records:
        if str(record.get("facility_type", "")).strip().upper() == str(facility_type).strip().upper():
            return float(record.get("cc_rate", 0.0))
    return 0.0

def get_last_month_end_date() -> date:
    today = date.today()
    first_day_of_current_month = date(today.year, today.month, 1)
    return first_day_of_current_month - timedelta(days=1)

def get_non_funded_ac_profile_form(page: ft.Page):
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

    raw_cache = get_all_non_funded_ac_profiles() or {}
    full_db_cache = {str(k).strip(): v for k, v in raw_cache.items()}

    last_month_end = get_last_month_end_date()
    nf_reporting_date_str = last_month_end.strftime("%d/%m/%Y")

    dropdown_options = {
        "Cont. Liability Type": list(NON_FUNDED_FACILITY_TYPES),
        "SICR/Impairment": ["None", "SICR", "Impairment"]
    }

    all_field_names = [
        "Reporting Date", "Customer Number", "Customer Name",
        "Account Number", "Cont. Liability Type", "Account Limit",
        "Amount of Liability", "Issue Date", "Expiry Date", 
        "Overdue Period in Days", "Margin Kept", "CCF", "EAD",
        "Staging by DPD", "SICR/Impairment", "QJ Stage", "Final Stage",
        "SICR/Impairment Reason"
    ]

    # --- 1. EVENT HANDLERS ---
    def autofill_customer_name(e=None):
        cust_num = input_fields["Customer Number"].value.strip() if input_fields["Customer Number"].value else ""
        if cust_num:
            matched_name = get_customer_name_by_number(cust_num)
            if matched_name:
                input_fields["Customer Name"].value = matched_name
                page.overlay.append(ft.SnackBar(content=ft.Text(f"Customer Name found: {matched_name}"), bgcolor="#00e676", open=True))
                input_fields["Customer Name"].update()
        page.update()

    def check_duplicate_ac(e=None):
        ac_num = input_fields["Account Number"].value.strip() if input_fields["Account Number"].value else ""
        if not ac_num:
            return

        if ac_num in full_db_cache:
            populate_fields(ac_num)
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Existing Non-Funded A/C {ac_num} loaded for update."), bgcolor="#0288d1", open=True))
        elif is_account_exists_in_table(ac_num, "funded_ac_profiles"):
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Warning: Account {ac_num} exists in Funded A/C Profiles!"), bgcolor="#ff9800", open=True))
        page.update()

    def update_final_stage():
        stage_ranks = {"Stage-1": 1, "Stage-2": 2, "Stage-3": 3}
        qj_stage = str(input_fields["QJ Stage"].value or "").strip()
        dpd_stage = str(input_fields["Staging by DPD"].value or "").strip()
        final_rank = max(stage_ranks.get(qj_stage, 1), stage_ranks.get(dpd_stage, 1))
        input_fields["Final Stage"].value = f"Stage-{final_rank}"

    def update_qj_stage(e=None):
        sicr_control = input_fields.get("SICR/Impairment")
        if e is not None and getattr(e, "control", None) is sicr_control:
            sicr_value = e.control.value
        else:
            sicr_value = sicr_control.value if sicr_control else ""
        sicr_val = str(sicr_value or "").strip()

        target_stage = {
            "None": "Stage-1",
            "SICR": "Stage-2",
            "Impairment": "Stage-3",
        }.get(sicr_val, "Stage-1")

        if "QJ Stage" in input_fields:
            input_fields["QJ Stage"].value = target_stage
            update_final_stage()
            page.update()

    def calculate_non_funded_ac(e=None):
        rep_d = last_month_end
        exp_d = nf_exp_datepicker.value.date() if getattr(nf_exp_datepicker, "value", None) else None

        overdue_days = 0
        if rep_d and exp_d:
            if exp_d < rep_d:
                overdue_days = (rep_d - exp_d).days

        input_fields["Overdue Period in Days"].value = str(overdue_days)

        if overdue_days <= 30:
            input_fields["Staging by DPD"].value = "Stage-1"
        elif 30 < overdue_days <= 90:
            input_fields["Staging by DPD"].value = "Stage-2"
        else:
            input_fields["Staging by DPD"].value = "Stage-3"
        update_final_stage()

        facility_type = input_fields["Cont. Liability Type"].value
        ccf_val = get_non_funded_ccf_rate(facility_type)
        input_fields["CCF"].value = f"{ccf_val:.4f}"

        amt_liability = 0.0
        margin_kept = 0.0
        try:
            amt_liability = float(input_fields["Amount of Liability"].value or 0)
        except ValueError:
            pass

        try:
            margin_kept = float(input_fields["Margin Kept"].value or 0)
        except ValueError:
            pass

        ead_val = max(0.0, (amt_liability - margin_kept) * ccf_val)
        input_fields["EAD"].value = f"{ead_val:.2f}"

        input_fields["Overdue Period in Days"].update()
        input_fields["Staging by DPD"].update()
        input_fields["CCF"].update()
        input_fields["EAD"].update()
        page.update()

    # --- 2. CONTROL CREATION ---
    nf_issue_datepicker = CustomDatePicker(page, "Issue Date", width=260, on_change_callback=calculate_non_funded_ac)
    nf_exp_datepicker = CustomDatePicker(page, "Expiry Date", width=260, on_change_callback=calculate_non_funded_ac)

    for label_name in all_field_names:
        if label_name == "Issue Date":
            input_fields[label_name] = nf_issue_datepicker
        elif label_name == "Expiry Date":
            input_fields[label_name] = nf_exp_datepicker
        elif label_name == "Reporting Date":
            input_fields[label_name] = ft.TextField(label=label_name, value=nf_reporting_date_str, read_only=True, **base_field_style)
        elif label_name == "QJ Stage":
            input_fields[label_name] = ft.TextField(label=label_name, value="Stage-1", read_only=True, **base_field_style)
        elif label_name == "Final Stage":
            input_fields[label_name] = ft.TextField(label=label_name, value="Stage-1", read_only=True, **base_field_style)
        elif label_name in ["Overdue Period in Days", "CCF", "EAD", "Staging by DPD"]:
            default_val = "0" if label_name == "Overdue Period in Days" else ("Stage-1" if label_name == "Staging by DPD" else "0.00")
            display_label = {
                "CCF": "Credit Conversion Factor (CCF)",
                "EAD": "Exposure At Default (EAD)",
            }.get(label_name, label_name)
            input_fields[label_name] = ft.TextField(label=display_label, value=default_val, read_only=True, **base_field_style)
        elif label_name in dropdown_options:
            input_fields[label_name] = ft.Dropdown(
                label="Facility Type" if label_name == "Cont. Liability Type" else label_name,
                options=[ft.dropdown.Option(opt) for opt in dropdown_options[label_name]],
                value="None" if label_name == "SICR/Impairment" else None,
                on_select=update_qj_stage if label_name == "SICR/Impairment" else None,
                **base_field_style
            )
        else:
            input_fields[label_name] = ft.TextField(
                label=label_name,
                keyboard_type=ft.KeyboardType.NUMBER if label_name in ["Account Limit", "Amount of Liability", "Margin Kept"] else ft.KeyboardType.TEXT,
                **base_field_style
            )

    # --- 3. ATTACH EVENT HANDLERS EXPLICITLY ---
    input_fields["Cont. Liability Type"].on_select = calculate_non_funded_ac
    input_fields["Amount of Liability"].on_change = calculate_non_funded_ac
    input_fields["Margin Kept"].on_change = calculate_non_funded_ac

    input_fields["Customer Number"].on_change = autofill_customer_name
    input_fields["Account Number"].on_change = check_duplicate_ac

    # Grid Construction
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
        input_fields["Cont. Liability Type"].value = str(data.get("cont_type") or "")
        input_fields["Account Limit"].value = f"{float(data.get('ac_limit', 0)):.2f}"
        input_fields["Amount of Liability"].value = f"{float(data.get('amt_liability', 0)):.2f}"
        input_fields["Overdue Period in Days"].value = str(data.get("overdue_days", 0))
        input_fields["Margin Kept"].value = f"{float(data.get('margin_kept', 0)):.2f}"
        input_fields["CCF"].value = str(data.get("ccf", "0.00"))
        input_fields["EAD"].value = f"{float(data.get('ead', 0)):.2f}"
        input_fields["Staging by DPD"].value = str(data.get("staging_by_dpd") or "Stage-1")
        input_fields["SICR/Impairment"].value = str(data.get("sicr_impairment") or "None")
        input_fields["SICR/Impairment Reason"].value = str(data.get("qj_reason") or "")

        if data.get("issue_date"):
            nf_issue_datepicker.set_date_from_string(data["issue_date"])
        if data.get("exp_date"):
            nf_exp_datepicker.set_date_from_string(data["exp_date"])

        calculate_non_funded_ac()
        update_qj_stage()

    def clear_form_fields():
        for k, tf in input_fields.items():
            if k == "Reporting Date":
                continue
            elif isinstance(tf, CustomDatePicker):
                tf.clear()
            elif k in ["Overdue Period in Days", "CCF", "EAD"]:
                tf.value = "0" if k == "Overdue Period in Days" else "0.00"
            elif k == "Staging by DPD":
                tf.value = "Stage-1"
            elif k == "QJ Stage":
                tf.value = "Stage-1"
            elif k == "SICR/Impairment Reason":
                tf.value = ""
            elif k == "SICR/Impairment":
                tf.value = "None"
            else:
                tf.value = ""
        calculate_non_funded_ac()
        update_qj_stage()

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
                ft.DataCell(ft.Text(str(c_data.get("cont_type", "")), color="white", size=11)),
                ft.DataCell(ft.Text(str(c_data.get("ead", "0.00")), color="white", size=11)),
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
                ft.DataColumn(ft.Text("Exposure At Default (EAD)", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("DPD Stage", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("QJ Stage", color="white", weight="bold", size=11)),
                ft.DataColumn(ft.Text("Actions", color="white", weight="bold", size=11)),
            ],
            border=ft.Border.all(0.5, "#1e534b"),
            heading_row_color="#0c3832",
            heading_row_height=36,
            data_row_min_height=34,
            column_spacing=12,
            rows=rows
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
        fetched = get_all_non_funded_ac_profiles() or {}
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

        calculate_non_funded_ac()
        update_qj_stage()

        payload = {
            "ac_num": ac_num,
            "reporting_date": last_month_end.strftime("%Y-%m-%d"),
            "cust_num": input_fields["Customer Number"].value.strip() if input_fields["Customer Number"].value else "",
            "cust_name": input_fields["Customer Name"].value.strip() if input_fields["Customer Name"].value else "",
            "cont_type": input_fields["Cont. Liability Type"].value or "",
            "ac_limit": parse_flt(input_fields["Account Limit"].value),
            "amt_liability": parse_flt(input_fields["Amount of Liability"].value),
            "issue_date": nf_issue_datepicker.value.date().strftime("%Y-%m-%d") if getattr(nf_issue_datepicker, "value", None) else None,
            "exp_date": nf_exp_datepicker.value.date().strftime("%Y-%m-%d") if getattr(nf_exp_datepicker, "value", None) else None,
            "overdue_days": parse_int(input_fields["Overdue Period in Days"].value),
            "margin_kept": parse_flt(input_fields["Margin Kept"].value),
            "ccf": input_fields["CCF"].value or "0.00",
            "ead": parse_flt(input_fields["EAD"].value),
            "staging_by_dpd": input_fields["Staging by DPD"].value or "Stage-1",
            "sicr_impairment": input_fields["SICR/Impairment"].value or "None",
            "qj_stage": input_fields["QJ Stage"].value or "",
            "qj_reason": input_fields["SICR/Impairment Reason"].value.strip() if input_fields["SICR/Impairment Reason"].value else ""
        }

        try:
            save_non_funded_ac_profile(payload)
            refresh_cache()
            clear_form_fields()
            render_history_table(grid_search_tf.value or "")
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Non-Funded A/C {ac_num} saved successfully!"), bgcolor="#00e676", open=True))
        except Exception as err:
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Error saving record: {str(err)}"), bgcolor="red", open=True))
        page.update()

    def execute_delete(ac_num):
        if not ac_num: return
        try:
            delete_non_funded_ac_profile_by_id(ac_num)
            refresh_cache()
            clear_form_fields()
            render_history_table(grid_search_tf.value or "")
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Non-Funded A/C {ac_num} deleted successfully!"), bgcolor="#ff5252", open=True))
        except Exception as err:
            page.overlay.append(ft.SnackBar(content=ft.Text(f"Error deleting: {str(err)}"), bgcolor="red", open=True))
        page.update()

    add_btn = ft.ElevatedButton(
        content=ft.Text("Add / Edit Non-Funded A/C", color="black", weight="bold", size=14),
        on_click=on_save_click,
        style=ft.ButtonStyle(bgcolor="#78eb64", shape=ft.RoundedRectangleBorder(radius=20)),
        height=42, width=240
    )

    input_form_card = ft.Container(
        content=ft.Column([
            ft.Container(content=ft.Text("Non-Funded Account Profile Entry", size=20, weight="bold", color="#00e676"), alignment=ft.Alignment(0, 0), padding=ft.Padding(0, 0, 0, 15)),
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