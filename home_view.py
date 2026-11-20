import flet as ft

def get_home_view():
    dashboard_chart_height = 210

    # ক্যালকুলেশন বক্স জেনারেটর
    def create_calc_box(text, bg_color, description):
        return ft.Container(
            content=ft.Text(text, size=14, weight="bold", color="white", text_align="center"),
            bgcolor=bg_color,
            width=85,
            height=50,
            border_radius=30,
            alignment=ft.Alignment(0, 0),
            tooltip=ft.Tooltip(
                message=f"{text}\n{description}",
                trigger_mode=ft.TooltipTriggerMode.TAP,
                bgcolor=bg_color,
                text_style=ft.TextStyle(color="white", size=12),
                text_align=ft.TextAlign.START,
                padding=ft.Padding(14, 12, 14, 12),
                size_constraints=ft.BoxConstraints(min_width=280, max_width=360),
                prefer_below=False,
            ),
        )
        
    home_view_layout = ft.Column([
        ft.Row([
            create_calc_box(
                "PD",
                "#00bfa5",
                "Probability of Default. Calculated using the rolling-rate / stage-migration method.",
            ),
            ft.Text("➔", size=16, color="#00e676", weight="bold"),
            create_calc_box(
                "APD",
                "#14b8a6",
                "Adjusted PD. PD adjusted for microeconomic variables using a multiple linear regression method.",
            ),
            ft.Text("➔", size=16, color="#00e676", weight="bold"),
            create_calc_box(
                "LGD",
                "#0f766e",
                "Loss Given Default. Collateral values are discounted.",
            ),
            ft.Text("➔", size=16, color="#00e676", weight="bold"),
            create_calc_box(
                "EAD",
                "#15803d",
                "Exposure at Default. Outstanding balance plus accrued (calculated) interest, with credit conversion factors considered.",
            ),
            ft.Text("➔", size=16, color="#00e676", weight="bold"),
            create_calc_box("ECL", "#00e676", "Expected Credit Loss."),
        ], alignment="center", spacing=8)
    ], alignment="center")

    # ড্যাশবোর্ড বার-চার্ট জেনারেটর
    def create_dashboard_bar(label, value, color_hex, max_val=50, chart_height=100, font_size=7):
        bar_height = max(4, (value / max_val) * chart_height)
        return ft.Container(
            content=ft.Column([
                ft.Text(str(value), size=font_size, color="white70", weight="bold"),
                ft.Container(height=bar_height, bgcolor=color_hex, border_radius=3),
                ft.Text(label, size=font_size, color="white60", weight="bold", no_wrap=True)
            ], horizontal_alignment="center", spacing=2, alignment="end"),
            margin=ft.Margin(7, 0, 7, 0),
            expand=True
        )

    # সাইজ অনুযায়ী বার-চার্ট
    bar_chart_size = ft.Container(
        content=ft.Column([
            ft.Row([
                create_dashboard_bar("Cot", 25, "#a855f7", max_val=30, chart_height=110), 
                create_dashboard_bar("Mic", 20, "#3b82f6", max_val=30, chart_height=110),
                create_dashboard_bar("Sml", 18, "#ef4444", max_val=30, chart_height=110), 
                create_dashboard_bar("Med", 15, "#84cc16", max_val=30, chart_height=110),
                create_dashboard_bar("Lrg", 18, "#ef4444", max_val=30, chart_height=110), 
                create_dashboard_bar("Ind", 12, "#00e676", max_val=30, chart_height=110),
                create_dashboard_bar("Agr", 9, "#3b82f6", max_val=30, chart_height=110), 
                create_dashboard_bar("Stf", 10, "#a7ffeb", max_val=30, chart_height=110),
            ], alignment="spaceEvenly", vertical_alignment="end", spacing=2, expand=True),
            ft.Container(height=8),
            ft.Text("Loan Distribution by Size", size=13, weight="bold", color="white70", text_align="center"),
        ], horizontal_alignment="center"),
        bgcolor="#0a2e27", padding=12, border_radius=14, width=320, height=dashboard_chart_height, border=ft.Border.all(width=1, color="#144d41")
    )

    # টাইপ অনুযায়ী বার-চার্ট
    bar_chart_type = ft.Container(
        content=ft.Column([
            ft.Row([
                create_dashboard_bar("Cont", 45, "#3b82f6", max_val=50, chart_height=110), 
                create_dashboard_bar("Dmd", 30, "#ef4444", max_val=50, chart_height=110),
                create_dashboard_bar("Term", 25, "#84cc16", max_val=50, chart_height=110), 
                create_dashboard_bar("BG", 10, "#f59e0b", max_val=50, chart_height=110),
                create_dashboard_bar("LC", 15, "#a855f7", max_val=50, chart_height=110),
            ], alignment="spaceEvenly", vertical_alignment="end", spacing=4, expand=True),
            ft.Container(height=8),
            ft.Text("Loan Distribution by Type", size=13, weight="bold", color="white70", text_align="center"),
        ], horizontal_alignment="center"),
        bgcolor="#0a2e27", padding=12, border_radius=14, width=320, height=dashboard_chart_height, border=ft.Border.all(width=1, color="#144d41")
    )

    # সেক্টর অনুযায়ী ডাটা ও বার-চার্ট
    sector_data = [
        ("Garments", 45, "#00e676"), ("Food", 30, "#3b82f6"), ("Jute", 15, "#84cc16"),
        ("NGO", 12, "#f59e0b"), ("Govt", 25, "#a855f7"), ("NBFI", 20, "#ef4444"),
        ("Agri", 18, "#00bfa5"), ("Shipping", 14, "#3b82f6"), ("Chemical", 22, "#a855f7"),
        ("Pharma", 35, "#84cc16"), ("Cement", 28, "#f59e0b"), ("Engr", 19, "#ef4444"),
        ("Fuel", 40, "#00e676"), ("ICT", 26, "#3b82f6"), ("Paper", 10, "#a7ffeb"),
        ("Real Est", 32, "#f59e0b"), ("Tannery", 8, "#ef4444"), ("Hotel", 16, "#84cc16")
    ]

    sector_bars = [
        create_dashboard_bar(label, val, col, max_val=50, chart_height=75, font_size=7) 
        for label, val, col in sector_data
    ]

    bar_chart_sector = ft.Container(
        content=ft.Column([
            ft.Row(sector_bars, alignment="spaceEvenly", vertical_alignment="end", spacing=1, expand=True),
            ft.Container(height=4),
            ft.Text("Loan Distribution by Sector", size=13, weight="bold", color="white70", text_align="center"),
        ], horizontal_alignment="center", spacing=2),
        bgcolor="#0a2e27", padding=ft.Padding(12, 8, 12, 8), border_radius=14, width=660, height=dashboard_chart_height, border=ft.Border.all(width=1, color="#144d41")
    )

    def create_mid_chart_bar(label, value, color_hex, max_val=100, chart_height=90):
        bar_height = max(4, (value / max_val) * chart_height)
        return ft.Column([
            ft.Text(str(value), size=8, color="white70", weight="bold"),
            ft.Container(width=20, height=bar_height, bgcolor=color_hex, border_radius=4),
            ft.Text(label, size=8, color="white60", weight="bold", no_wrap=True)
        ], horizontal_alignment="center", spacing=3, alignment="end")

    loan_stages_chart = ft.Container(
        content=ft.Column([
            ft.Row([
                create_mid_chart_bar("S1", 65, "#00e676", max_val=100),
                create_mid_chart_bar("S2", 25, "#e0dd1f", max_val=100),
                create_mid_chart_bar("S3", 10, "#ea490a", max_val=100),
                create_mid_chart_bar("Total", 100, "#136a7b", max_val=100),
                create_mid_chart_bar("ECL", 15, "#6c5074", max_val=100),
            ], alignment="spaceEvenly", vertical_alignment="end", spacing=4, expand=True),
            ft.Container(height=6),
            ft.Text("Loan Stages & ECL", size=13, weight="bold", color="white70", text_align="center"),
        ], horizontal_alignment="center"),
        bgcolor="#0a2e27",
        padding=12,
        border_radius=14,
        width=320,
        height=dashboard_chart_height,
        border=ft.Border.all(width=1, color="#144d41")
    )

    loan_stage_shifting_chart = ft.Container(
        content=ft.Column([
            ft.Row([
                create_mid_chart_bar("S1-S2", 4, "#9e4b77", max_val=10),
                create_mid_chart_bar("S1-S3", 6, "#f75f5f", max_val=10),
                create_mid_chart_bar("S2-S3", 2, "#f30c0c", max_val=10),
                create_mid_chart_bar("S3-S2", 4, "#1de9b6", max_val=10),
                create_mid_chart_bar("S3-S1", 2, "#2add24", max_val=10),
                create_mid_chart_bar("S2-S1", 6, "#0bfe07", max_val=10),
            ], alignment="spaceEvenly", vertical_alignment="end", spacing=2, expand=True),
            ft.Container(height=6),
            ft.Text("Loan Stage Shifting", size=13, weight="bold", color="white70", text_align="center"),
        ], horizontal_alignment="center"),
        bgcolor="#0a2e27",
        padding=12,
        border_radius=14,
        width=320,
        height=dashboard_chart_height,
        border=ft.Border.all(width=1, color="#144d41")
    )

    # চার্ট লেআউট
    charts_blank_area = ft.Column([
        ft.Row([bar_chart_size, bar_chart_type], alignment="center", spacing=20),
        ft.Row([loan_stages_chart, loan_stage_shifting_chart], alignment="center", spacing=20),
        bar_chart_sector
    ], horizontal_alignment="center", spacing=15)

    return home_view_layout, charts_blank_area