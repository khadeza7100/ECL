def get_average_credit_conversion_rate(facility_type, ccf_records):
    requested_type = str(facility_type or "").strip().lower()
    matching_rates = [
        float(record.get("cc_rate", 0.0))
        for record in ccf_records
        if str(record.get("facility_type", "")).strip().lower() == requested_type
    ]
    if not matching_rates and requested_type in ("continuous", "continuous loan"):
        matching_rates = [
            float(record.get("cc_rate", 0.0))
            for record in ccf_records
            if str(record.get("facility_type", "")).strip().lower() == "ccod"
        ]
    return sum(matching_rates) / len(matching_rates) if matching_rates else 0.0


def get_non_funded_credit_conversion_rate(facility_type, ccf_records):
    if not facility_type:
        return 0.0
    for record in ccf_records:
        if str(record.get("facility_type", "")).strip().upper() == str(facility_type).strip().upper():
            return float(record.get("cc_rate", 0.0))
    return 0.0


def calculate_funded_ead(
    loan_limit,
    loan_outstanding,
    accrued_interest,
    calculated_interest,
    facility_type,
    credit_conversion_rate,
):
    credit_conversion_rate = float(f"{credit_conversion_rate:.4f}")
    undrawn_commitment = max(
        0.0,
        loan_limit - loan_outstanding - accrued_interest - calculated_interest,
    )
    base_ead = loan_outstanding + accrued_interest + calculated_interest
    normalized_facility_type = str(facility_type or "").strip().lower()

    if normalized_facility_type in (
        "continuous",
        "continuous loan",
        "ccod",
        "credit card",
    ):
        ead = base_ead + credit_conversion_rate * undrawn_commitment
    else:
        ead = base_ead
    return undrawn_commitment, ead


def calculate_non_funded_ead(amount_of_liability, margin_kept, credit_conversion_rate):
    return max(0.0, (amount_of_liability - margin_kept) * credit_conversion_rate)
