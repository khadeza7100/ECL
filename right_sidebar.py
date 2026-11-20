import flet as ft

def get_right_sidebar(page, all_submenu_controls, handle_submenu_click, return_to_home_view):
    menu_sections = []

    def on_menu_section_change(e):
        if e.control.expanded:
            for section in menu_sections:
                if section is not e.control:
                    section.expanded = False
        page.update()

    # Submenu item helper
    def create_sub_item(text, ui_action=None):
        text_control = ft.Text(f"  └─ {text}", size=12, color="white70")
        all_submenu_controls[text] = text_control 
        return ft.Container(
            content=text_control, 
            padding=ft.Padding(15, 5, 5, 5), 
            on_click=lambda e: handle_submenu_click(text, ui_action), 
            border_radius=4, 
            ink=True
        )

    # Menu section generator
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

    right_sidebar_box_items = ft.Column([
        create_menu_section("ECL Reports", [
            create_sub_item("Stage-1-Accounts"), 
            create_sub_item("Stage-2-Accounts"), 
            create_sub_item("Stage-3-Accounts")
        ], "#1de9b6"),
        create_menu_section("Testing & Validation", [
            create_sub_item("Back Testing"), 
            create_sub_item("Stress Testing")
        ], "#00bfa5"),
        create_menu_section("Parameters & Logs", [
            create_sub_item("PD by Category"), 
            create_sub_item("Haircut by Type")
        ], "#00e676")
    ], scroll=ft.ScrollMode.ALWAYS, expand=True)

    # Full Right Sidebar Layout
    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Row([ft.Text("📋", size=16), ft.Text("Reports & Testing", size=15, weight="bold", color="white")]), 
                on_click=return_to_home_view, 
                ink=True, 
                padding=4
            ), 
            right_sidebar_box_items
        ]),
        bgcolor="#0a2e27", 
        padding=12, 
        border_radius=8, 
        width=260, 
        height=710, 
        border=ft.Border.all(width=1, color="#0a2e27")
    )