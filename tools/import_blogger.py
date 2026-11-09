#!/usr/bin/env python3
"""Convert the Blogger export of kcna.ondralinek.cz into Hugo content.

Downloads the Blogger Atom feeds (posts + comments), all post images, and writes:

  content/zpravy/<year>/<month>/<slug>.html   one page per post, original URL preserved
  data/comments/<slug>.yaml                   comments for the post
  static/img/<year>/<month>/<slug>-<n>.<ext>  locally mirrored images

Re-running is safe: cached feeds and already downloaded images are reused unless
--refresh is passed.

Usage:
  python3 tools/import_blogger.py
  python3 tools/import_blogger.py --refresh
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import http.client
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".cache" / "blogger"
POSTS_DIR = ROOT / "content" / "zpravy"
COMMENTS_DIR = ROOT / "data" / "comments"
IMAGES_DIR = ROOT / "static" / "img"

BASE = "https://kcna.ondralinek.cz"
FEED = BASE + "/feeds/posts/default?alt=atom&max-results=150&start-index={start}"
COMMENTS_FEED = BASE + "/feeds/comments/default?alt=atom&max-results=150&start-index={start}"
CANONICAL_HOSTS = ("kcna.ondralinek.cz",)

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "thr": "http://purl.org/syndication/thread/1.0",
}

UA = "Mozilla/5.0 (compatible; kcna-hugo-export/1.0)"


def fetch(url: str, dest: Path, refresh: bool = False, timeout: int = 60, retries: int = 4) -> bytes:
    if dest.exists() and not refresh and dest.stat().st_size > 0:
        return dest.read_bytes()
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            return data
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError) as exc:
            last_error = exc
            time.sleep(1.0 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {last_error}")


def fetch_posts(refresh: bool) -> list[ET.Element]:
    entries: dict[str, ET.Element] = {}
    start = 1
    while True:
        data = fetch(FEED.format(start=start), CACHE / f"posts-{start}.xml", refresh)
        root = ET.fromstring(data)
        batch = root.findall("atom:entry", NS)
        for entry in batch:
            entries[entry.findtext("atom:id", default="", namespaces=NS)] = entry
        total = int(root.findtext("openSearch:totalResults", default="0", namespaces={
            "openSearch": "http://a9.com/-/spec/opensearchrss/1.0/"}))
        if not batch or start + len(batch) > total:
            break
        start += len(batch)
    return list(entries.values())


def fetch_comments(refresh: bool) -> list[ET.Element]:
    data = fetch(COMMENTS_FEED.format(start=1), CACHE / "comments-1.xml", refresh)
    root = ET.fromstring(data)
    return root.findall("atom:entry", NS)


def post_slug(entry: ET.Element) -> str:
    for link in entry.findall("atom:link", NS):
        if link.get("rel") == "alternate" and link.get("type") == "text/html":
            href = link.get("href", "")
            path = href.split("kcna.ondralinek.cz/")[-1]
            return path[:-5] if path.endswith(".html") else path
    raise ValueError("entry without alternate link")


def plain_text(html: str) -> str:
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</h[1-6]>", " ", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )
    return re.sub(r"\s+", " ", text).strip()


def yaml_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


IMAGE_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
SRC_RE = re.compile(r"""\bsrc\s*=\s*(["'])(.*?)\1""", re.IGNORECASE)
HREF_RE = re.compile(r"""\bhref\s*=\s*(["'])(.*?)\1""", re.IGNORECASE)
POST_LINK_RE = re.compile(
    r"""https?://(?:www\.)?(?:kcna\.ondralinek\.cz|kcna\.linek\.co\.uk|kcna\.cz|kcna-news\.blogspot\.com)/(\d{4}/\d{2}/[^"'\s?#]+\.html)""",
    re.IGNORECASE,
)


def image_ext(content_type: str, url: str) -> str:
    mapping = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
        "image/bmp": ".bmp",
    }
    ctype = (content_type or "").split(";")[0].strip().lower()
    if ctype in mapping:
        return mapping[ctype]
    suffix = Path(url.split("?")[0]).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    return ".jpg"


class ImageMirror:
    def __init__(self, refresh: bool = False) -> None:
        self.refresh = refresh
        self.by_url: dict[str, str] = {}
        self.downloaded = 0
        self.failed: set[str] = set()
        self.dead_file = CACHE / "dead-images.txt"
        if self.dead_file.exists():
            self.failed.update(self.dead_file.read_text(encoding="utf-8").split())

    def lookup(self, url: str, slug: str, index: int) -> str | None:
        url = url.strip()
        if url.startswith("//"):
            url = "https:" + url
        if url in self.by_url:
            return self.by_url[url]
        if url in self.failed:
            return None
        if not url.startswith(("http://", "https://")):
            return None
        return self._download(url, slug, index)

    def _download(self, url: str, slug: str, index: int) -> str | None:
        year, month, stem = slug.split("/")
        cache_file = CACHE / "images" / hashlib.sha1(url.encode()).hexdigest()
        try:
            data = fetch(url, cache_file, self.refresh, timeout=10, retries=1)
        except RuntimeError:
            self.failed.add(url)
            return None
        ext = image_ext("", url)
        rel = f"/img/{year}/{month}/{stem}-{index}{ext}"
        dest = ROOT / "static" / rel.lstrip("/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        self.by_url[url] = rel
        if url in self.failed:
            self.failed.discard(url)
        self.downloaded += 1
        return rel


def rewrite_content(html: str, slug: str, mirror: ImageMirror) -> str:
    counter = {"n": 0}

    def fix_img(match: re.Match[str]) -> str:
        tag = match.group(0)
        src_match = SRC_RE.search(tag)
        if not src_match:
            return tag
        counter["n"] += 1
        original = src_match.group(2)
        rel = mirror.lookup(original, slug, counter["n"])
        if not rel:
            return (
                '<img src="/img/missing.svg" class="img-missing" '
                f'alt="Původní obrázek není dostupný" loading="lazy" '
                f'data-original-src="{original.replace(chr(34), "&quot;")}">'
            )
        tag = SRC_RE.sub(f'src="{rel}"', tag, count=1)
        if "loading=" not in tag:
            core = tag[:-1].rstrip()  # drop the closing ">"
            if core.endswith("/"):  # XHTML style "<img ... />"
                core = core[:-1].rstrip()
            tag = core + ' loading="lazy" decoding="async">'
        return tag

    html = IMAGE_TAG_RE.sub(fix_img, html)

    def fix_a(match: re.Match[str]) -> str:
        tag = match.group(0)
        href_match = HREF_RE.search(tag)
        if not href_match:
            return tag
        href = href_match.group(2)
        rel = None
        if href in mirror.by_url:
            rel = mirror.by_url[href]
        elif "<img" in tag.lower():
            counter["n"] += 1
            rel = mirror.lookup(href, slug, counter["n"])
        if rel:
            tag = HREF_RE.sub(f'href="{rel}"', tag, count=1)
        return tag

    html = re.sub(r"<a\b[^>]*>", fix_a, html, flags=re.IGNORECASE)
    html = POST_LINK_RE.sub(lambda m: "/" + m.group(1), html)
    html = re.sub(r"""<a\s+name=["']more["']\s*></a>""", "", html, flags=re.IGNORECASE)
    # Blogger embedded http:// YouTube iframes; upgrade them so they are not
    # blocked as mixed content once the site is served over https.
    html = re.sub(
        r"""(<iframe[^>]*\bsrc=["'])(?:http:)?//(?:www\.)?youtube(?:-nocookie)?\.com/""",
        r"\1https://www.youtube-nocookie.com/",
        html,
        flags=re.IGNORECASE,
    )
    html = re.sub(r"\s+<(br|/p|/div)", lambda m: "<" + m.group(1), html)
    return html.strip()


def build_index(entries: list[ET.Element]) -> dict[str, str]:
    index = {}
    for entry in entries:
        slug = post_slug(entry)
        index[entry.findtext("atom:id", default="", namespaces=NS)] = slug
    return index


def write_post(entry: ET.Element, mirror: ImageMirror) -> str:
    slug = post_slug(entry)
    html = entry.findtext("atom:content", default="", namespaces=NS)
    title = entry.findtext("atom:title", default="", namespaces=NS)
    published = entry.findtext("atom:published", default="", namespaces=NS)
    updated = entry.findtext("atom:updated", default="", namespaces=NS)
    labels = [c.get("term", "") for c in entry.findall("atom:category", NS) if c.get("term")]

    body = rewrite_content(html, slug, mirror)
    description = plain_text(body)
    if len(description) > 280:
        cut = description[:280].rsplit(" ", 1)[0]
        description = cut + "…"

    year, month, name = slug.split("/")
    front = [
        "---",
        f"title: {yaml_str(title)}",
        f"slug: {yaml_str(name)}",
        f"url: {yaml_str('/' + slug + '.html')}",
        f"date: {published}",
    ]
    if updated and updated[:10] != published[:10]:
        front.append(f"lastmod: {updated}")
    front.append(f"description: {yaml_str(description)}")
    if labels:
        front.append("popisky:")
        front.extend(f"  - {yaml_str(label)}" for label in labels)
    front.append("---")

    dest = POSTS_DIR / year / month / f"{name}.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(front) + "\n\n" + body + "\n", encoding="utf-8")
    return slug


def write_comments(comments: list[ET.Element], post_index: dict[str, str]) -> int:
    by_post: dict[str, list[dict[str, str]]] = {}
    for comment in comments:
        reply = comment.find("thr:in-reply-to", NS)
        post_id = reply.get("ref") if reply is not None else None
        slug = post_index.get(post_id or "")
        if not slug:
            continue
        author = comment.findtext("atom:author/atom:name", default="", namespaces=NS)
        if author.strip().lower() in {"", "anonymous"}:
            author = "Anonymní"
        by_post.setdefault(slug, []).append({
            "author": author,
            "date": comment.findtext("atom:published", default="", namespaces=NS),
            "text": comment.findtext("atom:content", default="", namespaces=NS).strip(),
        })

    if COMMENTS_DIR.exists():
        for old in COMMENTS_DIR.glob("*.yaml"):
            old.unlink()
    COMMENTS_DIR.mkdir(parents=True, exist_ok=True)

    for slug, items in by_post.items():
        items.sort(key=lambda c: c["date"])
        lines = []
        for item in items:
            lines.append(f"- author: {yaml_str(item['author'])}")
            lines.append(f"  date: {item['date'] or '2010-01-01T00:00:00+01:00'}")
            lines.append(f"  text: {yaml_str(item['text'])}")
        dest = COMMENTS_DIR / f"{slug.replace('/', '__')}.yaml"
        dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sum(len(v) for v in by_post.values())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="re-download feeds and images")
    args = parser.parse_args()

    print("· fetching feeds")
    entries = fetch_posts(args.refresh)
    comments = fetch_comments(args.refresh)
    print(f"  {len(entries)} posts, {len(comments)} comments")

    post_index = build_index(entries)
    entries.sort(key=lambda e: e.findtext("atom:published", default="", namespaces=NS))
    mirror = ImageMirror(args.refresh)

    print("· writing content (downloading images)")
    slugs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(write_post, entry, mirror) for entry in entries]
        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            slugs.append(future.result())
            if i % 100 == 0:
                print(f"  {i}/{len(entries)} posts, {mirror.downloaded} images")

    print(f"  {len(slugs)} posts written, {mirror.downloaded} images downloaded, "
          f"{len(mirror.failed)} images unreachable")

    count = write_comments(comments, post_index)
    print(f"  {count} comments written")

    if mirror.failed:
        failed_file = CACHE / "dead-images.txt"
        failed_file.write_text("\n".join(sorted(mirror.failed)) + "\n", encoding="utf-8")
        print(f"  unreachable URLs listed in {failed_file.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
