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

## Phase 2: User Accounts & Resume Management

### Authentication

User accounts are powered by **django-allauth** with the following configuration:

- Email/password signup and login
- Social login via **Google** and **GitHub** (OAuth credentials required in `.env`)
- Email verification: controlled by `EMAIL_VERIFICATION` in `.env`
  (`none` | `optional` | `mandatory`)
- Password reset via email
- Session persistence — no account required to use the workspace

### User Model

Extends Django's `AbstractUser` with these additional fields:

| Field | Purpose |
|---|---|
| `display_name` | Preferred public name |
| `avatar_url` | Filled automatically by social login |
| `bio` | Short tagline for future public profile |
| `website` | Personal or portfolio URL |

Social connections (GitHub, Google) are managed via allauth's
`SocialAccount` model — no manual token storage required.

### Resume Model

| Field | Type | Notes |
|---|---|---|
| `user` | FK → User | Owner |
| `title` | CharField | User-defined name |
| `slug` | SlugField | Auto-generated, unique |
| `html_content` | TextField | Resume HTML |
| `css_content` | TextField | Resume CSS |
| `framework` | CharField | none / tailwind / bootstrap |
| `paper_size` | CharField | a4 / letter / legal / a5 |
| `photo_url` | URLField | Optional profile photo URL |
| `is_public` | BooleanField | Controls public slug visibility |
| `created_at` | DateTimeField | Auto |
| `updated_at` | DateTimeField | Auto on save |

### Workspace + Account Integration

- **Autosave:** Editor state is saved to the Django session every 1.5s.
  If a saved resume is loaded (slug present in session), changes are also
  written to the database record automatically.
- **Save as new:** A modal prompts for a title (and optional photo URL)
  and creates a new `Resume` record linked to the user.
- **New Resume flow:** A confirmation modal checks for unsaved work before
  clearing the workspace. Users can save first or discard and start fresh.
- **Open from profile:** Loading a saved resume writes its content to the
  session and redirects to the workspace.

### Public Resume URLs

Saved resumes can be published at `/r/<slug>/`.

- Toggle visibility per resume from the profile page (eye icon).
- Public pages render sanitized HTML/CSS via `bleach` — script tags,
  event handlers, and dangerous CSS patterns are stripped.
- A fixed attribution bar shows the owner's name and links back to
  Code2Resume.
- Private or non-existent slugs render a custom 404 page.
- The public page enforces desktop-width layout (`min-width` set to paper
  width) so resume formatting is preserved on all screen sizes.

### Key URLs

| URL | View |
|---|---|
| `/accounts/signup/` | Create account |
| `/accounts/login/` | Sign in |
| `/accounts/logout/` | Sign out |
| `/accounts/password/reset/` | Request password reset |
| `/u/profile/` | Resume list + profile |
| `/u/profile/edit/` | Edit profile fields |
| `/u/resume/<slug>/open/` | Load resume into workspace |
| `/u/resume/<slug>/delete/` | Delete resume |
| `/u/resume/<slug>/toggle-public/` | Toggle public/private |
| `/resume/new/` | Clear workspace (with confirmation) |
| `/resume/save-as/` | Save current workspace as named resume |
| `/r/<slug>/` | Public resume page |

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
- **Phase 3 — Template Library:** Pre-built HTML/CSS resume skeletons to fork and customise.
- **Phase 4 — AI Integration:** Content recommendations, grammar polish, and ATS-optimization checks powered by an LLM.
- **Phase 5 — Live Deploy:** Final preparations and all setup touches for deployment.

---

## Attribution

**Code2Resume** is a project under the **Brand Nova** umbrella, focused on building high-performance, developer-first tools.

Built with ❤ by [Brand Nova](https://brandnova.pythonanywhere.com)

> *Built for developers who care about the source code of their career.*