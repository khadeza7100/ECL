import flet as ft

def get_left_sidebar(page, all_submenu_controls, handle_submenu_click, return_to_home_view, get_form_action):
    menu_sections = []

    def on_menu_section_change(e):
        if e.control.expanded:
            for section in menu_sections:
                if section is not e.control:
                    section.expanded = False
        page.update()

    # Submenu item creation logic
    def create_sub_item(key, text, ui_action=None):
        # Give every submenu item a useful default action when no custom
        # callback is supplied.
        if ui_action is None:
            ui_action = lambda e: get_form_action(key)

        text_control = ft.Text(f"  └─ {text}", size=12, color="white70")
        all_submenu_controls[key] = text_control 
        return ft.Container(
            content=text_control, 
            padding=ft.Padding(15, 5, 5, 5), 
            on_click=lambda e: handle_submenu_click(key, ui_action), 
            border_radius=4, 
            ink=True
        )

    # Menu section widget generator
    def create_menu_section(title, sub_items, color):
        section = ft.ExpansionTile(
            title=ft.Text(title, size=13, weight="bold", color=color), 
            controls=sub_items, 
            collapsed_text_color=color, 
            text_color="white", 
            dense=True, 
            expanded=False,
            on_change=on_menu_section_change,
        )
        menu_sections.append(section)
        return section

    # Left sidebar item structure
    left_sidebar_items = ft.Column([
        create_menu_section("Customer Profile", [
            create_sub_item("corporate", "Corporate Profile", lambda e: get_form_action("corporate")),
            create_sub_item("individual", "Individual Profile", lambda e: get_form_action("individual")), 
            create_sub_item("collateral", "Collateral Profile", lambda e: get_form_action("collateral")), 
            create_sub_item("credit_ratings", "Credit Rating Profile", lambda e: get_form_action("credit_ratings")),
            create_sub_item("funded_ac", "Funded A/C Profile", lambda e: get_form_action("funded_ac")), 
            create_sub_item("non_funded_ac", "Non-Funded A/C Profile", lambda e: get_form_action("non_funded_ac"))              
        ], "#00e676"),

        create_menu_section("Upload CSV", [
            create_sub_item("upload_corporate", "Corporate Profile", lambda e: get_form_action("upload_corporate")),
            create_sub_item("upload_individual", "Individual Profile", lambda e: get_form_action("upload_individual")),
            create_sub_item("upload_collateral", "Collateral Profile", lambda e: get_form_action("upload_collateral")),
            create_sub_item("upload_credit_ratings", "Credit Rating Profile", lambda e: get_form_action("upload_credit_ratings")),
            create_sub_item("upload_funded_ac", "Funded A/C Profile", lambda e: get_form_action("upload_funded_ac")),
            create_sub_item("upload_non_funded_ac", "Non-Funded A/C Profile", lambda e: get_form_action("upload_non_funded_ac")),
        ], "#1de9b6"),

        create_menu_section("Global Settings", [
            create_sub_item("proxy_data_model", "Proxy Data & Model Selection", lambda e: get_form_action("proxy_data_model")),
            create_sub_item("economic_variables", "Economic Variables", lambda e: get_form_action("economic_variables")),
            create_sub_item("haircut", "Collateral Haircut", lambda e: get_form_action("haircut")),
            create_sub_item("ccf", "Credit Conversion Factor", lambda e: get_form_action("ccf")),
            create_sub_item("discounting_factor", "Discounting Factor", lambda e: get_form_action("discounting_factor")),
            create_sub_item("loan_staging_criteria", "Loan Staging Criteria",lambda e: get_form_action("loan_staging_criteria")), 
            create_sub_item("calc_smr", "Stage Migration Rate", lambda e: get_form_action("calc_smr")),
            
        ], "#a7ffeb"),

        create_menu_section("Expected Credit Loss", [
            create_sub_item("calc_pd", "Calculate PD"),
            create_sub_item("calc_lgd", "Calculate LGD"),
            create_sub_item("calc_ead", "Calculate EAD"),
            create_sub_item("calc_ecl", "Calculate ECL")
        ], "#1de9b6"),
    ], scroll=ft.ScrollMode.ALWAYS, expand=True)

    # Full Left Sidebar Container
    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Row([ft.Text("📊", size=16), ft.Text("ECL Navigation", size=15, weight="bold", color="white")]), 
                on_click=return_to_home_view, 
                ink=True, 
                padding=4
            ), 
            left_sidebar_items
        ]),
        bgcolor="#0a2e27", 
        padding=12, 
        border_radius=8, 
        width=260, 
        height=710, 
        border=ft.Border.all(width=1, color="#0a2e27")
    )