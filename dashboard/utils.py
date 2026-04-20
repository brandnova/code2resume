"""
All data queries for the dashboard. Views call these functions.
"""
from datetime import date, timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Q, Sum
from django.db.models.functions import TruncDate


def get_date_range(period: str):
    """Return (start_date, end_date) for a named period."""
    today = timezone.localdate()
    periods = {
        'today':   (today,                        today),
        '7d':      (today - timedelta(days=6),    today),
        '30d':     (today - timedelta(days=29),   today),
        '90d':     (today - timedelta(days=89),   today),
        'year':    (today - timedelta(days=364),  today),
    }
    return periods.get(period, periods['30d'])


def daterange(start: date, end: date):
    """Yield every date from start to end inclusive."""
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def fill_series(stat_qs, start: date, end: date, field: str):
    from django.utils import timezone
    today = timezone.localdate()
    lookup = {row.date: getattr(row, field) for row in stat_qs}

    # Patch today with live raw count if today is in range
    if start <= today <= end and today not in lookup:
        lookup[today] = _get_today_raw(field)

    labels, values = [], []
    for d in daterange(start, end):
        labels.append(d.strftime('%b %d'))
        values.append(lookup.get(d, 0))
    return labels, values


def _get_today_raw(field: str) -> int:
    """Get today's count directly from raw tables for fields not yet aggregated."""
    from django.utils import timezone
    today = timezone.localdate()
    try:
        if field == 'unique_visitors':
            from dashboard.models import SiteVisit
            return SiteVisit.objects.filter(date=today).count()
        elif field == 'new_users':
            from accounts.models import User
            return User.objects.filter(date_joined__date=today).count()
        elif field == 'resumes_created':
            from accounts.models import Resume
            return Resume.objects.filter(created_at__date=today).count()
        elif field == 'pdfs_exported':
            from dashboard.models import PDFExport
            return PDFExport.objects.filter(created_at__date=today, success=True).count()
        elif field == 'pdf_failures':
            from dashboard.models import PDFExport
            return PDFExport.objects.filter(created_at__date=today, success=False).count()
        elif field == 'template_loads':
            from dashboard.models import TemplateLoad
            return TemplateLoad.objects.filter(created_at__date=today).count()
    except Exception:
        pass
    return 0


# ------------------------------------------------------------------ #
# Overview cards
# ------------------------------------------------------------------ #

def overview_cards(start: date, end: date) -> dict:
    from dashboard.models import DailyStat, PDFExport, SiteVisit, TemplateLoad
    from accounts.models import User, Resume
    from django.utils import timezone

    today = timezone.localdate()

    # For historical days use DailyStat (fast aggregates)
    # For today use raw tables directly (DailyStat for today won't exist until the cron runs)
    stats = DailyStat.objects.filter(date__range=(start, end))

    # Aggregate from DailyStat for days that have been processed
    from django.db.models import Sum
    agg = stats.aggregate(
        s_visitors  = Sum('unique_visitors'),
        s_new_users = Sum('new_users'),
        s_resumes   = Sum('resumes_created'),
        s_pdfs      = Sum('pdfs_exported'),
        s_failures  = Sum('pdf_failures'),
        s_tpls      = Sum('template_loads'),
    )

    # Add today's raw counts on top if today falls within the range
    today_visitors  = 0
    today_new_users = 0
    today_resumes   = 0
    today_pdfs      = 0
    today_failures  = 0
    today_tpls      = 0

    if start <= today <= end:
        today_visitors  = SiteVisit.objects.filter(date=today).count()
        today_new_users = User.objects.filter(date_joined__date=today).count()
        today_resumes   = Resume.objects.filter(created_at__date=today).count()
        today_pdfs      = PDFExport.objects.filter(created_at__date=today, success=True).count()
        today_failures  = PDFExport.objects.filter(created_at__date=today, success=False).count()
        today_tpls      = TemplateLoad.objects.filter(created_at__date=today).count()

    total_visitors  = (agg['s_visitors']  or 0) + today_visitors
    total_new_users = (agg['s_new_users'] or 0) + today_new_users
    total_resumes   = (agg['s_resumes']   or 0) + today_resumes
    total_pdfs      = (agg['s_pdfs']      or 0) + today_pdfs
    total_failures  = (agg['s_failures']  or 0) + today_failures
    total_tpl_loads = (agg['s_tpls']      or 0) + today_tpls

    alltime_users   = User.objects.count()
    alltime_resumes = Resume.objects.count()

    total_attempts = total_pdfs + total_failures
    success_rate   = round((total_pdfs / total_attempts * 100), 1) if total_attempts else 100.0

    from django.db.models import Avg
    avg_duration = PDFExport.objects.filter(
        created_at__date__range=(start, end),
        success=True,
    ).aggregate(a=Avg('duration_ms'))['a'] or 0

    return {
        'total_visitors':  total_visitors,
        'total_new_users': total_new_users,
        'total_resumes':   total_resumes,
        'total_pdfs':      total_pdfs,
        'total_tpl_loads': total_tpl_loads,
        'success_rate':    success_rate,
        'avg_duration_ms': round(avg_duration),
        'alltime_users':   alltime_users,
        'alltime_resumes': alltime_resumes,
    }


# ------------------------------------------------------------------ #
# Chart series
# ------------------------------------------------------------------ #

def visitors_series(start: date, end: date):
    from dashboard.models import DailyStat
    qs = DailyStat.objects.filter(date__range=(start, end))
    return fill_series(qs, start, end, 'unique_visitors')


def resumes_series(start: date, end: date):
    from dashboard.models import DailyStat
    qs = DailyStat.objects.filter(date__range=(start, end))
    return fill_series(qs, start, end, 'resumes_created')


def pdfs_series(start: date, end: date):
    from dashboard.models import DailyStat
    qs = DailyStat.objects.filter(date__range=(start, end))
    return fill_series(qs, start, end, 'pdfs_exported')


def new_users_series(start: date, end: date):
    from dashboard.models import DailyStat
    qs = DailyStat.objects.filter(date__range=(start, end))
    return fill_series(qs, start, end, 'new_users')


# ------------------------------------------------------------------ #
# Breakdown tables
# ------------------------------------------------------------------ #

def framework_breakdown(start: date, end: date):
    from dashboard.models import PDFExport
    return list(
        PDFExport.objects
        .filter(created_at__date__range=(start, end), success=True)
        .values('framework')
        .annotate(count=Count('id'))
        .order_by('-count')
    )


def paper_breakdown(start: date, end: date):
    from dashboard.models import PDFExport
    return list(
        PDFExport.objects
        .filter(created_at__date__range=(start, end), success=True)
        .values('paper_size')
        .annotate(count=Count('id'))
        .order_by('-count')
    )


def template_breakdown(start: date, end: date):
    from dashboard.models import TemplateLoad
    return list(
        TemplateLoad.objects
        .filter(created_at__date__range=(start, end))
        .values('template__title', 'template__is_premium', 'template__slug')
        .annotate(count=Count('id'))
        .order_by('-count')[:10]
    )


# ------------------------------------------------------------------ #
# Exports page
# ------------------------------------------------------------------ #

def export_detail(start: date, end: date):
    from dashboard.models import PDFExport
    rows = (
        PDFExport.objects
        .filter(created_at__date__range=(start, end))
        .select_related('user')
        .order_by('-created_at')[:200]
    )
    return rows


def export_failure_rate_series(start: date, end: date):
    from dashboard.models import DailyStat, PDFExport
    from django.utils import timezone
    today = timezone.localdate()

    qs = DailyStat.objects.filter(date__range=(start, end))
    lookup = {row.date: row for row in qs}

    # Patch today
    if start <= today <= end and today not in lookup:
        class _TodayRow:
            pdfs_exported = PDFExport.objects.filter(
                created_at__date=today, success=True).count()
            pdf_failures  = PDFExport.objects.filter(
                created_at__date=today, success=False).count()
        lookup[today] = _TodayRow()

    labels, success_vals, failure_vals = [], [], []
    for d in daterange(start, end):
        labels.append(d.strftime('%b %d'))
        row = lookup.get(d)
        success_vals.append(row.pdfs_exported if row else 0)
        failure_vals.append(row.pdf_failures  if row else 0)
    return labels, success_vals, failure_vals


# ------------------------------------------------------------------ #
# Users page
# ------------------------------------------------------------------ #

def recent_users(limit=50):
    from accounts.models import User
    return User.objects.order_by('-date_joined')[:limit]


def user_resume_counts():
    from accounts.models import User
    return (
        User.objects
        .annotate(resume_count=Count('resumes'))
        .order_by('-resume_count')[:20]
    )

