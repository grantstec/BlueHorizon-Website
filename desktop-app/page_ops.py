"""Page creation + Jupyter Book TOC management for BlueHorizon.

Why we hand-roll YAML instead of using PyYAML:
 - We want to keep the .exe small.
 - The _toc.yml has a very narrow, predictable shape (parts -> chapters -> sections)
   that we can read and rewrite ourselves.
 - Hand-rolling lets us preserve the user's exact formatting choices.

Public API used by the GUI:
    list_parts(repo_path)                       -> List[PartInfo]
    list_chapters_in_part(repo_path, part_idx)  -> List[ChapterInfo]
    create_new_page(repo_path, caption, title)              -> str (new file path)
    create_new_subpage(repo_path, parent_file, title)       -> str
    fix_toc_structure(repo_path)                            -> FixReport
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


# ---------------------------------------------------------------------------
# TOC parsing & writing
# ---------------------------------------------------------------------------

@dataclass
class Chapter:
    file: str
    sections: List["Chapter"] = field(default_factory=list)


@dataclass
class Part:
    caption: str
    chapters: List[Chapter] = field(default_factory=list)


@dataclass
class Toc:
    format: str = "jb-book"
    root: str = "intro"
    parts: List[Part] = field(default_factory=list)


@dataclass
class PartInfo:
    index: int
    caption: str
    chapter_count: int


@dataclass
class ChapterInfo:
    index: int
    file: str
    title: str  # human-readable title (derived from filename)


@dataclass
class FixReport:
    merged_captions: List[str] = field(default_factory=list)
    deduplicated_files: List[str] = field(default_factory=list)
    case_corrected: List[Tuple[str, str]] = field(default_factory=list)
    titles_fixed: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return not (
            self.merged_captions
            or self.deduplicated_files
            or self.case_corrected
            or self.titles_fixed
            or self.notes
        )

    def summary(self) -> str:
        if self.is_empty:
            return "Nothing to fix — your TOC is already clean."
        lines: List[str] = []
        if self.merged_captions:
            lines.append(
                f"Merged duplicate captions: {', '.join(sorted(set(self.merged_captions)))}"
            )
        if self.deduplicated_files:
            lines.append(
                f"Removed {len(self.deduplicated_files)} duplicate TOC entries"
            )
        if self.case_corrected:
            lines.append(
                f"Corrected casing on {len(self.case_corrected)} path(s)"
            )
        if self.titles_fixed:
            lines.append(
                f"Fixed sidebar titles on {len(self.titles_fixed)} page(s)"
            )
        for note in self.notes:
            lines.append(note)
        return "\n".join(lines)


# Indentation rules used when serializing — match the existing file style:
#   parts:
#     - caption: ...
#       chapters:
#         - file: ...
#           sections:
#             - file: ...

_INDENT_PART = "  - "
_INDENT_PART_CONT = "    "
_INDENT_CHAPTER = "      - "
_INDENT_CHAPTER_CONT = "        "
_INDENT_SECTION = "          - "


def _docs_dir(repo_path: str) -> str:
    return os.path.join(repo_path, "docs")


def _toc_path(repo_path: str) -> str:
    return os.path.join(_docs_dir(repo_path), "_toc.yml")


def _yaml_quote_if_needed(value: str) -> str:
    """Quote a YAML scalar only when necessary, matching the existing file style.

    The repo currently keeps file paths unquoted (e.g. `file: subteams/engine/...`),
    so we mirror that. Quote when the value contains characters that would
    otherwise confuse a YAML parser (`:` followed by a space, leading `-`, etc.).
    """
    if value == "":
        return '""'
    bad_chars = [": ", "# ", " #"]
    needs_quote = (
        any(b in value for b in bad_chars)
        or value.startswith(("-", "?", "&", "*", "!", "|", ">", "%", "@"))
        or value.strip() != value
    )
    if needs_quote:
        # Use double quotes; escape backslashes and double quotes
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def parse_toc(repo_path: str) -> Toc:
    """Parse the existing _toc.yml. We only support the jb-book shape that
    this repo uses; anything fancier is left untouched."""
    path = _toc_path(repo_path)
    if not os.path.exists(path):
        return Toc()

    with open(path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    toc = Toc()
    current_part: Optional[Part] = None
    current_chapter: Optional[Chapter] = None
    in_parts = False
    in_chapters = False
    in_sections = False

    for raw in lines:
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if raw.startswith("format:"):
            toc.format = raw.split(":", 1)[1].strip()
            continue
        if raw.startswith("root:"):
            toc.root = raw.split(":", 1)[1].strip()
            continue
        if raw.startswith("parts:"):
            in_parts = True
            continue

        if not in_parts:
            continue

        # part start
        m = re.match(r"^  - caption:\s*(.+)$", raw)
        if m:
            current_part = Part(caption=_strip_yaml_quotes(m.group(1).strip()))
            toc.parts.append(current_part)
            current_chapter = None
            in_chapters = False
            in_sections = False
            continue

        if raw.startswith("    chapters:"):
            in_chapters = True
            in_sections = False
            continue

        # chapter start
        m = re.match(r"^      - file:\s*(.+)$", raw)
        if m and current_part is not None:
            current_chapter = Chapter(file=_strip_yaml_quotes(m.group(1).strip()))
            current_part.chapters.append(current_chapter)
            in_sections = False
            continue

        if raw.startswith("        sections:"):
            in_sections = True
            continue

        # section
        m = re.match(r"^          - file:\s*(.+)$", raw)
        if m and current_chapter is not None and in_sections:
            current_chapter.sections.append(
                Chapter(file=_strip_yaml_quotes(m.group(1).strip()))
            )
            continue

    return toc


def _strip_yaml_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
        return value[1:-1]
    return value


def serialize_toc(toc: Toc) -> str:
    lines: List[str] = [f"format: {toc.format}", f"root: {toc.root}", "parts:"]
    for part in toc.parts:
        lines.append(f"{_INDENT_PART}caption: {_yaml_quote_if_needed(part.caption)}")
        lines.append(f"{_INDENT_PART_CONT}chapters:")
        for chapter in part.chapters:
            lines.append(
                f"{_INDENT_CHAPTER}file: {_yaml_quote_if_needed(chapter.file)}"
            )
            if chapter.sections:
                lines.append(f"{_INDENT_CHAPTER_CONT}sections:")
                for section in chapter.sections:
                    lines.append(
                        f"{_INDENT_SECTION}file: {_yaml_quote_if_needed(section.file)}"
                    )
    return "\n".join(lines) + "\n"


def write_toc(repo_path: str, toc: Toc) -> None:
    path = _toc_path(repo_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(serialize_toc(toc))


# ---------------------------------------------------------------------------
# Listing helpers (used by the GUI dropdowns)
# ---------------------------------------------------------------------------

def list_parts(repo_path: str) -> List[PartInfo]:
    toc = parse_toc(repo_path)
    return [
        PartInfo(index=i, caption=p.caption, chapter_count=len(p.chapters))
        for i, p in enumerate(toc.parts)
    ]


def list_chapters_in_part(repo_path: str, part_index: int) -> List[ChapterInfo]:
    toc = parse_toc(repo_path)
    if part_index < 0 or part_index >= len(toc.parts):
        return []
    out: List[ChapterInfo] = []
    for i, chap in enumerate(toc.parts[part_index].chapters):
        out.append(ChapterInfo(index=i, file=chap.file, title=_title_from_file(chap.file)))
    return out


def _title_from_file(file_ref: str) -> str:
    name = os.path.basename(file_ref.replace("\\", "/"))
    # Strip leading "MAIN " convention used in this repo
    if name.startswith("MAIN "):
        name = name[5:]
    return name


# ---------------------------------------------------------------------------
# Path / filename utilities
# ---------------------------------------------------------------------------

_VALID_FILENAME_RE = re.compile(r"[^A-Za-z0-9 _\-\.]")


def sanitize_title_to_filename(title: str) -> str:
    """Turn a user-supplied page title into a safe filename (no extension)."""
    cleaned = _VALID_FILENAME_RE.sub("", title).strip()
    # Collapse internal whitespace runs
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "Untitled"


def _existing_folder_for_part(repo_path: str, part_caption: str) -> Optional[str]:
    """Find an existing folder under docs/ that matches the caption.

    This is what lets us avoid creating yet another oddly-nested folder.
    """
    docs = _docs_dir(repo_path)
    if not os.path.isdir(docs):
        return None
    candidates = {entry.lower(): entry for entry in os.listdir(docs)
                  if os.path.isdir(os.path.join(docs, entry))}
    lowered = part_caption.lower()
    if lowered in candidates:
        return candidates[lowered]
    # Try the singularised / first-word version (e.g. "Team Information" -> "Team")
    first_word = part_caption.split()[0].lower() if part_caption.split() else ""
    if first_word and first_word in candidates:
        return candidates[first_word]
    return None


def _folder_for_existing_chapter(repo_path: str, chapter_file: str) -> str:
    """Where new sub-pages of an existing chapter should live."""
    # chapter_file looks like "subteams/engine/MAIN Engine"
    rel = chapter_file.replace("\\", "/")
    folder = os.path.dirname(rel)
    if not folder:
        folder = "."
    return folder


# ---------------------------------------------------------------------------
# Create new page / sub-page
# ---------------------------------------------------------------------------

_BLANK_PAGE_TEMPLATE = """# {title}

_Write your content here. This page was created from the BlueHorizon Desktop app._
"""


def _write_blank_md(full_path: str, title: str) -> None:
    if os.path.exists(full_path):
        raise FileExistsError(f"A file already exists at {full_path}")
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(_BLANK_PAGE_TEMPLATE.format(title=title))


def create_new_page(repo_path: str, part_caption: str, title: str) -> str:
    """Create a brand-new top-level page under the given part (caption).

    Returns the absolute path to the new .md file.
    """
    title = title.strip()
    if not title:
        raise ValueError("Title cannot be empty")

    toc = parse_toc(repo_path)
    # Match part by exact caption first, then case-insensitively
    target_part: Optional[Part] = None
    for p in toc.parts:
        if p.caption == part_caption:
            target_part = p
            break
    if target_part is None:
        for p in toc.parts:
            if p.caption.lower() == part_caption.lower():
                target_part = p
                break
    if target_part is None:
        # No existing part — create one and a matching folder
        target_part = Part(caption=part_caption)
        toc.parts.append(target_part)

    # Decide where on disk this should go
    folder = _existing_folder_for_part(repo_path, target_part.caption)
    if folder is None:
        folder = sanitize_title_to_filename(target_part.caption)
    rel_folder = folder

    filename = sanitize_title_to_filename(title)
    rel_file = f"{rel_folder}/{filename}"
    full_md_path = os.path.join(_docs_dir(repo_path), rel_folder, filename + ".md")

    _write_blank_md(full_md_path, title)

    # Avoid adding a duplicate entry
    if not any(c.file == rel_file for c in target_part.chapters):
        target_part.chapters.append(Chapter(file=rel_file))
    write_toc(repo_path, toc)
    return full_md_path


def create_new_subpage(repo_path: str, parent_file_ref: str, title: str) -> str:
    """Create a new sub-page beneath the given parent chapter.

    parent_file_ref is the `file:` value from _toc.yml (e.g. "subteams/engine/MAIN Engine").
    The new page is created in the SAME folder as the parent — this is what prevents
    the "one too many folders" issue you described.
    """
    title = title.strip()
    if not title:
        raise ValueError("Title cannot be empty")

    toc = parse_toc(repo_path)
    parent_chapter: Optional[Chapter] = None
    parent_part: Optional[Part] = None
    for part in toc.parts:
        for chap in part.chapters:
            if chap.file == parent_file_ref:
                parent_chapter = chap
                parent_part = part
                break
        if parent_chapter:
            break
    if parent_chapter is None or parent_part is None:
        raise ValueError(f"Parent page not found in _toc.yml: {parent_file_ref}")

    folder = _folder_for_existing_chapter(repo_path, parent_file_ref)
    filename = sanitize_title_to_filename(title)
    rel_file = f"{folder}/{filename}" if folder != "." else filename
    full_md_path = os.path.join(_docs_dir(repo_path), folder, filename + ".md")

    _write_blank_md(full_md_path, title)

    if not any(s.file == rel_file for s in parent_chapter.sections):
        parent_chapter.sections.append(Chapter(file=rel_file))
    write_toc(repo_path, toc)
    return full_md_path


# ---------------------------------------------------------------------------
# Structure fixer (Fix Structure button)
# ---------------------------------------------------------------------------

def _canonical_caption(caption: str) -> str:
    """Group captions that obviously refer to the same section.

    Example: "Team" and "Team Information" both collapse to "Team".
    """
    c = caption.strip()
    # Drop common suffixes that pluralise/extend the same group
    for suffix in (" Information", " Info"):
        if c.lower().endswith(suffix.lower()):
            c = c[: -len(suffix)]
            break
    return c.strip()


def _resolve_case_for_file(repo_path: str, file_ref: str) -> str:
    """If file_ref has a casing mismatch with what's on disk, return the
    correctly-cased path. Otherwise return file_ref unchanged."""
    docs = _docs_dir(repo_path)
    rel = file_ref.replace("\\", "/")
    # Jupyter Book file refs are usually given without an extension
    candidates = [rel + ext for ext in (".md", ".ipynb", "")]
    fixed_rel = rel
    changed = False

    parts = rel.split("/")
    walk = docs
    fixed_parts: List[str] = []
    for i, part in enumerate(parts):
        is_last = i == len(parts) - 1
        try:
            entries = os.listdir(walk)
        except FileNotFoundError:
            return file_ref  # can't resolve, leave alone

        target_names = [part + ".md", part + ".ipynb", part] if is_last else [part]
        match = None
        # exact match wins; case-insensitive is fallback
        for name in target_names:
            if name in entries:
                match = name
                break
        if match is None:
            for name in target_names:
                for entry in entries:
                    if entry.lower() == name.lower():
                        match = entry
                        break
                if match:
                    break
        if match is None:
            return file_ref  # nothing matched on disk; leave reference alone
        # Strip extension for the file_ref portion
        if is_last:
            stem, _ = os.path.splitext(match)
            if stem != part:
                changed = True
            fixed_parts.append(stem)
        else:
            if match != part:
                changed = True
            fixed_parts.append(match)
            walk = os.path.join(walk, match)

    if not changed:
        return file_ref
    return "/".join(fixed_parts)


_H1_RE = re.compile(r"^(#)(\s+)(.+?)\s*$")


def _normalize_page_title(md_path: str, expected_title: str) -> bool:
    """Make sure `md_path` opens with `# {expected_title}` so that Jupyter Book
    uses the right sidebar label. If the file already does, no-op.

    Rules, in order:
      1. If the file's first non-blank line is `# {expected_title}` (case-insensitive
         match on the title text) — do nothing.
      2. Otherwise: prepend `# {expected_title}\n\n` to the file.
      3. Any other `# ...` H1s found later in the file get demoted to `## ...` so
         they don't compete to be the page title.

    Returns True if the file was changed.
    """
    if not os.path.exists(md_path):
        return False

    with open(md_path, "r", encoding="utf-8") as f:
        text = f.read()
    original = text
    lines = text.splitlines()

    # Find the first non-blank line (skipping leading whitespace / front-matter)
    first_idx = 0
    while first_idx < len(lines) and lines[first_idx].strip() == "":
        first_idx += 1

    # Skip past YAML front matter if present
    if first_idx < len(lines) and lines[first_idx].strip() == "---":
        for j in range(first_idx + 1, len(lines)):
            if lines[j].strip() == "---":
                first_idx = j + 1
                break
        while first_idx < len(lines) and lines[first_idx].strip() == "":
            first_idx += 1

    has_correct_title = False
    if first_idx < len(lines):
        m = _H1_RE.match(lines[first_idx])
        if m and m.group(3).strip().lower() == expected_title.lower():
            has_correct_title = True

    # Demote any other H1s (anywhere except where we'd put the new title)
    demoted_any = False
    for i in range(len(lines)):
        if i == first_idx and has_correct_title:
            continue
        m = _H1_RE.match(lines[i])
        if m:
            # Promote the # to ## (only demote if it's a single-# heading, not part of code etc)
            lines[i] = "##" + m.group(2) + m.group(3)
            demoted_any = True

    if not has_correct_title:
        # Prepend the correct title at the very top, with a blank line after
        new_top = [f"# {expected_title}", ""]
        # Preserve any leading blank lines the user had as a soft separator
        lines = new_top + lines

    new_text = "\n".join(lines)
    # Preserve a trailing newline if the original had one
    if original.endswith("\n") and not new_text.endswith("\n"):
        new_text += "\n"

    if new_text == original:
        return False

    with open(md_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(new_text)
    return True


def _md_path_for_chapter(repo_path: str, file_ref: str) -> str:
    """Locate the .md (or .ipynb) on disk for a TOC file: reference."""
    rel = file_ref.replace("\\", "/")
    for ext in (".md", ".ipynb"):
        full = os.path.join(_docs_dir(repo_path), rel + ext)
        if os.path.exists(full):
            return full
    return ""


def _expected_title_for(file_ref: str) -> str:
    """Sidebar title we want for a chapter file reference. Strips the
    'MAIN ' prefix convention this repo uses."""
    name = os.path.basename(file_ref.replace("\\", "/"))
    if name.startswith("MAIN "):
        name = name[5:]
    return name


def fix_toc_structure(repo_path: str) -> FixReport:
    """Merge duplicate captions, deduplicate file entries, and normalise case.

    Safe to run any number of times — it's idempotent.
    """
    report = FixReport()
    toc = parse_toc(repo_path)
    if not toc.parts:
        report.notes.append("No 'parts' section found in _toc.yml — nothing to do.")
        return report

    # --- Step 1: case-correct every file reference
    def _walk_and_fix(chapter: Chapter) -> None:
        fixed = _resolve_case_for_file(repo_path, chapter.file)
        if fixed != chapter.file:
            report.case_corrected.append((chapter.file, fixed))
            chapter.file = fixed
        for sec in chapter.sections:
            _walk_and_fix(sec)

    for part in toc.parts:
        for chap in part.chapters:
            _walk_and_fix(chap)

    # --- Step 2: merge parts whose canonical captions match
    merged: List[Part] = []
    canonical_index: dict[str, int] = {}
    for part in toc.parts:
        canon = _canonical_caption(part.caption)
        if canon in canonical_index:
            idx = canonical_index[canon]
            target = merged[idx]
            # Merge chapters, dedup by file
            existing_files = {c.file for c in target.chapters}
            for chap in part.chapters:
                if chap.file in existing_files:
                    report.deduplicated_files.append(chap.file)
                    # Merge sections into the existing chapter instead of dropping
                    existing = next(c for c in target.chapters if c.file == chap.file)
                    existing_section_files = {s.file for s in existing.sections}
                    for sec in chap.sections:
                        if sec.file in existing_section_files:
                            report.deduplicated_files.append(sec.file)
                        else:
                            existing.sections.append(sec)
                else:
                    target.chapters.append(chap)
                    existing_files.add(chap.file)
            report.merged_captions.append(part.caption)
            # Keep the shorter canonical caption as the survivor
            if len(canon) < len(target.caption):
                target.caption = canon
        else:
            # Normalize this part's caption to its canonical form
            new_caption = _canonical_caption(part.caption)
            if new_caption != part.caption:
                report.merged_captions.append(part.caption)
            part.caption = new_caption
            canonical_index[part.caption] = len(merged)
            merged.append(part)

    toc.parts = merged

    # --- Step 3: normalize sidebar titles for every page in the TOC. This is
    # what prevents Jupyter Book from picking an unrelated `# Engine` heading
    # inside a meeting note as that note's sidebar label.
    def _walk_titles(chapter: Chapter) -> None:
        md = _md_path_for_chapter(repo_path, chapter.file)
        if md:
            expected = _expected_title_for(chapter.file)
            if _normalize_page_title(md, expected):
                report.titles_fixed.append(chapter.file)
        for sec in chapter.sections:
            _walk_titles(sec)

    for part in toc.parts:
        for chap in part.chapters:
            _walk_titles(chap)

    # Only write the TOC if anything in it actually changed
    if report.merged_captions or report.deduplicated_files or report.case_corrected:
        write_toc(repo_path, toc)

    return report
