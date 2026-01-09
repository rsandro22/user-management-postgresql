@echo off

set DB_NAME=user_management
set /p PGUSER="Enter PostgreSQL username (default: postgres): "
if "%PGUSER%"=="" set PGUSER=postgres

set /p PGPASSWORD="Enter PostgreSQL password: "

echo.
echo Terminating existing connections...
psql -U %PGUSER% -d postgres -c "SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '%DB_NAME%' AND pid <> pg_backend_pid();" 2>nul

echo.
echo Dropping database %DB_NAME% if exists...
dropdb --if-exists -U %PGUSER% %DB_NAME%

echo Creating database %DB_NAME%...
createdb -U %PGUSER% %DB_NAME%

echo.
echo Loading schema...
psql -U %PGUSER% %DB_NAME% -f db/schema.sql

echo Loading triggers...
psql -U %PGUSER% %DB_NAME% -f db/triggers.sql

echo Loading views...
psql -U %PGUSER% %DB_NAME% -f db/views.sql

echo.
echo ========================================
echo Database initialized successfully!
echo ========================================
echo.
echo You can now connect using:
echo   psql -U %PGUSER% %DB_NAME%
echo.
pause