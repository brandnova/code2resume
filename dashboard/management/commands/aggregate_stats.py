"""
aggregate_stats — populates DailyStat rows from raw event tables.

Usage:
    python manage.py aggregate_stats              # aggregates yesterday
    python manage.py aggregate_stats --days 30    # back-fills last 30 days
    python manage.py aggregate_stats --date 2025-06-01  # one specific date

Design notes:
- Each run is fully idempotent: it uses update_or_create, so running it
  twice for the same date is safe and produces the same result.
- Raw event rows (SiteVisit, PDFExport, TemplateLoad) are kept for 90
  days then pruned by this command on each run. DailyStat rows are kept
  forever as the permanent historical record.
- The command is the primary aggregation path. tasks.py wraps the same
  logic for Celery beat — when you activate Celery, nothing here changes.
"""

from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Q


class Command(BaseCommand):
    help = 'Aggregate raw event data into DailyStat rows.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days', type=int, default=1,
            help='Number of past days to aggregate (default: 1 = yesterday)',
        )
        parser.add_argument(
            '--date', type=str, default=None,
            help='Aggregate a specific date (YYYY-MM-DD). Overrides --days.',
        )
        parser.add_argument(
            '--prune', action='store_true', default=True,
            help='Prune raw event rows older than 90 days (default: True)',
        )

    def handle(self, *args, **options):
        from dashboard.models import SiteVisit, PDFExport, TemplateLoad, DailyStat
        from accounts.models import User

        # Determine which dates to process
        if options['date']:
            try:
                target_dates = [date.fromisoformat(options['date'])]
            except ValueError:
                self.stderr.write(f"Invalid date format: {options['date']}. Use YYYY-MM-DD.")
                return
        else:
            today = timezone.localdate()
            target_dates = [
                today - timedelta(days=i)
                for i in range(1, options['days'] + 1)
            ]

        for target_date in target_dates:
            self._aggregate_date(
                target_date, SiteVisit, PDFExport, TemplateLoad, DailyStat, User
            )

        if options['prune']:
            self._prune_raw_events(SiteVisit, PDFExport, TemplateLoad)

        self.stdout.write(self.style.SUCCESS('aggregate_stats complete.'))

    def _aggregate_date(self, d, SiteVisit, PDFExport, TemplateLoad, DailyStat, User):
        unique_visitors = SiteVisit.objects.filter(date=d).count()
        authed_visitors = SiteVisit.objects.filter(date=d, is_authed=True).count()

        new_users = User.objects.filter(
            date_joined__date=d
        ).count()

        from accounts.models import Resume
        resumes_created = Resume.objects.filter(
            created_at__date=d
        ).count()

        pdfs_exported = PDFExport.objects.filter(
            created_at__date=d, success=True
        ).count()

        pdf_failures = PDFExport.objects.filter(
            created_at__date=d, success=False
        ).count()

        template_loads = TemplateLoad.objects.filter(
            created_at__date=d
        ).count()

        stat, created = DailyStat.objects.update_or_create(
            date=d,
            defaults={
                'unique_visitors': unique_visitors,
                'authed_visitors': authed_visitors,
                'new_users':       new_users,
                'resumes_created': resumes_created,
                'pdfs_exported':   pdfs_exported,
                'pdf_failures':    pdf_failures,
                'template_loads':  template_loads,
            }
        )

        action = 'Created' if created else 'Updated'
        self.stdout.write(
            f"  {action} {d}: "
            f"{unique_visitors} visitors, "
            f"{new_users} new users, "
            f"{resumes_created} resumes, "
            f"{pdfs_exported} PDFs"
        )

    def _prune_raw_events(self, SiteVisit, PDFExport, TemplateLoad):
        cutoff = timezone.localdate() - timedelta(days=90)

        sv = SiteVisit.objects.filter(date__lt=cutoff).delete()[0]
        pe = PDFExport.objects.filter(created_at__date__lt=cutoff).delete()[0]
        tl = TemplateLoad.objects.filter(created_at__date__lt=cutoff).delete()[0]

        if any([sv, pe, tl]):
            self.stdout.write(
                f"  Pruned: {sv} visits, {pe} exports, {tl} template loads "
                f"(older than {cutoff})"
            )

