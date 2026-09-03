
CREATE OR REPLACE PROCEDURE sp_book_appointment(
    p_patient_id UUID,
    p_clinic_id UUID,
    p_copay_amount DECIMAL(10,2)
)
LANGUAGE plpgsql AS $$
BEGIN
    SET TRANSACTION ISOLATION LEVEL REPEATABLE READ;

    -- Verify balance availability
    IF (SELECT hsa_balance FROM patients WHERE id = p_patient_id) < p_copay_amount THEN
        RAISE EXCEPTION 'Insufficient HSA funds for copay deduction';
    END IF;

    -- Balance deduction triggers wallet_audit_logs entry automatically
    UPDATE patients 
    SET hsa_balance = hsa_balance - p_copay_amount 
    WHERE id = p_patient_id;

    -- Inserting record triggers idx_active_consult validation
    INSERT INTO appointments (patient_id, clinic_id, copay_amount, status, created_at)
    VALUES (p_patient_id, p_clinic_id, p_copay_amount, 'WAITING', NOW());

    COMMIT;
EXCEPTION WHEN OTHERS THEN
    ROLLBACK;
    RAISE;
END;
$$;

