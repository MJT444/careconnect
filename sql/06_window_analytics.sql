
WITH daily_clinic_revenue AS (
    SELECT 
        clinic_id,
        DATE_TRUNC('day', created_at) AS rev_date,
        SUM(copay_amount) AS daily_copay_total
    FROM appointments
    GROUP BY clinic_id, DATE_TRUNC('day', created_at)
),
moving_averages AS (
    SELECT 
        clinic_id,
        rev_date,
        daily_copay_total,
        AVG(daily_copay_total) OVER (
            PARTITION BY clinic_id 
            ORDER BY rev_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS moving_7day_avg,
        SUM(daily_copay_total) OVER (PARTITION BY clinic_id) AS total_clinic_revenue
    FROM daily_clinic_revenue
)
SELECT 
    c.name AS clinic_name,
    m.rev_date,
    m.daily_copay_total,
    ROUND(m.moving_7day_avg, 2) AS moving_7day_avg,
    DENSE_RANK() OVER (ORDER BY m.total_clinic_revenue DESC) AS global_revenue_rank
FROM moving_averages m
JOIN clinics c ON m.clinic_id = c.id
ORDER BY global_revenue_rank, m.rev_date;