#!/usr/bin/env python3
"""Static validation for Agent Skills metadata, local references and demo outputs.
No third-party dependencies.
"""
from __future__ import annotations

import argparse
import json
import hashlib
import pathlib
import re
import sys

REQUIRED = [
    "SKILL.md", "README.md", "README_EN.md", "VERSION", "LICENSE",
    "references/author-profile.md", "references/topic-discovery.md",
    "references/research-and-factcheck.md", "references/outline-and-capture.md",
    "references/editing-rules.md", "references/title-generator.md",
    "references/wechat-formatting.md", "references/publishing-checklist.md",
    "references/review-and-learning.md", "references/workflow-state.md", "references/visual-generation.md",
    "references/brand-visual-policy.md", "references/handraw-integration.md",
    "references/handraw-upstream-license.txt", "assets/handraw-config.json",
    "scripts/handraw_bridge.py", "scripts/handraw_demo_renderer.py", "scripts/render_illustrated.py", "scripts/install_handraw_upstream.py", "requirements-visual.txt",
    "examples/demo-article-illustrated.md", "examples/demo-article-handraw-illustrated-preview.html",
    "examples/handraw-demo/image-map.json",
    "examples/handraw-demo/README.md", "examples/handraw-demo/cover-169-colored-pencil-2.35x1.png",
    "examples/handraw-demo/cover-167-risograph-2.35x1.png",
    "examples/handraw-demo/inline-01-drafts-vs-delivery-4x3.png",
    "examples/handraw-demo/inline-02-rework-loop-4x3.png",
    "examples/handraw-demo/inline-03-done-checklist-4x3.png", "assets/brand-profile.json", "assets/brand-override.template.json",
    "assets/brands/xiaokangxxs/manifest.json", "assets/brands/xiaokangxxs/character-3d.png",
    "assets/brands/xiaokangxxs/logo-lockup.png", "assets/brands/xiaokangxxs/logo-mark.png",
    "assets/brands/xiaokangxxs/avatar.png", "scripts/brand_pack.py",
    "examples/brand-cover-demo-16x9.png", "examples/brand-cover-demo-2.35x1.png",
    "examples/demo-article-branded-preview.html",
    "assets/author-profile.template.md", "assets/topic-card.template.md",
    "assets/article-template.md", "assets/source-ledger.template.csv",
    "assets/publishing-checklist.template.md",
    "assets/cover-image-brief.template.md", "assets/inline-image-plan.template.md",
    "scripts/render_article.py", "scripts/validate_skill.py",
    "examples/demo-article.md", "examples/demo-article-preview.html",
    "examples/demo-publish-pack.md", "examples/demo-workflow-record.md",
    "tests/test-cases.md", "tests/acceptance-checklist.md", "tests/test-report.md",
]


def validate(root: pathlib.Path) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED:
        if not (root / relative).is_file():
            errors.append(f"Missing required file: {relative}")
    entry = root / "SKILL.md"
    if not entry.is_file():
        return errors
    body = entry.read_text(encoding="utf-8")
    front = re.match(r"\A---\n(.*?)\n---\n", body, re.S)
    if not front:
        errors.append("SKILL.md must start with a valid --- YAML frontmatter block")
        return errors
    mapping = {}
    for line in front.group(1).splitlines():
        if line.startswith(" "):
            continue
        match = re.match(r"^([a-z][a-z0-9-]*):\s*(.*)$", line)
        if match:
            mapping[match.group(1)] = match.group(2).strip().strip('"\'')
    name, description = mapping.get("name", ""), mapping.get("description", "")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        errors.append("Invalid skill name")
    if name != root.name:
        errors.append(f"SKILL name {name!r} must match folder {root.name!r}")
    if not description or len(description) > 1024:
        errors.append("Description must contain 1–1024 chars")
    if len(body.splitlines()) >= 500:
        errors.append("SKILL.md is too long (>=500 lines)")
    for ref in re.findall(r"\]\(((?:references|assets|scripts)/[^)]+)\)", body):
        if not (root / ref).is_file():
            errors.append(f"Broken linked reference: {ref}")
    for fragment in ["标准共创", "快速", "演示", "确认", "L1", "事实", "不编造", "封面图", "正文配图", "brand-profile.json", "3D", "handraw-style", "handraw-integration.md"]:
        if fragment not in body:
            errors.append(f"Core workflow rule missing: {fragment}")
    version = root / "VERSION"
    if version.exists() and not re.fullmatch(r"\d+\.\d+\.\d+", version.read_text().strip()):
        errors.append("VERSION must follow semantic x.y.z pattern")
    article = root / "examples/demo-article.md"
    if article.exists():
        data = article.read_text(encoding="utf-8")
        if not data.startswith("# "):
            errors.append("Demo article needs a first-line Markdown title")
        if len(data) < 1400:
            errors.append("Demo article appears unexpectedly short")
        if "[待核实]" in data:
            errors.append("Unresolved placeholder in demo article")
    profile_path = root / "assets/brand-profile.json"
    try:
        if profile_path.is_file():
            profile = json.loads(profile_path.read_text(encoding="utf-8"))
            brands = profile.get("registered_brands", {})
            active = profile.get("active_brand", "")
            if active not in brands:
                errors.append("Active brand missing from registered brands")
            if "xiaokangxxs" not in brands:
                errors.append("Bundled default brand must be registered")
            for brand_id, relative in brands.items():
                manifest_path = (root / relative).resolve()
                if not manifest_path.is_relative_to(root.resolve()) or not manifest_path.is_file():
                    errors.append(f"Missing or unsafe brand manifest: {brand_id}")
                    continue
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if manifest.get("brand_id") != brand_id:
                    errors.append(f"Brand id mismatch for {brand_id}")
                for key, filename in manifest.get("assets", {}).items():
                    image = (manifest_path.parent / filename).resolve()
                    if not image.is_relative_to(manifest_path.parent.resolve()) or not image.is_file():
                        errors.append(f"Missing or unsafe brand image: {brand_id}/{key}")
                        continue
                    expected = manifest.get("sha256", {}).get(key)
                    if expected and expected != hashlib.sha256(image.read_bytes()).hexdigest():
                        errors.append(f"Brand image checksum failed: {brand_id}/{key}")
    except (ValueError, KeyError, json.JSONDecodeError, OSError) as e:
        errors.append(f"Invalid brand-profile or manifest: {e}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate the xiaokangxxs-wechat-writer bundle")
    parser.add_argument("path", nargs="?", type=pathlib.Path, default=pathlib.Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    root = args.path.resolve()
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print(f"[PASS] {root.name}: {len(REQUIRED)} expected files present; metadata, references and demo article checked")
    return 0


if __name__ == "__main__":
    sys.exit(main())
