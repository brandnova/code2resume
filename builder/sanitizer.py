"""
HTML/CSS sanitizer for user-submitted resume content.
Used before rendering on public-facing pages.

Strategy:
- HTML: allowlist of safe tags and attributes using bleach.
  Script tags, event handlers, iframes, object/embed are all stripped.
- CSS: basic regex sanitization removing expressions, url() with
  non-data schemes, and JS injection vectors.

This does NOT sanitize content in the private workspace iframe —
that runs sandboxed. This ONLY applies to the public /r/<slug>/ view.
"""

import re
import bleach

# Tags a resume could reasonably use
ALLOWED_TAGS = [
    'a', 'abbr', 'b', 'blockquote', 'br', 'caption', 'cite', 'code',
    'col', 'colgroup', 'dd', 'del', 'details', 'dfn', 'div', 'dl', 'dt',
    'em', 'figcaption', 'figure', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'hr', 'i', 'img', 'ins', 'kbd', 'li', 'mark', 'ol', 'p', 'pre',
    'q', 's', 'samp', 'section', 'small', 'span', 'strong', 'sub',
    'summary', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th', 'thead',
    'time', 'tr', 'u', 'ul', 'var',
]

ALLOWED_ATTRIBUTES = {
    '*':   ['class', 'id', 'style', 'title', 'aria-label', 'aria-hidden',
            'role', 'data-*'],
    'a':   ['href', 'target', 'rel'],
    'img': ['src', 'alt', 'width', 'height', 'loading'],
    'td':  ['colspan', 'rowspan'],
    'th':  ['colspan', 'rowspan', 'scope'],
    'col': ['span'],
    'time':['datetime'],
}

# CSS patterns that could be used for injection
_CSS_DANGEROUS = re.compile(
    r'(javascript\s*:|expression\s*\(|@import|behavior\s*:|'
    r'-moz-binding\s*:|vbscript\s*:|data\s*:\s*text/html)',
    re.IGNORECASE
)

# url() calls pointing to non-data, non-https resources
_CSS_BAD_URL = re.compile(
    r'url\s*\(\s*["\']?\s*(?!data:|https?:|/)',
    re.IGNORECASE
)


def sanitize_html(html: str) -> str:
    """
    Strip disallowed tags and attributes from resume HTML.
    Preserves classes, inline styles, and layout structure.
    """
    if not html:
        return ''
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
        strip_comments=True,
    )


def sanitize_css(css: str) -> str:
    """
    Remove dangerous CSS patterns while preserving valid styling.
    """
    if not css:
        return ''
    css = _CSS_DANGEROUS.sub('/* removed */', css)
    css = _CSS_BAD_URL.sub('url(/* removed */', css)
    return css