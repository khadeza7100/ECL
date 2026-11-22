import math

from components.pd_calculations import get_yearly_net_migration_rates
from components.regression import fit_multiple_regression


EV_PREDICTORS = ("GDP Growth", "Loan Rate", "Inflation")
PD_STAGE_NET_RATES = {
    "Stage-1": "Stage-2",
    "Stage-2": "Stage-3",
}


def _parse_predictor_values(year_data):
    values = []
    for variable in EV_PREDICTORS:
        raw_value = year_data.get(variable)
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            return None
        if not math.isfinite(value):
            return None
        values.append(value)
    return values


def build_pd_regression_models(economic_data, migration_data):
    yearly_net_rates = get_yearly_net_migration_rates(migration_data)
    ev_by_year = {
        str(year).strip(): _parse_predictor_values(values)
        for year, values in economic_data.items()
    }
    pd_by_facility = {}
    for (year, facility_type, stage), net_rate in yearly_net_rates.items():
        if stage in PD_STAGE_NET_RATES.values():
            pd_by_facility.setdefault(facility_type, {})[(year, stage)] = net_rate

    facility_types = sorted(
        pd_by_facility,
        key=lambda facility: (
            facility == "Unspecified",
            facility.lower()
        )
    )
    matched_years = set()
    regressions = []

    for facility_type in facility_types:
        for pd_stage, net_rate_stage in PD_STAGE_NET_RATES.items():
            matched = []
            facility_pd = pd_by_facility[facility_type]
            for year, predictor_values in ev_by_year.items():
                pd_rate = facility_pd.get((year, net_rate_stage))
                if predictor_values is None or pd_rate is None:
                    continue
                matched.append((year, predictor_values, pd_rate))

            matched.sort(key=lambda item: item[0])
            matched_years.update(year for year, _, _ in matched)
            observations = [
                {
                    "year": year,
                    "predictors": predictors,
                    "historical_pd": pd_rate,
                }
                for year, predictors, pd_rate in matched
            ]
            model = fit_multiple_regression(
                EV_PREDICTORS,
                [predictors for _, predictors, _ in matched],
                [pd_rate for _, _, pd_rate in matched],
            )
            regressions.append({
                "facility_type": facility_type,
                "pd_stage": pd_stage,
                "years": [year for year, _, _ in matched],
                "observations": observations,
                "model": model,
            })

    return sorted(matched_years), regressions
