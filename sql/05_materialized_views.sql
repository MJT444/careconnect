
-- Materialized View for Monthly Discharges & Copay Revenues
CREATE MATERIALIZED VIEW mv_clinic_monthly_discharges AS
SELECT c.id AS clinic_id, c.name AS clinic_name, 
       DATE_TRUNC('month', a.created_at) AS month_period,
       COUNT(a.id) AS total_discharges, 
       SUM(a.copay_amount) AS total_copay_revenue
FROM clinics c
JOIN appointments a ON c.id = a.clinic_id
WHERE a.status = 'DISCHARGED'
GROUP BY c.id, c.name, DATE_TRUNC('month', a.created_at);

-- Unique index required for REFRESH CONCURRENTLY
CREATE UNIQUE INDEX idx_mv_clinic_monthly 
ON mv_clinic_monthly_discharges (clinic_id, month_period);

CREATE OR REPLACE FUNCTION refresh_clinic_monthly_mv() RETURNS void AS $$
BEGIN
  REFRESH MATERIALIZED VIEW CONCURRENTLY mv_clinic_monthly_discharges;
END;
$$ LANGUAGE plpgsql;