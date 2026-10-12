"""Validate the paper catalog and regenerate its Markdown and CSV views.

Run from any directory: python scripts/build_paper_dictionary.py
Use --check to validate that committed views match the canonical JSON.
This script reads documentation only; it never opens experimental data.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "paper_dictionary.json"
REQUIRED = (
    "id", "title", "authors", "year", "publication", "category", "relevance",
    "priority", "problem", "observations", "conditioning", "prediction_or_output",
    "contribution_to_world_model", "evidence", "limitations", "repo_connection",
    "source_url", "project_url", "code_url", "data_url", "source_section",
    "review_depth", "verified_on",
)
URL_FIELDS = ("source_url", "project_url", "code_url", "data_url")


def validate(catalog: dict) -> list[dict]:
    assert catalog["schema_version"] == 1, "Unknown schema version"
    topics = {x["id"] for x in catalog["categories"]}
    assert len(topics) == len(catalog["categories"]), "Duplicate category"
    papers = catalog["papers"]
    assert papers, "Empty dictionary"
    titles: set[str] = set()
    for key, paper in papers.items():
        assert all(field in paper for field in REQUIRED), f"Missing field: {key}"
        assert key == paper["id"], f"Key/id mismatch: {key}"
        assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", key), f"Invalid id: {key}"
        assert paper["category"] in topics, f"Unknown category: {key}"
        assert paper["priority"] in {"P0", "P1", "P2"}, key
        assert paper["relevance"] in {"direct", "enabling", "adjacent"}, key
        assert paper["review_depth"] in {"full-text-sections", "abstract-and-metadata"}, key
        assert isinstance(paper["year"], int) and 1900 <= paper["year"] <= 2026, key
        assert paper["verified_on"] == catalog["review_date"], key
        for field in REQUIRED:
            if field not in URL_FIELDS and field != "year":
                assert isinstance(paper[field], str) and paper[field].strip(), f"{key}: {field}"
        for field in URL_FIELDS:
            value = paper[field]
            if value is None:
                assert field != "source_url", f"No primary source: {key}"
            else:
                parsed = urlparse(value)
                assert parsed.scheme in {"https", "http"} and parsed.netloc, f"{key}: {field}"
        title_key = re.sub(r"[^a-z0-9]", "", paper["title"].lower())
        assert title_key not in titles, f"Duplicate title: {key}"
        titles.add(title_key)
    for step in catalog["reading_path"]:
        assert step["paper_id"] in papers, f"Missing reading-path id: {step}"
    return sorted(papers.values(), key=lambda p: (
        next(i for i, t in enumerate(catalog["categories"]) if t["id"] == p["category"]),
        p["priority"], p["year"], p["id"],
    ))


def cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def markdown(catalog: dict, papers: list[dict]) -> str:
    counts = Counter(p["category"] for p in papers)
    lines = [
        "# Tactile Paper Dictionary", "",
        f"Reviewed **{catalog['review_date']}** (America/Los_Angeles). **{len(papers)} papers**.",
        "", "A curated map of tactile research relevant to a contact physics engine and an "
        "action-conditioned world model. Read the [research synthesis](tactile_world_model_review.md) "
        "and [repository audit](repository_research_audit.md) for decisions and current evidence.",
        "", "[Canonical JSON](paper_dictionary.json) · [Filterable CSV](paper_dictionary.csv)",
        "", "## Table of contents", "",
        "- [Scope and field definitions](#scope-and-field-definitions)",
        "- [Recommended reading path](#recommended-reading-path)",
    ]
    for topic in catalog["categories"]:
        lines.append(f"- [{topic['title']} ({counts[topic['id']]})](#{topic['id']})")
    lines.extend([
        "", '<a id="scope-and-field-definitions"></a>',
        "## Scope and field definitions", "",
        catalog["scope"], "",
        "**Direct** means the paper addresses a contact-state, parameter, dynamics, observation "
        "or planning interface. **Enabling** supplies sensors, data or numerical methods. "
        "**Adjacent** offers transferable ideas with a different objective.",
        "",
        "**P0**: closest prior work or immediate baseline. **P1**: useful implementation or next-stage "
        "reading. **P2**: later extension. Priorities and world-model contributions are our assessments, "
        "not reported paper results.",
        "",
        "**Year** is the earliest manuscript/publication year independently verified in this review; "
        "the publication field records venue dates separately. It does not guarantee the earliest "
        "online submission. **Full-text-sections** means the listed sections were inspected, not that "
        "every experiment was reproduced. **Abstract-and-metadata** means broader triage. "
        "Resource links identify verified author releases/pages; null means not verified, not unavailable. "
        "A linked release does not imply its files, license, calibration or runnable dependencies were tested.",
        "",
        "Evidence describes the paper's reported results. Limitations and repository connections "
        "also include our assessment of transfer to this project. Entry sources are listed next "
        "to each paper; publication status is not inferred from a conference name in search results.",
        "",
        '<a id="recommended-reading-path"></a>', "## Recommended reading path", "",
        "| Order | Paper | Read for |", "| --- | --- | --- |",
    ])
    for i, step in enumerate(catalog["reading_path"], 1):
        p = catalog["papers"][step["paper_id"]]
        lines.append(f"| {i} | [{cell(p['title'])}](#{p['id']}) | {cell(step['reason'])} |")
    for topic in catalog["categories"]:
        group = [p for p in papers if p["category"] == topic["id"]]
        lines.extend([
            "", f'<a id="{topic["id"]}"></a>', f'## {topic["title"]}', "",
            topic["description"], "",
            "| Paper | Year | Priority / relevance | Output |",
            "| --- | --- | --- | --- |",
        ])
        for p in group:
            lines.append(f"| [{cell(p['title'])}](#{p['id']}) | {p['year']} | "
                         f"{p['priority']} / {p['relevance']} | {cell(p['prediction_or_output'])} |")
        for p in group:
            links = [f"[Paper / primary source]({p['source_url']})"]
            for field, label in (("project_url", "Author project"), ("code_url", "Code"), ("data_url", "Data / release")):
                if p[field]:
                    links.append(f"[{label}]({p[field]})")
            lines.extend([
                "", f'<a id="{p["id"]}"></a>', f'### {p["title"]}', "",
                f"**{p['authors']} · {p['year']} · {p['priority']} · {p['relevance']}**  ",
                p["publication"], "", " · ".join(links), "",
                f"- **Problem:** {p['problem']}",
                f"- **Inputs:** {p['observations']} **Conditioning:** {p['conditioning']}",
                f"- **Output:** {p['prediction_or_output']}",
                f"- **World-model contribution (assessment):** {p['contribution_to_world_model']}",
                f"- **Reported evidence:** {p['evidence']}",
                f"- **Limits / transfer assessment:** {p['limitations']}",
                f"- **Repository connection:** {p['repo_connection']}",
                "",
                f"Review: `{p['review_depth']}`; {p['source_section']} Verified {p['verified_on']}.",
            ])
    lines.extend([
        "", "## Maintaining this dictionary", "",
        "Edit the canonical JSON, retain stable paper IDs, verify new claims against primary sources, "
        "and regenerate the two views:", "",
        "```powershell", "python scripts/build_paper_dictionary.py",
        "python scripts/build_paper_dictionary.py --check", "```", "",
        "The original six-entry [related-work comparison](related_work.csv) remains a historical "
        "snapshot of the brief-contact study. This dictionary is the current broader literature index.",
        "",
    ])
    return "\n".join(lines)


def csv_view(papers: list[dict]) -> str:
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=REQUIRED, lineterminator="\n")
    writer.writeheader()
    for paper in papers:
        writer.writerow({field: paper[field] for field in REQUIRED})
    return output.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    catalog = json.loads(SOURCE.read_text(encoding="utf-8"))
    papers = validate(catalog)
    views = {
        ROOT / "docs" / "paper_dictionary.md": markdown(catalog, papers),
        ROOT / "docs" / "paper_dictionary.csv": csv_view(papers),
    }
    for path, content in views.items():
        if args.check:
            assert path.exists() and path.read_text(encoding="utf-8") == content, f"Stale view: {path.name}"
        else:
            path.write_text(content, encoding="utf-8", newline="\n")
    print(f"Validated {len(papers)} papers in {len(catalog['categories'])} categories; "
          f"{'views match' if args.check else 'views generated'}.")


if __name__ == "__main__":
    main()
