/* ============================================================
   Code2Resume — workspace.js
   ============================================================ */

const DEFAULT_HTML = window.__C2R_HTML__;
const DEFAULT_CSS  = window.__C2R_CSS__;
const DEFAULT_FW   = window.__C2R_FW__;
const DEFAULT_PAPER = window.__C2R_PAPER__;
const SESSION_SAVE_URL = window.__C2R_SAVE_URL__;

const FRAMEWORK_CDN = {
    none:      "",
    tailwind:  '<script src="https://cdn.tailwindcss.com"><\/script>',
    bootstrap: '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">',
};

// Paper sizes: width and height in px at 96dpi
const PAPER_DIMENSIONS = {
    a4:     { w: 794,  h: 1123 },
    letter: { w: 816,  h: 1056 },
    legal:  { w: 816,  h: 1344 },
    a5:     { w: 559,  h: 794  },
};

const MAX_PAGES = 8;
const CSRF_TOKEN = document.cookie.match(/csrftoken=([^;]+)/)?.[1] ?? "";

/* ---- debounce utility ---- */
function debounce(fn, ms) {
    let timer;
    return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

function resumeWorkspace() {
    return {
        /* ---- state ---- */
        htmlCode:        DEFAULT_HTML,
        cssCode:         DEFAULT_CSS,
        framework:       DEFAULT_FW,
        paper:           DEFAULT_PAPER,
        activeTab:       "html",
        showPageBreaks:  true,
        isExporting:     false,
        iframeDocument:  "",
        mobileView:      "editor",
        sessionSaved:    true,
        showShortcuts: false,

        _htmlJar: null,
        _cssJar:  null,
        _saveDebounced: null,

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

        /* ---- init ---- */
        init() {
            this._saveDebounced = debounce(() => this.saveSession(), 1500);
            this.updatePreview();
            this.initEditors();
            this.initExportReset();
            this.initKeyboardShortcuts();
        },

        /* ---- CodeJar + hljs ---- */
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

            /*
             * Use hljs.highlight() (value API) instead of highlightElement() (DOM API).
             * This avoids the "unescaped HTML" warning: we pass plain text in,
             * get highlighted HTML out, and write it ourselves.
             */
            const highlighter = (editor) => {
                const code    = editor.textContent ?? "";
                const result  = hljs.highlight(code, { language: lang, ignoreIllegals: true });
                editor.innerHTML = result.value;
            };

            el.textContent = this[stateKey];
            highlighter(el);   // initial highlight before CodeJar takes over

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
<body>
${this.htmlCode}
</body>
</html>`;
        },

        /* ---- tab / paper switching ---- */
        switchTab(tab) {
            this.activeTab = tab;
        },

        onPaperChange() {
            this.updatePreview();
            this.sessionSaved = false;
            this._saveDebounced();
        },

        onFrameworkChange() {
            this.updatePreview();
            this.sessionSaved = false;
            this._saveDebounced();
        },

        toggleMobileView() {
            this.mobileView = this.mobileView === 'editor' ? 'preview' : 'editor';
        },

        /* ---- session persistence ---- */
        async saveSession() {
            try {
                await fetch(SESSION_SAVE_URL, {
                    method:  'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken':  CSRF_TOKEN,
                    },
                    body: JSON.stringify({
                        html:      this.htmlCode,
                        css:       this.cssCode,
                        framework: this.framework,
                        paper:     this.paper,
                    }),
                });
                this.sessionSaved = true;
            } catch (_) {
                /* silent fail — not critical */
            }
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

        /* ---- keyboard shortcuts modal ---- */
        openShortcuts() {
            this.showShortcuts = true;
        },

        closeShortcuts() {
            this.showShortcuts = false;
        },

        /* ---- keyboard shortcuts ---- */
        initKeyboardShortcuts() {
            document.addEventListener('keydown', (e) => {
                const ctrl = e.ctrlKey || e.metaKey;

                // Escape — close shortcuts modal
                if (e.key === 'Escape') {
                    this.showShortcuts = false;
                    return;
                }

                // ? — open shortcuts modal (no modifier needed)
                if (e.key === '?' && !e.ctrlKey && !e.metaKey) {
                    // Only if focus is NOT inside an editor
                    const active = document.activeElement;
                    const inEditor = active?.closest('#html-editor, #css-editor');
                    if (!inEditor) {
                        e.preventDefault();
                        this.showShortcuts = true;
                    }
                    return;
                }

                if (!ctrl) return;

                if (e.key === 's') {
                    e.preventDefault();
                    this.saveSession();
                }

                if (e.key === '1') {
                    e.preventDefault();
                    this.switchTab('html');
                }

                if (e.key === '2') {
                    e.preventDefault();
                    this.switchTab('css');
                }

                // Ctrl+/ — open shortcuts modal from anywhere
                if (e.key === '/') {
                    e.preventDefault();
                    this.showShortcuts = !this.showShortcuts;
                }
            });
        },
    };
}