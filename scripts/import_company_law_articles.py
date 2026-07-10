#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import html
import os
import re
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class VersionSource:
    slug: str
    url: str
    html_path: Path
    raw_path: Path
    xml_path: Path
    expected_articles: int


SOURCES = [
    VersionSource(
        slug="cn_company_law_1993",
        url="https://zh.wikisource.org/wiki/中华人民共和国公司法_(1993年)",
        html_path=ROOT / "object-store/company_law/1993/wikisource_company_law_1993.html",
        raw_path=ROOT / "object-store/company_law/1993/raw.txt",
        xml_path=ROOT / "xml-akn/company_law/1993.xml",
        expected_articles=230,
    ),
    VersionSource(
        slug="cn_company_law_1999",
        url="https://zh.wikisource.org/wiki/中华人民共和国公司法_(1999年)",
        html_path=ROOT / "object-store/company_law/1999/wikisource_company_law_1999.html",
        raw_path=ROOT / "object-store/company_law/1999/raw.txt",
        xml_path=ROOT / "xml-akn/company_law/1999.xml",
        expected_articles=230,
    ),
    VersionSource(
        slug="cn_company_law_2004",
        url="https://zh.wikisource.org/wiki/中华人民共和国公司法_(2004年)",
        html_path=ROOT / "object-store/company_law/2004/wikisource_company_law_2004.html",
        raw_path=ROOT / "object-store/company_law/2004/raw.txt",
        xml_path=ROOT / "xml-akn/company_law/2004.xml",
        expected_articles=230,
    ),
    VersionSource(
        slug="cn_company_law_2005",
        url="https://www.gjxfj.gov.cn/gjxfj/xxgk/fgwj/flfg/webinfo/2016/03/1460585589899465.htm",
        html_path=ROOT / "object-store/company_law/2005/gjxfj_company_law_2005.html",
        raw_path=ROOT / "object-store/company_law/2005/raw.txt",
        xml_path=ROOT / "xml-akn/company_law/2005.xml",
        expected_articles=219,
    ),
    VersionSource(
        slug="cn_company_law_2013",
        url="https://zh.wikisource.org/wiki/中华人民共和国公司法_(2013年)",
        html_path=ROOT / "object-store/company_law/2013/wikisource_company_law_2013.html",
        raw_path=ROOT / "object-store/company_law/2013/raw.txt",
        xml_path=ROOT / "xml-akn/company_law/2013.xml",
        expected_articles=218,
    ),
    VersionSource(
        slug="cn_company_law_2018",
        url="https://www.sipf.com.cn/flfg/2020/03/12855.shtml",
        html_path=ROOT / "object-store/company_law/2018/sipf_company_law_2018.html",
        raw_path=ROOT / "object-store/company_law/2018/raw.txt",
        xml_path=ROOT / "xml-akn/company_law/2018.xml",
        expected_articles=218,
    ),
    VersionSource(
        slug="cn_company_law_2023",
        url="https://fgk.chinatax.gov.cn/zcfgk/c100009/c5233383/content.html",
        html_path=ROOT / "object-store/company_law/2023/chinatax_company_law_2023.html",
        raw_path=ROOT / "object-store/company_law/2023/raw.txt",
        xml_path=ROOT / "xml-akn/company_law/2023.xml",
        expected_articles=266,
    ),
]


ARTICLE_RE = re.compile(r"^(第[一二三四五六七八九十百千零〇]+条)", re.MULTILINE)
CHAPTER_RE = re.compile(r"^(第[一二三四五六七八九十百千零〇]+章)\s*(.*)$")
SECTION_RE = re.compile(r"^(第[一二三四五六七八九十百千零〇]+节)\s*(.*)$")


def main() -> None:
    wanted = set(sys.argv[1:]) if len(sys.argv) > 1 else {s.slug for s in SOURCES}
    for source in SOURCES:
        if source.slug not in wanted:
            continue
        print(f"importing {source.slug}")
        source.html_path.parent.mkdir(parents=True, exist_ok=True)
        source.raw_path.parent.mkdir(parents=True, exist_ok=True)
        source.xml_path.parent.mkdir(parents=True, exist_ok=True)

        html_text = fetch(source.url)
        source.html_path.write_text(html_text, encoding="utf-8")
        text = extract_text(html_text)
        source.raw_path.write_text(text + "\n", encoding="utf-8")

        units = parse_units(source.slug, text)
        article_count = sum(1 for unit in units if unit["unit_type"] == "article")
        if article_count != source.expected_articles:
            raise SystemExit(
                f"{source.slug}: expected {source.expected_articles} articles, got {article_count}"
            )

        source.xml_path.write_text(to_xml(source.slug, units), encoding="utf-8")
        upsert_units(source.slug, units)
        update_hashes(source)
        print(f"  articles: {article_count}")
        print(f"  xml: {source.xml_path}")


def fetch(url: str) -> str:
    req = urllib.request.Request(iri_to_uri(url), headers={"User-Agent": "legal-corpus-local/0.1"})
    with urllib.request.urlopen(req, timeout=30) as response:
        data = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
    return data.decode(charset, errors="replace")


def iri_to_uri(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit(
        (
            parts.scheme,
            parts.netloc,
            quote(parts.path),
            quote(parts.query, safe="=&?/:"),
            quote(parts.fragment),
        )
    )


def extract_text(html_text: str) -> str:
    soup = BeautifulSoup(html_text, "lxml")
    for tag in soup(["script", "style", "noscript", "iframe"]):
        tag.decompose()

    candidates = []
    selectors = [
        ".article-content",
        ".TRS_Editor",
        ".content",
        ".main",
        "#printact",
        "body",
    ]
    for selector in selectors:
        for node in soup.select(selector):
            text = node.get_text("\n", strip=True)
            if "第一条" in text and "公司" in text:
                candidates.append(text)

    text = max(candidates, key=len) if candidates else soup.get_text("\n", strip=True)
    lines = [normalize_line(line) for line in text.splitlines()]
    lines = [line for line in lines if line]

    start = next((i for i, line in enumerate(lines) if line.startswith("第一条")), None)
    if start is None:
        start = next((i for i, line in enumerate(lines) if "第一条" in line), 0)
    end = len(lines)
    for i, line in enumerate(lines[start:], start=start):
        if line.startswith(("附：", "附件：", "扫一扫", "相关链接", "本作品来自", "Public domain")):
            end = i
            break
    return "\n".join(lines[start:end])


def normalize_line(line: str) -> str:
    line = html.unescape(line)
    line = line.replace("\u3000", " ").replace("\xa0", " ")
    line = re.sub(r"\s+", " ", line)
    return line.strip()


def parse_units(version_slug: str, text: str) -> list[dict[str, object]]:
    article_positions = list(ARTICLE_RE.finditer(text))
    if not article_positions:
        raise ValueError("no articles found")

    prefix = text[: article_positions[0].start()]
    chapter_titles = parse_headings(prefix)

    units: list[dict[str, object]] = []
    chapter_order = 0
    current_chapter_id = None
    current_section_id = None

    for idx, match in enumerate(article_positions, start=1):
        start = match.start()
        end = article_positions[idx].start() if idx < len(article_positions) else len(text)
        article_text = text[start:end].strip()
        article_no = match.group(1)
        unit_number_int = chinese_article_number(article_no)

        chapter_title = chapter_titles.get(idx, {}).get("chapter")
        section_title = chapter_titles.get(idx, {}).get("section")
        if chapter_title:
            chapter_order += 1
            current_section_id = None
            current_chapter_id = f"{version_slug}:chapter_{chapter_order}"
            units.append(
                {
                    "stable_id": current_chapter_id,
                    "parent_stable_id": None,
                    "unit_type": "chapter",
                    "unit_number": chapter_title[0],
                    "unit_number_int": chapter_order,
                    "title": chapter_title[1],
                    "text": None,
                    "canonical_ref": f"{version_slug.replace('cn_company_law_', 'company_law:')}:chapter_{chapter_order}",
                    "path": f"/chapter[{chapter_order}]",
                    "order_index": chapter_order * 10000,
                }
            )
        if section_title:
            current_section_id = f"{version_slug}:chapter_{chapter_order}:section_{section_title[2]}"
            units.append(
                {
                    "stable_id": current_section_id,
                    "parent_stable_id": current_chapter_id,
                    "unit_type": "section",
                    "unit_number": section_title[0],
                    "unit_number_int": section_title[2],
                    "title": section_title[1],
                    "text": None,
                    "canonical_ref": f"{version_slug.replace('cn_company_law_', 'company_law:')}:chapter_{chapter_order}:section_{section_title[2]}",
                    "path": f"/chapter[{chapter_order}]/section[{section_title[2]}]",
                    "order_index": chapter_order * 10000 + section_title[2] * 100,
                }
            )

        parent = current_section_id or current_chapter_id
        body = ARTICLE_RE.sub("", article_text, count=1).strip()
        units.append(
            {
                "stable_id": f"{version_slug}:article_{unit_number_int}",
                "parent_stable_id": parent,
                "unit_type": "article",
                "unit_number": article_no,
                "unit_number_int": unit_number_int,
                "title": None,
                "text": body,
                "canonical_ref": f"{version_slug.replace('cn_company_law_', 'company_law:')}:article_{unit_number_int}",
                "path": f"/article[{unit_number_int}]",
                "order_index": unit_number_int,
            }
        )
    return units


def parse_headings(prefix: str) -> dict[int, dict[str, tuple]]:
    headings: dict[int, dict[str, tuple]] = {}
    current_chapter = None
    section_counter = 0
    tokens = [normalize_line(line) for line in prefix.splitlines()]
    for i, token in enumerate(tokens):
        chapter = CHAPTER_RE.match(token)
        section = SECTION_RE.match(token)
        next_article = find_next_article_number(tokens, i)
        if chapter and next_article:
            current_chapter = (chapter.group(1), chapter.group(2).strip())
            section_counter = 0
            headings.setdefault(next_article, {})["chapter"] = current_chapter
        elif section and next_article:
            section_counter += 1
            headings.setdefault(next_article, {})["section"] = (
                section.group(1),
                section.group(2).strip(),
                section_counter,
            )
    return headings


def find_next_article_number(tokens: list[str], pos: int) -> int | None:
    for token in tokens[pos + 1 : pos + 12]:
        match = ARTICLE_RE.search(token)
        if match:
            return chinese_article_number(match.group(1))
    return None


def chinese_article_number(article_no: str) -> int:
    text = article_no.removeprefix("第").removesuffix("条")
    digits = {"零": 0, "〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
    units = {"十": 10, "百": 100, "千": 1000}
    total = 0
    current = 0
    for char in text:
        if char in digits:
            current = digits[char]
        elif char in units:
            if current == 0:
                current = 1
            total += current * units[char]
            current = 0
    return total + current


def to_xml(version_slug: str, units: list[dict[str, object]]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<law slug="{version_slug}" format="legal-corpus-simple-akn">',
    ]
    for unit in units:
        attrs = {
            "type": unit["unit_type"],
            "ref": unit["canonical_ref"],
            "number": unit["unit_number"],
            "path": unit["path"],
        }
        attr_text = " ".join(f'{k}="{html.escape(str(v), quote=True)}"' for k, v in attrs.items() if v)
        lines.append(f"  <unit {attr_text}>")
        if unit["title"]:
            lines.append(f"    <heading>{html.escape(str(unit['title']))}</heading>")
        if unit["text"]:
            lines.append(f"    <content>{html.escape(str(unit['text']))}</content>")
        lines.append("  </unit>")
    lines.append("</law>")
    return "\n".join(lines) + "\n"


def upsert_units(version_slug: str, units: list[dict[str, object]]) -> None:
    env = os.environ.copy()
    env.setdefault("PGHOST", "127.0.0.1")
    env.setdefault("PGPORT", "5432")
    env.setdefault("PGDATABASE", "legal_corpus")
    env.setdefault("PGUSER", "legal_corpus")
    env.setdefault("PGPASSWORD", "legal_corpus_dev")

    sql = ["BEGIN;"]
    sql.append(
        f"DELETE FROM legal_units WHERE version_id = (SELECT id FROM legal_versions WHERE slug = {q(version_slug)});"
    )
    id_exprs = {}
    for unit in units:
        stable_id = str(unit["stable_id"])
        parent_stable_id = unit.get("parent_stable_id")
        parent_expr = id_exprs.get(parent_stable_id, "NULL") if parent_stable_id else "NULL"
        text = unit.get("text")
        text_hash = hashlib.sha256(str(text or "").encode("utf-8")).hexdigest() if text else None
        sql.append(
            """
            INSERT INTO legal_units (
              version_id, parent_id, unit_type, unit_number, unit_number_int,
              title, text, canonical_ref, path, order_index, text_hash
            ) VALUES (
              (SELECT id FROM legal_versions WHERE slug = {version_slug}),
              {parent_id},
              {unit_type},
              {unit_number},
              {unit_number_int},
              {title},
              {text},
              {canonical_ref},
              {path},
              {order_index},
              {text_hash}
            );
            """.format(
                version_slug=q(version_slug),
                parent_id=parent_expr,
                unit_type=q(unit["unit_type"]),
                unit_number=q(unit["unit_number"]),
                unit_number_int=unit["unit_number_int"] if unit["unit_number_int"] is not None else "NULL",
                title=q(unit["title"]),
                text=q(text),
                canonical_ref=q(unit["canonical_ref"]),
                path=q(unit["path"]),
                order_index=unit["order_index"],
                text_hash=q(text_hash),
            )
        )
        id_exprs[stable_id] = f"(SELECT id FROM legal_units WHERE canonical_ref = {q(unit['canonical_ref'])})"
    sql.append("COMMIT;")

    subprocess.run(
        ["psql", "-v", "ON_ERROR_STOP=1", "-q"],
        input="\n".join(sql),
        text=True,
        env=env,
        check=True,
    )


def update_hashes(source: VersionSource) -> None:
    env = os.environ.copy()
    env.setdefault("PGHOST", "127.0.0.1")
    env.setdefault("PGPORT", "5432")
    env.setdefault("PGDATABASE", "legal_corpus")
    env.setdefault("PGUSER", "legal_corpus")
    env.setdefault("PGPASSWORD", "legal_corpus_dev")
    raw_hash = hashlib.sha256(source.raw_path.read_bytes()).hexdigest()
    html_hash = hashlib.sha256(source.html_path.read_bytes()).hexdigest()
    sql = f"""
    UPDATE legal_versions
    SET raw_text_uri = {q(relative(source.raw_path))},
        xml_uri = {q(relative(source.xml_path))}
    WHERE slug = {q(source.slug)};

    UPDATE sources
    SET storage_uri = {q(relative(source.html_path))},
        sha256 = {q(html_hash)}
    WHERE url = {q(source.url)};
    """
    subprocess.run(["psql", "-v", "ON_ERROR_STOP=1", "-q", "-c", sql], env=env, check=True)
    print(f"  raw sha256: {raw_hash}")


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def q(value: object) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


if __name__ == "__main__":
    main()
