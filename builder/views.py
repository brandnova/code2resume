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


@ensure_csrf_cookie
def workspace(request):
    session_state        = request.session.get('resume_state', {})
    new_resume_requested = request.session.pop('new_resume_requested', False)
    request.session.modified = True

    # Defensive: never pass None or empty string when we have a default
    html = session_state.get('html') or DEFAULT_HTML
    css  = session_state.get('css')  or DEFAULT_CSS

    context = {
        'default_html':         html,
        'default_css':          css,
        'default_fw':           session_state.get('framework',    'none'),
        'default_paper':        session_state.get('paper',        'a4'),
        'resume_title':         session_state.get('resume_title', ''),
        'resume_slug':          session_state.get('resume_slug',  ''),
        'default_photo':        session_state.get('photo_url',    ''),
        'frameworks':           list(FRAMEWORK_CDN_MAP.keys()),
        'paper_sizes':          list(PAPER_SIZES.keys()),
        'new_resume_requested': new_resume_requested,
        'session_has_content':  bool((session_state.get('html') or '').strip()),
        'session_is_saved':     bool(session_state.get('resume_slug', '')),
        'session_resume_title': session_state.get('resume_title', ''),
    }
    return render(request, 'builder/workspace.html', context)


@require_POST
def save_session(request):
    """
    Receives editor state and persists it to the Django session.
    Saves to user account if authenticated.
    Called by the frontend on a debounced interval.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    state = {
        'html':      data.get('html',      ''),
        'css':       data.get('css',       ''),
        'framework': data.get('framework', 'none'),
        'paper':     data.get('paper',     'a4'),
    }

    # Persist to session for anonymous and authenticated users alike
    resume_slug  = request.session.get('resume_state', {}).get('resume_slug')
    resume_title = request.session.get('resume_state', {}).get('resume_title', 'Untitled Resume')
    state['resume_slug']  = resume_slug
    state['resume_title'] = resume_title
    request.session['resume_state'] = state
    request.session.modified = True

    # If authenticated and a resume slug is in session, sync to the DB
    if request.user.is_authenticated and resume_slug:
        from accounts.models import Resume
        try:
            resume = Resume.objects.get(slug=resume_slug, user=request.user)
            resume.html_content = state['html']
            resume.css_content  = state['css']
            resume.framework    = state['framework']
            resume.paper_size   = state['paper']
            resume.save()
        except Resume.DoesNotExist:
            pass

    return JsonResponse({"status": "ok"})


@require_POST
def save_as_resume(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=401)

    from accounts.models import Resume
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    title = data.get('title', 'Untitled Resume').strip() or 'Untitled Resume'

    resume = Resume.objects.create(
        user         = request.user,
        title        = title,
        html_content = data.get('html',      ''),
        css_content  = data.get('css',       ''),
        framework    = data.get('framework', 'none'),
        paper_size   = data.get('paper',     'a4'),
        photo_url    = data.get('photo_url', ''),
    )

    # Update session to track this resume going forward
    state = request.session.get('resume_state', {})
    state['resume_slug']  = resume.slug
    state['resume_title'] = resume.title
    request.session['resume_state'] = state
    request.session.modified = True

    return JsonResponse({"status": "ok", "slug": resume.slug, "title": resume.title})


@require_POST
def update_resume(request):
    """
    Updates an existing resume. Called from the save modal when editing.
    Requires the resume slug to be passed in the request body.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Login required"}, status=401)

    from accounts.models import Resume
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    slug = data.get('slug', '').strip()
    if not slug:
        return JsonResponse({"error": "Slug is required"}, status=400)

    try:
        resume = Resume.objects.get(slug=slug, user=request.user)
    except Resume.DoesNotExist:
        return JsonResponse({"error": "Resume not found"}, status=404)

    title = data.get('title', '').strip() or resume.title
    resume.title        = title
    resume.html_content = data.get('html', '')
    resume.css_content  = data.get('css', '')
    resume.framework    = data.get('framework', 'none')
    resume.paper_size   = data.get('paper', 'a4')
    resume.photo_url    = data.get('photo_url', '')
    resume.save()

    # Update session to reflect the changed title (if it changed)
    state = request.session.get('resume_state', {})
    state['resume_title'] = resume.title
    request.session['resume_state'] = state
    request.session.modified = True

    return JsonResponse({"status": "ok", "slug": resume.slug, "title": resume.title})


def new_resume(request):
    """
    GET: Marks the session with a 'wants_new' flag and redirects
         to the workspace. The workspace JS reads this flag on load
         and shows the confirmation modal if there is existing work.
    POST: Actually clears the session state (called by the discard button confirm).
    """
    if request.method == 'POST':
        request.session.pop('resume_state', None)
        request.session.modified = True
        return JsonResponse({'status': 'cleared'})

    # GET — set a flag and send the user to the workspace
    request.session['new_resume_requested'] = True
    request.session.modified = True
    return redirect('builder:workspace')


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

