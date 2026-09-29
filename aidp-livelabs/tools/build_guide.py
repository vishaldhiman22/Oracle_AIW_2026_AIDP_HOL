"""Build the offline workshop reader from Markdown using installed Pandoc."""
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    pages = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md")),
             ROOT / "docs/images/README.md"]
    for source in pages:
        relative = source.relative_to(ROOT)
        prefix = "../" * (len(relative.parts) - 1)
        content = source.read_text()
        # Only rewrite local Markdown destinations which have a generated reader.
        def reader_link(match):
            target = match.group(1)
            path = target.split("#", 1)[0]
            if not path.startswith(("https:", "http:")) and (source.parent / path).resolve() in pages:
                target = target.replace(".md", ".html", 1)
            return "](" + target + ")"
        content = re.sub(r"\]\(([^)]+)\)", reader_link, content)
        title = content.splitlines()[0].lstrip("# ")
        subprocess.run([
            "pandoc", "--from=gfm", "--to=html5", "--standalone", "--toc",
            "--toc-depth=2", "--section-divs", "--wrap=none",
            "--template=" + str(ROOT / "tools/guide-template.html"),
            "--metadata=pagetitle:" + title,
            "--variable=root:" + prefix,
            "--output=" + str(source.with_suffix(".html")),
        ], input=content, text=True, check=True)
        print("Built", relative.with_suffix(".html"))


if __name__ == "__main__":
    main()
