# xiaokangxxs-wechat-writer

> A collaborative WeChat Official Account writing skill focused on preserving the author's real voice instead of generating generic “viral” copy.

**Version: v1.3.2** · Agent Skills bundle · Chinese-first · offline HTML preview · no auto publishing

## What it does

1. Collects inspiration and routes topic discovery through two tracks: trending topics or non-trending insights.
2. Searches personal knowledge sources only when access is explicitly available, and keeps a ledger of facts, opinions, and pending verification items.
3. Expands the original seven-step writing flow into a 10-stage workflow from author profile to publishing review.
4. Supports voice-to-text notes, fragmented thoughts, or full drafts; editing levels L1/L2/L3 prevent over-writing the author's intent.
5. Includes the user-provided default brand: **3D mascot, original logo, Chinese wordmark, avatar, and the account name 小康新鲜事儿**. Every default cover should feature the 3D mascot and the actual brand logo, unless explicitly disabled.
6. Produces titles, summary, **cover image briefs and generation rules**, **inline illustration placement plans and prompts**, and a mobile-oriented HTML preview.
7. When image tools are available and the user asks for it, the skill can generate a cover image and 0–4 inline images; otherwise it outputs reusable briefs and prompts.
8. Supports an explicit demo mode for end-to-end testing without pretending that simulated inputs are user-approved content.

## Installation

Keep the extracted folder structure as `xiaokangxxs-wechat-writer/SKILL.md` and copy it to your host's Skills directory. For example, Codex-compatible agents may discover Skills from `$HOME/.agents/skills/` or `.agents/skills/`. Exact loading rules depend on your host.

## Brand assets and replacement

Default files live in `assets/brands/xiaokangxxs/` with `assets/brand-profile.json` as the active-profile pointer. Users can provide their own images and account name; register them with `python scripts/brand_pack.py create --brand-id my-brand --account-name "My Account" --character path/to/ip.png --logo-mark path/to/logo.png --activate`. Use `python scripts/brand_pack.py activate xiaokangxxs` to switch back. Missing assets are NOT inherited from an unrelated brand. The original brand images are excluded from the MIT license and must not be treated as public-domain assets.

See `references/brand-visual-policy.md` for exact rules.

## Local scripts

```bash
python scripts/validate_skill.py .
python scripts/render_article.py examples/demo-article.md --output examples/demo-article-preview.html
```

The scripts use only the Python standard library, do not access the network, and do not publish to WeChat.

## Key references

- `references/visual-generation.md` explains how to plan and optionally generate cover and inline images.
- `assets/cover-image-brief.template.md` and `assets/inline-image-plan.template.md` provide reusable templates.
- `examples/demo-publish-pack.md` shows a sample publish package including image prompts.

## License

MIT.

## Handraw-style integration (v1.3)

Integrates numbered visual-style routing and cover/illustration planning based on [yang0/handraw-style](https://github.com/yang0/handraw-style), with full credit to author **yang0**. Use a user-selected style number (e.g. legacy `169` = `FH-015 Colored Pencil Diary`) or dynamically recommend one using actual article context. The five verified offline sample styles work without downloading the full gallery; for any other style, provide an authorized GitHub source or the local upstream folder. Original brand character and logo pixels are preserved in composites.

The demonstrations in `examples/handraw-demo/` were locally composited from the user's supplied brand assets and pencil-effect graphic elements. They did not use the upstream reference images or a generative image model. Run `python scripts/handraw_bridge.py --style 169 --theme 'Topic'` for a reusable structured prompt.
