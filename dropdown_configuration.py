from datetime import date

from database import get_dropdown_options
from components.facility_types import (
    ALL_FACILITY_TYPES,
    FUNDED_FACILITY_TYPES,
    NON_FUNDED_FACILITY_TYPES,
)


DROPDOWN_CONFIGURATIONS = {
    "year": (
        "Year",
        [str(year) for year in range(2020, date.today().year + 1)],
    ),
    "corporate.legal_entity_type": (
        "Corporate Profile - Legal Entity Type",
        ["Pvt Ltd", "PLC", "Gov Corp", "Proprietorship", "Partnership"],
    ),
    "corporate.business_type": (
        "Corporate Profile - Business Type",
        ["Trading", "Service", "Industry", "Agriculture", "Staff"],
    ),
    "corporate.size_of_business": (
        "Corporate Profile - Size of Business",
        ["Informal", "Cottage", "Micro", "Small", "Medium", "Large"],
    ),
    "corporate.location_district": (
        "Corporate Profile - Location District",
        ["Dhaka", "Chittagong", "Sylhet", "Rajshahi", "Khulna", "Barisal"],
    ),
    "corporate.default_history": (
        "Corporate Profile - Default History",
        ["Yes", "No"],
    ),
    "corporate.repayment_behavior": (
        "Corporate Profile - Repayment Behavior",
        ["Satisfactory", "Good", "Moderate", "Bad", "Worst"],
    ),
    "corporate.cib_status": (
        "Corporate Profile - Latest CIB Status",
        ["STD-0", "STD-1", "STD-2", "SMA", "SS", "DF", "BL", "BLW", "RSDL"],
    ),
    "corporate.audit_objections": (
        "Corporate Profile - Major Audit Objections",
        ["Yes", "No"],
    ),
    "individual.legal_entity_type": (
        "Individual Profile - Legal Entity Type",
        ["Bangladeshi", "NRB"],
    ),
    "individual.district": (
        "Individual Profile - District",
        ["Dhaka", "Chittagong", "Sylhet", "Rajshahi"],
    ),
    "individual.gender": ("Individual Profile - Gender", ["Male", "Female", "Other"]),
    "individual.religion": (
        "Individual Profile - Religion",
        ["Islam", "Hindu", "Christian", "Buddhist"],
    ),
    "individual.marital_status": (
        "Individual Profile - Marital Status",
        ["Married", "Single", "Widow", "Divorced"],
    ),
    "individual.education": (
        "Individual Profile - Education",
        ["PHD", "Mphil", "Masters", "Bachelor", "HSC", "SSC"],
    ),
    "individual.occupation": (
        "Individual Profile - Occupation",
        ["Business", "Service", "Self-Employed", "Retired"],
    ),
    "individual.default_history": (
        "Individual Profile - Default History",
        ["Yes", "No"],
    ),
    "individual.repayment_behavior": (
        "Individual Profile - Repayment Behavior",
        ["Satisfactory", "Good", "Moderate", "Bad", "Worst"],
    ),
    "individual.cib_status": (
        "Individual Profile - Latest CIB Status",
        ["STD-0", "STD-1", "STD-2", "SMA", "SS", "DF", "BL", "BLW", "RSDL"],
    ),
    "individual.audit_objections": (
        "Individual Profile - Major Audit Objections",
        ["Yes", "No"],
    ),
    "collateral.type": (
        "Collateral Profile / Haircut - Collateral Type",
        ["Flat", "Land", "Building", "Project", "Fin.Instrument", "Share", "Gold", "Govt.Guarantee"],
    ),
    "collateral.measurement_unit": (
        "Collateral Profile - Measurement Unit",
        ["Decimal", "Ton", "Vori", "Number", "Squre Feet"],
    ),
    "collateral.quality": (
        "Collateral Profile - Quality of Collateral",
        ["Genuinge", "Disputed", "Major Audit Obj.", "Fake", "NA"],
    ),
    "credit_rating.value": (
        "Credit Ratings - ICRRS Rating / Credit Scoring",
        ["Excellent", "Good", "Marginal", "Unacceptable"],
    ),
    "credit_rating.company": (
        "Credit Ratings - Credit Rating Company",
        ["Alpha Rating", "CRAB", "CRISL", "Mega"],
    ),
    "funded.facility_type": ("Funded A/C - Nature of Loan", FUNDED_FACILITY_TYPES),
    "funded.approval_type": (
        "Funded A/C - Last Approval Type",
        ["New", "Renewal", "Enhancement", "RSDL", "Restructure"],
    ),
    "account.impairment": (
        "Funded / Non-Funded A/C - SICR/Impairment",
        ["None", "SICR", "Impairment"],
    ),
    "non_funded.facility_type": (
        "Non-Funded A/C - Cont. Liability Type",
        NON_FUNDED_FACILITY_TYPES,
    ),
    "facility.all": (
        "CCF / Stage Migration / Historical PD - Facility Type",
        ALL_FACILITY_TYPES,
    ),
}


def get_configured_dropdown_options(dropdown_key):
    _, default_options = DROPDOWN_CONFIGURATIONS[dropdown_key]
    return get_dropdown_options(dropdown_key, default_options)


def get_configured_year_options(existing_values=()):
    year_options = set(get_configured_dropdown_options("year"))
    year_options.update(
        str(value).strip()
        for value in existing_values
        if len(str(value).strip()) == 4 and str(value).strip().isdigit()
    )
    return sorted(year_options, key=int)
