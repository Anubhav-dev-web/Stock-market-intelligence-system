SELECT table_schema, table_name
FROM information_schema.tables
WHERE table_schema IN ('raw','analytics')
ORDER BY table_schema, table_name
