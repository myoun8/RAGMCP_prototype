#!/usr/bin/env python3
"""
full_document_ingestion.py

Converts original files in each pack's originals/ directory into normalized
Markdown files using the RChat API.  Skips files that already have a
corresponding normalized .md.  For each new file, streams the model's output,
then asks the user to confirm the target folder before writing.

Usage:
  python scripts/full_document_ingestion.py \\
      [--model <model-name>] \\
      [--api-key KEY] [--pack PACK] [--dry-run]

--api-key defaults to the RCHAT_API_KEY env var.

PDF support requires:  pip install pypdf
"""

import argparse
import os
import re
import sys
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional

from openai import OpenAI

# ── Repo layout ────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from _common import PACKS  # noqa: E402

WORKFLOW_STAGES = [
    "overview",
    "instrument_control",
    "experiment_planning",
    "sample_environment",
    "raw_data",
    "metadata",
    "data_reduction",
    "data_reduction_analysis",
    "data_analysis",
    "troubleshooting",
    "examples",
    "citations_publications",
    "software_installation",
    "developer_reference",
]

SOURCE_TYPE_MAP = {
    "web_pages":     "web_page",
    "pdfs":          "pdf",
    "papers":        "paper",
    "manuals":       "manual",
    "notebooks":     "notebook",
    "scripts":       "code",
    "data_examples": "example",
}

CONVERTIBLE_EXTENSIONS = {".html", ".pdf", ".py", ".ipynb", ".txt", ".rst", ".md"}
ASSET_EXTENSIONS = {
    ".css", ".js", ".png", ".jpg", ".jpeg", ".svg", ".ico", ".gif",
    ".webp", ".woff", ".woff2", ".ttf", ".eot", ".map",
}
SKIP_NAMES = {".gitkeep", "README.md"}

RCHAT_API_KEY_ENV_VAR = "RCHAT_API_KEY"
RCHAT_ENDPOINT       = "https://rchat.nist.gov/api/v1/chat/completions"
RCHAT_BASE_URL       = RCHAT_ENDPOINT.replace("/chat/completions", "")
DEFAULT_MODEL        = "gemma-4-31B-it"
MAX_CONTENT_CHARS    = 50_000


# ── HTML text extraction (stdlib only) ────────────────────────────────────────

class _HTMLTextExtractor(HTMLParser):
    SKIP_TAGS  = frozenset({"script", "style", "nav", "header", "footer", "noscript", "iframe"})
    BLOCK_TAGS = frozenset({"p", "div", "h1", "h2", "h3", "h4", "h5", "h6",
                            "li", "tr", "td", "th", "blockquote", "pre", "br"})

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag, *_):
        if tag in self.SKIP_TAGS:
            self._skip_depth += 1
        elif tag in self.BLOCK_TAGS and self._skip_depth == 0:
            if self.parts and self.parts[-1] != "\n":
                self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)

    def handle_data(self, data):
        if self._skip_depth == 0:
            stripped = data.strip()
            if stripped:
                self.parts.append(stripped)


def extract_html_text(html: str) -> str:
    # Prepend head URLs so the model can identify the canonical source URL
    head_text = ""
    head_match = re.search(r"<head[^>]*>(.*?)</head>", html, re.DOTALL | re.IGNORECASE)
    if head_match:
        urls = re.findall(r'(?:href|content|src)="([^"]*)"', head_match.group(1))
        head_text = "<!-- head URLs: " + "  ".join(urls) + " -->\n\n"

    parser = _HTMLTextExtractor()
    parser.feed(html)
    body = "\n".join(parser.parts)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return head_text + body


# ── PDF text extraction ────────────────────────────────────────────────────────

def extract_pdf_text(path: Path) -> str:
    try:
        import pypdf  # type: ignore
    except ImportError:
        print("  [!] pypdf not installed — cannot read PDF.  Run: pip install pypdf")
        return ""
    reader = pypdf.PdfReader(str(path))
    pages = []
    for i, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(f"[Page {i}]\n{text}")
    return "\n\n".join(pages)


# ── Source ID helpers ──────────────────────────────────────────────────────────

def _scan_existing_ids(pack_dir: Path, prefix: str) -> set[int]:
    pattern = re.compile(rf"\b{re.escape(prefix)}-(\d+)\b", re.IGNORECASE)
    ids: set[int] = set()
    norm_dir = pack_dir / "normalized"
    if not norm_dir.exists():
        return ids
    for md in norm_dir.rglob("*.md"):
        try:
            text = md.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for m in pattern.finditer(text):
            ids.add(int(m.group(1)))
    return ids


def next_source_id(pack_dir: Path, prefix: str, in_run_ids: set[int]) -> str:
    used = _scan_existing_ids(pack_dir, prefix) | in_run_ids
    n = max(used, default=0) + 1
    in_run_ids.add(n)
    return f"{prefix}-{n:03d}"


# ── Skip detection ─────────────────────────────────────────────────────────────

def _normalized_stems(pack_dir: Path) -> set[str]:
    norm_dir = pack_dir / "normalized"
    if not norm_dir.exists():
        return set()
    return {md.stem for md in norm_dir.rglob("*.md")}


def already_normalized(stem: str, normalized_stems: set[str]) -> bool:
    if stem in normalized_stems:
        return True
    # Handle slight name variations (e.g. ncnr_acknowledge ↔ ncnr_acknowledgement)
    for ns in normalized_stems:
        if ns.startswith(stem) or stem.startswith(ns):
            return True
    return False


# ── Collect originals ──────────────────────────────────────────────────────────

def collect_originals(pack_dir: Path) -> list[Path]:
    originals_dir = pack_dir / "originals"
    if not originals_dir.exists():
        return []
    results: list[Path] = []
    for path in sorted(originals_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name in SKIP_NAMES:
            continue
        if path.suffix.lower() in ASSET_EXTENSIONS:
            continue
        if path.suffix.lower() not in CONVERTIBLE_EXTENSIONS:
            continue
        rel_parts = path.relative_to(originals_dir).parts
        if any(part.endswith("_files") for part in rel_parts[:-1]):
            continue
        results.append(path)
    return results


# ── Prompt ────────────────────────────────────────────────────────────────────

_SYSTEM = (
    "You are a scientific documentation specialist converting raw source files into "
    "normalized Markdown for a RAG knowledge base about NIST NCNR neutron-scattering "
    "instruments. Return ONLY the complete normalized Markdown — no explanation, no "
    "preamble, no code fences. Start with the YAML frontmatter block (---) and end "
    "with a <!-- Source: ... --> HTML comment."
)


def _build_prompt(
    pack: str,
    instrument: str,
    source_id: str,
    source_type: str,
    rel_path: str,
    content: str,
    today: str,
) -> str:
    stages_str = " | ".join(WORKFLOW_STAGES)
    body = content[:MAX_CONTENT_CHARS]
    if len(content) > MAX_CONTENT_CHARS:
        body += "\n\n[... content truncated at 50 000 chars ...]"

    return f"""\
Convert the following source document into a normalized Markdown file for the NCNR RAG knowledge base.

## Document context
- Pack / instrument  : {pack} / {instrument}
- Relative path      : {rel_path}
- Assigned source_id : {source_id}
- Inferred source_type (from originals/ subdir): {source_type}
- Today's date       : {today}

## Required YAML frontmatter
Produce ALL fields below using exactly the controlled values listed.

---
doc_id: <stem of source filename, e.g. candor_overview>
source_id: {source_id}
title: <concise descriptive title>
instrument: {instrument}
workflow_stage: <exactly one of: {stages_str}>
source_type: <web_page | pdf_handout | presentation_pdf | manual | paper | notebook | code | example | faq | reference>
access_level: <public | internal | restricted>
status: <current | legacy | deprecated | draft | needs_review | archived | historical | historical_reference>
owner: <responsible team or person>
last_reviewed: {today}
source_url_or_path: <canonical URL if web page; filename only if local file>
source_last_updated: <YYYY-MM-DD if identifiable from content, else omit>
citation_required: <true | false>
# optional — include only when applicable:
# software: NICE | Reductus | Refl1D | Igor | SasView | DAVE | none
# deprecation_notice: true
# related_source_ids: OTHER-001
---

## Normalization rules
1. Open with `---` YAML, blank line, then `# <Title>` heading matching the frontmatter title.
2. Convert to clean Markdown: headings, bullet lists, numbered steps, code blocks, tables.
3. Keep: all technical content — specs, parameters, procedures, equations, code, tables, URLs.
4. Remove: site chrome — nav menus, cookie banners, sharing/print buttons, login widgets, JS/CSS artifacts.
5. Replace personal contact details (names, emails, phones) with `[contact details omitted]`.
6. If the source carries an explicit deprecation / "no longer updated" banner, set
   `status: deprecated` and add a blockquote after the title heading:
   `> DEPRECATION NOTICE: <paraphrase the banner text.>`
7. Choose `workflow_stage` based on the document's primary purpose, not its file path.
8. Close with an HTML comment summarising what was removed:
   `<!-- Source: <title and URL>. <notes on omissions.> -->`

## Source document content
{body}
"""


# ── API call ──────────────────────────────────────────────────────────────────

def call_api(model: str, api_key: str, user_prompt: str) -> str:
    """Stream a chat completion from RChat and return the full response text."""
    client = OpenAI(api_key=api_key, base_url=RCHAT_BASE_URL)
    parts: list[str] = []
    with client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": _SYSTEM},
            {"role": "user",   "content": user_prompt},
        ],
        stream=True,
    ) as stream:
        for chunk in stream:
            piece = chunk.choices[0].delta.content or ""
            if piece:
                print(piece, end="", flush=True)
                parts.append(piece)
    print()
    return "".join(parts)


# ── Frontmatter helpers ────────────────────────────────────────────────────────

def _get_field(markdown: str, field: str) -> Optional[str]:
    m = re.search(rf"^{re.escape(field)}:\s*(.+)", markdown, re.MULTILINE)
    return m.group(1).strip() if m else None


def _set_field(markdown: str, field: str, value: str) -> str:
    return re.sub(
        rf"^({re.escape(field)}:\s*)\S.*",
        rf"\g<1>{value}",
        markdown, count=1, flags=re.MULTILINE,
    )


def _clean_output(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r"^```[a-z]*\n", "", text)
    text = re.sub(r"\n```\s*$", "", text)
    text = text.strip()
    first_fm = text.find("---")
    if first_fm > 0:
        text = text[first_fm:]
    return text + "\n"


# ── User confirmation ──────────────────────────────────────────────────────────

def confirm_and_write(
    pack: str,
    original_stem: str,
    markdown: str,
    dry_run: bool,
) -> Optional[Path]:
    pack_dir = REPO_ROOT / pack
    stage = _get_field(markdown, "workflow_stage")

    fm_match = re.match(r"^---\n(.*?)\n---", markdown, re.DOTALL)
    print(f"\n{'─' * 62}")
    if fm_match:
        print(fm_match.group(0))
        print()
    print(f"Proposed stage  : {stage or '(not detected)'}")
    print(f"Proposed path   : {pack}/normalized/{stage}/{original_stem}.md")
    print(f"Valid stages    : {', '.join(WORKFLOW_STAGES)}")
    print("─" * 62)

    while True:
        ans = input(
            "Accept? [Enter = yes  |  <stage_name> = change stage  |  s = skip  |  q = quit] > "
        ).strip()

        if ans == "":
            chosen = stage
            break
        elif ans.lower() == "s":
            print("  Skipping.")
            return None
        elif ans.lower() == "q":
            print("Aborting.")
            sys.exit(0)
        elif ans in WORKFLOW_STAGES:
            chosen = ans
            print(f"  Stage changed to: {chosen}")
            break
        else:
            print(f"  '{ans}' is not a valid stage.\n  Options: {', '.join(WORKFLOW_STAGES)}")

    if chosen != stage:
        markdown = _set_field(markdown, "workflow_stage", chosen)

    target_dir  = REPO_ROOT / 'context_database' / pack / "normalized" / chosen
    target_path = target_dir / f"{original_stem}.md"

    if dry_run:
        print(f"  [dry-run] Would write → {target_path.relative_to(REPO_ROOT)}")
        return None

    target_dir.mkdir(parents=True, exist_ok=True)
    target_path.write_text(markdown, encoding="utf-8")
    print(f"  Written → {target_path.relative_to(REPO_ROOT)}")
    return target_path


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--model", default=DEFAULT_MODEL, metavar="NAME",
        help=f"RChat model name (default: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--api-key", default=None, metavar="KEY",
        help=f"API key (falls back to {RCHAT_API_KEY_ENV_VAR} env var)",
    )
    parser.add_argument(
        "--pack", choices=PACKS,
        help="Process only this pack (default: all packs)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would be done without writing any files",
    )
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get(RCHAT_API_KEY_ENV_VAR) or ""

    print(f"Model    : {args.model}")
    if args.dry_run:
        print("[dry-run mode — no files will be written]")

    today = date.today().isoformat()
    packs = [args.pack] if args.pack else PACKS

    for pack in packs:
        pack_dir = REPO_ROOT / 'context_database' / pack
        if not pack_dir.exists():
            print(f"\n[{pack}] Directory not found, skipping.")
            continue

        instrument = pack.upper()
        prefix     = instrument
        norm_stems = _normalized_stems(pack_dir)
        originals  = collect_originals(pack_dir)
        to_convert = [o for o in originals if not already_normalized(o.stem, norm_stems)]
        in_run_ids: set[int] = set()

        print(f"\n{'═' * 62}")
        print(f"  Pack: {pack}  |  {len(originals)} originals  |  {len(to_convert)} to convert")
        print(f"{'═' * 62}")

        if not to_convert:
            print("  All originals already normalized — nothing to do.")
            continue

        for original in to_convert:
            rel_path = str(original.relative_to(REPO_ROOT))
            print(f"\n► {rel_path}")

            # ── Extract text content ──
            ext = original.suffix.lower()
            if ext == ".html":
                raw     = original.read_text(encoding="utf-8", errors="ignore")
                content = extract_html_text(raw)
            elif ext == ".pdf":
                content = extract_pdf_text(original)
                if not content.strip():
                    print("  [!] Could not extract PDF text — skipping.")
                    continue
            else:
                try:
                    content = original.read_text(encoding="utf-8", errors="ignore")
                except OSError as exc:
                    print(f"  [!] Could not read file ({exc}) — skipping.")
                    continue

            if not content.strip():
                print("  [!] Empty content — skipping.")
                continue

            subdir      = original.parent.name
            source_type = SOURCE_TYPE_MAP.get(subdir, "document")
            source_id   = next_source_id(pack_dir, prefix, in_run_ids)
            print(f"  Assigned source_id: {source_id}")

            prompt = _build_prompt(
                pack=pack, instrument=instrument, source_id=source_id,
                source_type=source_type, rel_path=rel_path,
                content=content, today=today,
            )

            print("\n  ── Model output ────────────────────────────────────────")
            try:
                raw_output = call_api(args.model, api_key, prompt)
            except Exception as exc:
                print(f"\n  [!] API error: {exc}")
                in_run_ids.discard(int(source_id.split("-")[1]))
                continue
            print("  ────────────────────────────────────────────────────────")

            markdown = _clean_output(raw_output)
            written  = confirm_and_write(pack, original.stem, markdown, args.dry_run)

            if written:
                norm_stems.add(original.stem)

    print("\nDone.")


if __name__ == "__main__":
    main()
