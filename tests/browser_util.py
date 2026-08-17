"""Shared Playwright helpers for the browser tiers.

Input support cannot be measured by watching the DOM: a canvas game reacting
to ArrowLeft only mutates a JS variable, and half the games bind clicks with
addEventListener rather than an onclick attribute. So we instrument
EventTarget.prototype.addEventListener *before* any page script runs, record
every registration, and count real handler invocations. That gives a direct
answer to "did pressing this key run any of the game's code?"
"""

import contextlib

from playwright.sync_api import sync_playwright

# Installed via add_init_script, so it wraps listeners the games register later.
_INSTRUMENT = """
window.__hits = {};
window.__listeners = [];
const _add = EventTarget.prototype.addEventListener;
EventTarget.prototype.addEventListener = function (type, fn, opts) {
  try {
    let desc = 'other';
    if (this === window) desc = 'window';
    else if (this === document) desc = 'document';
    else if (this.tagName) desc = this.tagName.toLowerCase() +
        (this.id ? '#' + this.id : (this.className ? '.' + String(this.className).split(' ')[0] : ''));
    window.__listeners.push({type, target: desc});
    // Tag the element itself rather than reconstructing a selector later:
    // a listener on a bare <div> would otherwise match every div on the page.
    if (this.nodeType === 1 &&
        ['click', 'pointerdown', 'touchstart'].includes(type)) {
      this.setAttribute('data-kb-click-bound', '1');
    }
    if (typeof fn === 'function') {
      const wrapped = function (...a) {
        window.__hits[type] = (window.__hits[type] || 0) + 1;
        return fn.apply(this, a);
      };
      return _add.call(this, type, wrapped, opts);
    }
  } catch (e) { /* never break the page we're measuring */ }
  return _add.call(this, type, fn, opts);
};
"""


@contextlib.contextmanager
def browser_page(viewport, base_url, path, touch=False, browser=None):
    """A page with console/pageerror/failed-request capture attached.

    Yields (page, problems) where problems accumulates anything that would
    show up as breakage for a real player.

    Pass `browser` (the session-scoped fixture) to reuse one Chromium across
    the whole run — launching per test costs ~15s each and turned the suite
    into a 35-minute job. Contexts are still per-call, so state stays isolated.
    """
    problems = []
    owns_browser = browser is None
    pw = sync_playwright().start() if owns_browser else None
    if owns_browser:
        browser = pw.chromium.launch()
    ctx = browser.new_context(
        viewport=viewport,
        has_touch=touch,
        is_mobile=False,   # is_mobile needs non-headless-shell chromium
    )
    ctx.add_init_script(_INSTRUMENT)
    page = ctx.new_page()
    page.on('pageerror', lambda e: problems.append(f'pageerror: {e}'))
    page.on('console', lambda m: problems.append(f'console.{m.type}: {m.text}')
            if m.type == 'error' else None)
    page.on('requestfailed',
            lambda r: problems.append(f'requestfailed: {r.url}'))
    # Not networkidle: several games load images from DuckDuckGo/Unsplash,
    # and waiting for those to settle added ~10s per page for no test value.
    page.goto(f'{base_url}/games/{path}', wait_until='domcontentloaded')
    page.wait_for_timeout(400)
    try:
        yield page, problems
    finally:
        ctx.close()
        if owns_browser:
            browser.close()
            pw.stop()


def active_screen(page):
    """id of the visible .screen, or None for canvas games without them."""
    return page.evaluate("""() => {
        const el = document.querySelector('.screen.active')
            || [...document.querySelectorAll('.screen')]
                 .find(s => getComputedStyle(s).display !== 'none');
        return el ? el.id : null;
    }""")


def visible(page, selector):
    try:
        el = page.query_selector(selector)
        return bool(el and el.is_visible())
    except Exception:
        return False


def focusable_count(page):
    """Elements a keyboard user can actually reach."""
    return page.evaluate("""() => document.querySelectorAll(
        'button:not([disabled]), [tabindex]:not([tabindex="-1"]), a[href], input, select'
    ).length""")


def clickable_but_unfocusable(page):
    """Elements wired for click that a keyboard can never reach.

    Covers both binding styles — the onclick attribute AND addEventListener
    (recorded by the init-script instrumentation). Memory Match binds its
    div cards the second way, so an attribute-only scan misses them entirely.
    """
    return page.evaluate("""() => {
        const out = new Set();
        const consider = (el) => {
            if (!el || !el.tagName) return;
            const tag = el.tagName.toLowerCase();
            if (['button', 'a', 'input', 'select', 'textarea'].includes(tag)) return;
            if (el.hasAttribute('tabindex')) return;
            if (!el.isConnected) return;
            if (getComputedStyle(el).display === 'none') return;
            // id first — it's what identifies a one-off control like a touch
            // overlay; class is the fallback for repeated elements (cards, bins).
            out.add(tag + (el.id ? '#' + el.id
                    : (el.className ? '.' + String(el.className).split(' ')[0] : '')));
        };
        document.querySelectorAll('[onclick]').forEach(consider);
        document.querySelectorAll('[data-kb-click-bound]').forEach(consider);
        return [...out];
    }""")


def hits(page):
    """How many times each event type actually fired a game handler."""
    return page.evaluate('() => window.__hits || {}')


def listener_types(page):
    """Event types the game registered — proof of intent, independent of DOM."""
    return page.evaluate(
        '() => [...new Set((window.__listeners || []).map(l => l.type))].sort()')


def reset_hits(page):
    page.evaluate('() => { window.__hits = {}; }')


def start_game(page, selector):
    """Click the game's start control; returns True if something changed."""
    before = active_screen(page)
    el = page.query_selector(selector)
    if not el:
        return False, before, before
    try:
        el.click(timeout=3000)
    except Exception:
        return False, before, before
    page.wait_for_timeout(600)
    return True, before, active_screen(page)
