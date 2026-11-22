import math

import flet as ft

from components.economic_variable_data import (
    ECONOMIC_VARIABLES,
    read_complete_economic_observations,
)
from components.ev_validation_ui import get_recalculate_button
from components.regression import fit_multiple_regression
from database import get_all_economic_variables


def get_vif_form(page: ft.Page, on_recalculate=None, recalculation_state=None):
    economic_data = get_all_economic_variables() or {}
    years, values_by_year = read_complete_economic_observations(economic_data)
    sample_size = len(years)
    residual_degrees_of_freedom = sample_size - len(ECONOMIC_VARIABLES)
    rows = []

    for target_index, variable in enumerate(ECONOMIC_VARIABLES):
        predictors = [
            predictor
            for index, predictor in enumerate(ECONOMIC_VARIABLES)
            if index != target_index
        ]
        predictor_indices = [
            index for index in range(len(ECONOMIC_VARIABLES))
            if index != target_index
        ]
        predictor_rows = [
            [values_by_year[year][index] for index in predictor_indices]
            for year in years
        ]
        outcomes = [values_by_year[year][target_index] for year in years]
        model = fit_multiple_regression(predictors, predictor_rows, outcomes)

        if model is None or model["r_squared"] is None:
            r_squared_text = "N/A"
            vif_text = "N/A"
            interpretation = "Insufficient data or singular model"
            color = "#ffcc80"
        else:
            r_squared = model["r_squared"]
            remainder = 1.0 - r_squared
            vif = math.inf if remainder <= 1e-12 else 1.0 / remainder
            r_squared_text = f"{r_squared:.4f}"
            vif_text = "Inf" if math.isinf(vif) else f"{vif:.4f}"
            if vif < 5.0:
                interpretation = "Low"
                color = "#78eb64"
            elif vif < 10.0:
                interpretation = "Moderate"
                color = "#ffcc80"
            else:
                interpretation = "High"
                color = "#ff8a80"

        rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(variable, color="white", size=12)),
            ft.DataCell(ft.Text(r_squared_text, color="white", size=12)),
            ft.DataCell(ft.Text(vif_text, color=color, weight="bold", size=12)),
            ft.DataCell(ft.Text(str(sample_size), color="white", size=12)),
            ft.DataCell(ft.Text(str(residual_degrees_of_freedom), color="white", size=12)),
            ft.DataCell(ft.Text(interpretation, color=color, size=12)),
        ]))

    if not rows:
        rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text("No complete annual EV observations found.", color="white70", italic=True, size=12)),
            *[ft.DataCell(ft.Text("", size=12)) for _ in range(5)]
        ]))

    complete_years_text = ", ".join(years) if years else "none"
    note = (
        "VIF = 1 / (1 - R²), where each variable is regressed against the other "
        "seven EVs. Complete years: "
        f"{complete_years_text}. VIF < 5 is low, 5-10 moderate, and >= 10 high "
        "(common screening thresholds). The small sample can make estimates unstable."
    )

    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text("Variance Inflation Factor", size=20, weight="bold", color="#00e676"),
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
                                ft.DataColumn(ft.Text("Economic Variable", color="white", weight="bold", size=12)),
                                ft.DataColumn(ft.Text("Auxiliary R²", color="white", weight="bold", size=12)),
                                ft.DataColumn(ft.Text("VIF", color="white", weight="bold", size=12)),
                                ft.DataColumn(ft.Text("N", color="white", weight="bold", size=12)),
                                ft.DataColumn(ft.Text("Residual df", color="white", weight="bold", size=12)),
                                ft.DataColumn(ft.Text("Collinearity", color="white", weight="bold", size=12)),
                            ],
                            rows=rows,
                            border=ft.Border.all(0.5, "#1e534b"),
                            heading_row_color="#0c3832",
                            heading_row_height=40,
                            data_row_min_height=36,
                            column_spacing=18,
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
