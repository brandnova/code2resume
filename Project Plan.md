# Project Plan: "Code2resume" (Internal Name)
Goal: A simplified, high-performance web app for developers to write, preview, and export HTML/CSS resumes with utility framework support.
1. The Technical Stack

* Framework: Django (Monolith architecture).
* Frontend Interactivity: * HTMX: For seamless communication with the backend (e.g., triggering the PDF generation without page refreshes).
   * Alpine.js: For local state management (the "Live" part of the preview) and switching between framework CDNs.
* Styling: Tailwind CSS (for the app UI) and a "Framework Injector" for the resume preview.
* PDF Engine: Playwright (Python). It will run a headless Chromium instance to "print" the HTML to a PDF file.
2. Phase 1: MVP Core Features (The "Anonymous" Launch)

* The Split-Pane Workspace:
   * Editor Side: Clean text areas for HTML and CSS.
   * Preview Side: An isolated `<iframe>` that renders the code in real-time using Alpine.js `srcdoc`.
* Framework Toggle: A dropdown menu allowing users to select None, Tailwind, or Bootstrap. This will dynamically inject the respective CDN link into the `<iframe>` head.
* The PDF "Magic Button":
   * User clicks "Download PDF."
   * HTMX sends the HTML/CSS/Framework choice to a Django view.
   * Playwright renders the page in the background and returns the PDF file as a download response.
* Print Preview Overlay: A visual guide (CSS-based) on the preview pane to show A4 page breaks, helping users avoid cutting off text mid-sentence.
3. Engineering for the Future (The "Nova" Roadmap)
To ensure the initial build doesn't become technical debt, we will implement these "hooks":

* Modular PDF Service: Write the Playwright logic as a standalone service class. Later, when we add AI recommendations, the service can easily be expanded to send the "text-only" version of the resume to an LLM for analysis.
* State-Ready Backend: Even though Phase 1 is anonymous, the Django view will be structured to accept a `user` object. For now, it will be `None`, making the transition to User Authentication and Saved Slugs a simple matter of swapping a variable.
* Storage Strategy: Anonymous resumes will be handled as "Session" data or temporary POST payloads. Once login is added, we’ll move this to a `Resume` model linked to a user profile.
4. Brand Integration

* Visual Language: The app will use a clean, modern, and simple UI, nothing too flashy. Let it actually look like an MVP
* Attribution: A minimal footer: "A Brand Nova Project" or "Built with ❤️ by Brand Nova" with a link back to my V3 portfolio (brandnova.pythonanywhere.com).

