/* ============================================================
   Code2Resume — workspace.js
   Alpine.js component + CodeJar initialization
   ============================================================ */

const DEFAULT_HTML = window.__C2R_HTML__;
const DEFAULT_CSS  = window.__C2R_CSS__;

const FRAMEWORK_CDN = {
    none:      "",
    tailwind:  '<script src="https://cdn.tailwindcss.com"><\/script>',
    bootstrap: '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css">',
};

const A4_HEIGHT_PX = 1123;
const MAX_PAGES    = 6;

function resumeWorkspace() {
    return {
        /* ---- state ---- */
        htmlCode:       DEFAULT_HTML,
        cssCode:        DEFAULT_CSS,
        framework:      "none",
        activeTab:      "html",
        showPageBreaks: true,
        isExporting:    false,
        iframeDocument: "",
        mobileView:     "editor",   // "editor" | "preview"

        /* private — CodeJar instances */
        _htmlJar: null,
        _cssJar:  null,

        /* ---- computed ---- */
        get pageBreakPositions() {
            return Array.from({ length: MAX_PAGES - 1 }, (_, i) => (i + 1) * A4_HEIGHT_PX);
        },

        /* ---- init ---- */
        init() {
            this.updatePreview();
            this.initEditors();
            this.initExportReset();
        },

        /* ---- CodeJar setup ---- */
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

            /* Prime the element with current content */
            el.textContent = this[stateKey];

            /* Highlighter fn — strips stale hljs marker to force re-highlight */
            const highlighter = (editor) => {
                editor.removeAttribute('data-highlighted');
                hljs.highlightElement(editor);
            };

            /* Run initial highlight before CodeJar takes over */
            highlighter(el);

            const jar = window.CodeJar(el, highlighter, { tab: '  ' });

            jar.onUpdate(code => {
                this[stateKey] = code;
                this.updatePreview();
            });

            if (lang === 'html') this._htmlJar = jar;
            else                  this._cssJar  = jar;
        },

        /* ---- preview ---- */
        updatePreview() {
            const fw = FRAMEWORK_CDN[this.framework] || "";
            this.iframeDocument = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
${fw}
<style>
html, body { margin: 0; padding: 0; }
${this.cssCode}
</style>
</head>
<body>
${this.htmlCode}
</body>
</html>`;
        },

        /* ---- tab switching ---- */
        switchTab(tab) {
            this.activeTab = tab;
        },

        /* ---- mobile view toggle ---- */
        toggleMobileView() {
            this.mobileView = this.mobileView === 'editor' ? 'preview' : 'editor';
        },

        /* ---- PDF export ---- */
        prepareExport(formEl) {
            formEl.querySelector('[name=html]').value      = this.htmlCode;
            formEl.querySelector('[name=css]').value       = this.cssCode;
            formEl.querySelector('[name=framework]').value = this.framework;
            this.isExporting = true;
        },

        initExportReset() {
            document.addEventListener('visibilitychange', () => {
                if (document.visibilityState === 'visible') {
                    this.isExporting = false;
                }
            });
            /* Hard fallback */
            setInterval(() => {
                if (this.isExporting) this.isExporting = false;
            }, 12000);
        },
    };
}