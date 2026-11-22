import csv
import io
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Callable

from components.reporting_dates import is_valid_reporting_date, parse_reporting_date
from database import (
    save_collateral_profile,
    save_corporate_profile,
    save_credit_ratings_profile,
    save_funded_ac_profile,
    save_individual_profile,
    save_non_funded_ac_profile,
    is_customer_exists_in_table,
)


@dataclass(frozen=True)
class ProfileImportSpec:
    title: str
    save_record: Callable[[dict], None]
    headers: tuple
    numeric_fields: tuple
    integer_fields: tuple = ()
    optional_headers: tuple = ()


PROFILE_IMPORT_SPECS = {
    "corporate": ProfileImportSpec(
        "Corporate Profile",
        save_corporate_profile,
        (
            "customer_number", "customer_name", "legal_entity", "business_type",
            "fixed_asset", "manpower_count", "business_turnover", "business_size",
            "category", "business_sector", "product_service_name",
            "location_district", "default_history", "repayment_behavior",
            "cib_status", "audit_objection",
        ),
        ("fixed_asset", "business_turnover"),
        ("manpower_count",),
    ),
    "individual": ProfileImportSpec(
        "Individual Profile",
        save_individual_profile,
        (
            "customer_number", "customer_name", "legal_entity", "district",
            "gender", "religion", "marital_status", "dob", "education",
            "occupation", "salary_income", "other_income",
            "monthly_installment", "family_expense", "income_expense_ratio",
            "total_asset", "total_liability", "net_worth", "default_history",
            "repayment_behavior", "cib_status", "audit_objection",
        ),
        (
            "salary_income", "other_income", "monthly_installment",
            "family_expense", "income_expense_ratio", "total_asset",
            "total_liability", "net_worth",
        ),
    ),
    "collateral": ProfileImportSpec(
        "Collateral Profile",
        save_collateral_profile,
        (
            "customer_number", "customer_name", "security_type", "quantity",
            "measurement_unit", "valuation_date", "market_value", "fsv",
            "collateral_quality",
        ),
        ("quantity", "market_value", "fsv"),
        optional_headers=("id",),
    ),
    "credit_ratings": ProfileImportSpec(
        "Credit Rating Profile",
        save_credit_ratings_profile,
        (
            "customer_number", "customer_name", "year_financials",
            "current_ratio", "net_profit_margin", "icr", "dscr",
            "debt_equity", "fin_debt_nw", "icrrs_rating", "icrrs_year",
            "rating_company", "short_term_rating", "long_term_rating",
            "rating_year", "rating_expiry_date", "scoring", "scoring_year",
        ),
        (
            "current_ratio", "net_profit_margin", "icr", "dscr",
            "debt_equity", "fin_debt_nw",
        ),
    ),
    "funded_ac": ProfileImportSpec(
        "Funded A/C Profile",
        save_funded_ac_profile,
        (
            "ac_num", "reporting_date", "cust_num", "cust_name", "nature",
            "approval_type", "approval_date", "loan_limit", "loan_out",
            "accrued_int", "calc_int", "exp_date", "first_inst_due",
            "due_install", "install_size", "amt_recovered",
            "install_recovered", "overdue_install", "overdue_in_days",
            "overdue_amt", "ecl_category", "ead", "staging_by_dpd",
            "sicr_impairment", "qj_stage", "qj_reason",
        ),
        (
            "loan_limit", "loan_out", "accrued_int", "calc_int",
            "due_install", "install_size", "amt_recovered",
            "install_recovered", "overdue_install", "overdue_amt", "ead",
            "pv_collateral", "lgd",
        ),
        ("overdue_in_days",),
        optional_headers=("pv_collateral", "lgd"),
    ),
    "non_funded_ac": ProfileImportSpec(
        "Non-Funded A/C Profile",
        save_non_funded_ac_profile,
        (
            "ac_num", "reporting_date", "cust_num", "cust_name", "cont_type",
            "amt_liability", "issue_date", "exp_date", "overdue_days",
            "margin_kept", "ac_limit", "ccf", "ead", "staging_by_dpd",
            "sicr_impairment", "qj_stage", "qj_reason",
        ),
        (
            "amt_liability", "margin_kept", "ac_limit", "ead",
            "pv_collateral", "lgd",
        ),
        ("overdue_days",),
        optional_headers=("pv_collateral", "lgd"),
    ),
}

PROFILE_REQUIRED_KEYS = {
    "corporate": "customer_number",
    "individual": "customer_number",
    "collateral": "customer_number",
    "credit_ratings": "customer_number",
    "funded_ac": "ac_num",
    "non_funded_ac": "ac_num",
}


class ProfileImportError(ValueError):
    pass


def parse_profile_csv(profile_type, content):
    if profile_type not in PROFILE_IMPORT_SPECS:
        raise ProfileImportError(f"Unsupported profile type: {profile_type}")

    spec = PROFILE_IMPORT_SPECS[profile_type]
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ProfileImportError("The CSV must use UTF-8 encoding.") from error

    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    raw_headers = next(reader, None)
    if not raw_headers:
        raise ProfileImportError("The CSV file is empty or has no header row.")

    headers = [header.strip() for header in raw_headers]
    if any(not header for header in headers):
        raise ProfileImportError("CSV headers cannot be blank.")
    if len({header.casefold() for header in headers}) != len(headers):
        raise ProfileImportError("CSV headers must be unique.")

    expected_headers = set(spec.headers)
    optional_headers = set(spec.optional_headers)
    supplied_headers = set(headers)
    missing = expected_headers - supplied_headers
    unexpected = supplied_headers - expected_headers - optional_headers
    if missing or unexpected:
        details = []
        if missing:
            details.append("Missing: " + ", ".join(sorted(missing)))
        if unexpected:
            details.append("Unexpected: " + ", ".join(sorted(unexpected)))
        raise ProfileImportError("CSV headers do not match this profile. " + "; ".join(details))

    records = []
    numeric_fields = set(spec.numeric_fields)
    integer_fields = set(spec.integer_fields)
    required_key = PROFILE_REQUIRED_KEYS[profile_type]

    def read_rows():
        try:
            yield from reader
        except csv.Error as error:
            raise ProfileImportError(
                f"CSV parsing failed near row {reader.line_num}: {error}"
            ) from error

    for raw_row in read_rows():
        row_number = reader.line_num
        if not raw_row or all(not value.strip() for value in raw_row):
            continue
        if len(raw_row) != len(headers):
            raise ProfileImportError(
                f"CSV row {row_number} has {len(raw_row)} values; expected {len(headers)}."
            )

        record = {header: value.strip() for header, value in zip(headers, raw_row)}
        if not record.get(required_key):
            raise ProfileImportError(f"CSV row {row_number} is missing {required_key}.")

        if "reporting_date" in record:
            reporting_date = parse_reporting_date(record["reporting_date"])
            if not is_valid_reporting_date(reporting_date):
                raise ProfileImportError(
                    f"CSV row {row_number} has an invalid reporting_date. "
                    "It must be a month-end date on or before today."
                )
            record["reporting_date"] = reporting_date.isoformat()

        for field in numeric_fields | integer_fields:
            raw_value = record.get(field, "")
            if not raw_value:
                record[field] = 0 if field in integer_fields else Decimal(0)
                continue
            try:
                number = Decimal(raw_value)
            except InvalidOperation as error:
                raise ProfileImportError(
                    f"CSV row {row_number} has an invalid number in {field}: {raw_value!r}."
                ) from error
            if not number.is_finite():
                raise ProfileImportError(
                    f"CSV row {row_number} has a non-finite number in {field}."
                )
            if field in integer_fields:
                if number != number.to_integral_value():
                    raise ProfileImportError(
                        f"CSV row {row_number} requires a whole number in {field}."
                    )
                record[field] = int(number)
            else:
                record[field] = number

        if "id" in spec.optional_headers:
            raw_id = record.get("id", "")
            if raw_id:
                try:
                    id_value = Decimal(raw_id)
                except (InvalidOperation, ValueError) as error:
                    raise ProfileImportError(
                        f"CSV row {row_number} has an invalid collateral id: {raw_id!r}."
                    ) from error
                if not id_value.is_finite() or id_value != id_value.to_integral_value():
                    raise ProfileImportError(
                        f"CSV row {row_number} collateral id must be a whole number."
                    )
                record["id"] = int(id_value)
                if record["id"] <= 0:
                    raise ProfileImportError(
                        f"CSV row {row_number} collateral id must be positive."
                    )
            else:
                record["id"] = None

        records.append((row_number, record))

    if not records:
        raise ProfileImportError("The CSV contains no profile rows.")
    return spec, records


def import_profile_csv(profile_type, content):
    spec, records = parse_profile_csv(profile_type, content)

    for row_number, record in records:
        customer_number = record.get("customer_number")
        if profile_type == "corporate" and is_customer_exists_in_table(
            customer_number, "individual_profiles"
        ):
            raise ProfileImportError(
                f"CSV row {row_number}: customer {customer_number!r} already "
                "exists in Individual Profiles."
            )
        if profile_type == "individual" and is_customer_exists_in_table(
            customer_number, "corporate_profiles"
        ):
            raise ProfileImportError(
                f"CSV row {row_number}: customer {customer_number!r} already "
                "exists in Corporate Profiles."
            )
        if profile_type in ("collateral", "credit_ratings"):
            exists_in_corporate = is_customer_exists_in_table(
                customer_number, "corporate_profiles"
            )
            exists_in_individual = is_customer_exists_in_table(
                customer_number, "individual_profiles"
            )
            if not (exists_in_corporate or exists_in_individual):
                raise ProfileImportError(
                    f"CSV row {row_number}: customer {customer_number!r} does "
                    "not exist in Corporate or Individual Profiles."
                )

    imported_count = 0
    for row_number, record in records:
        try:
            spec.save_record(record)
        except Exception as error:
            raise ProfileImportError(
                f"Import stopped at CSV row {row_number} after {imported_count} "
                f"successful rows: {error}"
            ) from error
        imported_count += 1
    return imported_count
