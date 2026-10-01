from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_remote_rendering_does_not_use_innerhtml():
    js = (ROOT / 'frontend' / 'app.js').read_text(encoding='utf-8')
    assert '.innerHTML' not in js


def test_tabs_have_accessible_roles_and_relationships():
    html = (ROOT / 'frontend' / 'index.html').read_text(encoding='utf-8')
    assert 'role="tablist"' in html
    assert 'role="tab"' in html
    assert 'role="tabpanel"' in html
    assert 'aria-controls="panelLookup"' in html
    assert 'aria-controls="panelInteractions"' in html


def test_frontend_has_reduced_motion_fallback():
    css = (ROOT / 'frontend' / 'style.css').read_text(encoding='utf-8')
    assert '@media (prefers-reduced-motion: reduce)' in css


def test_interaction_copy_does_not_present_no_match_as_safe():
    html = (ROOT / 'frontend' / 'index.html').read_text(encoding='utf-8').lower()
    js = (ROOT / 'frontend' / 'app.js').read_text(encoding='utf-8').lower()
    assert 'safe to take' not in html + js
    assert 'does not rule out' in html
