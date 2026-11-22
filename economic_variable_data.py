import math


ECONOMIC_VARIABLES = (
    "Exchange Rate",
    "Inflation",
    "GDP Growth",
    "Un Employment Rate",
    "Deposit Rate",
    "Loan Rate",
    "Bank Rate",
    "Call Money Rate",
)


def read_complete_economic_observations(economic_data):
    years = []
    values_by_year = {}

    for year, row in economic_data.items():
        try:
            values = [float(row.get(variable, "")) for variable in ECONOMIC_VARIABLES]
        except (TypeError, ValueError):
            continue
        if not all(math.isfinite(value) for value in values):
            continue
        normalized_year = str(year).strip()
        if not normalized_year:
            continue
        years.append(normalized_year)
        values_by_year[normalized_year] = values

    years.sort()
    return years, values_by_year
