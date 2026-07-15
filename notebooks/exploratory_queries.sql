-- Check duplicate years for ADANIPORTS
SELECT
    company_id,
    year,
    COUNT(*) AS records
FROM profitandloss
WHERE company_id = 'ADANIPORTS'
GROUP BY company_id, year
HAVING COUNT(*) > 1;

-- View all ADANIPORTS records
SELECT *
FROM profitandloss
WHERE company_id = 'ADANIPORTS'
ORDER BY year, id;

SELECT
    company_id,
    year,
    COUNT(*) AS records
FROM profitandloss
WHERE company_id = 'ADANIPORTS'
GROUP BY company_id, year
HAVING COUNT(*) > 1;

SELECT *
FROM profitandloss
WHERE company_id = 'ADANIPORTS'
ORDER BY year, id;