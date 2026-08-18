#!/usr/bin/env python3
"""Validaciones automáticas sobre users.csv y events.csv generados.

Cubre las reglas de docs/02_DATA_GENERATION_SPEC.md §14 y el checklist
adicional pedido para esta fase.
"""

import csv
import json
import os
from collections import defaultdict
from datetime import datetime

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

FORBIDDEN_COLUMNS = {
    "lifecycle_stage", "first_action_timestamp", "time_to_first_action",
    "onboarding_status", "activation_status", "first_value_date",
    "days_to_first_value", "activation_score", "registration_abandonment",
}

VALID_EVENT_NAMES = {
    "registration_started", "registration_completed",
    "onboarding_started", "profile_completed", "onboarding_completed",
    "data_source_connected", "dashboard_created", "insight_viewed",
    "session_started", "dashboard_viewed", "feature_used", "dashboard_shared",
}

ONCE_PER_IDENTITY = {
    "registration_started", "registration_completed",
    "onboarding_started", "profile_completed", "onboarding_completed",
}

NO_USER_ID_ALLOWED = {"registration_started", "session_started"}
REQUIRES_USER_ID = VALID_EVENT_NAMES - NO_USER_ID_ALLOWED - {"registration_started"}

COUNTRIES = {
    "Mexico", "Brazil", "Colombia", "Argentina", "Peru", "Chile", "Venezuela",
    "Ecuador", "Bolivia", "Guatemala", "Dominican Republic", "Honduras",
    "Paraguay", "Uruguay",
}
ROLES = {
    "Marketing Manager", "Marketing Director", "Growth Manager", "Growth Director",
    "Product Manager", "Product Director", "Data Analyst", "Business Analyst",
    "BI Analyst", "Data Scientist", "Sales Manager", "Sales Director",
    "Operations Manager", "Operations Director", "Founder / CEO",
}
INDUSTRIES = {
    "SaaS / Software", "Financial Services", "Healthcare", "Retail / E-commerce",
    "Education", "Professional Services", "Manufacturing", "Telecommunications",
    "Media / Entertainment", "Travel / Hospitality", "Logistics / Transportation",
    "Real Estate", "Consumer Goods", "Other",
}
COMPANY_SIZES = {"1-10", "11-50", "51-200", "201-500", "501-1000", "1001-5000", "5001+"}
USE_CASES = {
    "Marketing Analytics", "Sales Analytics", "Product Analytics", "Customer Analytics",
    "Operations Analytics", "Financial Analytics", "Executive Reporting",
    "Business Intelligence", "Performance Monitoring", "Data Exploration",
}
CHANNELS = {
    "Organic Search", "Paid Search", "Paid Social", "Organic Social", "Referral",
    "Direct", "Partner", "Content", "Email", "Event / Webinar",
}

COHORT_START = datetime(2026, 7, 1, 0, 0, 0)
COHORT_END = datetime(2026, 7, 31, 23, 59, 59)
SIM_CUTOFF = datetime(2026, 9, 20, 23, 59, 59)


def parse_dt(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")


def main():
    errors = []
    warnings = []

    # --- Cargar users.csv ---
    users = {}
    with open(os.path.join(DATA_DIR, "users.csv"), newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            users[row["user_id"]] = row

    print(f"[users.csv] filas: {len(users)}  columnas: {fieldnames}")

    # 1. Exactamente 10.000 cuentas
    if len(users) != 10_000:
        errors.append(f"users.csv no tiene 10000 filas, tiene {len(users)}")
    else:
        print("OK - 10,000 cuentas completadas")

    # columnas prohibidas
    bad_cols = FORBIDDEN_COLUMNS & set(fieldnames)
    if bad_cols:
        errors.append(f"Columnas derivadas prohibidas encontradas en users.csv: {bad_cols}")
    else:
        print("OK - sin columnas derivadas prohibidas en users.csv")

    # unicidad de user_id
    if len(users) != len(set(users.keys())):
        errors.append("user_id no es único en users.csv")
    else:
        print("OK - user_id único")

    # unicidad de email
    emails = [r["email"] for r in users.values()]
    if len(emails) != len(set(emails)):
        errors.append("email no es único en users.csv")
    else:
        print("OK - email único")

    # signup_date dentro de julio + catálogos + converted_to_paid binario
    country_counts = defaultdict(int)
    role_counts = defaultdict(int)
    industry_counts = defaultdict(int)
    size_counts = defaultdict(int)
    usecase_counts = defaultdict(int)
    channel_counts = defaultdict(int)
    converted_counts = defaultdict(int)

    for uid, row in users.items():
        try:
            sd = parse_dt(row["signup_date"])
        except ValueError:
            errors.append(f"signup_date inválido para {uid}: {row['signup_date']}")
            continue
        if not (COHORT_START <= sd <= COHORT_END):
            errors.append(f"signup_date fuera de julio 2026 para {uid}: {sd}")

        if row["country"] not in COUNTRIES:
            errors.append(f"country inválido para {uid}: {row['country']}")
        if row["role"] not in ROLES:
            errors.append(f"role inválido para {uid}: {row['role']}")
        if row["industry"] not in INDUSTRIES:
            errors.append(f"industry inválido para {uid}: {row['industry']}")
        if row["company_size"] not in COMPANY_SIZES:
            errors.append(f"company_size inválido para {uid}: {row['company_size']}")
        if row["use_case"] not in USE_CASES:
            errors.append(f"use_case inválido para {uid}: {row['use_case']}")
        if row["acquisition_channel"] not in CHANNELS:
            errors.append(f"acquisition_channel inválido para {uid}: {row['acquisition_channel']}")
        if row["converted_to_paid"] not in ("0", "1"):
            errors.append(f"converted_to_paid no binario para {uid}: {row['converted_to_paid']}")

        country_counts[row["country"]] += 1
        role_counts[row["role"]] += 1
        industry_counts[row["industry"]] += 1
        size_counts[row["company_size"]] += 1
        usecase_counts[row["use_case"]] += 1
        channel_counts[row["acquisition_channel"]] += 1
        converted_counts[row["converted_to_paid"]] += 1

    if not errors:
        print("OK - signup_date y catálogos válidos para todas las filas revisadas hasta ahora")

    print(f"\nVariabilidad de dimensiones (n_valores_distintos / total_catalogo):")
    print(f"  country: {len(country_counts)}/14  min={min(country_counts.values())} max={max(country_counts.values())}")
    print(f"  role: {len(role_counts)}/15  min={min(role_counts.values())} max={max(role_counts.values())}")
    print(f"  industry: {len(industry_counts)}/14  min={min(industry_counts.values())} max={max(industry_counts.values())}")
    print(f"  company_size: {len(size_counts)}/7  min={min(size_counts.values())} max={max(size_counts.values())}")
    print(f"  use_case: {len(usecase_counts)}/10  min={min(usecase_counts.values())} max={max(usecase_counts.values())}")
    print(f"  acquisition_channel: {len(channel_counts)}/10  min={min(channel_counts.values())} max={max(channel_counts.values())}")
    print(f"  converted_to_paid distribution: {dict(converted_counts)}")

    for name, counts, catalog_size in [
        ("country", country_counts, 14), ("role", role_counts, 15),
        ("industry", industry_counts, 14), ("company_size", size_counts, 7),
        ("use_case", usecase_counts, 10), ("acquisition_channel", channel_counts, 10),
    ]:
        if len(counts) < catalog_size:
            errors.append(f"{name} no usa todos los valores del catálogo ({len(counts)}/{catalog_size})")

    # --- Cargar events.csv ---
    events = []
    with open(os.path.join(DATA_DIR, "events.csv"), newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        ev_fieldnames = reader.fieldnames
        for row in reader:
            events.append(row)

    print(f"\n[events.csv] filas: {len(events)}  columnas: {ev_fieldnames}")

    bad_cols_ev = FORBIDDEN_COLUMNS & set(ev_fieldnames)
    if bad_cols_ev:
        errors.append(f"Columnas derivadas prohibidas encontradas en events.csv: {bad_cols_ev}")
    else:
        print("OK - sin columnas derivadas prohibidas en events.csv")

    event_ids = set()
    by_user = defaultdict(list)
    by_anon = defaultdict(list)
    event_name_counts = defaultdict(int)
    max_ts = None

    for row in events:
        eid = row["event_id"]
        if eid in event_ids:
            errors.append(f"event_id duplicado: {eid}")
        event_ids.add(eid)

        name = row["event_name"]
        event_name_counts[name] += 1
        if name not in VALID_EVENT_NAMES:
            errors.append(f"event_name fuera de taxonomía: {name}")

        try:
            ts = parse_dt(row["event_timestamp"])
        except ValueError:
            errors.append(f"event_timestamp inválido en {eid}: {row['event_timestamp']}")
            continue
        if max_ts is None or ts > max_ts:
            max_ts = ts
        if ts > SIM_CUTOFF:
            errors.append(f"evento posterior al cutoff de simulación: {eid} {ts}")

        uid = row["user_id"] if row["user_id"] else None
        aid = row["anonymous_id"]
        if not aid:
            errors.append(f"anonymous_id vacío en {eid}")

        if uid is None and name in REQUIRES_USER_ID:
            errors.append(f"evento post-signup con user_id nulo: {eid} {name}")
        if uid is not None and uid not in users:
            errors.append(f"user_id en events.csv no existe en users.csv: {eid} {uid}")

        try:
            meta = json.loads(row["metadata"])
            if not isinstance(meta, dict):
                errors.append(f"metadata no es objeto JSON en {eid}")
        except json.JSONDecodeError:
            errors.append(f"metadata no es JSON válido en {eid}: {row['metadata']}")

        by_user[uid].append((ts, name)) if uid else None
        by_anon[aid].append((ts, name, uid))

    if len(event_ids) != len(events):
        errors.append("event_id no es único en events.csv")
    else:
        print("OK - event_id único")

    print(f"\nDistribución de event_name:")
    for name in sorted(event_name_counts, key=lambda k: -event_name_counts[k]):
        print(f"  {name}: {event_name_counts[name]}")

    print(f"\nÚltimo event_timestamp observado: {max_ts}")

    # Ocurrencia única para eventos "once per identity"
    for aid, evs in by_anon.items():
        counts = defaultdict(int)
        for ts, name, uid in evs:
            counts[name] += 1
        for name in ONCE_PER_IDENTITY:
            if counts[name] > 1:
                errors.append(f"evento de ocurrencia única repetido para {aid}: {name} x{counts[name]}")

    # 2. Integridad referencial: cobertura de cuentas — cada user_id en users.csv
    #    tiene un registration_completed con mismo timestamp que signup_date
    reg_completed_ts_by_user = {}
    for row in events:
        if row["event_name"] == "registration_completed" and row["user_id"]:
            reg_completed_ts_by_user[row["user_id"]] = row["event_timestamp"]

    missing_reg_completed = set(users.keys()) - set(reg_completed_ts_by_user.keys())
    if missing_reg_completed:
        errors.append(f"{len(missing_reg_completed)} usuarios sin evento registration_completed")
    else:
        print("\nOK - todo user_id de users.csv tiene evento registration_completed")

    mismatched = 0
    for uid, row in users.items():
        ev_ts = reg_completed_ts_by_user.get(uid)
        if ev_ts is not None and ev_ts != row["signup_date"]:
            mismatched += 1
    if mismatched:
        errors.append(f"{mismatched} usuarios con signup_date != timestamp de registration_completed")
    else:
        print("OK - signup_date coincide exactamente con el timestamp de registration_completed")

    # 3. Coherencia temporal por identidad (anonymous_id)
    temporal_errors = 0
    for aid, evs in by_anon.items():
        evs_sorted = sorted(evs, key=lambda x: x[0])
        started = [e for e in evs if e[1] == "registration_started"]
        completed = [e for e in evs if e[1] == "registration_completed"]
        if started and completed:
            if completed[0][0] < started[0][0]:
                temporal_errors += 1
        # ningún evento antes de registration_started de la misma identidad
        if started:
            rs_ts = started[0][0]
            for ts, name, uid in evs:
                if ts < rs_ts:
                    temporal_errors += 1
    if temporal_errors:
        errors.append(f"{temporal_errors} violaciones de coherencia temporal (evento antes de registration_started, o registration_completed antes de registration_started)")
    else:
        print("OK - coherencia temporal: ningún evento precede a registration_started; registration_completed no precede a registration_started")

    # onboarding/FV/behavior no antes de signup_date
    post_signup_families = REQUIRES_USER_ID
    violations_post_signup = 0
    signup_by_user = {uid: parse_dt(row["signup_date"]) for uid, row in users.items()}
    for row in events:
        if row["event_name"] in post_signup_families and row["user_id"]:
            ts = parse_dt(row["event_timestamp"])
            sd = signup_by_user[row["user_id"]]
            if ts < sd:
                violations_post_signup += 1
    if violations_post_signup:
        errors.append(f"{violations_post_signup} eventos post-signup con timestamp anterior a signup_date")
    else:
        print("OK - ningún evento post-signup precede a signup_date")

    # secuencia lógica interna: onboarding_completed no antes de onboarding_started, etc.
    seq_violations = 0
    ORDER_CHECKS = [
        ("onboarding_started", "profile_completed"),
        ("profile_completed", "onboarding_completed"),
    ]
    TRACK_FIRST_OCCURRENCE = (
        ONCE_PER_IDENTITY - {"registration_started", "registration_completed"}
    ) | {"data_source_connected", "dashboard_created", "insight_viewed"}
    per_user_first_ts = defaultdict(dict)
    for row in events:
        if row["user_id"] and row["event_name"] in TRACK_FIRST_OCCURRENCE:
            uid = row["user_id"]
            name = row["event_name"]
            ts = parse_dt(row["event_timestamp"])
            if name not in per_user_first_ts[uid]:
                per_user_first_ts[uid][name] = ts
    for uid, d in per_user_first_ts.items():
        for a, b in ORDER_CHECKS:
            if a in d and b in d and d[b] < d[a]:
                seq_violations += 1
    if seq_violations:
        errors.append(f"{seq_violations} violaciones de secuencia onboarding_started/profile_completed/onboarding_completed")
    else:
        print("OK - secuencia interna de onboarding respetada")

    # 4. Registration Abandonment reconstruible
    abandoned = 0
    for aid, evs in by_anon.items():
        names = {e[1] for e in evs}
        if "registration_started" in names and "registration_completed" not in names:
            abandoned += 1
    print(f"\nIdentidades con registration_started sin registration_completed (abandono reconstruible): {abandoned}")
    if abandoned == 0:
        errors.append("No hay identidades reconstruibles como Registration Abandonment")

    # 5. First Value: rápido / tardío / ausente
    first_value_fast = 0
    first_value_late = 0
    first_value_never = 0
    days_list = []
    for uid, row in users.items():
        sd = parse_dt(row["signup_date"])
        d = per_user_first_ts.get(uid, {})
        ds = d.get("data_source_connected")
        db = d.get("dashboard_created")
        iv = d.get("insight_viewed")
        if ds and db and iv:
            fv_ts = max(ds, db, iv)  # completa la secuencia con la última de las 3 primeras ocurrencias
            days = (fv_ts - sd).total_seconds() / 86400
            days_list.append(days)
            if days <= 7:
                first_value_fast += 1
            else:
                first_value_late += 1
        else:
            first_value_never += 1

    print(f"\nFirst Value <= 7 dias (Activated): {first_value_fast}")
    print(f"First Value > 7 dias (Late Value): {first_value_late}")
    print(f"Sin First Value (Not Activated): {first_value_never}")
    if days_list:
        print(f"days_to_first_value: min={min(days_list):.2f} max={max(days_list):.2f} avg={sum(days_list)/len(days_list):.2f}")

    for label, count in [("Activated", first_value_fast), ("Late Value", first_value_late), ("Not Activated", first_value_never)]:
        if count < 200:
            errors.append(f"Grupo {label} demasiado pequeño para ser 'no trivial': {count}")

    # 6. converted_to_paid no depende directamente de activation
    # comprobación de no-determinismo: dentro de cada grupo (activated/late/never) debe
    # haber tanto converted=1 como converted=0
    group_of_user = {}
    for uid, row in users.items():
        sd = parse_dt(row["signup_date"])
        d = per_user_first_ts.get(uid, {})
        ds, db, iv = d.get("data_source_connected"), d.get("dashboard_created"), d.get("insight_viewed")
        if ds and db and iv:
            fv_ts = max(ds, db, iv)
            days = (fv_ts - sd).total_seconds() / 86400
            group_of_user[uid] = "activated" if days <= 7 else "late_value"
        else:
            group_of_user[uid] = "not_activated"

    conv_by_group = defaultdict(lambda: [0, 0])
    for uid, row in users.items():
        g = group_of_user[uid]
        c = int(row["converted_to_paid"])
        conv_by_group[g][c] += 1

    print("\nconverted_to_paid por grupo de First Value (para verificar ausencia de determinismo):")
    for g, (c0, c1) in conv_by_group.items():
        rate = c1 / (c0 + c1) if (c0 + c1) else 0
        print(f"  {g}: converted=0 -> {c0}, converted=1 -> {c1}, rate={rate:.2%}")

    for g, (c0, c1) in conv_by_group.items():
        if c0 == 0 or c1 == 0:
            errors.append(f"converted_to_paid parece determinista dentro del grupo {g} (c0={c0}, c1={c1})")

    # 9. Cruce dimensiones x resultado — solo para mostrar variabilidad, no para
    #    imponer conclusiones (se reporta, no se interpreta como bottleneck)
    print("\nActivation rate por country (informativo, no interpretativo):")
    by_country_group = defaultdict(lambda: defaultdict(int))
    for uid, row in users.items():
        by_country_group[row["country"]][group_of_user[uid]] += 1
    for c in sorted(by_country_group):
        d = by_country_group[c]
        total = sum(d.values())
        act_rate = d.get("activated", 0) / total
        print(f"  {c}: n={total} activated_rate={act_rate:.1%}")

    # --- resumen final ---
    print("\n" + "=" * 70)
    if errors:
        print(f"VALIDACIÓN: {len(errors)} ERRORES ENCONTRADOS")
        for e in errors:
            print(f"  - {e}")
    else:
        print("VALIDACIÓN: TODOS LOS CHECKS PASARON")
    if warnings:
        print(f"\nAdvertencias ({len(warnings)}):")
        for w in warnings:
            print(f"  - {w}")

    return len(errors) == 0


if __name__ == "__main__":
    ok = main()
    raise SystemExit(0 if ok else 1)
