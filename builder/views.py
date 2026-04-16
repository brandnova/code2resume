import json
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import ensure_csrf_cookie

from .services import PDFService

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
    """
    Main editor view. Loads saved session state if present, otherwise defaults.
    """
    session_state = request.session.get('resume_state', {})

    context = {
        "default_html":  session_state.get('html',      DEFAULT_HTML),
        "default_css":   session_state.get('css',       DEFAULT_CSS),
        "default_fw":    session_state.get('framework', 'none'),
        "default_paper": session_state.get('paper',     'a4'),
        "frameworks":    list(FRAMEWORK_CDN_MAP.keys()),
        "paper_sizes":   list(PAPER_SIZES.keys()),
    }
    return render(request, "builder/workspace.html", context)


@require_POST
def save_session(request):
    """
    Receives editor state and persists it to the Django session.
    Called by the frontend on a debounced interval.
    """
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    request.session['resume_state'] = {
        'html':      data.get('html',      ''),
        'css':       data.get('css',       ''),
        'framework': data.get('framework', 'none'),
        'paper':     data.get('paper',     'a4'),
    }
    request.session.modified = True
    return JsonResponse({"status": "ok"})


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