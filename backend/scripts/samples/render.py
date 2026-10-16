"""HTML 내용이 바뀐 문서만 PNG로 재렌더링한다. 김유정 원본7장은 변경하지 않는다."""

import hashlib
import json
from pathlib import Path


def fingerprint(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_folder(folder: Path):
    """기존 캡처 해시가 맞으면 브라우저를 열지 않아 실측 캐시와 시연 이미지를 보존한다."""
    if folder.name == "kim_yujeong":
        return 0
    manifest_path = folder / "render_manifest.json"
    records = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    pending = []
    for html in sorted((folder / "html").glob("*.html")):
        png = folder / "png" / (html.stem + ".png")
        old = records.get(html.stem, {})
        if (
            not png.exists()
            or old.get("html_sha256") != fingerprint(html)
            or old.get("png_sha256") != fingerprint(png)
        ):
            pending.append((html, png))
    if not pending:
        return 0
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            tab = browser.new_page(viewport={"width": 1240, "height": 1754}, device_scale_factor=1)
            for html, png in pending:
                tab.goto(html.resolve().as_uri(), wait_until="load")
                tab.screenshot(path=str(png), full_page=True)
                records[html.stem] = {
                    "html_sha256": fingerprint(html),
                    "png_sha256": fingerprint(png),
                    "renderer": "Playwright Chromium A4",
                }
        finally:
            browser.close()
    manifest_path.write_text(json.dumps(records, ensure_ascii=False, indent=2))
    return len(pending)
