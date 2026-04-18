#!/usr/bin/env bash
set -e

echo ""
echo "========================================"
echo "  Code2Resume — Render Build Script"
echo "========================================"
echo ""

# ---- Python dependencies ----
echo "==> [1/6] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# ---- Playwright ----
echo "==> [2/6] Installing Playwright Chromium..."
playwright install chromium

# ---- Static files ----
echo "==> [3/6] Collecting static files..."
python manage.py collectstatic --noinput

# ---- Database migrations ----
echo "==> [4/6] Running migrations..."
python manage.py migrate

# ---- Django Sites framework ----
echo "==> [5/6] Configuring sites framework..."
python manage.py shell << 'PYEOF'
import os
from django.contrib.sites.models import Site

domain = os.environ.get('RENDER_EXTERNAL_HOSTNAME', 'localhost:8000')
name   = os.environ.get('SITE_NAME', 'Code2Resume')

site, created = Site.objects.update_or_create(
    id=1,
    defaults={'domain': domain, 'name': name}
)
action = 'Created' if created else 'Updated'
print(f"  {action} site: {site.domain}")
PYEOF

# ---- Superuser ----
echo "==> [6/6] Creating superuser if not exists..."
python manage.py shell << 'PYEOF'
import os
from django.contrib.auth import get_user_model

User  = get_user_model()
email = os.environ.get('DJANGO_SUPERUSER_EMAIL',    'admin@code2resume.dev')
passw = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'changeme123!')

if not User.objects.filter(email=email).exists():
    User.objects.create_superuser(
        username=email,
        email=email,
        password=passw,
        display_name='Admin',
    )
    print(f"  Superuser created: {email}")
else:
    print(f"  Superuser already exists: {email}")
PYEOF

echo ""
echo "========================================"
echo "  Build complete."
echo "========================================"
echo ""