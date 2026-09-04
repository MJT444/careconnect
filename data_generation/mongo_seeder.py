import random
from datetime import datetime, timedelta, timezone

from faker import Faker
from pymongo import MongoClient

fake = Faker()

MONGO_URI = "mongodb://localhost:27017/medical_db"
DB_NAME = "medical_db"

NURSE_COUNT = 500
TARGET_PINGS = 500_000
PINGS_PER_NURSE = TARGET_PINGS // NURSE_COUNT

REVIEW_COUNT = 20_000
BATCH_SIZE = 5_000

CENTER_LAT = 17.3850
CENTER_LNG = 78.4867
JITTER_DEGREES = 0.03

PING_MAX_AGE_MINUTES = 100

REVIEW_TAGS = [
    "friendly", "professional", "long_wait", "clean_facility",
    "rushed", "attentive", "great_bedside_manner", "on_time",
    "helpful_staff", "would_recommend", "poor_communication",
    "compassionate", "efficient", "outdated_equipment",
]


def random_point(center_lat, center_lng, jitter):
    lat = center_lat + random.uniform(-jitter, jitter)
    lng = center_lng + random.uniform(-jitter, jitter)
    return {"type": "Point", "coordinates": [round(lng, 6), round(lat, 6)]}


def generate_nurse_pings():
    now = datetime.now(timezone.utc)
    nurse_ids = [fake.uuid4() for _ in range(NURSE_COUNT)]

    for nurse_id in nurse_ids:
        batch = []
        for _ in range(PINGS_PER_NURSE):
            age_minutes = random.uniform(0, PING_MAX_AGE_MINUTES)
            batch.append({
                "nurse_id": nurse_id,
                "location": random_point(CENTER_LAT, CENTER_LNG, JITTER_DEGREES),
                "status": random.choices(
                    ["ACTIVE", "OFFLINE"], weights=[0.7, 0.3]
                )[0],
                "created_at": now - timedelta(minutes=age_minutes),
            })
            if len(batch) >= BATCH_SIZE:
                yield batch
                batch = []
        if batch:
            yield batch


def generate_patient_reviews():
    patient_ids = [fake.uuid4() for _ in range(2_000)]
    clinic_ids = [fake.uuid4() for _ in range(200)]

    batch = []
    for _ in range(REVIEW_COUNT):
        batch.append({
            "patient_id": random.choice(patient_ids),
            "clinic_id": random.choice(clinic_ids),
            "rating": random.choices(
                [1, 2, 3, 4, 5], weights=[0.05, 0.08, 0.15, 0.32, 0.40]
            )[0],
            "tags": random.sample(REVIEW_TAGS, k=random.randint(1, 3)),
            "created_at": fake.date_time_between(
                start_date="-90d", end_date="now", tzinfo=timezone.utc
            ),
        })
        if len(batch) >= BATCH_SIZE:
            yield batch
            batch = []
    if batch:
        yield batch


def main():
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    print("Clearing existing NursePings and PatientReviews...")
    db.NursePings.delete_many({})
    db.PatientReviews.delete_many({})

    print(f"Seeding ~{TARGET_PINGS:,} NursePings across {NURSE_COUNT} nurses...")
    inserted = 0
    for batch in generate_nurse_pings():
        db.NursePings.insert_many(batch, ordered=False)
        inserted += len(batch)
        print(f"  {inserted:,} pings inserted", end="\r")
    print(f"\nDone: {inserted:,} NursePings documents.")

    print(f"Seeding {REVIEW_COUNT:,} PatientReviews...")
    inserted = 0
    for batch in generate_patient_reviews():
        db.PatientReviews.insert_many(batch, ordered=False)
        inserted += len(batch)
        print(f"  {inserted:,} reviews inserted", end="\r")
    print(f"\nDone: {inserted:,} PatientReviews documents.")

    client.close()


if __name__ == "__main__":
    main()