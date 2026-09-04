-- Wallet Audit Trigger
CREATE OR REPLACE FUNCTION log_hsa_balance_change()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.hsa_balance <> OLD.hsa_balance THEN
        INSERT INTO wallet_audit_logs (patient_id, amount_changed, action_type, balance_after)
        VALUES (
            NEW.id,
            ABS(NEW.hsa_balance - OLD.hsa_balance),
            CASE WHEN NEW.hsa_balance > OLD.hsa_balance THEN 'CREDIT' ELSE 'DEBIT' END,
            NEW.hsa_balance
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_hsa_balance
AFTER UPDATE OF hsa_balance ON patients
FOR EACH ROW EXECUTE FUNCTION log_hsa_balance_change();

