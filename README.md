# Hospital Appointment & HSA Management Database

## Overview

This project implements a PostgreSQL-based hospital appointment and HSA (Health Savings Account) management system.

It demonstrates database concepts including relational schema design, constraints, indexes, triggers, stored procedures, materialized views, and window functions.

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
```

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

## Database Concepts Demonstrated

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