import flet as ft

from components.ev_validation_ui import get_recalculate_button
from components.pd_regression import (
    EV_PREDICTORS,
    build_pd_regression_models,
)
from database import get_all_economic_variables, get_all_stage_migration_rates


def get_p_value_form(page: ft.Page, on_recalculate=None, recalculation_state=None):
    economic_data = get_all_economic_variables() or {}
    migration_data = get_all_stage_migration_rates() or []
    matched_years, regressions = build_pd_regression_models(
        economic_data,
        migration_data,
    )
    rows = []
    result_count = 0

    for regression in regressions:
        facility_type = regression["facility_type"]
        pd_stage = regression["pd_stage"]
        matched_count = len(regression["years"])
        model = regression["model"]

        if model is None:
            reason = "Insufficient data or collinear predictors"
            for variable in EV_PREDICTORS:
                rows.append(ft.DataRow(cells=[
                    ft.DataCell(ft.Text(facility_type, color="white", size=11)),
                    ft.DataCell(ft.Text(pd_stage, color="white", size=11)),
                    ft.DataCell(ft.Text(variable, color="white", size=11)),
                    ft.DataCell(ft.Text("-", color="white70", size=11)),
                    ft.DataCell(ft.Text("-", color="white70", size=11)),
                    ft.DataCell(ft.Text("N/A", color="#ffcc80", size=11)),
                    ft.DataCell(ft.Text(str(matched_count), color="white", size=11)),
                    ft.DataCell(ft.Text("-", color="white70", size=11)),
                    ft.DataCell(ft.Text(reason, color="#ffcc80", size=11)),
                ]))
            continue

        result_count += len(model["results"])
        for result in model["results"]:
            p_value = result["p_value"]
            p_value_text = (
                "<0.000001" if p_value < 0.000001 else f"{p_value:.6f}"
            )
            rows.append(ft.DataRow(cells=[
                ft.DataCell(ft.Text(facility_type, color="white", size=11)),
                ft.DataCell(ft.Text(pd_stage, color="white", size=11)),
                ft.DataCell(ft.Text(result["variable"], color="white", size=11)),
                ft.DataCell(ft.Text(f"{result['coefficient']:.4f}", color="white", size=11)),
                ft.DataCell(ft.Text(f"{result['t_statistic']:.4f}", color="white", size=11)),
                ft.DataCell(ft.Text(p_value_text, color="#78eb64", weight="bold", size=11)),
                ft.DataCell(ft.Text(str(matched_count), color="white", size=11)),
                ft.DataCell(ft.Text(str(model["degrees_of_freedom"]), color="white", size=11)),
                ft.DataCell(ft.Text(
                    "Significant" if p_value < 0.05 else "Not significant",
                    color="#78eb64" if p_value < 0.05 else "white70",
                    size=11
                )),
            ]))

    if not rows:
        rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text("No year-matched EV and PD observations found.", color="white70", italic=True, size=12)),
            *[ft.DataCell(ft.Text("", size=11)) for _ in range(8)]
        ]))

    warning_text = (
        f"Year-matched observations: {len(matched_years)} year(s)"
        f"{' (' + ', '.join(matched_years) + ')' if matched_years else ''}. "
        "Each facility type and PD stage is fit separately using GDP Growth, Loan Rate, "
        "and Inflation. P-values are two-sided t-tests for the regression coefficients; "
        "interpret cautiously with the small annual sample."
    )
    if result_count == 0 and matched_years:
        warning_text += " Models with insufficient observations or collinear predictors are marked N/A."

    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text("P-Value", size=20, weight="bold", color="#00e676"),
                alignment=ft.Alignment(0, 0),
                padding=ft.Padding(0, 0, 0, 10),
            ),
            ft.Container(
                content=ft.Column([
                    get_recalculate_button(page, on_recalculate, recalculation_state),
                    ft.Text(warning_text, color="white70", size=12),
                    ft.Container(height=8),
                    ft.Row([
                        ft.DataTable(
                            width=1000,
                            columns=[
                                ft.DataColumn(ft.Text("Facility Type", color="white", weight="bold", size=11)),
                                ft.DataColumn(ft.Text("PD Stage", color="white", weight="bold", size=11)),
                                ft.DataColumn(ft.Text("EV Predictor", color="white", weight="bold", size=11)),
                                ft.DataColumn(ft.Text("Std. Coefficient", color="white", weight="bold", size=11)),
                                ft.DataColumn(ft.Text("t-statistic", color="white", weight="bold", size=11)),
                                ft.DataColumn(ft.Text("P-Value", color="white", weight="bold", size=11)),
                                ft.DataColumn(ft.Text("N", color="white", weight="bold", size=11)),
                                ft.DataColumn(ft.Text("Residual df", color="white", weight="bold", size=11)),
                                ft.DataColumn(ft.Text("alpha=0.05", color="white", weight="bold", size=11)),
                            ],
                            rows=rows,
                            border=ft.Border.all(0.5, "#1e534b"),
                            heading_row_color="#0c3832",
                            heading_row_height=40,
                            data_row_min_height=36,
                            column_spacing=15,
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
