SELECT schema_name FROM information_schema.schemata
WHERE schema_name IN ('raw','staging','analytics')
ORDER BY schema_name
