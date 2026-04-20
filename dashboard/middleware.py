import hashlib
from django.utils import timezone


class VisitTrackingMiddleware:
    """
    Records one SiteVisit row per unique (session_hash, date) pair.
    Uses get_or_create so refreshes and repeat visits within the same
    day are silently ignored — exactly one row per visitor per day.

    Only tracks the workspace root and landing page to avoid inflating
    counts with API/AJAX/admin/static requests.

    The session key is hashed with SHA-256 before storage — no raw
    session keys or personal data are ever written to the DB.

    Gracefully skips tracking if the database is unavailable (e.g.
    during migrations or Render cold starts) so it never breaks requests.
    """

    TRACKED_PATHS = {'/', '/home/'}

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path in self.TRACKED_PATHS and request.method == 'GET':
            self._record(request)

        return response

    def _record(self, request):
        try:
            # Ensure a session key exists (creates one for anonymous users)
            if not request.session.session_key:
                request.session.create()

            raw  = request.session.session_key or ''
            h    = hashlib.sha256(raw.encode()).hexdigest()
            today = timezone.localdate()

            from dashboard.models import SiteVisit
            SiteVisit.objects.get_or_create(
                session_hash=h,
                date=today,
                defaults={'is_authed': request.user.is_authenticated},
            )
        except Exception:
            # Never let tracking break a real request
            pass

