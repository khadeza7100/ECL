from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_HALF_UP


_PV_QUANTUM = Decimal("0.0001")
_ZERO = Decimal("0")


def _to_nonnegative_decimal(value, field_name, record_id):
    try:
        amount = Decimal(str(value or 0))
    except (InvalidOperation, ValueError):
        raise ValueError(f"{field_name} for {record_id} must be a valid number.")

    if not amount.is_finite() or amount < 0:
        raise ValueError(f"{field_name} for {record_id} must be a non-negative number.")
    return amount


def _account_items(records):
    if isinstance(records, dict):
        return records.items()
    return (
        (record.get("ac_num"), record)
        for record in records
    )


def build_proportional_collateral_allocations(
    collateral_records,
    funded_accounts,
    non_funded_accounts,
):
    collateral_by_customer = {}
    collateral_without_customer = 0
    for index, collateral in enumerate(collateral_records):
        customer_number = str(collateral.get("customer_number") or "").strip()
        if not customer_number:
            collateral_without_customer += 1
            continue

        record_id = collateral.get("id") or f"row {index + 1}"
        present_value = _to_nonnegative_decimal(
            collateral.get("lgd"),
            "Collateral present value",
            record_id,
        )
        collateral_by_customer[customer_number] = (
            collateral_by_customer.get(customer_number, _ZERO) + present_value
        )

    accounts_by_customer = {}
    result_rows = []
    for account_type, records in (
        ("Funded", funded_accounts),
        ("Non-Funded", non_funded_accounts),
    ):
        for account_key, account in _account_items(records):
            account_number = str(account.get("ac_num") or account_key or "").strip()
            customer_number = str(account.get("cust_num") or "").strip()
            ead = _to_nonnegative_decimal(
                account.get("ead"),
                "EAD",
                account_number or account_type,
            )
            result = {
                "customer_number": customer_number,
                "customer_name": str(account.get("cust_name") or "").strip(),
                "account_type": account_type,
                "account_number": account_number,
                "ead": ead,
                "customer_ead": _ZERO,
                "customer_pv": _ZERO,
                "allocated_pv": None,
                "status": "Ready",
            }
            if not account_number:
                result["status"] = "Skipped: missing account number"
                result_rows.append(result)
                continue
            if not customer_number:
                result["status"] = "Skipped: missing customer number"
                result_rows.append(result)
                continue
            accounts_by_customer.setdefault(customer_number, []).append(result)

    funded_allocations = {}
    non_funded_allocations = {}
    skipped_customers = 0
    customers_without_collateral = 0
    for customer_number, customer_accounts in accounts_by_customer.items():
        if customer_number not in collateral_by_customer:
            customers_without_collateral += 1
            for account in customer_accounts:
                account["status"] = "Skipped: no collateral records"
            continue

        customer_pv = collateral_by_customer.get(customer_number, _ZERO)
        total_ead = sum(
            (account["ead"] for account in customer_accounts),
            _ZERO,
        )
        for account in customer_accounts:
            account["customer_ead"] = total_ead
            account["customer_pv"] = customer_pv

        if total_ead == 0:
            skipped_customers += 1
            for account in customer_accounts:
                account["status"] = "Skipped: total EAD is zero"
            continue

        ordered_accounts = sorted(
            customer_accounts,
            key=lambda account: (
                account["account_type"],
                account["account_number"],
            ),
        )
        positive_accounts = [
            (index, account)
            for index, account in enumerate(ordered_accounts)
            if account["ead"] > 0
        ]
        total_units = int(
            (customer_pv / _PV_QUANTUM).to_integral_value(rounding=ROUND_HALF_UP)
        )
        units_by_index = {}
        remainders = []
        for index, account in positive_accounts:
            exact_units = (
                customer_pv * account["ead"] / total_ead / _PV_QUANTUM
            )
            rounded_down_units = int(
                exact_units.to_integral_value(rounding=ROUND_DOWN)
            )
            units_by_index[index] = rounded_down_units
            remainders.append((index, exact_units - rounded_down_units))

        remaining_units = total_units - sum(units_by_index.values())
        for index, _ in sorted(
            remainders,
            key=lambda item: (-item[1], item[0]),
        )[:remaining_units]:
            units_by_index[index] += 1

        for index, account in enumerate(ordered_accounts):
            if account["ead"] == 0:
                allocation = _ZERO
            else:
                allocation = Decimal(units_by_index[index]) * _PV_QUANTUM

            account["allocated_pv"] = allocation
            target_allocations = (
                funded_allocations
                if account["account_type"] == "Funded"
                else non_funded_allocations
            )
            target_allocations[account["account_number"]] = allocation
        result_rows.extend(customer_accounts)

    result_rows.sort(key=lambda account: (
        account["customer_number"],
        account["account_type"],
        account["account_number"],
    ))
    return {
        "rows": result_rows,
        "funded_allocations": funded_allocations,
        "non_funded_allocations": non_funded_allocations,
        "skipped_customers": skipped_customers,
        "customers_without_collateral": customers_without_collateral,
        "collateral_without_customer": collateral_without_customer,
        "collateral_customers_without_accounts": len(
            set(collateral_by_customer).difference(accounts_by_customer)
        ),
    }
