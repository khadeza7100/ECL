import flet as ft

from components.ev_validation_ui import get_recalculate_button
from components.pd_regression import (
    EV_PREDICTORS,
    build_pd_regression_models,
)
from database import get_all_economic_variables, get_all_stage_migration_rates


def get_r_squared_form(page: ft.Page, on_recalculate=None, recalculation_state=None):
    economic_data = get_all_economic_variables() or {}
    migration_data = get_all_stage_migration_rates() or []
    matched_years, regressions = build_pd_regression_models(
        economic_data,
        migration_data,
    )

    rows = []
    for regression in regressions:
        model = regression["model"]
        if model is None:
            r_squared_text = "N/A"
            variance_text = "N/A"
            degrees_of_freedom_text = "N/A"
            color = "#ffcc80"
        else:
            r_squared = model["r_squared"]
            degrees_of_freedom_text = str(model["degrees_of_freedom"])
            if r_squared is None:
                r_squared_text = "N/A"
                variance_text = "N/A"
                color = "#ffcc80"
            else:
                r_squared_text = f"{r_squared:.4f}"
                variance_text = f"{r_squared * 100:.2f}%"
                color = "#78eb64"

        rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(regression["facility_type"], color="white", size=11)),
            ft.DataCell(ft.Text(regression["pd_stage"], color="white", size=11)),
            ft.DataCell(ft.Text(r_squared_text, color=color, weight="bold", size=11)),
            ft.DataCell(ft.Text(variance_text, color=color, size=11)),
            ft.DataCell(ft.Text(str(len(regression["years"])), color="white", size=11)),
            ft.DataCell(ft.Text(degrees_of_freedom_text, color="white", size=11)),
        ]))

    if not rows:
        rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text("No year-matched EV and PD observations found.", color="white70", italic=True, size=12)),
            *[ft.DataCell(ft.Text("", size=11)) for _ in range(5)]
        ]))

    note = (
        "R² = 1 - SSE/SST, where SSE is the regression residual sum of squares "
        "and SST is the total sum of squares around the mean PD. Each facility "
        "type and PD stage uses a separate multiple regression with "
        f"{', '.join(EV_PREDICTORS)}. Matched years: "
        f"{', '.join(matched_years) if matched_years else 'none'}. "
        "R² describes in-sample fit, not causation or out-of-sample predictive accuracy; "
        "the limited annual sample warrants caution. N/A means insufficient data, "
        "collinear predictors, or no variation in PD."
    )

    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text("R-Squared", size=20, weight="bold", color="#00e676"),
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding(0, 0, 0, 10),
            ),
            ft.Container(
                content=ft.Column([
                    get_recalculate_button(page, on_recalculate, recalculation_state),
                    ft.Text(note, color="white70", size=12),
                    ft.Container(height=8),
                    ft.Row([
                        ft.DataTable(
                            width=900,
                            columns=[
                                ft.DataColumn(ft.Text("Facility Type", color="white", weight="bold", size=11)),
                                ft.DataColumn(ft.Text("PD Stage", color="white", weight="bold", size=11)),
                                ft.DataColumn(ft.Text("R-Squared", color="white", weight="bold", size=11)),
                                ft.DataColumn(ft.Text("Variance Explained", color="white", weight="bold", size=11)),
                                ft.DataColumn(ft.Text("N", color="white", weight="bold", size=11)),
                                ft.DataColumn(ft.Text("Residual df", color="white", weight="bold", size=11)),
                            ],
                            rows=rows,
                            border=ft.Border.all(0.5, "#1e534b"),
                            heading_row_color="#0c3832",
                            heading_row_height=40,
                            data_row_min_height=36,
                            column_spacing=12,
                        )
                    ], scroll=ft.ScrollMode.AUTO),
                ]),
                padding=15,
                border=ft.Border.all(width=1, color="#00e676"),
                border_radius=8,
                bgcolor="#061d19",
            ),
        ], scroll=ft.ScrollMode.AUTO, expand=True),
        expand=True,
    )
