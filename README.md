# Code2Resume

A developer-centric, "Resume-as-Code" builder that gives you total control over your professional presentation. No clunky drag-and-drop interfaces—just pure HTML, CSS, and your favorite utility frameworks.

**Code2Resume** allows you to build your resume in a real-time split-pane editor and export a pixel-perfect PDF powered by a headless browser engine.

---

## 🚀 Phase 1: The "Anonymous" MVP
This initial launch focuses on a high-utility, "Paste & Download" workflow. No accounts required, just open, code, and export.

### Core Features
* **Split-Pane Workspace:**
    * **Editor:** High-performance text areas for raw HTML and CSS.
    * **Live Preview:** An isolated `<iframe>` environment using Alpine.js `srcdoc` for instant, reactive rendering as you type.
* **Framework Support:** Toggle between **Tailwind CSS**, **Bootstrap**, or **Vanilla CSS** via a simple dropdown. The app dynamically injects the required CDNs into your preview.
* **Playwright PDF Engine:** A "Magic Button" that triggers a view. It uses Playwright (Headless Chromium) to capture your code and generate a PDF that is a 1:1 mirror of the browser render.
* **Print-Aware UI:** A CSS-based overlay on the preview pane that highlights A4 page boundaries, ensuring your content never gets awkwardly cut off by a page break.

---

## 🛠️ Tech Stack
* **Backend:** Django (Monolith)
* **Frontend Interactivity:** HTMX & Alpine.js
* **Styling:** Tailwind CSS (App UI)
* **PDF Generation:** Playwright (Python)
* **Environment:** Fedora KDE / Python 3.x

---

## 🏁 Getting Started

### Prerequisites
* Python 3.10+
* Playwright browsers installed (`playwright install chromium`)

### Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/brandnova/code2resume.git
   cd code2resume
   ```

2. **Set up virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   python -m playwright install chromium
   ```

4. **Run the migrations & server:**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

---

## 🛰️ Roadmap
Code2Resume is built to grow. Future iterations will include:
* **User Accounts:** Save multiple resumes and access them via a unique, sharable "Live Slug" URL.
* **AI Integration:** Content recommendations, grammar polishing, and ATS-optimization checks.
* **Pre-built Skeletons:** Premium HTML/CSS templates to fork and customize.
* **One-Click Deploy:** Turn your resume into a hosted landing page instantly.

---

## 🖋️ Brand Nova
**Code2Resume** is a project under the **Brand Nova** umbrella, focused on building high-performance, developer-first tools with a cinematic touch.

> *Built for developers who care about the source code of their career.*