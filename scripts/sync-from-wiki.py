#!/usr/bin/env python3
"""This script synchronizes the README.md with the wiki."""
import argparse
import re
import sys
from glob import glob
from pathlib import Path
from typing import List, Dict, Optional


skipped_files = ["Home.md", "Categories.md", "Contributing.md"]

wikibase = "https://github.com/Eising/droid-tricks/wiki/Single-button-mute-with-clocked-un%E2%80%90mute-a-la-algoquencer"

DEFAULT_CATEGORY = "Uncategorized"

OUTPUT_FILE = "README.md"

TSnippet = Dict[str, str]

PREAMPLE = """# A collection of various DROID tricks

DROID tricks contains a list of various tricks tricks for the [DROID Universal CV Processor](https://shop.dermannmitdermaschine.de/pages/droid-universal-cv-processor).

Anyone can add their own tricks to this repository, and it's very simple.

Just add a page to the [Wiki](../../wiki/).

For more information about how to do this, see the wiki page about [Contributing](../../wiki/Contributing).

# DROID tricks"""


def get_categories(workdir: Optional[str] = None) -> List[str]:
    """Get categories."""
    categories = [DEFAULT_CATEGORY]
    if workdir and not workdir.endswith("/"):
        workdir = workdir + "/"

    categories_file = Path(workdir) / "Categories.md"

    if not Path(workdir).exists() or not categories_file.exists():
        print("Incorrect wiki directory.")
        sys.exit(1)

    with open(f"{workdir}Categories.md") as f:
        for line in list(f):
            if res := re.match(r"\* (\w+)$", line):
                category = res.group(1).rstrip()
                categories.append(category)

    return categories


def get_snippets(workdir: Optional[str] = None) -> List[TSnippet]:
    """Synchronize wiki."""
    if workdir and not workdir.endswith("/"):
        workdir = workdir + "/"

    snippets: List[TSnippet] = []
    for mdfile in glob(f"{workdir}*.md"):
        filename = Path(mdfile).name
        if filename in skipped_files or filename.startswith("_"):
            continue
        category = DEFAULT_CATEGORY
        title = filename.replace("-", " ").replace(".md", "")
        preview: Optional[str] = None
        with open(mdfile, mode="r", encoding="utf-8") as f:
            content_parts = [x.strip() for x in f.read().split("```")]
            if len(content_parts) > 1:
                preview = content_parts[0]
            last_line = content_parts[-1].split("\n")[-1]

        if res := re.match(r"Category: (\w+)$", last_line):
            category = res.group(1)

        snippets.append(
            {
                "wikifile": filename,
                "title": title,
                "category": category,
                "preview": preview,
            }
        )

    return snippets


def generate_markdown_link(wikipage: str, text: str) -> str:
    """Generate a markdown link."""
    if wikipage.endswith(".md"):
        wikipage = wikipage.replace(".md", "")
    wikilink = f"../../wiki/{wikipage}"
    return f"[{text}]({wikilink})"


def format_preview(preview: str, level: int = 3) -> str:
    """Format the preview of a snippet.

    This splits lines into chunks defined by their headline level, and makes
    them relative to a given headline level.
    """
    lines = preview.split("\n")
    new_preview = []
    headline_seen = False
    headline_seen_level: Optional[int] = None
    content_seen = False
    for linenum, line in enumerate(lines):
        if headline := re.match(r"^\s*(\#+) (.*)$", line):
            rel_level = len(headline.group(1))
            if content_seen is False:
                # skip the first headline
                headline_seen = True
                headline_seen_level = rel_level
                continue
            else:
                if headline_seen and rel_level == headline_seen_level:
                    # Break the loop if multiple sections exist with the same
                    # headline level.
                    break
                new_level = level + rel_level
                headline_str = "#" * new_level
                new_preview.append(f"{headline_str} {headline.group(2)}")
        elif re.match(r"^\s*$", line):
            # Skip empty lines in the beginning.
            if not content_seen:
                continue
            new_preview.append(line)
        else:
            content_seen = True
            new_preview.append(line)

    return "\n".join(new_preview)


def generate_snippets(categories: List[str], snippets: List[TSnippet]) -> str:
    """Generate snippets."""
    output = []
    for category in set(categories):
        cat_snippets = [
            snippet for snippet in snippets if snippet["category"] == category
        ]
        if not cat_snippets:
            continue
        output.append(f"* {category}")
        for snippet in cat_snippets:
            title = snippet["title"]
            wikifile = snippet["wikifile"]
            link = generate_markdown_link(wikifile, title)
            output.append(f"  * {link}")

    output.append("")

    return "\n".join(output)


def main(workdir: Optional[str] = None, output_file: str = OUTPUT_FILE) -> None:
    """Main method."""
    categories = get_categories(workdir)
    snippets = get_snippets(workdir)
    snippet_content = generate_snippets(categories, snippets)
    full_output = PREAMPLE + "\n" + snippet_content
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(full_output)


def cli() -> argparse.Namespace:
    """Parse arguments."""
    description = (
        "This script parses a list of markdown files containing snippets, and "
        "organizes an index of them in a single markdown file. It's meant to "
        "run from a github action, but can be run standalone for testing."
    )
    parser = argparse.ArgumentParser(
        usage="Generate a combined markdown from pages in the wiki.",
        description=description,
    )

    parser.add_argument(
        "directory",
        default="droid-tricks.wiki",
        help="Location of the folder with the wiki pages.",
    )

    parser.add_argument(
        "outputfile",
        default=OUTPUT_FILE,
        help="Path to the file to write the result to.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = cli()

    main(args.directory, args.outputfile)
