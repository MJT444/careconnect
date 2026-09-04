--  custom ENUM type for appointment status
CREATE TYPE appointment_status AS ENUM ('WAITING', 'IN_CONSULTATION', 'DISCHARGED');

--  patients table
CREATE TABLE patients (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    hsa_balance DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT chk_hsa_balance CHECK (hsa_balance >= 0.00)
);

-- clinics table
CREATE TABLE clinics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    latitude DECIMAL(9,6) NOT NULL,
    longitude DECIMAL(9,6) NOT NULL,
    is_accepting_patients BOOLEAN NOT NULL DEFAULT TRUE
);

--  wallet_audit_logs table
CREATE TABLE wallet_audit_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    patient_id UUID NOT NULL,
    amount_changed DECIMAL(10,2) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    balance_after DECIMAL(10,2) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE
);

--  appointments table
CREATE TABLE appointments (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    patient_id UUID NOT NULL,
    clinic_id UUID NOT NULL,
    copay_amount DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    status appointment_status NOT NULL DEFAULT 'WAITING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (clinic_id) REFERENCES clinics(id) ON DELETE CASCADE
);
