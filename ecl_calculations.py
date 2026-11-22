import math
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from components.pd_regression import (
    EV_PREDICTORS,
    build_pd_regression_models,
)
from components.regression import predict_multiple_regression


_STAGE_RANKS = {
    "stage-1": (1, "Stage-1"),
    "stage-2": (2, "Stage-2"),
    "stage-3": (3, "Stage-3"),
}
_ECL_QUANTUM = Decimal("0.01")


def _account_decimal(value):
    if value is None or str(value).strip() == "":
        return None
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return amount if amount.is_finite() else None


def _sum_account_amounts(accounts, field_name):
    total = Decimal("0")
    for account in accounts:
        amount = _account_decimal(account.get(field_name))
        if amount is not None:
            total += amount
    return total


def _normalize_facility_type(value):
    facility_type = str(value or "").strip().casefold()
    return {
        "demand": "demand loan",
        "continuous": "continuous loan",
        "term": "term loan",
    }.get(facility_type, facility_type)


def _account_stage(account):
    stage_values = [
        str(account.get("staging_by_dpd") or "").strip(),
        str(account.get("qj_stage") or "").strip(),
    ]
    recognized_stages = [
        _STAGE_RANKS[stage.casefold()]
        for stage in stage_values
        if stage.casefold() in _STAGE_RANKS
    ]
    if any(stage and stage.casefold() not in _STAGE_RANKS for stage in stage_values):
        return None
    return max(recognized_stages, default=(1, "Stage-1"))[1]


def _predictors_for_year(economic_data, year):
    year_data = economic_data.get(str(year).strip(), {})
    predictors = []
    for variable in EV_PREDICTORS:
        try:
            value = float(year_data.get(variable))
        except (TypeError, ValueError):
            return None
        if not math.isfinite(value):
            return None
        predictors.append(value)
    return predictors


def _build_adjusted_pd_by_facility(economic_data, migration_data, year):
    matched_years, regressions = build_pd_regression_models(
        economic_data,
        migration_data,
    )
    predictors = _predictors_for_year(economic_data, year)
    adjusted_pd = {}
    models_by_key = {
        (
            _normalize_facility_type(regression["facility_type"]),
            regression["pd_stage"],
        ): regression
        for regression in regressions
    }

    for key, regression in models_by_key.items():
        model = regression["model"]
        prediction = (
            predict_multiple_regression(model, predictors)
            if model is not None and predictors is not None
            else None
        )
        adjusted_pd[key] = (
            min(1.0, max(0.0, prediction))
            if prediction is not None else None
        )

    return adjusted_pd, matched_years, predictors is not None


def build_ecl_calculations(
    funded_accounts,
    non_funded_accounts,
    economic_data,
    migration_data,
    year,
):
    adjusted_pd_by_facility, matched_years, has_current_predictors = (
        _build_adjusted_pd_by_facility(economic_data, migration_data, year)
    )
    rows = []
    total_ecl = Decimal("0")
    calculated_count = 0
    total_funded_outstanding = _sum_account_amounts(funded_accounts, "loan_out")
    total_non_funded_outstanding = _sum_account_amounts(
        non_funded_accounts,
        "amt_liability",
    )

    for account_type, accounts, facility_key in (
        ("Funded", funded_accounts, "nature"),
        ("Non-Funded", non_funded_accounts, "cont_type"),
    ):
        for account in accounts:
            account_number = str(account.get("ac_num") or "").strip()
            facility_type = str(account.get(facility_key) or "").strip()
            stage = _account_stage(account)
            ead = _account_decimal(account.get("ead"))
            lgd = _account_decimal(account.get("lgd"))
            apd = None
            ecl = None

            if stage == "Stage-3":
                apd = 1.0
                status = "Stage-3 APD set to 100%"
            elif stage is None:
                status = "Unrecognized account stage"
            elif not has_current_predictors:
                status = f"Current-year economic variables unavailable for {year}"
            else:
                model_key = (
                    _normalize_facility_type(facility_type),
                    stage,
                )
                if model_key not in adjusted_pd_by_facility:
                    status = f"No APD model for {facility_type or 'unknown facility'} / {stage}"
                else:
                    apd = adjusted_pd_by_facility[model_key]
                    status = (
                        "Calculated"
                        if apd is not None
                        else f"APD model unavailable for {facility_type} / {stage}"
                    )

            if ead is None or ead < 0:
                ecl = None
                status = "Missing or invalid EAD"
            elif lgd is None:
                ecl = None
                status = "Missing or invalid LGD"
            elif apd is not None:
                lgd_value = max(Decimal("0"), lgd)
                ecl = (
                    Decimal(str(apd)) * lgd_value * ead
                ).quantize(_ECL_QUANTUM, rounding=ROUND_HALF_UP)
                total_ecl += ecl
                calculated_count += 1
                if lgd < 0:
                    status = "Calculated; negative LGD treated as 0%"

            rows.append({
                "customer_number": str(account.get("cust_num") or "").strip(),
                "customer_name": str(account.get("cust_name") or "").strip(),
                "account_type": account_type,
                "account_number": account_number,
                "facility_type": facility_type,
                "stage": stage or "Unknown",
                "ead": ead,
                "apd": apd,
                "lgd": max(Decimal("0"), lgd) if lgd is not None else None,
                "ecl": ecl,
                "status": status,
            })

    rows.sort(key=lambda account: (
        account["customer_number"],
        account["account_type"],
        account["account_number"],
    ))
    return {
        "rows": rows,
        "total_ecl": total_ecl.quantize(_ECL_QUANTUM),
        "total_funded_outstanding": total_funded_outstanding.quantize(
            _ECL_QUANTUM,
            rounding=ROUND_HALF_UP,
        ),
        "total_non_funded_outstanding": total_non_funded_outstanding.quantize(
            _ECL_QUANTUM,
            rounding=ROUND_HALF_UP,
        ),
        "total_outstanding": (
            total_funded_outstanding + total_non_funded_outstanding
        ).quantize(_ECL_QUANTUM, rounding=ROUND_HALF_UP),
        "calculated_count": calculated_count,
        "matched_years": matched_years,
        "has_current_predictors": has_current_predictors,
    }
