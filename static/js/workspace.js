/* ============================================================
   Code2Resume — workspace.js
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


/* ============================================================
   Main Alpine component
   ============================================================ */

function resumeWorkspace() {
    return {

        /* ---- state ---- */
        htmlCode:           DEFAULT_HTML,
        cssCode:            DEFAULT_CSS,
        framework:          DEFAULT_FW,
        paper:              DEFAULT_PAPER,
        activeTab:          "html",
        showPageBreaks:     true,
        isExporting:        false,
        iframeDocument:     "",
        mobileView:         "editor",
        sessionSaved:       true,
        showShortcuts:      false,
        mobileMenuOpen:     false,
        theme:              getSavedTheme(),

        /* save modal */
        showSaveModal:      false,
        saveTitle:          window.__C2R_RESUME_TITLE__ || '',
        currentResumeSlug:  window.__C2R_RESUME_SLUG__  || '',
        saveError:          '',
        isSaving:           false,
        photoUrl:           window.__C2R_PHOTO_URL__     || '',

        /* new resume modal */
        showNewResumeModal: false,
        newResumeWarning:   false,
        newResumeTitle:     '',

        /* private */
        _htmlJar:           null,
        _cssJar:            null,
        _saveDebounced:     null,


        /* ============================================================
           Computed
           ============================================================ */

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
            return this.theme === 'dark';
        },


        /* ============================================================
           Init
           ============================================================ */

        init() {
            this._saveDebounced = debounce(() => this.saveSession(), 1500);

            /*
             * Initialize with existing slug (if editing a saved resume).
             * This is critical: if slug is set, the save title should also be set.
             */
            if (window.__C2R_RESUME_SLUG__) {
                this.currentResumeSlug = window.__C2R_RESUME_SLUG__;
                this.saveTitle         = window.__C2R_RESUME_TITLE__;
            }

            /*
             * New resume flow.
             * The server sets __C2R_NEW_REQUESTED__ when the user clicks
             * "New Resume" link. If there's any content in the session,
             * we should show the modal to warn before discarding.
             *
             * Show modal if:
             * - new_resume_requested = true AND
             * - session has content (unsaved work) regardless of save status
             */
            if (window.__C2R_NEW_REQUESTED__) {
                const hasContent = window.__C2R_SESSION_HAS_CONTENT__;
                const isSaved = window.__C2R_SESSION_IS_SAVED__;

                if (hasContent) {
                    /*
                     * Has content — warn user before discarding.
                     * Show title if it's a saved resume being edited.
                     */
                    this.newResumeWarning  = isSaved; // Only show "unsaved changes to [title]" if saved
                    this.newResumeTitle    = window.__C2R_SESSION_TITLE__ || '';
                    this.$nextTick(() => { this.showNewResumeModal = true; });
                } else {
                    /*
                     * No content — just load defaults without prompting.
                     * Session either empty or was already cleared.
                     */
                    this._applyDefaultContent();
                    fetch(window.__C2R_NEW_RESUME_URL__, {
                        method:  'POST',
                        headers: { 'X-CSRFToken': CSRF_TOKEN },
                    }).catch(() => {});
                }
            }

            this.updatePreview();
            this.initEditors();
            this.initExportReset();
            this.initKeyboardShortcuts();

            /*
             * Auto-open save modal when user is redirected back here
             * after logging in via the "Save → login → return" flow.
             */
            const params = new URLSearchParams(window.location.search);
            if (params.get('save') === '1') {
                window.history.replaceState({}, '', window.location.pathname);
                this.$nextTick(() => this.openSaveModal());
            }
        },


        /* ============================================================
           Theme
           ============================================================ */

        toggleTheme() {
            this.theme = this.isDark ? 'light' : 'dark';
            applyTheme(this.theme);
            localStorage.setItem('c2r-theme', this.theme);
            updateThemeIcons();
            this._rehighlight('html-editor', 'html');
            this._rehighlight('css-editor',  'css');
        },

        _rehighlight(elId, lang) {
            const el = document.getElementById(elId);
            if (!el || typeof hljs === 'undefined') return;
            const result = hljs.highlight(el.textContent ?? "", {
                language: lang,
                ignoreIllegals: true,
            });
            el.innerHTML = result.value;
        },


        /* ============================================================
           CodeJar editors
           ============================================================ */

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
             * Use hljs.highlight() (value API) instead of highlightElement()
             * to avoid the "unescaped HTML" console warnings that fire when
             * the DOM API sees already-highlighted innerHTML.
             */
            const highlighter = (editor) => {
                const result = hljs.highlight(editor.textContent ?? "", {
                    language: lang,
                    ignoreIllegals: true,
                });
                editor.innerHTML = result.value;
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


        /* ============================================================
           Preview
           ============================================================ */

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


        /* ============================================================
           Tab / paper / framework controls
           ============================================================ */

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


        /* ============================================================
           Mobile
           ============================================================ */

        toggleMobileView() {
            this.mobileView     = this.mobileView === 'editor' ? 'preview' : 'editor';
            this.mobileMenuOpen = false;
        },

        closeMobileMenu() {
            this.mobileMenuOpen = false;
        },


        /* ============================================================
           Session persistence
           ============================================================ */

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
                        photo_url: this.photoUrl,
                    }),
                });
                this.sessionSaved = true;
            } catch (_) { /* silent — not critical */ }
        },


        /* ============================================================
           PDF export
           ============================================================ */

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
            /* Hard fallback in case visibilitychange doesn't fire */
            setInterval(() => { if (this.isExporting) this.isExporting = false; }, 12000);
        },


        /* ============================================================
           Shortcuts modal
           ============================================================ */

        openShortcuts()  {
            this.showShortcuts  = true;
            this.mobileMenuOpen = false;
        },

        closeShortcuts() {
            this.showShortcuts = false;
        },


        /* ============================================================
           Keyboard shortcuts
           ============================================================ */

        initKeyboardShortcuts() {
            document.addEventListener('keydown', (e) => {
                const ctrl = e.ctrlKey || e.metaKey;

                /* Escape — close whatever is open, in priority order */
                if (e.key === 'Escape') {
                    if (this.showNewResumeModal) { this.showNewResumeModal = false; return; }
                    if (this.showSaveModal)      { this.closeSaveModal();           return; }
                    if (this.showShortcuts)      { this.closeShortcuts();           return; }
                    if (this.mobileMenuOpen)     { this.mobileMenuOpen = false;     return; }
                }

                /* ? — open shortcuts panel (only when focus is outside editors) */
                if (e.key === '?' && !ctrl) {
                    const inEditor = document.activeElement?.closest('#html-editor, #css-editor');
                    if (!inEditor) { e.preventDefault(); this.showShortcuts = true; }
                    return;
                }

                if (!ctrl) return;

                /* Ctrl+K — toggle shortcuts modal */
                if (e.key === 'k' || e.key === 'K') {
                    e.preventDefault();
                    e.stopImmediatePropagation();
                    this.showShortcuts = !this.showShortcuts;
                    return;
                }

                /* Ctrl+S — save session immediately */
                if (e.key === 's') {
                    e.preventDefault();
                    this.saveSession();
                    return;
                }

                /* Ctrl+1 / Ctrl+2 — switch editor tabs */
                if (e.key === '1') { e.preventDefault(); this.switchTab('html'); return; }
                if (e.key === '2') { e.preventDefault(); this.switchTab('css');  return; }
            });
        },


        /* ============================================================
           Save modal (save-as / update)
           ============================================================ */

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
            if (!title) {
                this.saveError = 'Please enter a title for your resume.';
                return;
            }

            this.isSaving  = true;
            this.saveError = '';

            try {
                const isUpdate = !!this.currentResumeSlug;
                const endpoint = isUpdate ? window.__C2R_UPDATE_URL__ : window.__C2R_SAVE_AS_URL__;
                
                const body = {
                    title:     title,
                    html:      this.htmlCode,
                    css:       this.cssCode,
                    framework: this.framework,
                    paper:     this.paper,
                    photo_url: this.photoUrl,
                };

                if (isUpdate) {
                    body.slug = this.currentResumeSlug;
                }

                const res = await fetch(endpoint, {
                    method:  'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken':  CSRF_TOKEN,
                    },
                    body: JSON.stringify(body),
                });

                const data = await res.json();

                if (res.ok) {
                    this.currentResumeSlug = data.slug;
                    this.saveTitle         = data.title;
                    this.sessionSaved      = true;
                    this.closeSaveModal();

                    /*
                     * Only clear session and load defaults for NEW resumes (save-as).
                     * For updates, keep the slug so auto-save continues to update the DB.
                     */
                    if (!isUpdate) {
                        await fetch(window.__C2R_NEW_RESUME_URL__, {
                            method:  'POST',
                            headers: { 'X-CSRFToken': CSRF_TOKEN },
                        }).catch(() => {});
                        this._applyDefaultContent();
                    }
                } else {
                    this.saveError = data.error || 'Something went wrong. Please try again.';
                }
            } catch (_) {
                this.saveError = 'Network error. Please try again.';
            } finally {
                this.isSaving = false;
            }
        },


        /* ============================================================
           New resume flow
           ============================================================ */

        /*
         * executeNewResume() is called by the "Discard & start new" button
         * in the confirmation modal. It POSTs to clear the server session,
         * then applies the default template locally without a page reload.
         */
        async executeNewResume() {
            /* Clear the slug FIRST so auto-save doesn't re-add it after clearing session */
            this.currentResumeSlug = '';
            
            try {
                await fetch(window.__C2R_NEW_RESUME_URL__, {
                    method:  'POST',
                    headers: { 'X-CSRFToken': CSRF_TOKEN },
                });
            } catch (_) { /* non-critical */ }

            this.showNewResumeModal = false;
            this.newResumeWarning   = false;
            this._applyDefaultContent();
        },

        /*
         * Applies the hardcoded default HTML/CSS to both the Alpine state
         * and the CodeJar editor instances. Used by both the conflict-free
         * path in init() and the "Discard" button in the modal.
         */
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

            /*
             * CodeJar instances must be updated via their own API —
             * direct DOM manipulation would break the editor's internal
             * undo history and cursor state.
             */
            if (this._htmlJar) this._htmlJar.updateCode(h);
            if (this._cssJar)  this._cssJar.updateCode(c);

            this.updatePreview();
        },

    }; // end resumeWorkspace
}