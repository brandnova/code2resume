/* ============================================================
   workspace.js
   Theme functions (applyTheme, getSavedTheme, toggleGlobalTheme)
   are global — defined in toasts.js, loaded before this file.
   ============================================================ */

const DEFAULT_HTML     = window.__C2R_HTML__;
const DEFAULT_CSS      = window.__C2R_CSS__;
const DEFAULT_FW       = window.__C2R_FW__;
const DEFAULT_PAPER    = window.__C2R_PAPER__;
const SESSION_SAVE_URL = window.__C2R_SAVE_URL__;
const CSRF_TOKEN       = document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? "";

const FRAMEWORK_CDN = {
    none:      "",
    tailwind:  '<script src="https://cdn.tailwindcss.com"><\/script>',
    bootstrap: '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">',
};

const PAPER_DIMENSIONS = {
    a4:     { w: 794,  h: 1123 },
    letter: { w: 816,  h: 1056 },
    legal:  { w: 816,  h: 1344 },
    a5:     { w: 559,  h: 794  },
};

const MAX_PAGES = 8;

function debounce(fn, ms) {
    let t;
    return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
}


function resumeWorkspace() {
    return {

        /* ---- state ---- */
        htmlCode:          DEFAULT_HTML,
        cssCode:           DEFAULT_CSS,
        framework:         DEFAULT_FW,
        paper:             DEFAULT_PAPER,
        activeTab:         "html",
        showPageBreaks:    true,
        isExporting:       false,
        iframeDocument:    "",
        mobileView:        "editor",
        sessionSaved:      true,
        showShortcuts:     false,
        mobileMenuOpen:    false,

        /* save modal */
        showSaveModal:     false,
        saveTitle:         window.__C2R_RESUME_TITLE__ || '',
        currentResumeSlug: window.__C2R_RESUME_SLUG__  || '',
        saveError:         '',
        isSaving:          false,
        photoUrl:          window.__C2R_PHOTO_URL__    || '',

        /* new resume modal */
        showNewResumeModal: false,

        /* private */
        _htmlJar:          null,
        _cssJar:           null,
        _saveDebounced:    null,


        /* ---- computed ---- */

        get paperDims() {
            return PAPER_DIMENSIONS[this.paper] || PAPER_DIMENSIONS.a4;
        },

        get pageBreakPositions() {
            return Array.from(
                { length: MAX_PAGES - 1 },
                (_, i) => (i + 1) * this.paperDims.h
            );
        },

        get isDark() {
            return getSavedTheme() === 'dark';
        },


        /* ---- init ---- */

        init() {
            this._saveDebounced = debounce(() => this.saveSession(), 1500);
            this.updatePreview();
            this.initEditors();
            this.initExportReset();
            this.initKeyboardShortcuts();

            // ?new=1 — user arrived via "New Resume" link
            const params = new URLSearchParams(window.location.search);
            if (params.get('new') === '1') {
                window.history.replaceState({}, '', window.location.pathname);
                this.$nextTick(() => { this.showNewResumeModal = true; });
            }

            // ?save=1 — user was redirected here after login
            if (params.get('save') === '1') {
                window.history.replaceState({}, '', window.location.pathname);
                this.$nextTick(() => this.openSaveModal());
            }
        },


        /* ---- theme (delegates to toasts.js globals) ---- */

        toggleTheme() {
            toggleGlobalTheme();
            // Re-highlight editors after theme swap
            this._rehighlight('html-editor', 'html');
            this._rehighlight('css-editor',  'css');
        },

        _rehighlight(elId, lang) {
            const el = document.getElementById(elId);
            if (!el || typeof hljs === 'undefined') return;
            el.innerHTML = hljs.highlight(
                el.textContent ?? "",
                { language: lang, ignoreIllegals: true }
            ).value;
        },


        /* ---- CodeJar ---- */

        initEditors() {
            const tryInit = () => {
                if (typeof window.CodeJar === 'undefined' || typeof window.hljs === 'undefined') {
                    setTimeout(tryInit, 50);
                    return;
                }
                this._setupJar('html-editor', 'htmlCode', 'html');
                this._setupJar('css-editor',  'cssCode',  'css');
            };
            tryInit();
        },

        _setupJar(elId, stateKey, lang) {
            const el = document.getElementById(elId);
            if (!el) return;

            const highlighter = (editor) => {
                editor.innerHTML = hljs.highlight(
                    editor.textContent ?? "",
                    { language: lang, ignoreIllegals: true }
                ).value;
            };

            el.textContent = this[stateKey];
            highlighter(el);

            const jar = window.CodeJar(el, highlighter, { tab: '  ' });
            jar.onUpdate(code => {
                this[stateKey] = code;
                this.updatePreview();
                this.sessionSaved = false;
                this._saveDebounced();
            });

            if (lang === 'html') this._htmlJar = jar;
            else                  this._cssJar  = jar;
        },


        /* ---- preview ---- */

        updatePreview() {
            const fw   = FRAMEWORK_CDN[this.framework] || "";
            const dims = this.paperDims;
            this.iframeDocument = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
${fw}
<style>
html, body { margin: 0; padding: 0; width: ${dims.w}px; }
${this.cssCode}
</style>
</head>
<body>${this.htmlCode}</body>
</html>`;
        },


        /* ---- controls ---- */

        switchTab(tab)      { this.activeTab = tab; },
        onPaperChange()     { this.updatePreview(); this.sessionSaved = false; this._saveDebounced(); },
        onFrameworkChange() { this.updatePreview(); this.sessionSaved = false; this._saveDebounced(); },

        toggleMobileView() {
            this.mobileView     = this.mobileView === 'editor' ? 'preview' : 'editor';
            this.mobileMenuOpen = false;
        },

        closeMobileMenu() { this.mobileMenuOpen = false; },


        /* ---- session auto-save ---- */

        async saveSession() {
            try {
                await fetch(SESSION_SAVE_URL, {
                    method:  'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
                    body: JSON.stringify({
                        html:      this.htmlCode,
                        css:       this.cssCode,
                        framework: this.framework,
                        paper:     this.paper,
                        photo_url: this.photoUrl,
                    }),
                });
                this.sessionSaved = true;
            } catch (_) { /* silent */ }
        },


        /* ---- PDF export ---- */

        prepareExport(formEl) {
            formEl.querySelector('[name=html]').value      = this.htmlCode;
            formEl.querySelector('[name=css]').value       = this.cssCode;
            formEl.querySelector('[name=framework]').value = this.framework;
            formEl.querySelector('[name=paper]').value     = this.paper;
            this.isExporting = true;
        },

        initExportReset() {
            document.addEventListener('visibilitychange', () => {
                if (document.visibilityState === 'visible') this.isExporting = false;
            });
            setInterval(() => { if (this.isExporting) this.isExporting = false; }, 12000);
        },


        /* ---- shortcuts modal ---- */

        openShortcuts()  { this.showShortcuts  = true;  this.mobileMenuOpen = false; },
        closeShortcuts() { this.showShortcuts  = false; },


        /* ---- keyboard shortcuts ---- */

        initKeyboardShortcuts() {
            document.addEventListener('keydown', (e) => {
                const ctrl = e.ctrlKey || e.metaKey;

                if (e.key === 'Escape') {
                    if (this.showNewResumeModal) { this.showNewResumeModal = false; return; }
                    if (this.showSaveModal)      { this.closeSaveModal();           return; }
                    if (this.showShortcuts)      { this.closeShortcuts();           return; }
                    if (this.mobileMenuOpen)     { this.mobileMenuOpen = false;     return; }
                }

                if (e.key === '?' && !ctrl) {
                    const inEditor = document.activeElement?.closest('#html-editor, #css-editor');
                    if (!inEditor) { e.preventDefault(); this.showShortcuts = true; }
                    return;
                }

                if (!ctrl) return;

                if (e.key === 'k' || e.key === 'K') {
                    e.preventDefault();
                    e.stopImmediatePropagation();
                    this.showShortcuts = !this.showShortcuts;
                    return;
                }

                if (e.key === 's') { e.preventDefault(); this.saveSession(); return; }
                if (e.key === '1') { e.preventDefault(); this.switchTab('html'); return; }
                if (e.key === '2') { e.preventDefault(); this.switchTab('css');  return; }
            });
        },


        /* ---- save modal ---- */

        openSaveModal() {
            this.saveError = '';
            this.showSaveModal = true;
            this.$nextTick(() => this.$refs.saveTitleInput?.focus());
        },

        closeSaveModal() {
            this.showSaveModal = false;
            this.saveError     = '';
        },

        async confirmSave() {
            const title = this.saveTitle.trim();
            if (!title) { this.saveError = 'Please enter a title.'; return; }

            this.isSaving  = true;
            this.saveError = '';

            try {
                const res = await fetch(window.__C2R_SAVE_AS_URL__, {
                    method:  'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
                    body: JSON.stringify({
                        slug:      this.currentResumeSlug, // empty string = create new
                        title:     title,
                        html:      this.htmlCode,
                        css:       this.cssCode,
                        framework: this.framework,
                        paper:     this.paper,
                        photo_url: this.photoUrl,
                    }),
                });

                const data = await res.json();

                if (res.ok) {
                    this.currentResumeSlug = data.slug;
                    this.saveTitle         = data.title;
                    this.sessionSaved      = true;
                    this.closeSaveModal();
                } else {
                    this.saveError = data.error || 'Something went wrong.';
                }
            } catch (_) {
                this.saveError = 'Network error. Please try again.';
            } finally {
                this.isSaving = false;
            }
        },


        /* ---- new resume flow ---- */

        async executeNewResume() {
            try {
                await fetch(window.__C2R_CLEAR_URL__, {
                    method:  'POST',
                    headers: { 'X-CSRFToken': CSRF_TOKEN },
                });
            } catch (_) { /* non-critical */ }

            /*
             * Full page reload to /  — this ensures the workspace reinitialises
             * from the now-empty session (default template). Alpine state, CodeJar
             * instances, and the currentResumeSlug are all wiped cleanly.
             * No risk of the old slug persisting in memory and triggering a DB sync.
             */
            window.location.href = '/';
        },

        cancelNewResume() {
            this.showNewResumeModal = false;
        },


        /* ---- default content (used only for _rehighlight after theme swap) ---- */

        _applyDefaultContent() {
            const h = window.__C2R_DEFAULT_HTML__;
            const c = window.__C2R_DEFAULT_CSS__;
            this.htmlCode          = h;
            this.cssCode           = c;
            this.framework         = 'none';
            this.paper             = 'a4';
            this.currentResumeSlug = '';
            this.saveTitle         = '';
            this.sessionSaved      = true;
            this.photoUrl          = '';
            if (this._htmlJar) this._htmlJar.updateCode(h);
            if (this._cssJar)  this._cssJar.updateCode(c);
            this.updatePreview();
        },

    };
}