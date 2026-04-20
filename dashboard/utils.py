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
    """
    Given a queryset of DailyStat rows, return two parallel lists:
    labels (ISO date strings) and values — with 0 for missing days.
    """
    lookup = {row.date: getattr(row, field) for row in stat_qs}
    labels, values = [], []
    for d in daterange(start, end):
        labels.append(d.strftime('%b %d'))
        values.append(lookup.get(d, 0))
    return labels, values


# ------------------------------------------------------------------ #
# Overview cards
# ------------------------------------------------------------------ #

def overview_cards(start: date, end: date) -> dict:
    from dashboard.models import DailyStat, PDFExport
    from accounts.models import User, Resume

    stats = DailyStat.objects.filter(date__range=(start, end))

    total_visitors   = stats.aggregate(s=Sum('unique_visitors'))['s'] or 0
    total_new_users  = stats.aggregate(s=Sum('new_users'))['s'] or 0
    total_resumes    = stats.aggregate(s=Sum('resumes_created'))['s'] or 0
    total_pdfs       = stats.aggregate(s=Sum('pdfs_exported'))['s'] or 0
    total_failures   = stats.aggregate(s=Sum('pdf_failures'))['s'] or 0
    total_tpl_loads  = stats.aggregate(s=Sum('template_loads'))['s'] or 0

    # All-time totals (independent of date filter)
    alltime_users    = User.objects.count()
    alltime_resumes  = Resume.objects.count()

    # Export success rate
    total_attempts   = total_pdfs + total_failures
    success_rate     = round((total_pdfs / total_attempts * 100), 1) if total_attempts else 100.0

    # Avg PDF duration in the period
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
    from dashboard.models import DailyStat
    qs = DailyStat.objects.filter(date__range=(start, end))
    labels = []
    success_vals, failure_vals = [], []
    lookup = {row.date: row for row in qs}
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

