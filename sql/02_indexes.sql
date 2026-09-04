-- Prevent multiple active consultations per patient
CREATE UNIQUE INDEX IF NOT EXISTS idx_active_consult
ON appointments (patient_id)
WHERE status IN ('WAITING', 'IN_CONSULTATION');

-- Supports clinic/date aggregation and ordering
CREATE INDEX IF NOT EXISTS idx_appointments_clinic_created
ON appointments (clinic_id, created_at)
INCLUDE (copay_amount);

-- Supports discharged-appointment materialized-view queries
CREATE INDEX IF NOT EXISTS idx_appointments_discharged
ON appointments (clinic_id, created_at)
INCLUDE (copay_amount)
WHERE status = 'DISCHARGED';


