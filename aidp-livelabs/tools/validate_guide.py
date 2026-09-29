"""Check generated reader links, anchors and screenshot files without network."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, content):
        super().__init__()
        self.refs, self.ids = [], set()
        self.feed(content)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if attrs.get(key):
                self.refs.append(attrs[key])


def main():
    paths = [ROOT / "README.html", *sorted((ROOT / "docs").rglob("*.html"))]
    pages = {p.resolve(): Page(p.read_text()) for p in paths}
    checked = 0
    for source, page in pages.items():
        for ref in page.refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc:
                continue
            destination = (source.parent / unquote(url.path)).resolve() if url.path else source
            assert destination.is_file(), (source, ref, "missing file")
            if url.fragment and destination in pages:
                assert unquote(url.fragment) in pages[destination].ids, (source, ref, "missing anchor")
            checked += 1
    images = []
    for path in sorted((ROOT / "docs/images").glob("*.png")):
        with Image.open(path) as img:
            width, height = img.size
            img.verify()
        assert width >= 1000 and height >= 500, path
        images.append({"file": str(path.relative_to(ROOT)), "width": width, "height": height})
    # Public edition intentionally omits account-specific screenshots.
    report = {"html_pages": len(pages), "local_links_and_anchors_checked": checked,
              "aidp_screenshots": images, "cloud_execution_claimed": "None: these checks validate local guide links, not cloud execution."}
    (ROOT / "validation/guide-validation.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
