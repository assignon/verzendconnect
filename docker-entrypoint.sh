#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z $DB_HOST ${DB_PORT:-5432}; do
    sleep 1
done
echo "Database is ready!"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Compile translations if gettext is available
if command -v msgfmt &> /dev/null; then
    echo "Compiling translations..."
    python manage.py compilemessages
fi

# Create logs directory if it doesn't exist
mkdir -p /app/logs

# Execute the main command
exec "$@"

