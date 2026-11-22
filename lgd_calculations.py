from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


_LGD_QUANTUM = Decimal("0.0001")


def _to_nonnegative_decimal(value, field_name, account_number):
    try:
        amount = Decimal(str(value or 0))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field_name} for {account_number} must be a valid number.")

    if not amount.is_finite() or amount < 0:
        raise ValueError(f"{field_name} for {account_number} must be non-negative.")
    return amount


def _account_items(records):
    if isinstance(records, dict):
        return records.items()
    return (
        (record.get("ac_num"), record)
        for record in records
    )


def build_lgd_calculations(funded_accounts, non_funded_accounts):
    rows = []
    funded_lgd = {}
    non_funded_lgd = {}
    skipped_zero_ead = 0

    for account_type, accounts in (
        ("Funded", funded_accounts),
        ("Non-Funded", non_funded_accounts),
    ):
        for account_key, account in _account_items(accounts):
            account_number = str(account.get("ac_num") or account_key or "").strip()
            customer_number = str(account.get("cust_num") or "").strip()
            ead = _to_nonnegative_decimal(
                account.get("ead"),
                "EAD",
                account_number or account_type,
            )
            pv_collateral = _to_nonnegative_decimal(
                account.get("pv_collateral"),
                "PV of Collateral",
                account_number or account_type,
            )

            if not account_number:
                status = "Skipped: missing account number"
                lgd = None
            elif ead == 0:
                status = "Skipped: EAD is zero"
                skipped_zero_ead += 1
                lgd = None
            else:
                lgd = max(
                    Decimal("0"),
                    (ead - pv_collateral) / ead,
                ).quantize(
                    _LGD_QUANTUM,
                    rounding=ROUND_HALF_UP,
                )
                status = "Ready"
                destination = funded_lgd if account_type == "Funded" else non_funded_lgd
                destination[account_number] = lgd

            rows.append({
                "customer_number": customer_number,
                "customer_name": str(account.get("cust_name") or "").strip(),
                "account_type": account_type,
                "account_number": account_number,
                "ead": ead,
                "pv_collateral": pv_collateral,
                "lgd": lgd,
                "status": status,
            })

    rows.sort(key=lambda account: (
        account["customer_number"],
        account["account_type"],
        account["account_number"],
    ))
    return {
        "rows": rows,
        "funded_lgd": funded_lgd,
        "non_funded_lgd": non_funded_lgd,
        "skipped_zero_ead": skipped_zero_ead,
    }
