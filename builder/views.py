import json
from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import ensure_csrf_cookie
from .sanitizer import sanitize_html, sanitize_css

from .services import PDFService

def landing(request):
    return render(request, 'home/landing.html')

FRAMEWORK_CDN_MAP = {
    "tailwind":  '<script src="https://cdn.tailwindcss.com"></script>',
    "bootstrap": '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">',
    "none":      "",
}

# Paper sizes: name -> (playwright_format, width_px_at_96dpi, height_px_at_96dpi)
PAPER_SIZES = {
    "a4":     ("A4",     794,  1123),
    "letter": ("Letter", 816,  1056),
    "legal":  ("Legal",  816,  1344),
    "a5":     ("A5",     559,   794),
}

DEFAULT_HTML = """\
<div class="resume">
  <header>
    <h1>Your Name</h1>
    <p>Software Engineer &mdash; your@email.com &mdash; Lagos, Nigeria</p>
  </header>

  <section>
    <h2>Experience</h2>
    <div class="job">
      <h3>Senior Developer &mdash; Acme Corp</h3>
      <span class="date">Jan 2022 &ndash; Present</span>
      <ul>
        <li>Built and maintained production Django applications serving 50k+ users.</li>
        <li>Led migration from monolith to service-oriented architecture.</li>
      </ul>
    </div>
  </section>

  <section>
    <h2>Skills</h2>
    <p>Python, Django, PostgreSQL, Redis, Docker, HTMX, Alpine.js</p>
  </section>
</div>"""

DEFAULT_CSS = """\
body {
  font-family: 'Segoe UI', sans-serif;
  font-size: 14px;
  color: #1a1a1a;
  margin: 0;
  padding: 2rem;
}

.resume {
  max-width: 800px;
  margin: 0 auto;
}

header {
  border-bottom: 2px solid #1a1a1a;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
}

h1 { font-size: 2rem; margin: 0 0 0.25rem; }

h2 {
  font-size: 1.1rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #ccc;
  padding-bottom: 0.25rem;
  margin-top: 1.5rem;
}

h3 { margin: 0.5rem 0 0.1rem; font-size: 1rem; }

.date { font-size: 0.85rem; color: #555; }

ul { margin: 0.4rem 0 0 1rem; padding: 0; }
li { margin-bottom: 0.25rem; }"""


def workspace(request):
    session_state = request.session.get('resume_state', {})
    context = {
        "default_html":  session_state.get('html',          DEFAULT_HTML),
        "default_css":   session_state.get('css',           DEFAULT_CSS),
        "default_fw":    session_state.get('framework',     'none'),
        "default_paper": session_state.get('paper',         'a4'),
        "resume_title":  session_state.get('resume_title',  ''),
        "resume_slug":   session_state.get('resume_slug',   ''),
        "default_photo": session_state.get('photo_url',     ''),
        "frameworks":    list(FRAMEWORK_CDN_MAP.keys()),
        "paper_sizes":   list(PAPER_SIZES.keys()),
        # Hardcoded defaults for the JS reset function
        "raw_default_html": DEFAULT_HTML,
        "raw_default_css":  DEFAULT_CSS,
    }
    return render(request, "builder/workspace.html", context)


@require_POST
def save_session(request):
    """
    Auto-save endpoint. Persists editor state to session.
    If user is authenticated and a resume slug is tracked, syncs to DB.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Carry forward slug/title from existing session — never overwrite from client
    existing = request.session.get('resume_state', {})
    state = {
        'html':         data.get('html',      ''),
        'css':          data.get('css',       ''),
        'framework':    data.get('framework', 'none'),
        'paper':        data.get('paper',     'a4'),
        'resume_slug':  existing.get('resume_slug',  ''),
        'resume_title': existing.get('resume_title', ''),
        'photo_url':    data.get('photo_url', ''),
    }

    request.session['resume_state'] = state
    request.session.modified = True

    # Sync to DB if authenticated and tracking a resume
    if request.user.is_authenticated and state['resume_slug']:
        from accounts.models import Resume
        try:
            resume = Resume.objects.get(slug=state['resume_slug'], user=request.user)
            resume.html_content = state['html']
            resume.css_content  = state['css']
            resume.framework    = state['framework']
            resume.paper_size   = state['paper']
            resume.photo_url    = state['photo_url']
            resume.save()
        except Resume.DoesNotExist:
            # Slug in session no longer exists — clear it silently
            state['resume_slug']  = ''
            state['resume_title'] = ''
            request.session['resume_state'] = state
            request.session.modified = True

    return JsonResponse({"status": "ok"})


@require_POST
def save_as_resume(request):
    """
    Manual save. Creates a new Resume record or updates an existing one
    if a slug is provided. Updates session to track the saved resume.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=401)

    from accounts.models import Resume
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    title     = data.get('title', '').strip() or 'Untitled Resume'
    slug      = data.get('slug',  '').strip()
    photo_url = data.get('photo_url', '').strip()

    if slug:
        # Update existing
        try:
            resume = Resume.objects.get(slug=slug, user=request.user)
            resume.title        = title
            resume.html_content = data.get('html',      '')
            resume.css_content  = data.get('css',       '')
            resume.framework    = data.get('framework', 'none')
            resume.paper_size   = data.get('paper',     'a4')
            resume.photo_url    = photo_url
            resume.save()
        except Resume.DoesNotExist:
            return JsonResponse({"error": "Resume not found"}, status=404)
    else:
        # Create new
        resume = Resume.objects.create(
            user         = request.user,
            title        = title,
            html_content = data.get('html',      ''),
            css_content  = data.get('css',       ''),
            framework    = data.get('framework', 'none'),
            paper_size   = data.get('paper',     'a4'),
            photo_url    = photo_url,
        )

    # Update session to track this resume
    state = request.session.get('resume_state', {})
    state['resume_slug']  = resume.slug
    state['resume_title'] = resume.title
    request.session['resume_state'] = state
    request.session.modified = True

    return JsonResponse({"status": "ok", "slug": resume.slug, "title": resume.title})


@require_POST
def clear_session(request):
    """
    Clears resume state from session. Called by the New Resume confirm button.
    Returns JSON — the frontend handles the page reload.
    """
    request.session.pop('resume_state', None)
    request.session.modified = True
    return JsonResponse({"status": "cleared"})


@require_POST
def export_pdf(request):
    """
    Renders the resume to PDF via Playwright and returns it as a download.
    """
    html      = request.POST.get("html",      "")
    css       = request.POST.get("css",       "")
    framework = request.POST.get("framework", "none")
    paper     = request.POST.get("paper",     "a4")

    framework_css   = FRAMEWORK_CDN_MAP.get(framework, "")
    paper_format, _, _ = PAPER_SIZES.get(paper, PAPER_SIZES["a4"])

    service = PDFService(
        html=html,
        css=css,
        framework_css=framework_css,
        paper_format=paper_format,
    )

    try:
        pdf_bytes = service.render_pdf()
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="resume.pdf"'
    return response


def public_resume(request, slug):
    """
    Public-facing resume page. Renders a user's saved resume if is_public=True.
    HTML and CSS are sanitized before rendering to prevent injection attacks.
    """
    from accounts.models import Resume

    try:
        resume = Resume.objects.select_related('user').get(slug=slug)
    except Resume.DoesNotExist:
        return render(request, 'builder/resume_404.html', status=404)

    if not resume.is_public:
        return render(request, 'builder/resume_404.html', status=404)

    framework_css = FRAMEWORK_CDN_MAP.get(resume.framework, '')
    paper_format, paper_w, paper_h = PAPER_SIZES.get(resume.paper_size, PAPER_SIZES['a4'])

    context = {
        'resume':        resume,
        'safe_html':     sanitize_html(resume.html_content),
        'safe_css':      sanitize_css(resume.css_content),
        'framework_css': framework_css,
        'paper_w':       paper_w,
        'paper_h':       paper_h,
        'owner':         resume.user,
    }
    return render(request, 'builder/public_resume.html', context)


def template_library(request):
    """
    Public browse page. Shows all active templates.
    Premium templates are visible but marked locked for free users.
    """
    from accounts.models import ResumeTemplate
    templates = ResumeTemplate.objects.filter(is_active=True)
    return render(request, 'builder/template_library.html', {
        'templates': templates,
    })


@require_POST
def load_template(request, slug):
    """
    Loads a template into the workspace session and redirects.
    Premium check hook is here — currently passes all users through.
    """
    from accounts.models import ResumeTemplate
    try:
        template = ResumeTemplate.objects.get(slug=slug, is_active=True)
    except ResumeTemplate.DoesNotExist:
        from django.http import Http404
        raise Http404

    # Premium enforcement hook — uncomment when subscriptions are live:
    # if template.is_premium and not getattr(request.user, 'is_premium', False):
    #     return JsonResponse({"error": "Premium template"}, status=403)

    # Load template content into session as a fresh unsaved state
    request.session['resume_state'] = {
        'html':         template.html_content,
        'css':          template.css_content,
        'framework':    template.framework,
        'paper':        template.paper_size,
        'photo_url':    '',
        'resume_slug':  '',   # not saved yet — user starts fresh
        'resume_title': '',
    }
    request.session.modified = True
    return redirect('builder:workspace')