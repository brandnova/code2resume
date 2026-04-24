## Phase 4 Implementation Plan

### What exists

The `PDFService.extract_plain_text()` method already strips HTML tags and returns plain text from the resume content. The `save_as_resume` and `save_session` endpoints already hold the full HTML and CSS. The `Resume` model has all content fields. The `accounts.User` model is ready for a `is_premium` boolean. The dashboard already tracks users and resumes. The template library already has `is_premium` flags on templates with enforcement hooks commented out.

---

### Part 1: Premium Subscription System

**The model change.** Add two fields to `accounts.User`:

```python
is_premium       = models.BooleanField(default=False)
premium_since    = models.DateTimeField(null=True, blank=True)
```

No payment processor in Phase 4 — you'll toggle `is_premium` manually from the dashboard or Django admin for now. The payment integration (Paystack/Flutterwave, consistent with your other projects) comes later. The field exists and everything checks against it.

**What gets gated.** Based on your notes:

- Resume templates marked `is_premium=True` — free users see the lock badge and are blocked at the `load_template` view
- AI features (all of Phase 4) — free users see a prompt to upgrade
- Resume count limit — free users capped at 3 active resumes (configurable via a `settings.py` constant `FREE_RESUME_LIMIT = 3`). The check happens in `save_as_resume` before creating a new record

**Dashboard management.** A new "Subscriptions" section in the dashboard will show: total premium vs free users, a table of premium users with their `premium_since` date, and a simple toggle button per user that calls a staff-only endpoint to flip `is_premium`. No payment integration needed at this stage — just manual control.

**The enforcement pattern.** Every gated view checks `request.user.is_premium` (or the anonymous fallback). When the check fails, the API returns `{"error": "premium_required", "upgrade_url": "/upgrade/"}` and the frontend shows an inline upgrade prompt rather than a hard redirect. This keeps the UX smooth.

---

### Part 2: AI Integration

**The approach.** Use Anthropic's API directly via `fetch` from a Django view — no LangChain, no heavy frameworks. The `PDFService.extract_plain_text()` hook provides the text. You pass it to Claude Sonnet with a structured prompt and get back JSON with the analysis fields. The response is streamed back to the frontend using Django's `StreamingHttpResponse` so users see results appearing progressively rather than waiting for the full response.

**What the AI does.** Three distinct features, each a separate endpoint:

1. **ATS Score** — rates the resume 0-100 against common ATS criteria (keyword density, section headings, formatting signals, length). Returns a score, a tier label (Poor/Fair/Good/Excellent), and three specific improvement bullets. Fast, ~3-5 seconds.

2. **Content Analysis** — deeper review: identifies weak action verbs, vague phrases ("responsible for", "helped with"), missing quantification, and sections that are present/missing. Returns structured feedback per section. ~8-12 seconds.

3. **AI Rewrite Suggestions** — given a selected block of text from the editor, suggests 2-3 alternative rewrites. This is the "inline" feature — a small panel that appears when the user selects text in the editor and clicks "Improve this". ~5-8 seconds.

**The UI.** A collapsible panel docked to the right side of the workspace (a third column, toggle-able). It has three tabs: ATS, Analysis, Improve. Authenticated premium users see the full panel. Free users see the panel but each tab shows an upgrade prompt instead of results. Anonymous users don't see the panel at all.

**The API key.** Stored in `.env` as `ANTHROPIC_API_KEY`. Never exposed to the frontend — all calls go through Django views.

**Rate limiting.** A simple per-user counter in the Django session (no Redis needed): 10 AI requests per day for premium users, enforced in the view. Resets at midnight. The counter is stored as `request.session['ai_requests_today']` and `request.session['ai_requests_date']`.

---

### Part 3: Dashboard additions for Phase 4

The existing dashboard gets two new sections:

**Subscriptions page** (`/dashboard/subscriptions/`) — premium vs free user split donut chart, premium user table with `premium_since` dates, and a toggle button per user. The toggle calls a `POST /dashboard/toggle-premium/<user_id>/` endpoint decorated with `@staff_member_required`.

**AI Usage page** (`/dashboard/ai-usage/`) — daily AI request counts (new `AIRequest` model: user, feature type, timestamp, token count), requests per feature type donut, top users by AI usage table.

---

### Implementation sequence

**Step A** — Premium model + enforcement + resume limit (no UI yet, just the backend gates)
**Step B** — AI endpoints + streaming response (backend only, tested via curl)
**Step C** — Workspace AI panel UI (frontend, gated behind premium check)
**Step D** — Dashboard subscriptions page + premium toggle
**Step E** — Dashboard AI usage page + upgrade prompt page

---

### Open questions before implementation

1. **Payment timing** — do you want a placeholder `/upgrade/` page now (just a "coming soon" card) so the upgrade prompts have somewhere to point, or skip it entirely until the payment phase?

2. **Anthropic API key** — do you have one ready, or should I structure the AI endpoints so they work with a mock response when the key is absent (easier for testing)?
> For testing, you could do that. You could also implement google's gemini studio cuz I have an api key there.

3. **Resume limit** — 3 active resumes for free users feels right for early stage. Agree, or different number?

4. **Streaming vs non-streaming** — streaming gives better UX but requires more careful frontend handling. Do you want the simpler non-streaming version first and upgrade later, or go streaming from the start?

