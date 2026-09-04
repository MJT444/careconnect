# CareConnect Database

## Overview

This project implements CareConnect's healthcare database across PostgreSQL and MongoDB. PostgreSQL manages the relational hospital appointment and HSA (Health Savings Account) system, while MongoDB supports real-time nurse location queries and patient review analytics.

It demonstrates relational schema design, constraints, indexes, triggers, stored procedures, materialized views, window functions, geospatial aggregation, TTL data retention, and multi-faceted analytics.

---

## Project Structure

```text
sql/
├── 01_schema_ddl.sql
├── 02_indexes.sql
├── 03_triggers_and_audit.sql
├── 04_stored_procedures.sql
├── 05_materialized_views.sql
└── 06_window_analytics.sql

mongo/
├── 01_collections_and_indexes.js
├── 02_workflow3_geonear.js
└── 03_workflow4_facet.js

performance/
├── mongo_execution_stats.json
└── postgres_explain_analyzes.txt
```

---

## PostgreSQL

---

## 1. Database Schema — `01_schema_ddl.sql`

This file creates the core database schema.

### Appointment Status

A custom PostgreSQL ENUM is created for appointment states:

- `WAITING`
- `IN_CONSULTATION`
- `DISCHARGED`

### Tables

#### `patients`

Stores patient information and HSA balances.

Fields include:

- `id` — UUID primary key
- `name` — Patient name
- `hsa_balance` — Current HSA balance

A `CHECK` constraint ensures that the HSA balance cannot be negative.

#### `clinics`

Stores clinic information.

Fields include:

- `id` — UUID primary key
- `name` — Clinic name
- `latitude` — Clinic latitude
- `longitude` — Clinic longitude
- `is_accepting_patients` — Indicates whether the clinic is accepting patients

#### `appointments`

Stores appointment information.

Fields include:

- `id` — UUID primary key
- `patient_id` — Reference to the patient
- `clinic_id` — Reference to the clinic
- `copay_amount` — Appointment copay
- `status` — Current appointment status
- `created_at` — Appointment creation timestamp

#### `wallet_audit_logs`

Stores a history of changes to patient HSA balances.

Fields include:

- `id`
- `patient_id`
- `amount_changed`
- `action_type`
- `balance_after`
- `timestamp`

Foreign keys maintain referential integrity between related tables.

---

## 2. Indexes — `02_indexes.sql`

This file creates indexes for performance optimization and business-rule enforcement.

### Active Appointment Constraint

A partial unique index prevents a patient from having multiple active appointments.

Active statuses are:

- `WAITING`
- `IN_CONSULTATION`

```sql
CREATE UNIQUE INDEX idx_active_consult
ON appointments (patient_id)
WHERE status IN ('WAITING', 'IN_CONSULTATION');
```

### Clinic Appointment Index

The `idx_appointments_clinic_created` index supports queries involving:

- Clinic
- Appointment creation time
- Copay amount

### Discharged Appointment Index

The `idx_appointments_discharged` partial index specifically optimizes queries involving discharged appointments.

This is useful for monthly discharge and revenue aggregation.

---

## 3. Triggers & Audit Logging — `03_triggers_and_audit.sql`

This file implements automatic auditing of HSA balance changes.

### Trigger Function

The function `log_hsa_balance_change()` automatically records changes whenever a patient's HSA balance is updated.

The audit entry records:

- Patient ID
- Amount changed
- Transaction type
- Balance after the transaction
- Timestamp

### Transaction Types

- If the balance increases: `CREDIT`
- If the balance decreases: `DEBIT`

### Trigger

The trigger `trg_audit_hsa_balance` runs after an HSA balance update.

This provides an automatic audit trail without requiring application-level logging.

---

## 4. Stored Procedure — `04_stored_procedures.sql`

This file contains the appointment-booking procedure: `sp_book_appointment()`.

The procedure handles both HSA copay deduction and appointment creation.

### Booking Workflow

1. Lock the patient's row using `FOR UPDATE`.
2. Verify that the patient exists.
3. Verify that the clinic exists.
4. Check whether the copay is valid.
5. Check whether the patient has sufficient HSA funds.
6. Deduct the copay from the patient's HSA balance.
7. Create the appointment with status `WAITING`.

### Concurrency Control

The patient's row is locked using:

```sql
SELECT ...
FROM patients
WHERE id = p_patient_id
FOR UPDATE;
```

This helps prevent concurrent transactions from spending the same HSA balance.

The HSA update also automatically creates an audit record through the trigger defined in `03_triggers_and_audit.sql`.

---

## 5. Materialized View — `05_materialized_views.sql`

This file creates the materialized view `mv_clinic_monthly_discharges`.

The view stores monthly discharge and copay-revenue statistics for each clinic.

### Metrics

The materialized view calculates:

- Clinic ID
- Clinic name
- Month
- Total discharged appointments
- Total copay revenue

Example:

| Clinic   | Month   | Total Discharges | Copay Revenue |
|----------|---------|-------------------|----------------|
| Clinic A | 2026-08 | 120               | 24000          |
| Clinic B | 2026-08 | 95                | 19500          |

### Concurrent Refresh

A unique index is created on `(clinic_id, month_period)`.

This allows the materialized view to be refreshed concurrently using:

```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_clinic_monthly_discharges;
```

A helper function is also provided: `refresh_clinic_monthly_mv()`, which performs the concurrent refresh.

---

## 6. Window Analytics — `06_window_analytics.sql`

This file performs revenue analytics using PostgreSQL window functions.

### Daily Clinic Revenue

The query first calculates the total copay revenue generated by each clinic for each day.

`clinic_id` + `date` → daily revenue

### 7-Day Moving Average

A seven-day moving average is calculated using:

```sql
AVG(daily_copay_total) OVER (
    PARTITION BY clinic_id
    ORDER BY rev_date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
)
```

This helps analyze short-term revenue trends for each clinic.

### Total Clinic Revenue

The total revenue generated by each clinic is calculated using:

```sql
SUM(daily_copay_total) OVER (
    PARTITION BY clinic_id
)
```

### Global Revenue Ranking

Clinics are ranked according to their total revenue using:

```sql
DENSE_RANK() OVER (
    ORDER BY total_clinic_revenue DESC
)
```

### Final Output

The query produces:

- Clinic name
- Revenue date
- Daily copay revenue
- 7-day moving average
- Global revenue rank

---

## PostgreSQL Concepts Demonstrated

This project demonstrates the following PostgreSQL concepts:

- Relational database design
- DDL
- UUID primary keys
- Foreign keys
- CHECK constraints
- Custom ENUM types
- Partial indexes
- Unique indexes
- Covering indexes using `INCLUDE`
- Row-level locking with `FOR UPDATE`
- PL/pgSQL procedures
- Trigger functions
- Automatic audit logging
- Materialized views
- Concurrent materialized-view refresh
- Aggregate functions
- Common Table Expressions (CTEs)
- Window functions
- Moving averages
- `DENSE_RANK()`
- Transaction-safe HSA deductions
- Query performance optimization

---

## Execution Order

The SQL files should be executed in the following order:

```
01_schema_ddl.sql
        ↓
02_indexes.sql
        ↓
03_triggers_and_audit.sql
        ↓
04_stored_procedures.sql
        ↓
05_materialized_views.sql
        ↓
06_window_analytics.sql
```

The order is important because later files depend on database objects created in earlier files.

---

## Requirements

- PostgreSQL
- `pgcrypto` extension for UUID generation using `gen_random_uuid()`

If required, enable the extension with:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

---

## Summary

The project models a healthcare appointment system where patients maintain HSA balances that can be used to pay appointment copays.

The database provides:

- Data integrity through constraints and foreign keys
- Concurrency protection through row-level locking
- Automatic financial auditing through triggers
- Efficient querying through indexes
- Precomputed reporting through materialized views
- Advanced analytics through PostgreSQL window functions

Together, these components demonstrate a robust PostgreSQL database design for managing healthcare appointments, patient HSA funds, financial auditing, and clinic revenue analytics.

---

## MongoDB Workflows

The MongoDB scripts use the `medical_db` database and implement Workflows 3 and 4 of the assignment.

### Collections

#### `NursePings`

Stores real-time geospatial location logs for mobile nurses. The collection is created by `mongo/01_collections_and_indexes.js` with:

- A `2dsphere` index on `location`, required by `$geoNear`
- A TTL index on `created_at` with `expireAfterSeconds: 7200`

Expected document shape:

```json
{
  "nurse_id": "<UUID/INT>",
  "location": { "type": "Point", "coordinates": [lng, lat] },
  "status": "ACTIVE | OFFLINE",
  "created_at": "ISODate"
}
```

#### `PatientReviews`

Stores patient-submitted reviews of clinics or appointments.

Expected document shape:

```json
{
  "patient_id": "<UUID>",
  "clinic_id": "<UUID>",
  "rating": "1-5",
  "tags": ["string", "..."],
  "created_at": "ISODate"
}
```

Neither collection has enforced validation. These field names are the contracts expected by the aggregation scripts; update the pipelines if the seeder scripts use different names.

### Workflow 3 — Nearest Mobile Nurse

`mongo/02_workflow3_geonear.js` finds the closest currently active nurse for coordinates supplied by the client application.

- Patient coordinates are not stored in PostgreSQL. The script uses the example `patientLng` and `patientLat` values at the top of the file.
- The search radius is capped at 5 km using `maxDistanceMeters = 5000`.
- The pipeline filters to `status: "ACTIVE"`, finds pings within the radius, keeps each nurse's most recent ping, sorts by distance, and returns the closest nurse.
- `$geoNear` requires the `NursePings.location` `2dsphere` index; without it, the stage cannot run.

Execute it with:

```bash
mongosh "mongodb://admin:password@localhost:27017/medical_db?authSource=admin" mongo/02_workflow3_geonear.js
```

### Workflow 4 — Multi-Faceted Review Analytics

`mongo/03_workflow4_facet.js` computes three statistics over `PatientReviews` in one aggregation using `$facet`:

1. `ratingDistribution` counts reviews for each star rating from 1 to 5.
2. `topTags` unwinds `tags`, counts tag occurrences, and returns the 10 most frequent tags.
3. `overallAverage` calculates the mean rating and total review count.

`$facet` scans the full input collection for each sub-pipeline by design. There is no equivalent index requirement to `$geoNear`; the explain proof should demonstrate correctness and reasonable execution time at 100k+ scale.

Execute it with:

```bash
mongosh "mongodb://admin:password@localhost:27017/medical_db?authSource=admin" mongo/03_workflow4_facet.js
```

### MongoDB Explain Plans

Detailed execution statistics are saved in `performance/mongo_execution_stats.json`.

#### Workflow 3

- Uses the `GEO_NEAR_2DSPHERE` stage backed by the `location_2dsphere` index.
- Applies an additional `FETCH` filter for active status.
- Sorts by distance and limits the result to one nurse.

#### Workflow 4

- Starts with a `COLLSCAN` because `$facet` must scan the full input to compute all analytics.
- Projects `rating` and `tags` before splitting into three parallel sub-pipelines.
- Uses grouping and sorting for `ratingDistribution`, unwinding followed by grouping, sorting, and limiting for `topTags`, and grouping for `overallAverage`.

---

## Combined Execution Order

Run the PostgreSQL files in this order because later files depend on objects created earlier:

```text
sql/01_schema_ddl.sql
        ↓
sql/02_indexes.sql
        ↓
sql/03_triggers_and_audit.sql
        ↓
sql/04_stored_procedures.sql
        ↓
sql/05_materialized_views.sql
        ↓
sql/06_window_analytics.sql
```

Initialize MongoDB collections and indexes before running its workflows:

```bash
mongosh "mongodb://admin:password@localhost:27017/medical_db?authSource=admin" mongo/01_collections_and_indexes.js
```

---

## Requirements

- PostgreSQL with the `pgcrypto` extension
- MongoDB and `mongosh`
- MongoDB database: `medical_db`

If required, enable PostgreSQL UUID generation with:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

The MongoDB commands assume the local connection string shown above. Update the credentials or host as needed.

---

## Summary

CareConnect combines PostgreSQL's transactional relational model with MongoDB's geospatial and aggregation capabilities. PostgreSQL provides data integrity, concurrency protection, financial auditing, efficient reporting, and revenue analytics. MongoDB provides expiring nurse location data, nearest-active-nurse discovery, and review analytics through a single `$facet` pipeline.