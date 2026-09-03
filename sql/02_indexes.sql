-- Prevents patients from holding multiple active consultations concurrently
CREATE UNIQUE INDEX idx_active_consult 
ON appointments (patient_id) 
WHERE status IN ('WAITING', 'IN CONSULTATION');


