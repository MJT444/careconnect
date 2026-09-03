import csv
import io
import os
import random
import time
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from faker import Faker
from sqlalchemy import create_engine
from dotenv import load_dotenv

fake = Faker()
load_dotenv()

DB_URI = os.getenv("DB_URI")
if not DB_URI:
    raise RuntimeError("DB_URI is missing from the .env file")

NUM_PATIENTS = 10_000
NUM_CLINICS = 100
NUM_AUDIT_LOGS = 100_000
NUM_APPOINTMENTS = 100_000


def copy_rows(connection, table, columns, rows):
    buffer = io.StringIO()
    writer = csv.writer(
        buffer,
        delimiter="\t",
        lineterminator="\n",
        quoting=csv.QUOTE_MINIMAL,
    )

    for row in rows:
        # Convert True/False booleans to lowercase 'true'/'false' for Postgres COPY compatibility
        processed_row = [
            str(item).lower() if isinstance(item, bool) else item for item in row
        ]
        writer.writerow(processed_row)

    buffer.seek(0)

    column_list = ",".join(f'"{column}"' for column in columns)

    # FIX: Cleaned up the delimiter syntax to prevent Postgres one-byte character errors
    copy_sql = f"""
        COPY "{table}" ({column_list})
        FROM STDIN
        WITH (FORMAT CSV, DELIMITER '\t')
    """

    with connection.cursor() as cursor:
        cursor.copy_expert(copy_sql, buffer)


def generate_patients():
    patients = []

    for _ in range(NUM_PATIENTS):
        patients.append(
            {
                "id": uuid.uuid4(),
                "name": fake.name(),
                "balance": Decimal(random.randint(1_000, 10_000)),
            }
        )

    return patients


def generate_clinics():
    return [
        {
            "id": uuid.uuid4(),
            "name": f"{fake.city()} Care Clinic",
            "latitude": round(random.uniform(43.5, 45.5), 6),
            "longitude": round(random.uniform(-79.8, -78.5), 6),
            "is_accepting_patients": random.choices(
                [True, False],
                weights=[90, 10],
                k=1,
            )[0],
        }
        for _ in range(NUM_CLINICS)
    ]


def generate_audit_logs(patients):
    balances = {patient["id"]: patient["balance"] for patient in patients}
    audit_logs = []

    start_date = datetime.now() - timedelta(days=730)

    for index in range(NUM_AUDIT_LOGS):
        patient_id = random.choice(list(balances))
        current_balance = balances[patient_id]

        amount = (
            Decimal(random.randint(100, 50_000)) / Decimal("100")
        ).quantize(Decimal("0.01"))

        if current_balance >= amount and random.choice([True, False]):
            amount_changed = -amount
            action_type = "DEBIT"
        else:
            amount_changed = amount
            action_type = "CREDIT"

        new_balance = (current_balance + amount_changed).quantize(
            Decimal("0.01")
        )
        balances[patient_id] = new_balance

        audit_logs.append(
            (
                patient_id,
                amount_changed,
                action_type,
                new_balance,
                start_date + timedelta(seconds=index * 630),
            )
        )

    # Store each patient's final balance in patients.hsa_balance.
    for patient in patients:
        patient["balance"] = balances[patient["id"]]

    return audit_logs


def generate_appointments(patients, clinics):
    start_date = datetime.now() - timedelta(days=730)

    return [
        (
            random.choice(patients)["id"],
            random.choice(clinics)["id"],
            (
                Decimal(random.randint(0, 20_000)) / Decimal("100")
            ).quantize(Decimal("0.01")),
            "DISCHARGED",
            start_date + timedelta(seconds=random.randint(0, 63_072_000)),
        )
        for _ in range(NUM_APPOINTMENTS)
    ]


def seed_database():
    start_time = time.time()
    engine = create_engine(DB_URI)
    connection = engine.raw_connection()

    try:
        patients = generate_patients()
        clinics = generate_clinics()
        audit_logs = generate_audit_logs(patients)
        appointments = generate_appointments(patients, clinics)

        copy_rows(
            connection,
            "patients",
            ["id", "name", "hsa_balance"],
            [
                (p["id"], p["name"], p["balance"])
                for p in patients
            ],
        )

        copy_rows(
            connection,
            "clinics",
            [
                "id",
                "name",
                "latitude",
                "longitude",
                "is_accepting_patients",
            ],
            [
                (
                    c["id"],
                    c["name"],
                    c["latitude"],
                    c["longitude"],
                    c["is_accepting_patients"],
                )
                for c in clinics
            ],
        )

        copy_rows(
            connection,
            "wallet_audit_logs",
            [
                "patient_id",
                "amount_changed",
                "action_type",
                "balance_after",
                "timestamp",
            ],
            audit_logs,
        )

        copy_rows(
            connection,
            "appointments",
            [
                "patient_id",
                "clinic_id",
                "copay_amount",
                "status",
                "created_at",
            ],
            appointments,
        )

        connection.commit()

        print("Seeding completed successfully.")
        print(f"Patients: {len(patients):,}")
        print(f"Clinics: {len(clinics):,}")
        print(f"Audit logs: {len(audit_logs):,}")
        print(f"Appointments: {len(appointments):,}")
        print(f"Elapsed time: {time.time() - start_time:.2f} seconds")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
        engine.dispose()


if __name__ == "__main__":
    seed_database()
