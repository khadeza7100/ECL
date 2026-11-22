import math

import flet as ft

from components.economic_variable_data import (
    ECONOMIC_VARIABLES,
    read_complete_economic_observations,
)
from components.ev_validation_ui import get_recalculate_button
from database import get_all_economic_variables


HIGH_CORRELATION_THRESHOLD = 0.8


def _pearson_correlation(left_values, right_values):
    if len(left_values) != len(right_values) or len(left_values) < 2:
        return None

    left_mean = sum(left_values) / len(left_values)
    right_mean = sum(right_values) / len(right_values)
    left_centered = [value - left_mean for value in left_values]
    right_centered = [value - right_mean for value in right_values]
    left_sum_squares = sum(value * value for value in left_centered)
    right_sum_squares = sum(value * value for value in right_centered)
    if left_sum_squares <= 1e-24 or right_sum_squares <= 1e-24:
        return None

    covariance_sum = sum(
        left * right for left, right in zip(left_centered, right_centered)
    )
    correlation = covariance_sum / math.sqrt(left_sum_squares * right_sum_squares)
    return min(1.0, max(-1.0, correlation))


def get_multicollinearity_form(page: ft.Page, on_recalculate=None, recalculation_state=None):
    economic_data = get_all_economic_variables() or {}
    years, values_by_year = read_complete_economic_observations(economic_data)
    observations_by_variable = {
        variable: [
            values_by_year[year][index]
            for year in years
        ]
        for index, variable in enumerate(ECONOMIC_VARIABLES)
    }

    correlation_matrix = {}
    high_correlation_pairs = []
    valid_pair_count = 0
    for row_index, row_variable in enumerate(ECONOMIC_VARIABLES):
        correlation_matrix[row_variable] = {}
        for column_index, column_variable in enumerate(ECONOMIC_VARIABLES):
            if row_index == column_index:
                correlation = 1.0 if len(years) >= 2 else None
            else:
                correlation = _pearson_correlation(
                    observations_by_variable[row_variable],
                    observations_by_variable[column_variable],
                )
            correlation_matrix[row_variable][column_variable] = correlation
            if column_index > row_index and correlation is not None:
                valid_pair_count += 1
            if (
                column_index > row_index
                and correlation is not None
                and abs(correlation) >= HIGH_CORRELATION_THRESHOLD
            ):
                high_correlation_pairs.append(
                    (row_variable, column_variable, correlation)
                )

    matrix_rows = []
    for row_variable in ECONOMIC_VARIABLES:
        cells = [ft.DataCell(ft.Text(row_variable, color="white", size=11))]
        for column_variable in ECONOMIC_VARIABLES:
            correlation = correlation_matrix[row_variable][column_variable]
            if correlation is None:
                text = "N/A"
                color = "#ffcc80"
            else:
                text = f"{correlation:.3f}"
                if row_variable == column_variable:
                    color = "#78eb64"
                else:
                    magnitude = abs(correlation)
                    color = "#ff8a80" if magnitude >= HIGH_CORRELATION_THRESHOLD else "white"
            cells.append(ft.DataCell(ft.Text(text, color=color, size=11)))
        matrix_rows.append(ft.DataRow(cells=cells))

    if len(years) < 2:
        high_correlation_text = "Not available: at least two complete years are required."
        high_correlation_color = "#ffcc80"
    elif high_correlation_pairs:
        high_correlation_text = "; ".join(
            f"{left} / {right}: {correlation:.3f}"
            for left, right, correlation in high_correlation_pairs
        )
        high_correlation_color = "#ff8a80"
    elif valid_pair_count == 0:
        high_correlation_text = "No valid pairwise correlations could be calculated."
        high_correlation_color = "#ffcc80"
    else:
        high_correlation_text = "No variable pairs met the |r| >= 0.80 screening threshold."
        high_correlation_color = "#78eb64"

    complete_years_text = ", ".join(years) if years else "none"
    note = (
        "Pairwise Pearson correlations use years with complete values for all eight "
        f"economic variables. Complete years: {complete_years_text}. "
        "Absolute correlation |r| >= 0.80 is flagged as a screening indicator; "
        "correlation alone does not rule out other forms of multicollinearity."
    )

    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Text("Multicollinearity", size=20, weight="bold", color="#00e676"),
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
                            width=1350,
                            columns=[
                                ft.DataColumn(ft.Text("Economic Variable", color="white", weight="bold", size=11)),
                                *[
                                    ft.DataColumn(ft.Text(variable, color="white", weight="bold", size=10))
                                    for variable in ECONOMIC_VARIABLES
                                ],
                            ],
                            rows=matrix_rows,
                            border=ft.Border.all(0.5, "#1e534b"),
                            heading_row_color="#0c3832",
                            heading_row_height=48,
                            data_row_min_height=36,
                            column_spacing=12,
                        )
                    ], scroll=ft.ScrollMode.AUTO),
                    ft.Container(height=8),
                    ft.Text(
                        f"High-correlation pairs (|r| >= {HIGH_CORRELATION_THRESHOLD:.2f}): "
                        f"{high_correlation_text}",
                        color=high_correlation_color,
                        size=12,
                        weight="bold",
                    ),
                    ft.Text(
                        f"Complete annual observations: {len(years)}",
                        color="white70",
                        size=11,
                    ),
                ]),
                padding=15,
                border=ft.Border.all(width=1, color="#00e676"),
                border_radius=8,
                bgcolor="#061d19",
            ),
        ], scroll=ft.ScrollMode.AUTO, expand=True),
        expand=True,
    )
