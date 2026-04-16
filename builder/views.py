from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from .services import PDFService

# Framework CDN map — extend this dict to add more frameworks later
FRAMEWORK_CDN_MAP = {
    "tailwind": '<link rel="stylesheet" href="https://cdn.tailwindcss.com">',
    "bootstrap": '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">',
    "none": "",
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

h1 {
  font-size: 2rem;
  margin: 0 0 0.25rem;
}

h2 {
  font-size: 1.1rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid #ccc;
  padding-bottom: 0.25rem;
  margin-top: 1.5rem;
}

h3 {
  margin: 0.5rem 0 0.1rem;
  font-size: 1rem;
}

.date {
  font-size: 0.85rem;
  color: #555;
}

ul {
  margin: 0.4rem 0 0 1rem;
  padding: 0;
}

li {
  margin-bottom: 0.25rem;
}"""


def workspace(request):
    """
    Main editor view. Passes default content and framework options to the template.
    The `user` object is already available via request.user — when auth is added,
    we'll load saved resume data here. For now, we use the defaults.
    """
    context = {
        "default_html": DEFAULT_HTML,
        "default_css": DEFAULT_CSS,
        "frameworks": ["none", "tailwind", "bootstrap"],
        # Future hook: user = request.user (will be AnonymousUser for now)
    }
    return render(request, "builder/workspace.html", context)


@require_POST
def export_pdf(request):
    """
    Receives HTML, CSS, and framework choice via POST.
    Returns a PDF file as an attachment download.
    HTMX will handle this as a standard form POST.
    """
    html = request.POST.get("html", "")
    css = request.POST.get("css", "")
    framework = request.POST.get("framework", "none")
    framework_css = FRAMEWORK_CDN_MAP.get(framework, "")

    service = PDFService(html=html, css=css, framework_css=framework_css)

    try:
        pdf_bytes = service.render_pdf()
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="resume.pdf"'
    return response