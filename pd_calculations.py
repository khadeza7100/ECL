def get_yearly_net_migration_rates(records):
    yearly_net_rates = {}

    for item in records:
        year = str(item.get("year", "")).strip()
        facility_type = str(item.get("facility_type") or "").strip() or "Unspecified"
        migrated_from = str(item.get("migrated_from", "")).strip()
        migrated_to = str(item.get("migrated_to", "")).strip()
        if not year or not migrated_from or not migrated_to:
            continue

        try:
            migration_rate = float(item.get("migration_rate", 0) or 0)
        except (TypeError, ValueError):
            migration_rate = 0.0

        from_key = (year, facility_type, migrated_from)
        to_key = (year, facility_type, migrated_to)
        yearly_net_rates.setdefault(from_key, 0.0)
        yearly_net_rates.setdefault(to_key, 0.0)
        yearly_net_rates[from_key] -= migration_rate
        yearly_net_rates[to_key] += migration_rate

    return yearly_net_rates
