"""
Celery task wrapper for aggregate_stats.
Currently dormant — the management command is the active aggregation path.

To activate when Celery + Redis are available:
1. Uncomment the @shared_task decorator and imports.
2. Add to settings.py:

    from celery.schedules import crontab
    CELERY_BEAT_SCHEDULE = {
        'aggregate-stats-nightly': {
            'task': 'dashboard.tasks.aggregate_stats_task',
            'schedule': crontab(hour=1, minute=0),  # 1am daily
        },
    }

3. Run: celery -A core worker -B --loglevel=info
"""

# from celery import shared_task
# from django.core.management import call_command

# @shared_task
def aggregate_stats_task():
    """
    Nightly aggregation. Wraps the management command so the logic
    lives in one place and both paths stay in sync.
    """
    # call_command('aggregate_stats', '--days', '1', '--prune')
    pass