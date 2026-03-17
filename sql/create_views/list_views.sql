SELECT table_name
FROM information_schema.views
WHERE table_schema = 'analytics'
ORDER BY table_name;
