from playwright.sync_api import sync_playwright


class PDFService:
    def __init__(self, html: str, css: str, framework_css: str = "", paper_format: str = "A4"):
        self.html          = html
        self.css           = css
        self.framework_css = framework_css
        self.paper_format  = paper_format

    def _build_document(self) -> str:
        """
        Assembles a complete, self-contained HTML document for rendering.
        The framework_css is a CDN <link> tag injected into the head.
        """
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    {self.framework_css}
    <style>
        /*
         * PDF-specific reset: let content determine height naturally.
         * This prevents Playwright from capturing trailing whitespace
         * when content doesn't fill the full page height.
         */
        html, body {{
            margin: 0;
            padding: 0;
            height: auto !important;
            min-height: unset !important;
        }}
        {self.css}
    </style>
</head>
<body>
    {self.html}
</body>
</html>"""

    def render_pdf(self) -> bytes:
        """
        Renders the assembled document to a PDF using a headless Chromium instance.
        Returns raw PDF bytes.
        """
        document = self._build_document()
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page    = browser.new_page()
            page.set_content(document, wait_until="networkidle")
            pdf_bytes = page.pdf(
                format=self.paper_format,
                print_background=True,
                # 'auto' height: Playwright respects natural content height
                # and won't pad to a full page if content is shorter.
                # Multi-page content still flows correctly across pages.
                height=None,
                margin={
                    "top":    "10mm",
                    "bottom": "10mm",
                    "left":   "10mm",
                    "right":  "10mm",
                },
            )
            browser.close()
        return pdf_bytes

    def extract_plain_text(self) -> str:
        """
        Future hook: strips HTML tags and returns plain text for LLM analysis.
        Not yet called anywhere — reserved for the AI recommendations phase.
        """
        from html.parser import HTMLParser

        class _Extractor(HTMLParser):
            def __init__(self):
                super().__init__()
                self.chunks = []
            def handle_data(self, data):
                self.chunks.append(data)

        p = _Extractor()
        p.feed(self.html)
        return " ".join(p.chunks).strip()