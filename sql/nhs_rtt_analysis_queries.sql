-- Executive RTT KPIs
SELECT
  SUM(total_waiting_list) AS total_waiting_list,
  SUM(within_18_weeks) * 1.0 / SUM(total_waiting_list) AS performance_18_weeks,
  SUM(waiting_52_plus_weeks) AS waiting_52_plus_weeks,
  SUM(waiting_52_plus_weeks) * 1.0 / SUM(total_waiting_list) AS long_waiter_share
FROM rtt_waiting_list_assessed;

-- Specialty performance
SELECT
  specialty,
  SUM(total_waiting_list) AS total_waiting_list,
  SUM(within_18_weeks) * 1.0 / SUM(total_waiting_list) AS performance_18_weeks,
  SUM(waiting_52_plus_weeks) AS waiting_52_plus_weeks,
  AVG(median_wait_weeks) AS avg_median_wait_weeks
FROM rtt_waiting_list_assessed
GROUP BY specialty
ORDER BY performance_18_weeks ASC;

-- Trust pressure summary
SELECT
  trust_code,
  trust_name,
  region,
  SUM(total_waiting_list) AS total_waiting_list,
  SUM(within_18_weeks) * 1.0 / SUM(total_waiting_list) AS performance_18_weeks,
  SUM(waiting_52_plus_weeks) * 1.0 / SUM(total_waiting_list) AS long_waiter_share,
  MAX(recovery_priority) AS recovery_priority
FROM rtt_waiting_list_assessed
GROUP BY trust_code, trust_name, region
ORDER BY long_waiter_share DESC;

-- Regional variation
SELECT
  region,
  SUM(total_waiting_list) AS total_waiting_list,
  SUM(within_18_weeks) * 1.0 / SUM(total_waiting_list) AS performance_18_weeks,
  SUM(waiting_52_plus_weeks) AS waiting_52_plus_weeks,
  AVG(median_wait_weeks) AS avg_median_wait_weeks
FROM rtt_waiting_list_assessed
GROUP BY region
ORDER BY performance_18_weeks ASC;

-- Monthly backlog trend
SELECT
  month,
  SUM(total_waiting_list) AS total_waiting_list,
  SUM(waiting_52_plus_weeks) AS waiting_52_plus_weeks,
  SUM(within_18_weeks) * 1.0 / SUM(total_waiting_list) AS performance_18_weeks
FROM rtt_waiting_list_assessed
GROUP BY month
ORDER BY month;

