/* ============================================================
   toasts.js — Global theme management + Django message toasts
   Loaded on every page via base.html
   ============================================================ */

/* ---- Theme ---- */

function getSavedTheme() {
    return localStorage.getItem('c2r-theme') || 'dark';
}

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

function updateThemeIcons() {
    var theme     = getSavedTheme();
    var sunIcons  = document.querySelectorAll('.theme-icon-sun');
    var moonIcons = document.querySelectorAll('.theme-icon-moon');
    sunIcons.forEach(function(el) {
        el.style.display = theme === 'dark' ? 'inline-block' : 'none';
    });
    moonIcons.forEach(function(el) {
        el.style.display = theme === 'light' ? 'inline-block' : 'none';
    });
}

function toggleGlobalTheme() {
    var next = getSavedTheme() === 'dark' ? 'light' : 'dark';
    localStorage.setItem('c2r-theme', next);
    applyTheme(next);
    updateThemeIcons();
}

/* Apply immediately to prevent flash — runs before DOM is ready */
applyTheme(getSavedTheme());

/* Update icons once DOM is available */
document.addEventListener('DOMContentLoaded', updateThemeIcons);


/* ---- Toast manager ---- */

function toastManager() {
    return {
        toasts:   [],
        _counter: 0,

        init() {
            if (window.__TOASTS_INITIALIZED__) return;
            window.__TOASTS_INITIALIZED__ = true;

            if (typeof __DJANGO_MESSAGES__ === 'undefined') return;
            __DJANGO_MESSAGES__.forEach(function(msg, i) {
                setTimeout(function() {
                    this.add(msg.message, msg.tags);
                }.bind(this), i * 150);
            }.bind(this));
        },

        add(message, tags) {
            var id       = ++this._counter;
            var type     = this._resolveType(tags);
            var duration = 6000;
            this.toasts.push({
                id:       id,
                message:  message,
                type:     type,
                icon:     this._resolveIcon(type),
                visible:  true,
                duration: duration,
            });
            setTimeout(function() { this.dismiss(id); }.bind(this), duration);
        },

        dismiss(id) {
            var toast = this.toasts.find(function(t) { return t.id === id; });
            if (toast) toast.visible = false;
            setTimeout(function() {
                this.toasts = this.toasts.filter(function(t) { return t.id !== id; });
            }.bind(this), 400);
        },

        _resolveType(tags) {
            if (!tags)                    return 'info';
            if (tags.includes('error'))   return 'error';
            if (tags.includes('success')) return 'success';
            if (tags.includes('warning')) return 'warning';
            return 'info';
        },

        _resolveIcon(type) {
            var icons = {
                success: 'fas fa-circle-check',
                error:   'fas fa-circle-exclamation',
                warning: 'fas fa-triangle-exclamation',
                info:    'fas fa-circle-info',
            };
            return icons[type] || icons.info;
        },
    };
}