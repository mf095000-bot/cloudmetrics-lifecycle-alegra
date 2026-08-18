#!/usr/bin/env python3
"""
Generador de users.csv y events.csv para CloudMetrics.

Implementa el contrato definido en:
- CLAUDE.md
- docs/00_WORKING_DOCUMENT.md
- docs/01_CONTEXT.md
- docs/02_DATA_GENERATION_SPEC.md
- docs/03_SIMULATION_PARAMETERS.md

Todas las decisiones técnicas delegadas explícitamente por
03_SIMULATION_PARAMETERS.md §5 se documentan en generation_params.json.

Principio anti-fabricación (versión revisada): las dimensiones de usuario
(country, role, industry, company_size, use_case, acquisition_channel)
pueden tener una influencia real, pero pequeña y difusa, sobre el
comportamiento posterior (progresión del funnel, velocidad hacia First
Value, converted_to_paid). Esa influencia se implementa como un efecto
aleatorio por cada valor de catálogo, generado con la semilla fija del
script -- nunca elegido a mano ni ajustado después de observar los
resultados para producir una historia. Los efectos están repartidos entre
las 6 dimensiones simultáneamente, de forma que ningún valor individual
(un país, un rol, etc.) queda diseñado como "ganador" o "perdedor": la
magnitud se calibró una única vez a nivel de escala general (sigma), nunca
por dirección de un valor específico. Esto permite que el diagnóstico
posterior (fase 4) encuentre relaciones genuinas entre quién es el usuario,
qué hace y qué resultado obtiene, sin que esas relaciones estén
predeterminadas por el diseño del generador.
"""

import csv
import json
import math
import os
import random
import string
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# 0. Configuración y semilla (reproducibilidad — decisión técnica delegada)
# ---------------------------------------------------------------------------

SEED = 20260701
random.seed(SEED)

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(OUT_DIR, exist_ok=True)

N_COMPLETED = 10_000

COHORT_START = datetime(2026, 7, 1, 0, 0, 0)
COHORT_END = datetime(2026, 7, 31, 23, 59, 59)

# Ventana de observación: se extiende bastante más allá de julio para que
# Late Value (>7 días) sea observable sin truncamiento artificial masivo.
# Decisión técnica: cutoff = 2026-09-20 (~51 días después del último signup
# posible del 31 de julio).
OBSERVATION_CUTOFF = datetime(2026, 9, 20, 23, 59, 59)

# Tasa de completitud de registro (registration_started -> registration_completed)
# Decisión técnica: abandono real mencionado en 03_SIMULATION_PARAMETERS.md §4,
# sin dominar el funnel.
REGISTRATION_COMPLETION_RATE = 0.62

# ---------------------------------------------------------------------------
# 1. Catálogos cerrados (03_SIMULATION_PARAMETERS.md §2) — NO SE MODIFICAN
# ---------------------------------------------------------------------------

COUNTRIES = [
    "Mexico", "Brazil", "Colombia", "Argentina", "Peru", "Chile", "Venezuela",
    "Ecuador", "Bolivia", "Guatemala", "Dominican Republic", "Honduras",
    "Paraguay", "Uruguay",
]
# Pesos con variabilidad realista, sin fijar un "país ganador" en Activation
# (el peso solo determina volumen de cuentas, no resultados).
COUNTRY_WEIGHTS = [16, 15, 12, 10, 8, 7, 6, 6, 5, 4, 4, 3, 2, 2]

ROLES = [
    "Marketing Manager", "Marketing Director", "Growth Manager", "Growth Director",
    "Product Manager", "Product Director", "Data Analyst", "Business Analyst",
    "BI Analyst", "Data Scientist", "Sales Manager", "Sales Director",
    "Operations Manager", "Operations Director", "Founder / CEO",
]
ROLE_WEIGHTS = [12, 5, 8, 3, 9, 4, 11, 8, 7, 6, 8, 3, 7, 3, 6]

INDUSTRIES = [
    "SaaS / Software", "Financial Services", "Healthcare", "Retail / E-commerce",
    "Education", "Professional Services", "Manufacturing", "Telecommunications",
    "Media / Entertainment", "Travel / Hospitality", "Logistics / Transportation",
    "Real Estate", "Consumer Goods", "Other",
]
INDUSTRY_WEIGHTS = [16, 10, 8, 14, 7, 9, 6, 5, 5, 4, 5, 4, 5, 2]

COMPANY_SIZES = ["1-10", "11-50", "51-200", "201-500", "501-1000", "1001-5000", "5001+"]
COMPANY_SIZE_WEIGHTS = [18, 26, 24, 14, 8, 6, 4]

USE_CASES = [
    "Marketing Analytics", "Sales Analytics", "Product Analytics", "Customer Analytics",
    "Operations Analytics", "Financial Analytics", "Executive Reporting",
    "Business Intelligence", "Performance Monitoring", "Data Exploration",
]
USE_CASE_WEIGHTS = [14, 12, 11, 10, 9, 8, 9, 12, 8, 7]

ACQUISITION_CHANNELS = [
    "Organic Search", "Paid Search", "Paid Social", "Organic Social", "Referral",
    "Direct", "Partner", "Content", "Email", "Event / Webinar",
]
CHANNEL_WEIGHTS = [20, 15, 12, 8, 10, 9, 6, 8, 7, 5]

# Metadata catalogs (decisiones técnicas delegadas por 02_DATA_GENERATION_SPEC.md §17.2)
SOURCE_TYPES = [
    "google_analytics", "salesforce_crm", "postgresql", "google_sheets", "hubspot",
    "stripe", "shopify", "mysql", "bigquery", "facebook_ads",
]
SOURCE_TYPE_WEIGHTS = [16, 10, 11, 14, 9, 8, 8, 10, 7, 7]

DASHBOARD_ORIGINS = ["template", "from_scratch"]
DASHBOARD_ORIGIN_WEIGHTS = [55, 45]

INSIGHT_TYPES = ["trend", "anomaly", "comparison", "forecast", "summary"]
INSIGHT_TYPE_WEIGHTS = [28, 14, 22, 14, 22]

FEATURES = [
    "filters", "sharing", "export", "alerts", "custom_fields",
    "scheduled_reports", "api_access", "annotations", "drill_down", "forecasting",
]
FEATURE_WEIGHTS = [18, 14, 13, 10, 8, 9, 6, 8, 8, 6]

FIRST_NAMES = [
    "Maria", "Jose", "Ana", "Juan", "Laura", "Carlos", "Camila", "Luis", "Valentina",
    "Diego", "Sofia", "Andres", "Daniela", "Miguel", "Paula", "Javier", "Isabella",
    "Ricardo", "Gabriela", "Fernando", "Lucia", "Sebastian", "Natalia", "Alejandro",
    "Carolina", "Rodrigo", "Mariana", "Felipe", "Andrea", "Eduardo", "Valeria",
    "Ivan", "Patricia", "Rafael", "Monica", "Gustavo", "Adriana", "Marcelo",
    "Fernanda", "Emilio",
]
LAST_NAMES = [
    "Garcia", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Perez",
    "Sanchez", "Ramirez", "Torres", "Flores", "Rivera", "Gomez", "Diaz", "Reyes",
    "Cruz", "Morales", "Ortiz", "Gutierrez", "Chavez", "Ramos", "Silva", "Vargas",
    "Castro", "Rojas", "Mendoza", "Jimenez", "Aguilar", "Vega", "Contreras",
]

DIMENSION_CATALOGS = {
    "country": COUNTRIES,
    "role": ROLES,
    "industry": INDUSTRIES,
    "company_size": COMPANY_SIZES,
    "use_case": USE_CASES,
    "acquisition_channel": ACQUISITION_CHANNELS,
}

# Sigmas de calibración de escala general (no de dirección por valor):
# magnitud elegida una sola vez, antes de observar ningún resultado, para
# que la heterogeneidad entre segmentos sea real pero no domine el sistema.
SIGMA_FUNNEL_LOGIT = 0.10       # por dimensión, en espacio logit
SIGMA_SPEED_LOG_HOURS = 0.15    # por dimensión, en espacio log-horas
SIGMA_CONVERSION_PROB = 0.02    # por dimensión, en espacio de probabilidad

# Efectos aleatorios por valor de catálogo, generados con la semilla fija.
# Nadie elige qué país/rol/industria/tamaño/use_case/canal "gana" -- lo
# decide random.gauss(). Se documentan íntegros en generation_params.json.
CATEGORY_FUNNEL_EFFECT = {
    dim: {val: random.gauss(0, SIGMA_FUNNEL_LOGIT) for val in values}
    for dim, values in DIMENSION_CATALOGS.items()
}
CATEGORY_SPEED_EFFECT = {
    dim: {val: random.gauss(0, SIGMA_SPEED_LOG_HOURS) for val in values}
    for dim, values in DIMENSION_CATALOGS.items()
}
CATEGORY_CONVERSION_EFFECT = {
    dim: {val: random.gauss(0, SIGMA_CONVERSION_PROB) for val in values}
    for dim, values in DIMENSION_CATALOGS.items()
}


def funnel_shift_for(identity):
    return sum(CATEGORY_FUNNEL_EFFECT[dim][identity[dim]] for dim in DIMENSION_CATALOGS)


def speed_shift_for(identity):
    return sum(CATEGORY_SPEED_EFFECT[dim][identity[dim]] for dim in DIMENSION_CATALOGS)


def conversion_shift_for(identity):
    return sum(CATEGORY_CONVERSION_EFFECT[dim][identity[dim]] for dim in DIMENSION_CATALOGS)


COMPANY_WORDS = [
    "nova", "cumbre", "vertex", "orbita", "andina", "azul", "delta", "prisma",
    "raiz", "lumen", "meridian", "polo", "cielo", "bosque", "sol", "atlas",
    "faro", "onda", "cauce", "tierra",
]


# ---------------------------------------------------------------------------
# 2. Utilidades
# ---------------------------------------------------------------------------

def weighted_choice(options, weights):
    return random.choices(options, weights=weights, k=1)[0]


def random_alnum(length):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def clamp(value, lo, hi):
    return max(lo, min(hi, value))


def logit(p):
    p = clamp(p, 1e-6, 1 - 1e-6)
    return math.log(p / (1 - p))


def sigmoid(x):
    x = clamp(x, -30, 30)
    return 1 / (1 + math.exp(-x))


def random_datetime_in_july():
    """Fecha uniforme por día dentro de julio, hora con sesgo a horario laboral."""
    day = random.randint(1, 31)
    # hora sesgada hacia horario laboral (normal truncada 8-20h)
    hour = clamp(int(round(random.gauss(14, 4))), 0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return datetime(2026, 7, day, hour, minute, second)


def lognormal_minutes(mean_minutes, sigma, min_minutes, max_minutes):
    mu = math.log(mean_minutes)
    val = random.lognormvariate(mu, sigma)
    return clamp(val, min_minutes, max_minutes)


# ---------------------------------------------------------------------------
# 3. Generación de identidades (pre-account universe)
# ---------------------------------------------------------------------------

n_registration_started = round(N_COMPLETED / REGISTRATION_COMPLETION_RATE)
n_never_completed = n_registration_started - N_COMPLETED

print(f"registration_started total: {n_registration_started}")
print(f"registration_completed (users.csv): {N_COMPLETED}")
print(f"abandonos de registro (nunca completan): {n_never_completed}")

anonymous_ids = set()


def new_anonymous_id():
    while True:
        aid = "A" + random_alnum(7)
        if aid not in anonymous_ids:
            anonymous_ids.add(aid)
            return aid


def new_session_id():
    return "S" + random_alnum(7)


# Cada identidad: dict con anonymous_id, registration_started_ts,
# completes (bool), registration_completed_ts (si completes)
identities = []
for i in range(n_registration_started):
    completes = i < N_COMPLETED  # asignaremos completitud tras shuffle
    identities.append({"completes": completes})

random.shuffle(identities)  # evita cualquier correlación con orden de generación

for idx, identity in enumerate(identities):
    identity["anonymous_id"] = new_anonymous_id()
    if identity["completes"]:
        signup_ts = random_datetime_in_july()
        gap_minutes = lognormal_minutes(mean_minutes=8, sigma=1.1, min_minutes=1, max_minutes=180)
        reg_started_ts = signup_ts - timedelta(minutes=gap_minutes)
        identity["registration_completed_ts"] = signup_ts
        identity["registration_started_ts"] = reg_started_ts
    else:
        # Identidades que abandonan: se distribuyen también en julio 2026
        # (misma ventana de adquisición que la cohorte completada).
        reg_started_ts = random_datetime_in_july()
        identity["registration_started_ts"] = reg_started_ts
        identity["registration_completed_ts"] = None

completed_identities = [i for i in identities if i["completes"]]
assert len(completed_identities) == N_COMPLETED

# ---------------------------------------------------------------------------
# 4. Asignación de user_id y dimensiones de usuario (independiente del
#    comportamiento posterior — ver principio anti-fabricación en el docstring)
# ---------------------------------------------------------------------------

for idx, identity in enumerate(completed_identities):
    identity["user_id"] = f"U{idx + 1:05d}"
    identity["country"] = weighted_choice(COUNTRIES, COUNTRY_WEIGHTS)
    identity["role"] = weighted_choice(ROLES, ROLE_WEIGHTS)
    identity["industry"] = weighted_choice(INDUSTRIES, INDUSTRY_WEIGHTS)
    identity["company_size"] = weighted_choice(COMPANY_SIZES, COMPANY_SIZE_WEIGHTS)
    identity["use_case"] = weighted_choice(USE_CASES, USE_CASE_WEIGHTS)
    identity["acquisition_channel"] = weighted_choice(ACQUISITION_CHANNELS, CHANNEL_WEIGHTS)
    fn = random.choice(FIRST_NAMES)
    ln = random.choice(LAST_NAMES)
    identity["first_name"] = fn
    identity["last_name"] = ln
    company_word = random.choice(COMPANY_WORDS)
    domain_suffix = random.choice(["io", "co", "app", "tech", "biz"])
    identity["email"] = (
        f"{fn.lower()}.{ln.lower()}{idx % 97}@{company_word}{random.randint(1,999)}.{domain_suffix}"
    )

# ---------------------------------------------------------------------------
# 5. Simulación del funnel post-signup (independiente de las dimensiones)
# ---------------------------------------------------------------------------

# Probabilidades de transición (decisión técnica: friccion plausible en cada
# paso, sin que ningún paso domine artificialmente el resto — todas quedan en
# un rango 0.70-0.92, ninguna preseleccionada como "el" bottleneck).
P_ONBOARDING_STARTED = 0.90
P_PROFILE_COMPLETED = 0.87
P_ONBOARDING_COMPLETED = 0.90
P_DATA_SOURCE_CONNECTED = 0.83
P_DASHBOARD_CREATED = 0.80
P_INSIGHT_VIEWED = 0.78

for identity in completed_identities:
    signup_ts = identity["registration_completed_ts"]

    identity["onboarding_started_ts"] = None
    identity["profile_completed_ts"] = None
    identity["onboarding_completed_ts"] = None
    identity["data_source_connected_ts"] = None
    identity["dashboard_created_ts"] = None
    identity["insight_viewed_ts"] = None

    # Desplazamiento de propensión de este usuario a través de sus 6
    # dimensiones (ver CATEGORY_FUNNEL_EFFECT arriba). Se aplica igual a las
    # 6 transiciones del funnel -- no privilegia ningún paso en particular.
    f_shift = funnel_shift_for(identity)
    p_onb_started = sigmoid(logit(P_ONBOARDING_STARTED) + f_shift)
    p_profile = sigmoid(logit(P_PROFILE_COMPLETED) + f_shift)
    p_onb_completed = sigmoid(logit(P_ONBOARDING_COMPLETED) + f_shift)
    p_dsc = sigmoid(logit(P_DATA_SOURCE_CONNECTED) + f_shift)
    p_dash = sigmoid(logit(P_DASHBOARD_CREATED) + f_shift)
    p_insight = sigmoid(logit(P_INSIGHT_VIEWED) + f_shift)

    if random.random() > p_onb_started:
        continue
    ts = signup_ts + timedelta(minutes=lognormal_minutes(45, 1.3, 1, 2880))
    if ts > OBSERVATION_CUTOFF:
        continue
    identity["onboarding_started_ts"] = ts

    if random.random() > p_profile:
        continue
    ts2 = ts + timedelta(minutes=lognormal_minutes(20, 1.1, 1, 720))
    if ts2 > OBSERVATION_CUTOFF:
        continue
    identity["profile_completed_ts"] = ts2

    if random.random() > p_onb_completed:
        continue
    ts3 = ts2 + timedelta(minutes=lognormal_minutes(12, 1.0, 1, 480))
    if ts3 > OBSERVATION_CUTOFF:
        continue
    identity["onboarding_completed_ts"] = ts3

    # --- Tiempo total desde onboarding_completed hasta completar First Value:
    # una única variable continua con cola pesada, de la que se derivan los
    # tres tramos. Esto crea variabilidad genuina de velocidad hacia First
    # Value (rápido / tardío / nunca) sin fijar de antemano proporciones
    # exactas por grupo -- la proporción que cae en cada lado de la ventana
    # de 7 días es una consecuencia de la distribución, no un parámetro
    # impuesto directamente. La mediana se desplaza levemente según las
    # dimensiones del usuario (CATEGORY_SPEED_EFFECT), reflejando que
    # distintos perfiles pueden avanzar a distinto ritmo -- sin fijar de
    # antemano cuál perfil es más rápido.
    speed_shift = speed_shift_for(identity)
    mu = math.log(48.0) + speed_shift  # mediana base ~48h (2 días)
    total_fv_hours = clamp(random.lognormvariate(mu, 1.6), 0.15, 1440)

    # Se reparte el tiempo total entre los tres tramos con pesos aleatorios
    # (no fijos), preservando la posibilidad de que cualquier tramo sea el
    # más lento para un usuario dado.
    w1, w2, w3 = random.random() + 0.05, random.random() + 0.05, random.random() + 0.05
    wsum = w1 + w2 + w3
    h1, h2, h3 = (total_fv_hours * w1 / wsum, total_fv_hours * w2 / wsum, total_fv_hours * w3 / wsum)

    if random.random() > p_dsc:
        continue
    ts4 = ts3 + timedelta(hours=h1)
    if ts4 > OBSERVATION_CUTOFF:
        continue
    identity["data_source_connected_ts"] = ts4

    if random.random() > p_dash:
        continue
    ts5 = ts4 + timedelta(hours=h2)
    if ts5 > OBSERVATION_CUTOFF:
        continue
    identity["dashboard_created_ts"] = ts5

    if random.random() > p_insight:
        continue
    ts6 = ts5 + timedelta(hours=h3)
    if ts6 > OBSERVATION_CUTOFF:
        continue
    identity["insight_viewed_ts"] = ts6

# ---------------------------------------------------------------------------
# 6. Comportamiento adicional (Behavior family) y señales de engagement
#    (se usan luego, de forma agregada, para converted_to_paid — nunca la
#    condición de Activation ≤7 días).
# ---------------------------------------------------------------------------

for identity in completed_identities:
    signup_ts = identity["registration_completed_ts"]
    stage_reached = sum(
        1
        for k in (
            "onboarding_started_ts", "profile_completed_ts", "onboarding_completed_ts",
            "data_source_connected_ts", "dashboard_created_ts", "insight_viewed_ts",
        )
        if identity[k] is not None
    )

    lam = 1.5 + 1.4 * stage_reached + random.uniform(-0.5, 1.5)
    n_sessions = max(0, int(round(random.gauss(lam, lam * 0.4))))
    identity["n_sessions"] = n_sessions

    session_ts_list = []
    for _ in range(n_sessions):
        offset_days = random.uniform(0, 60)
        ts = signup_ts + timedelta(days=offset_days)
        if ts <= OBSERVATION_CUTOFF and ts >= signup_ts:
            session_ts_list.append(ts)
    identity["session_ts_list"] = sorted(session_ts_list)

    identity["dashboard_viewed_ts_list"] = []
    if identity["dashboard_created_ts"] is not None:
        n_views = max(0, int(round(random.gauss(2.5 + stage_reached * 0.3, 1.8))))
        for _ in range(n_views):
            offset_days = random.uniform(0, 55)
            ts = identity["dashboard_created_ts"] + timedelta(days=offset_days)
            if ts <= OBSERVATION_CUTOFF:
                identity["dashboard_viewed_ts_list"].append(ts)

    identity["feature_used_events"] = []
    if identity["onboarding_completed_ts"] is not None:
        n_features = max(0, int(round(random.gauss(1.2 + stage_reached * 0.5, 1.5))))
        for _ in range(n_features):
            offset_days = random.uniform(0, 55)
            ts = identity["onboarding_completed_ts"] + timedelta(days=offset_days)
            if ts <= OBSERVATION_CUTOFF:
                feature = weighted_choice(FEATURES, FEATURE_WEIGHTS)
                identity["feature_used_events"].append((ts, feature))

    identity["dashboard_shared_ts_list"] = []
    if identity["dashboard_created_ts"] is not None and random.random() < 0.16:
        n_shared = random.randint(1, 2)
        for _ in range(n_shared):
            offset_days = random.uniform(0, 50)
            ts = identity["dashboard_created_ts"] + timedelta(days=offset_days)
            if ts <= OBSERVATION_CUTOFF:
                identity["dashboard_shared_ts_list"].append(ts)

    # Extra repeticiones de milestones de First Value (para que el orden
    # crudo de eventos no quede rígidamente fijado — 02_DATA_GENERATION_SPEC.md §7)
    identity["extra_source_events"] = []
    if identity["data_source_connected_ts"] is not None and random.random() < 0.28:
        for _ in range(random.randint(1, 2)):
            offset_days = random.uniform(0.5, 50)
            ts = identity["data_source_connected_ts"] + timedelta(days=offset_days)
            if ts <= OBSERVATION_CUTOFF:
                identity["extra_source_events"].append(ts)

    identity["extra_dashboard_events"] = []
    if identity["dashboard_created_ts"] is not None and random.random() < 0.24:
        for _ in range(random.randint(1, 2)):
            offset_days = random.uniform(0.5, 50)
            ts = identity["dashboard_created_ts"] + timedelta(days=offset_days)
            if ts <= OBSERVATION_CUTOFF:
                identity["extra_dashboard_events"].append(ts)

    identity["extra_insight_events"] = []
    if identity["insight_viewed_ts"] is not None:
        n_extra_insight = max(0, int(round(random.gauss(1.5 + stage_reached * 0.2, 1.5))))
        for _ in range(n_extra_insight):
            offset_days = random.uniform(0.2, 50)
            ts = identity["insight_viewed_ts"] + timedelta(days=offset_days)
            if ts <= OBSERVATION_CUTOFF:
                identity["extra_insight_events"].append(ts)

# ---------------------------------------------------------------------------
# 7. converted_to_paid — mecanismo basado en señales agregadas de engagement,
#    NUNCA en el umbral de 7 dias ni en un booleano equivalente a Activation.
# ---------------------------------------------------------------------------

BASE_CONVERSION_RATE = 0.11

for identity in completed_identities:
    n_sessions = identity["n_sessions"]
    n_features = len(set(f for _, f in identity["feature_used_events"]))
    shared = 1 if identity["dashboard_shared_ts_list"] else 0
    n_dashboard_views = len(identity["dashboard_viewed_ts_list"])

    score = (
        BASE_CONVERSION_RATE
        + 0.028 * math.log1p(n_sessions)
        + 0.02 * n_features
        + 0.05 * shared
        + 0.01 * math.log1p(n_dashboard_views)
        + conversion_shift_for(identity)  # efecto difuso por dimensiones de usuario
        + random.gauss(0, 0.07)  # ruido individual, evita determinismo
    )
    p_convert = clamp(score, 0.01, 0.95)
    identity["converted_to_paid"] = 1 if random.random() < p_convert else 0

# ---------------------------------------------------------------------------
# 8. Escritura de users.csv
# ---------------------------------------------------------------------------

users_path = os.path.join(OUT_DIR, "users.csv")
with open(users_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "user_id", "first_name", "last_name", "email", "country", "signup_date",
        "role", "industry", "company_size", "use_case", "acquisition_channel",
        "converted_to_paid",
    ])
    for identity in sorted(completed_identities, key=lambda x: x["user_id"]):
        writer.writerow([
            identity["user_id"],
            identity["first_name"],
            identity["last_name"],
            identity["email"],
            identity["country"],
            identity["registration_completed_ts"].strftime("%Y-%m-%d %H:%M:%S"),
            identity["role"],
            identity["industry"],
            identity["company_size"],
            identity["use_case"],
            identity["acquisition_channel"],
            identity["converted_to_paid"],
        ])

print(f"users.csv escrito: {users_path}")

# ---------------------------------------------------------------------------
# 9. Escritura de events.csv
# ---------------------------------------------------------------------------

event_rows = []  # (event_timestamp, event_name, user_id, anonymous_id, session_id, metadata_dict)


def add_event(ts, name, user_id, anonymous_id, session_id, metadata=None):
    event_rows.append((ts, name, user_id, anonymous_id, session_id, metadata or {}))


# 9.1 Identidades que abandonan el registro
for identity in identities:
    if identity["completes"]:
        continue
    aid = identity["anonymous_id"]
    sid = new_session_id()
    add_event(identity["registration_started_ts"], "registration_started", None, aid, sid)

# 9.2 Identidades que completan registro
for identity in completed_identities:
    aid = identity["anonymous_id"]
    uid = identity["user_id"]
    sid_reg = new_session_id()
    add_event(identity["registration_started_ts"], "registration_started", None, aid, sid_reg)
    add_event(identity["registration_completed_ts"], "registration_completed", uid, aid, sid_reg)

    if identity["onboarding_started_ts"] is not None:
        sid = new_session_id()
        add_event(identity["onboarding_started_ts"], "onboarding_started", uid, aid, sid)
    if identity["profile_completed_ts"] is not None:
        add_event(identity["profile_completed_ts"], "profile_completed", uid, aid, sid)
    if identity["onboarding_completed_ts"] is not None:
        add_event(identity["onboarding_completed_ts"], "onboarding_completed", uid, aid, sid)

    if identity["data_source_connected_ts"] is not None:
        sid = new_session_id()
        add_event(
            identity["data_source_connected_ts"], "data_source_connected", uid, aid, sid,
            {"source_type": weighted_choice(SOURCE_TYPES, SOURCE_TYPE_WEIGHTS)},
        )
    for ts in identity["extra_source_events"]:
        sid = new_session_id()
        add_event(
            ts, "data_source_connected", uid, aid, sid,
            {"source_type": weighted_choice(SOURCE_TYPES, SOURCE_TYPE_WEIGHTS)},
        )

    if identity["dashboard_created_ts"] is not None:
        sid = new_session_id()
        add_event(
            identity["dashboard_created_ts"], "dashboard_created", uid, aid, sid,
            {"origin": weighted_choice(DASHBOARD_ORIGINS, DASHBOARD_ORIGIN_WEIGHTS)},
        )
    for ts in identity["extra_dashboard_events"]:
        sid = new_session_id()
        add_event(
            ts, "dashboard_created", uid, aid, sid,
            {"origin": weighted_choice(DASHBOARD_ORIGINS, DASHBOARD_ORIGIN_WEIGHTS)},
        )

    if identity["insight_viewed_ts"] is not None:
        sid = new_session_id()
        add_event(
            identity["insight_viewed_ts"], "insight_viewed", uid, aid, sid,
            {"insight_type": weighted_choice(INSIGHT_TYPES, INSIGHT_TYPE_WEIGHTS)},
        )
    for ts in identity["extra_insight_events"]:
        sid = new_session_id()
        add_event(
            ts, "insight_viewed", uid, aid, sid,
            {"insight_type": weighted_choice(INSIGHT_TYPES, INSIGHT_TYPE_WEIGHTS)},
        )

    for ts in identity["session_ts_list"]:
        sid = new_session_id()
        add_event(ts, "session_started", uid, aid, sid)

    for ts in identity["dashboard_viewed_ts_list"]:
        sid = new_session_id()
        add_event(ts, "dashboard_viewed", uid, aid, sid)

    for ts, feature in identity["feature_used_events"]:
        sid = new_session_id()
        add_event(ts, "feature_used", uid, aid, sid, {"feature": feature})

    for ts in identity["dashboard_shared_ts_list"]:
        sid = new_session_id()
        add_event(ts, "dashboard_shared", uid, aid, sid)

# 9.3 Orden cronológico global + asignación de event_id
event_rows.sort(key=lambda r: r[0])

events_path = os.path.join(OUT_DIR, "events.csv")
with open(events_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "event_id", "event_timestamp", "event_name", "user_id", "anonymous_id",
        "session_id", "metadata",
    ])
    for i, (ts, name, uid, aid, sid, metadata) in enumerate(event_rows, start=1):
        writer.writerow([
            f"E{i:07d}",
            ts.strftime("%Y-%m-%d %H:%M:%S"),
            name,
            uid if uid is not None else "",
            aid,
            sid,
            json.dumps(metadata, ensure_ascii=False),
        ])

print(f"events.csv escrito: {events_path} ({len(event_rows)} eventos)")

# ---------------------------------------------------------------------------
# 10. Archivo de reproducibilidad
# ---------------------------------------------------------------------------

params = {
    "seed": SEED,
    "n_completed_users": N_COMPLETED,
    "n_registration_started_total": n_registration_started,
    "n_registration_abandoned": n_never_completed,
    "registration_completion_rate_target": REGISTRATION_COMPLETION_RATE,
    "cohort_start": COHORT_START.isoformat(),
    "cohort_end": COHORT_END.isoformat(),
    "observation_cutoff": OBSERVATION_CUTOFF.isoformat(),
    "funnel_transition_probabilities": {
        "onboarding_started_given_signup": P_ONBOARDING_STARTED,
        "profile_completed_given_onboarding_started": P_PROFILE_COMPLETED,
        "onboarding_completed_given_profile_completed": P_ONBOARDING_COMPLETED,
        "data_source_connected_given_onboarding_completed": P_DATA_SOURCE_CONNECTED,
        "dashboard_created_given_data_source_connected": P_DASHBOARD_CREATED,
        "insight_viewed_given_dashboard_created": P_INSIGHT_VIEWED,
    },
    "converted_to_paid_mechanism": (
        "logistic-ish score = base_rate + f(sessions, distinct_features_used, "
        "dashboard_shared, dashboard_views) + efecto difuso por dimensiones de "
        "usuario (conversion_shift_for) + gaussian noise; NUNCA usa el umbral "
        "de 7 dias ni ningun booleano equivalente a activation_status."
    ),
    "category_effects": {
        "description": (
            "Efectos aleatorios por valor de catalogo (generados con la semilla "
            "fija, nunca elegidos a mano ni reajustados tras observar resultados). "
            "Se suman a traves de las 6 dimensiones para producir un unico "
            "desplazamiento por usuario, aplicado a: (a) las 6 probabilidades de "
            "transicion del funnel en espacio logit, (b) la mediana de tiempo "
            "hacia First Value en espacio log-horas, (c) el score de "
            "converted_to_paid en espacio de probabilidad."
        ),
        "sigma_funnel_logit_per_dimension": SIGMA_FUNNEL_LOGIT,
        "sigma_speed_log_hours_per_dimension": SIGMA_SPEED_LOG_HOURS,
        "sigma_conversion_prob_per_dimension": SIGMA_CONVERSION_PROB,
        "funnel_effect": CATEGORY_FUNNEL_EFFECT,
        "speed_effect": CATEGORY_SPEED_EFFECT,
        "conversion_effect": CATEGORY_CONVERSION_EFFECT,
    },
    "notes": [
        "Las dimensiones de usuario (country, role, industry, company_size, "
        "use_case, acquisition_channel) se asignan sin condicionar el catalogo "
        "en si, pero SI tienen una influencia real (pequeña y difusa, ver "
        "category_effects) sobre el funnel, la velocidad hacia First Value y "
        "converted_to_paid -- para que el diagnostico QUIEN->QUE HACE->QUE "
        "RESULTADO tenga señal genuina que descubrir, sin que ningun valor de "
        "catalogo este diseñado de antemano como ganador o perdedor.",
        "session_started no se genera para identidades pre-account (decision "
        "tecnica: unicamente registration_started/registration_completed antes "
        "de crear cuenta, para mantener el modelo de identidad simple y "
        "coherente con 02_DATA_GENERATION_SPEC.md seccion 5).",
        "El orden entre los tres eventos de First Value no queda rigidamente "
        "fijado a nivel de eventos repetidos: una fraccion de usuarios genera "
        "ocurrencias adicionales de data_source_connected/dashboard_created/"
        "insight_viewed despues de completar la secuencia inicial.",
    ],
}

params_path = os.path.join(OUT_DIR, "generation_params.json")
with open(params_path, "w", encoding="utf-8") as f:
    json.dump(params, f, indent=2, ensure_ascii=False)

print(f"generation_params.json escrito: {params_path}")
