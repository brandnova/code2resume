import json
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.core.paginator import Paginator
from .utils import (
    get_date_range, overview_cards,
    visitors_series, resumes_series, pdfs_series, new_users_series,
    framework_breakdown, paper_breakdown, template_breakdown,
    export_detail, export_failure_rate_series,
    recent_users, user_resume_counts,
)

PERIOD_LABELS = {
    'today': 'Today',
    '7d':    'Last 7 days',
    '30d':   'Last 30 days',
    '90d':   'Last 90 days',
    'year':  'Last 12 months',
}


def _period_ctx(request):
    period = request.GET.get('period', '30d')
    if period not in PERIOD_LABELS:
        period = '30d'
    start, end = get_date_range(period)
    return period, start, end


@staff_member_required(login_url='/accounts/login/')
def overview(request):
    period, start, end = _period_ctx(request)

    cards       = overview_cards(start, end)
    vis_labels, vis_data       = visitors_series(start, end)
    res_labels, res_data       = resumes_series(start, end)
    pdf_labels, pdf_data       = pdfs_series(start, end)
    usr_labels, usr_data       = new_users_series(start, end)
    fw_breakdown               = framework_breakdown(start, end)
    pp_breakdown               = paper_breakdown(start, end)
    tpl_breakdown              = template_breakdown(start, end)

    context = {
        'page':          'overview',
        'period':        period,
        'period_label':  PERIOD_LABELS[period],
        'period_labels': PERIOD_LABELS,
        'start':         start,
        'end':           end,
        **cards,

        # JSON for Chart.js
        'vis_labels':    json.dumps(vis_labels),
        'vis_data':      json.dumps(vis_data),
        'res_labels':    json.dumps(res_labels),
        'res_data':      json.dumps(res_data),
        'pdf_labels':    json.dumps(pdf_labels),
        'pdf_data':      json.dumps(pdf_data),
        'usr_labels':    json.dumps(usr_labels),
        'usr_data':      json.dumps(usr_data),

        'fw_labels':     json.dumps([r['framework']  for r in fw_breakdown]),
        'fw_data':       json.dumps([r['count']       for r in fw_breakdown]),
        'pp_labels':     json.dumps([r['paper_size']  for r in pp_breakdown]),
        'pp_data':       json.dumps([r['count']       for r in pp_breakdown]),

        'tpl_breakdown': tpl_breakdown,
    }
    return render(request, 'dashboard/overview.html', context)


@staff_member_required(login_url='/accounts/login/')
def exports(request):
    period, start, end = _period_ctx(request)
    exp_labels, exp_success, exp_failures = export_failure_rate_series(start, end)
    
    # Paginate the exports detail
    all_rows = export_detail(start, end)
    paginator = Paginator(all_rows, 20)  # 20 items per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    pp   = paper_breakdown(start, end)
    fw   = framework_breakdown(start, end)

    context = {
        'page':          'exports',
        'period':        period,
        'period_label':  PERIOD_LABELS[period],
        'period_labels': PERIOD_LABELS,
        'start':         start,
        'end':           end,
        'page_obj':      page_obj,  # Use page_obj instead of rows
        'rows':          page_obj.object_list,  # Keep for compatibility

        'exp_labels':    json.dumps(exp_labels),
        'exp_success':   json.dumps(exp_success),
        'exp_failures':  json.dumps(exp_failures),
        'pp_labels':     json.dumps([r['paper_size'] for r in pp]),
        'pp_data':       json.dumps([r['count']      for r in pp]),
        'fw_labels':     json.dumps([r['framework']  for r in fw]),
        'fw_data':       json.dumps([r['count']      for r in fw]),
    }
    return render(request, 'dashboard/exports.html', context)


@staff_member_required(login_url='/accounts/login/')
def templates(request):
    period, start, end = _period_ctx(request)
    tpl = template_breakdown(start, end)

    from accounts.models import ResumeTemplate
    
    # Paginate the all_templates table
    all_templates_list = ResumeTemplate.objects.all().order_by('order', 'title')
    paginator = Paginator(all_templates_list, 15)  # 15 templates per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page':          'templates',
        'period':        period,
        'period_label':  PERIOD_LABELS[period],
        'period_labels': PERIOD_LABELS,
        'start':         start,
        'end':           end,
        'tpl_breakdown': tpl,
        'page_obj':      page_obj,
        'all_templates': page_obj.object_list,  # Keep for compatibility
        'tpl_labels':    json.dumps([r['template__title'] or 'Deleted' for r in tpl]),
        'tpl_data':      json.dumps([r['count'] for r in tpl]),
    }
    return render(request, 'dashboard/templates.html', context)


@staff_member_required(login_url='/accounts/login/')
def users(request):
    period, start, end = _period_ctx(request)
    usr_labels, usr_data = new_users_series(start, end)
    recent   = recent_users()
    top_users = user_resume_counts()

    context = {
        'page':          'users',
        'period':        period,
        'period_label':  PERIOD_LABELS[period],
        'period_labels': PERIOD_LABELS,
        'start':         start,
        'end':           end,
        'recent_users':  recent,
        'top_users':     top_users,
        'usr_labels':    json.dumps(usr_labels),
        'usr_data':      json.dumps(usr_data),
    }
    return render(request, 'dashboard/users.html', context)

