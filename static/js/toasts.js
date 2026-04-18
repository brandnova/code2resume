/* ============================================================
   Global theme management — available on all pages
   ============================================================ */

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    var darkLink  = document.querySelector('link[href*="highlight.min.css"]:not(#hljs-light-theme)');
    var lightLink = document.getElementById('hljs-light-theme');
    if (theme === 'light') {
        if (darkLink)  darkLink.disabled  = true;
        if (lightLink) lightLink.disabled = false;
    } else {
        if (darkLink)  darkLink.disabled  = false;
        if (lightLink) lightLink.disabled = true;
    }
}

function getSavedTheme() {
    return localStorage.getItem('c2r-theme') || 'dark';
}

function toggleGlobalTheme() {
    var current = getSavedTheme();
    var next    = current === 'dark' ? 'light' : 'dark';
    localStorage.setItem('c2r-theme', next);
    applyTheme(next);
}

/* Apply immediately on every page load to prevent flash */
applyTheme(getSavedTheme());

function updateThemeIcons() {
    var theme   = getSavedTheme();
    var sunIcons  = document.querySelectorAll('.theme-icon-sun');
    var moonIcons = document.querySelectorAll('.theme-icon-moon');
    sunIcons.forEach(function(el) {
        el.style.display = theme === 'light' ? 'none' : 'inline-block';
    });
    moonIcons.forEach(function(el) {
        el.style.display = theme === 'light' ? 'inline-block' : 'none';
    });
}

function toggleGlobalTheme() {
    var current = getSavedTheme();
    var next    = current === 'dark' ? 'light' : 'dark';
    localStorage.setItem('c2r-theme', next);
    applyTheme(next);
    updateThemeIcons();
}

/* Run on page load */
applyTheme(getSavedTheme());
document.addEventListener('DOMContentLoaded', updateThemeIcons);


/* ============================================================
   Toast notifications — available on all pages
   ============================================================ */
function toastManager() {
    return {
        toasts: [],
        _counter: 0,

        init() {
            // ✅ Guard against double initialization (window-level)
            if (window.__TOASTS_INITIALIZED__) return;
            window.__TOASTS_INITIALIZED__ = true;

            // ✅ Safety check for Django messages
            if (typeof __DJANGO_MESSAGES__ === 'undefined') return;

            // ✅ Add messages with staggered delay to avoid visual clutter
            __DJANGO_MESSAGES__.forEach((msg, i) => {
                setTimeout(() => this.add(msg.message, msg.tags), i * 150);
            });
        },

        add(message, tags) {
            const id = ++this._counter;
            const type = this._resolveType(tags);
            const duration = 6000;

            this.toasts.push({
                id,
                message,
                type,
                icon: this._resolveIcon(type),
                visible: true,
                duration,
            });

            setTimeout(() => this.dismiss(id), duration);
        },

        dismiss(id) {
            const toast = this.toasts.find(t => t.id === id);
            if (toast) toast.visible = false;
            // Wait for leave transition to finish before removing from array
            setTimeout(() => {
                this.toasts = this.toasts.filter(t => t.id !== id);
            }, 400); // Match this to your CSS transition duration
        },

        _resolveType(tags) {
            if (!tags) return 'info';
            if (tags.includes('error')) return 'error';
            if (tags.includes('success')) return 'success';
            if (tags.includes('warning')) return 'warning';
            return 'info';
        },

        _resolveIcon(type) {
            return {
                success: 'fa-solid fa-circle-check',
                error: 'fa-solid fa-circle-exclamation',
                warning: 'fa-solid fa-triangle-exclamation',
                info: 'fa-solid fa-circle-info',
            }[type] || 'fa-solid fa-circle-info';
        },
    };
}

