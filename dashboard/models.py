import uuid
from django.db import models
from django.utils import timezone


class SiteVisit(models.Model):
    """
    One row per unique visitor session per day.
    The combination of (session_hash, date) is unique, so refreshing
    the page never creates a duplicate. Anonymous and authenticated
    visitors are both tracked via their Django session key hash.
    No IP addresses or personal data are stored.
    """
    session_hash = models.CharField(max_length=64)
    date         = models.DateField(default=timezone.localdate)
    is_authed    = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('session_hash', 'date')
        indexes = [
            models.Index(fields=['date']),
        ]

    def __str__(self):
        return f"Visit {self.session_hash[:8]}… on {self.date}"


class PDFExport(models.Model):
    """
    One row per PDF export attempt. Records outcome and duration.
    User is nullable — anonymous exports are tracked too.
    """
    user       = models.ForeignKey(
        'accounts.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='pdf_exports'
    )
    paper_size = models.CharField(max_length=20)
    framework  = models.CharField(max_length=20)
    success    = models.BooleanField(default=True)
    duration_ms = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['created_at'])]

    def __str__(self):
        status = "OK" if self.success else "FAIL"
        return f"PDF {status} {self.paper_size} {self.created_at:%Y-%m-%d}"


class TemplateLoad(models.Model):
    """
    One row each time a user confirms loading a resume template.
    """
    template   = models.ForeignKey(
        'accounts.ResumeTemplate', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='loads'
    )
    user       = models.ForeignKey(
        'accounts.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='template_loads'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=['created_at'])]

    def __str__(self):
        tpl = self.template.title if self.template else 'deleted'
        return f"Load: {tpl} at {self.created_at:%Y-%m-%d}"


class DailyStat(models.Model):
    """
    Aggregated daily snapshot. Written by the aggregate_stats
    management command. The dashboard reads from this table for
    historical charts — fast, no heavy GROUP BY queries at render time.
    Recalculating a day's row is idempotent (update_or_create).
    """
    date             = models.DateField(unique=True)
    unique_visitors  = models.PositiveIntegerField(default=0)
    authed_visitors  = models.PositiveIntegerField(default=0)
    new_users        = models.PositiveIntegerField(default=0)
    resumes_created  = models.PositiveIntegerField(default=0)
    pdfs_exported    = models.PositiveIntegerField(default=0)
    pdf_failures     = models.PositiveIntegerField(default=0)
    template_loads   = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Stats {self.date}"
    
