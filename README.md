# Code2Resume

A developer-centric, "Resume-as-Code" builder that gives you total control over your professional presentation. No clunky drag-and-drop interfaces, just pure HTML, CSS, and your favorite utility frameworks.

**Code2Resume** lets you build your resume in a real-time split-pane editor and export
a pixel-perfect PDF powered by a headless Chromium engine.

---

## Phase 1: The "Anonymous" MVP

This initial launch focuses on a high-utility, paste-and-download workflow. No accounts required. Just open, code, and export.

### Core Features

**Split-Pane Workspace**
A full-viewport editor environment with two tabs (HTML and CSS) on the left and a live preview iframe on the right. The preview updates on every keystroke using Alpine.js `srcdoc` binding with no round-trips to the server.

**Syntax-Highlighted Code Editors**
Both editors are powered by CodeJar and Highlight.js, giving you proper syntax highlighting for HTML and CSS. The editor supports Tab-to-indent, Undo/Redo, and all native browser text editing shortcuts.

**Framework Injector**
A dropdown lets you select None, Tailwind CSS, or Bootstrap. The chosen framework's CDN is injected directly into the preview iframe, so utility classes render immediately as you type. The same framework choice is passed to the PDF engine at export time.

**Paper Size Selection**
Choose from A4, Letter, Legal, or A5. The preview container resizes to match the selected paper dimensions (at 96 dpi) and page-break guides reposition accordingly. The PDF is exported at the correct paper format.

**Page Break Guides**
A toggleable overlay draws dashed lines at page boundaries inside the preview, helping you avoid content being split awkwardly across pages.

**Playwright PDF Engine**
Clicking "Export PDF" submits your HTML, CSS, framework, and paper choice to a Django view. A `PDFService` class assembles a self-contained HTML document and passes it to a headless Chromium instance via Playwright, which renders and returns a PDF file download. The service is structured as a standalone class for easy extension (AI analysis, batch export) in future phases.

**Session Persistence**
Your HTML, CSS, framework, and paper selection are saved to the Django session automatically as you type (debounced at 1.5s). Refreshing the page or closing and reopening the browser restores your last working state.

**Theme Toggle**
Switch between a dark theme (default) and a light theme using the sun/moon button in the navbar. The Highlight.js theme swaps simultaneously (Atom One Dark ↔ GitHub). Theme preference is stored in `localStorage`.

**Keyboard Shortcuts**
| Shortcut | Action |
|---|---|
| `Ctrl+1` | Switch to HTML editor |
| `Ctrl+2` | Switch to CSS editor |
| `Ctrl+S` | Save session immediately |
| `Ctrl+K` | Toggle shortcuts panel |
| `?` | Open shortcuts panel (when outside editor) |
| `Esc` | Close modal or dropdown |
| `Tab` | Indent in editor |
| `Ctrl+Z / Y` | Undo / Redo |
| `Ctrl+C / X / V` | Copy / Cut / Paste |

**Mobile Responsive Layout**
On small screens the split pane collapses to a single full-screen panel. A hamburger menu in the navbar exposes a dropdown with framework, paper, guides, and view controls. The Export PDF and theme toggle buttons remain always visible.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 5.2 (monolith) |
| PDF Engine | Playwright (headless Chromium) |
| Frontend interactivity | Alpine.js, HTMX |
| Code editors | CodeJar + Highlight.js |
| App styling | Tailwind CSS + custom CSS variables |
| Session storage | Django server-side sessions |
| Theme persistence | `localStorage` |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js (for Tailwind build pipeline)
- Playwright Chromium: `python -m playwright install chromium`

### Installation

```bash
# 1. Clone and enter the project
git clone https://github.com/brandnova/code2resume.git
cd code2resume

# 2. Create and activate virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install Python dependencies
pip install -r requirements.txt
python -m playwright install chromium

# 4. Build Tailwind CSS
cd tailwind  # or wherever your build config lives
npm install
npm run dev # stop the server once rebuilding is complete.
npm run build

# 5. Run migrations and start the server
cd ../
python manage.py migrate
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` to open the workspace.

---

## Project Structure

```
code2resume/
├── core/                   # Django project settings and root URLs
├── builder/                # Main app
│   ├── services.py         # PDFService (Playwright rendering)
│   ├── views.py            # workspace, export_pdf, save_session
│   ├── urls.py
│   └── templatetags/
│       └── builder_extras.py   # tojson filter
├── templates/
│   ├── base.html
│   └── builder/
│       └── workspace.html
├── static/
│   ├── css/
│   │   ├── main.css            # Custom design tokens and component styles
│   │   ├── tailwind.min.css    # Built by Tailwind pipeline
│   │   ├── highlight.min.css   # Atom One Dark (dark theme)
│   │   └── highlight-light.min.css  # GitHub (light theme)
│   └── js/
│       ├── workspace.js        # Alpine component + CodeJar init
│       ├── alpine.min.js
│       ├── htmx.min.js
│       ├── highlight.min.js
│       └── codejar.min.js
└── manage.py
```

---

## Roadmap

- **Phase 2 — User Accounts:** Save multiple resumes linked to a profile, accessible via unique shareable slug URLs.
- **Phase 3 — AI Integration:** Content recommendations, grammar polish, and ATS-optimisation checks powered by an LLM.
- **Phase 4 — Template Library:** Pre-built HTML/CSS resume skeletons to fork and customise.
- **Phase 5 — Live Deploy:** Turn any saved resume into a hosted public landing page with one click.

---

## Attribution

**Code2Resume** is a project under the **Brand Nova** umbrella, focused on building high-performance, developer-first tools.

Built with ❤ by [Brand Nova](https://brandnova.pythonanywhere.com)

> *Built for developers who care about the source code of their career.*