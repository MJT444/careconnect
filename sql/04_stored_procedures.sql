CREATE OR REPLACE PROCEDURE sp_book_appointment(
    p_patient_id UUID,
    p_clinic_id UUID,
    p_copay_amount DECIMAL(10,2)
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_balance DECIMAL(10,2);
BEGIN
    SELECT hsa_balance
    INTO v_balance
    FROM patients
    WHERE id = p_patient_id
    FOR UPDATE;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Patient does not exist';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM clinics
        WHERE id = p_clinic_id
    ) THEN
        RAISE EXCEPTION 'Clinic does not exist';
    END IF;

    IF p_copay_amount < 0 OR v_balance < p_copay_amount THEN
        RAISE EXCEPTION 'Insufficient HSA funds for copay deduction';
    END IF;

    UPDATE patients
    SET hsa_balance = hsa_balance - p_copay_amount
    WHERE id = p_patient_id;

    INSERT INTO appointments (
        patient_id,
        clinic_id,
        copay_amount,
        status,
        created_at
    )
    VALUES (
        p_patient_id,
        p_clinic_id,
        p_copay_amount,
        'WAITING',
        NOW()
    );
END;
$$;

