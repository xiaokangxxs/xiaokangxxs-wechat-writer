#!/usr/bin/env python3
"""Register/activate brand assets for the writer skill. Standard library only.

Does not perform image generation, uploads, background removal, or network calls.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "assets/brand-profile.json"
ASSET_FIELDS = {"character_3d": "character", "logo_lockup": "logo_lockup", "logo_mark": "logo_mark", "avatar": "avatar"}


def detect_image(path: Path) -> tuple[str, str]:
    b = path.read_bytes()
    if len(b) < 24:
        raise ValueError(f"File is too short to be an image: {path}")
    if b.startswith(b"\x89PNG\r\n\x1a\n"):
        width, height = struct.unpack(">II", b[16:24])
        kind, suffix = "PNG", ".png"
    elif b[:3] == b"\xff\xd8\xff":
        width = height = 0
        kind, suffix = "JPEG", ".jpg"
    elif b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        width = height = 0
        kind, suffix = "WEBP", ".webp"
    else:
        raise ValueError(f"Unsupported image bytes (PNG/JPEG/WebP only): {path}")
    if width and (width < 128 or height < 128):
        raise ValueError(f"Image too small: {width}x{height} ({path})")
    return kind, suffix


def register_brand(brand_id: str, name: str, files: dict[str, Path], *, activate: bool) -> dict:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", brand_id):
        raise ValueError("brand-id must be lowercase letters/digits/hyphens")
    if brand_id == "xiaokangxxs":
        raise ValueError("The bundled default brand is immutable; choose a different brand-id")
    if not name.strip():
        raise ValueError("Account name must not be empty")
    if not files:
        raise ValueError("Supply at least one image (--character, --logo-lockup, --logo-mark, --avatar)")
    target = ROOT / "assets/brands" / brand_id
    if target.exists():
        raise FileExistsError(f"Brand exists: {target}. Choose a different brand-id; do not silently overwrite.")
    planned = {}
    for field, path in files.items():
        if not path.is_file():
            raise FileNotFoundError(f"Cannot read {field}: {path}")
        _, suffix = detect_image(path)
        planned[field] = (path, field.replace("_", "-") + suffix)
    target.mkdir(parents=True)
    paths = {}
    hashes = {}
    for field, (source, filename) in planned.items():
        dest = target / filename
        shutil.copyfile(source, dest)
        paths[field] = filename
        hashes[field] = hashlib.sha256(dest.read_bytes()).hexdigest()
    manifest = {
        "schema_version": "1.0", "brand_id": brand_id,
        "account_name": name.strip(), "account_platform": "微信公众号",
        "assets": paths,
        "colors": {"primary": "#2457D6", "dark": "#18233A", "light": "#FAFAF8"},
        "usage": {"cover_character": "required_if_available", "cover_logo": "required_if_available", "body_inline_character": "optional"},
        "sha256": hashes,
        "assets_rights": "User supplied. Confirm public distribution rights before publishing."
    }
    (target / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    profile["registered_brands"][brand_id] = f"assets/brands/{brand_id}/manifest.json"
    if activate:
        profile["active_brand"] = brand_id
    PROFILE.write_text(json.dumps(profile, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return manifest


def select_brand(brand_id: str) -> str:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    if brand_id not in profile["registered_brands"]:
        raise ValueError(f"Unknown brand: {brand_id}. Registered: {', '.join(profile['registered_brands'])}")
    profile["active_brand"] = brand_id
    PROFILE.write_text(json.dumps(profile, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return brand_id


def main(argv=None):
    p = argparse.ArgumentParser(description="Show, register, or activate writer brand assets (local files only)")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("show")
    make = sub.add_parser("create")
    make.add_argument("--brand-id", required=True)
    make.add_argument("--account-name", required=True)
    for flag in ASSET_FIELDS.values():
        make.add_argument("--" + flag.replace("_", "-"), type=Path)
    make.add_argument("--activate", action="store_true")
    choose = sub.add_parser("activate")
    choose.add_argument("brand_id")
    a = p.parse_args(argv)
    try:
        if a.cmd == "show":
            print(PROFILE.read_text(encoding="utf-8"))
        elif a.cmd == "activate":
            print("[OK] Active brand:", select_brand(a.brand_id))
        else:
            files = {}
            for field, flag in ASSET_FIELDS.items():
                path = getattr(a, flag)
                if path:
                    files[field] = path
            manifest = register_brand(a.brand_id, a.account_name, files, activate=a.activate)
            print("[OK] Brand registered:", manifest["brand_id"], "/", manifest["account_name"])
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print("[ERROR]", exc, file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
