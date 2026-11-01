"""Read-only snapshot of the public dxf2gcode wiki and its referenced media.

Original payloads are kept outside docs/ and ignored by Git. Publication rights
are deliberately not inferred from the application's software license.
"""

import argparse
from datetime import datetime, timezone
import hashlib
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.error
import urllib.parse
import urllib.request


ROOT = Path(__file__).resolve().parents[2]
BASE = "https://sourceforge.net"
WIKI = BASE + "/p/dxf2gcode/wiki/"
API = BASE + "/rest/p/dxf2gcode/wiki/"
ARCHIVE = ROOT / "doc/migration/sourceforge"


class ContentLinks(HTMLParser):
    """Collect links and images in rendered wiki/comment Markdown only."""

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.links = set()
        self.images = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "div":
            if self.depth:
                self.depth += 1
            elif "markdown_content" in attrs.get("class", "").split():
                self.depth = 1
        if self.depth:
            if tag == "a" and attrs.get("href"):
                self.links.add(attrs["href"])
            if tag == "img" and attrs.get("src"):
                self.images.add(attrs["src"])

    def handle_endtag(self, tag):
        if tag == "div" and self.depth:
            self.depth -= 1


def slug(text):
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", text).strip("_") or "unnamed"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", default=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.snapshot):
        parser.error("snapshot must be a simple directory name")
    snapshot = ARCHIVE / "snapshot" / args.snapshot
    snapshot.mkdir(parents=True, exist_ok=False)
    manifest = {
        "schema_version": 1,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "snapshot_root": snapshot.relative_to(ROOT).as_posix(),
        "scope": "Latest public wiki pages, rendered HTML, public discussion API and referenced media; not revision history or all project downloads.",
        "publication_status": "NOT CLEARED: local preservation only; snapshot excluded from Git and the website.",
        "resources": [], "pages": [], "warnings": [],
    }
    resources = {}
    assets = {}

    def fetch(url, relative, kind, **metadata):
        if url in resources:
            return resources[url]
        record = {"url": url, "kind": kind, "status": "pending", **metadata}
        resources[url] = record
        manifest["resources"].append(record)
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "dxf2gcode-documentation-archive/1.0"})
            with urllib.request.urlopen(request, timeout=25) as response:
                data = response.read()
                content_type = response.headers.get("Content-Type", "")
                record.update(http_status=response.status, final_url=response.url, content_type=content_type)
            is_html = "text/html" in content_type or data.lstrip().lower().startswith((b"<!doctype html", b"<html"))
            # Discussion attachments named "alternate" are legitimate HTML mail
            # bodies. Accept them only when the API's exact byte count matches.
            known_html_attachment = "/_discuss/" in url and "/attachment/" in url and record.get("expected_bytes") == len(data)
            if kind == "asset" and is_html and not known_html_attachment:
                # Login/error pages are not successful image or DXF downloads.
                record.update(status="unexpected_html", error="HTML response instead of media; file not accepted")
                return record
            target = snapshot / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            record.update(status="saved", path=target.relative_to(ROOT).as_posix(), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
            expected = record.get("expected_bytes")
            if expected is not None and expected != len(data):
                record["status"] = "size_mismatch"
            return record
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            record.update(status="unavailable", error=str(error))
            if isinstance(error, urllib.error.HTTPError):
                record["http_status"] = error.code
            return record

    def read_json(record):
        if record["status"] != "saved":
            return None
        try:
            return json.loads((ROOT / record["path"]).read_bytes())
        except (ValueError, UnicodeError) as error:
            record.update(status="invalid_json", error=str(error))
            return None

    def add_asset(url, title, source, author=None, expected_bytes=None):
        url = urllib.parse.urljoin(WIKI + urllib.parse.quote(title) + "/", url)
        url = urllib.parse.urldefrag(url)[0]
        if urllib.parse.urlsplit(url).scheme not in ("http", "https"):
            return
        item = assets.setdefault(url, {"source_pages": [], "discovered_via": [], "contributors": [], "rights_status": "unverified"})
        for key, value in (("source_pages", title), ("discovered_via", source), ("contributors", author)):
            if value and value not in item[key]:
                item[key].append(value)
        if expected_bytes is not None:
            item["expected_bytes"] = expected_bytes

    index_record = fetch(API, "wiki-index.json", "wiki_index")
    fetch(WIKI + "browse_pages/", "wiki-index.html", "wiki_index_html")
    index = read_json(index_record)
    if not index or "pages" not in index:
        manifest["warnings"].append("Could not obtain live page index; no completeness claim is possible.")
    else:
        for title in index["pages"]:
            quoted = urllib.parse.quote(title, safe="")
            page_url = WIKI + quoted + "/"
            folder = "pages/" + slug(title)
            api_record = fetch(API + quoted, folder + "/page.json", "page_api", page=title)
            html_record = fetch(page_url, folder + "/page.html", "page_html", page=title)
            history_record = fetch(page_url + "history", folder + "/history.html", "page_history_html", page=title)
            page = read_json(api_record)
            entry = {"title": title, "url": page_url, "api_url": API + quoted, "rights_status": "unverified", "internal_links": [], "external_links": []}
            manifest["pages"].append(entry)
            if history_record["status"] == "saved":
                history = (ROOT / history_record["path"]).read_text(encoding="utf-8")
                table = history[history.find("<table"):history.find("</table>")]
                history_text = unescape(re.sub(r"<[^>]+>", " ", table))
                entry["history_editors_observed"] = sorted(set(re.findall(r"\bby\s+([\w.*-]+)", history_text)))
                entry["authorship_note"] = "Editors on the retrieved history page; not proof of original authorship or a complete contributor list."
            links = ContentLinks()
            if html_record["status"] == "saved":
                links.feed((ROOT / html_record["path"]).read_text(encoding="utf-8"))
            if page:
                text = page["text"].encode("utf-8")
                target = snapshot / folder / "page.md"
                target.write_bytes(text)
                entry.update(markdown_path=target.relative_to(ROOT).as_posix(), markdown_sha256=hashlib.sha256(text).hexdigest(), modified_at=page.get("mod_date"))
                links.links.update(page.get("related_artifacts", []))
                for attachment in page.get("attachments", []):
                    add_asset(attachment["url"], title, "page attachment", expected_bytes=attachment.get("bytes"))
                # The API embeds only a limited number of posts; fetch all public pages.
                thread_url = page.get("discussion_thread_url")
                if thread_url:
                    seen = set()
                    for page_number in range(100):
                        thread_record = fetch(thread_url + f"?limit=100&page={page_number}", folder + f"/discussion-{page_number}.json", "discussion_api", page=title)
                        thread_data = read_json(thread_record)
                        if not thread_data:
                            manifest["warnings"].append(f"Discussion enumeration incomplete: {title}")
                            break
                        posts = thread_data.get("thread", {}).get("posts", [])
                        new_posts = [post for post in posts if post["slug"] not in seen]
                        if posts and not new_posts:
                            manifest["warnings"].append(f"Discussion pagination repeated posts: {title}")
                            break
                        for post in new_posts:
                            seen.add(post["slug"])
                            for attachment in post.get("attachments", []):
                                add_asset(attachment["url"], title, "discussion attachment", post.get("author"), attachment.get("bytes"))
                        if len(posts) < 100:
                            break
                    else:
                        manifest["warnings"].append(f"Discussion pagination limit reached: {title}")
                    entry["discussion_posts"] = len(seen)
            for url in links.images:
                add_asset(url, title, "embedded content image")
            for url in sorted(links.links):
                absolute = urllib.parse.urljoin(page_url, url)
                if "/attachment/" in absolute or "/screenshot/" in absolute or "docs.google.com/uc?" in absolute:
                    add_asset(absolute, title, "content link")
                if absolute.startswith(WIKI):
                    entry["internal_links"].append(absolute)
                elif urllib.parse.urlsplit(absolute).scheme in ("http", "https"):
                    entry["external_links"].append(absolute)
            print(f"Page: {title}", flush=True)

    for number, (url, metadata) in enumerate(sorted(assets.items()), 1):
        name = slug(urllib.parse.unquote(urllib.parse.urlsplit(url).path.rsplit("/", 1)[-1]))
        fetch(url, f"assets/{number:03d}-{name}", "asset", **metadata)
    fetch("https://slashdotmedia.com/terms-of-use/", "rights/slashdotmedia-terms.html", "rights_evidence")
    fetch("https://sourceforge.net/projects/dxf2gcode/", "rights/project-summary.html", "rights_evidence")
    manifest["summary"] = {
        "pages_indexed": len(manifest["pages"]),
        "pages_with_markdown": sum("markdown_path" in page for page in manifest["pages"]),
        "assets_discovered": len(assets),
        "assets_saved": sum(item["kind"] == "asset" and item["status"] == "saved" for item in manifest["resources"]),
        "incomplete_resources": sum(item["status"] != "saved" for item in manifest["resources"]),
    }
    ARCHIVE.mkdir(parents=True, exist_ok=True)
    output = ARCHIVE / "manifest.json"
    output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (snapshot / "manifest.json").write_bytes(output.read_bytes())
    print(json.dumps(manifest["summary"], indent=2))
    for item in manifest["resources"]:
        if item["status"] != "saved":
            print(item["status"], item["url"], item.get("error", ""))


if __name__ == "__main__":
    main()
