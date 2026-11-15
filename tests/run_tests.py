#!/usr/bin/env python3
"""Self-contained regression suite for this skill package."""
from __future__ import annotations

import importlib.util
import json
import pathlib
import re
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_module(path: pathlib.Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


renderer = load_module(ROOT / "scripts/render_article.py", "render_article")
validator = load_module(ROOT / "scripts/validate_skill.py", "validate_skill")
brand_pack = load_module(ROOT / "scripts/brand_pack.py", "brand_pack")
handraw = load_module(ROOT / "scripts/handraw_bridge.py", "handraw_bridge")


class PackagingTests(unittest.TestCase):
    def test_required_files_and_frontmatter(self):
        self.assertEqual([], validator.validate(ROOT))

    def test_markdown_escapes_untrusted_html(self):
        rendered = renderer.inline('<script>alert("x")</script>')
        self.assertNotIn('<script>', rendered)
        self.assertIn('&lt;script&gt;', rendered)

    def test_markdown_renders_emphasis(self):
        rendered = renderer.inline('这是**重点**')
        self.assertIn('<strong', rendered)
        self.assertIn('重点', rendered)

    def test_heading_excluded_from_body(self):
        title, content = renderer.parse_markdown('# 标题\n\n第一段\n')
        self.assertEqual('标题', title)
        self.assertNotIn('>标题</h', content)
        self.assertIn('第一段', content)

    def test_demo_html_is_standalone_and_utf8(self):
        path = ROOT / 'examples/demo-article-preview.html'
        data = path.read_text(encoding='utf-8')
        self.assertIn('charset="utf-8"', data)
        self.assertIn('id="wechat-article"', data)
        self.assertIn('复制排版正文', data)
        self.assertNotIn('src="https://', data)
        self.assertNotIn('href="https://', data)

    def test_preview_has_mobile_viewport(self):
        data = (ROOT / 'examples/demo-article-preview.html').read_text(encoding='utf-8')
        self.assertIn('name="viewport"', data)
        self.assertIn('max-width:680px', data)

    def test_full_article_is_substantial(self):
        data = (ROOT / 'examples/demo-article.md').read_text(encoding='utf-8')
        self.assertGreater(len(data), 1400)
        self.assertIn('## ', data)
        self.assertGreaterEqual(data.count('**'), 4)

    def test_titles_under_25_chars(self):
        text = (ROOT / 'examples/demo-publish-pack.md').read_text(encoding='utf-8')
        table = [s for s in text.splitlines() if s.startswith('| ') and not s.startswith('| 风格')]
        titles = [line.split('|')[2].strip() for line in table if line.count('|') >= 4 and '---' not in line]
        self.assertEqual(5, len(titles))
        for title in titles:
            self.assertLessEqual(len(title), 25, title)

    def test_summary_under_120_chars(self):
        text = (ROOT / 'examples/demo-publish-pack.md').read_text(encoding='utf-8')
        m = re.search(r'## 摘要[^\n]*\n\n(.+?)\n\n', text, re.S)
        self.assertIsNotNone(m)
        self.assertLessEqual(len(m.group(1).strip()), 120)

    def test_reproducible_preview(self):
        article = (ROOT / 'examples/demo-article.md').read_text(encoding='utf-8')
        actual = (ROOT / 'examples/demo-article-preview.html').read_text(encoding='utf-8')
        self.assertEqual(actual, renderer.render_document(article))

    def test_demo_marked_not_user_approved(self):
        record = (ROOT / 'examples/demo-workflow-record.md').read_text(encoding='utf-8')
        self.assertIn('非真实用户确认', record)
        self.assertIn('不虚构口述原文', record)


    def test_publish_pack_contains_cover_and_inline_image_plans(self):
        text = (ROOT / 'examples/demo-publish-pack.md').read_text(encoding='utf-8')
        self.assertIn('## 封面图方案', text)
        self.assertIn('## 正文配图计划', text)
        self.assertIn('图像生成提示词', text)

    def test_visual_generation_reference_exists(self):
        text = (ROOT / 'references/visual-generation.md').read_text(encoding='utf-8')
        self.assertIn('封面图', text)
        self.assertIn('正文配图', text)

    def test_brand_manifest_and_exact_source_bytes(self):
        manifest = json.loads((ROOT / 'assets/brands/xiaokangxxs/manifest.json').read_text(encoding='utf-8'))
        self.assertEqual('小康新鲜事儿', manifest['account_name'])
        self.assertEqual({'character_3d', 'logo_lockup', 'logo_mark', 'avatar'}, set(manifest['assets']))
        import hashlib
        for key, filename in manifest['assets'].items():
            img = ROOT / 'assets/brands/xiaokangxxs' / filename
            self.assertTrue(img.is_file())
            self.assertEqual(hashlib.sha256(img.read_bytes()).hexdigest(), manifest['sha256'][key])

    def test_active_brand_is_default_and_no_mix_rule(self):
        profile = json.loads((ROOT / 'assets/brand-profile.json').read_text(encoding='utf-8'))
        self.assertEqual('xiaokangxxs', profile['active_brand'])
        self.assertTrue(profile['do_not_mix_identities'])
        rules = (ROOT / 'references/brand-visual-policy.md').read_text(encoding='utf-8')
        self.assertIn('默认封面必须展示用户的 3D 形象', rules)
        self.assertIn('不要混合不同品牌', rules)

    def test_create_custom_brand_has_no_inherited_ip(self):
        # Use temporary profile and never mutate the checked-in default.
        with tempfile.TemporaryDirectory() as td:
            temp = pathlib.Path(td)
            (temp / 'assets/brands').mkdir(parents=True)
            (temp / 'assets/brand-profile.json').write_text(json.dumps({
                'active_brand': 'xiaokangxxs',
                'registered_brands': {'xiaokangxxs': 'assets/brands/xiaokangxxs/manifest.json'},
                'do_not_mix_identities': True,
            }), encoding='utf-8')
            prev_root, prev_profile = brand_pack.ROOT, brand_pack.PROFILE
            brand_pack.ROOT, brand_pack.PROFILE = temp, temp/'assets/brand-profile.json'
            try:
                logo = ROOT / 'assets/brands/xiaokangxxs/logo-mark.png'
                out = brand_pack.register_brand('another-account', '另一个公众号', {'logo_mark': logo}, activate=True)
                self.assertEqual({'logo_mark'}, set(out['assets']))
                self.assertNotIn('character_3d', out['assets'])
                active = json.loads(brand_pack.PROFILE.read_text(encoding='utf-8'))['active_brand']
                self.assertEqual('another-account', active)
            finally:
                brand_pack.ROOT, brand_pack.PROFILE = prev_root, prev_profile

    def test_cover_previews_have_brand_and_embedded_cover(self):
        import struct
        for fname in ['brand-cover-demo-16x9.png', 'brand-cover-demo-2.35x1.png']:
            b = (ROOT/'examples'/fname).read_bytes()
            self.assertTrue(b.startswith(b'\x89PNG\r\n\x1a\n'))
            width, height = struct.unpack('>II', b[16:24])
            self.assertGreater(width, 1000)
            self.assertGreater(height, 450)
            expected_ratio = 16/9 if '16x9' in fname else 2.35
            self.assertLess(abs(width/height-expected_ratio), .04)
        page = (ROOT/'examples/demo-article-branded-preview.html').read_text(encoding='utf-8')
        self.assertIn('src="brand-cover-demo-2.35x1.png"', page)
        self.assertIn('alt="文章封面预览"', page)
        self.assertNotIn('src="https://', page)

    def test_optional_upstream_installer_is_explicit_only(self):
        txt=(ROOT/'scripts/install_handraw_upstream.py').read_text(encoding='utf-8')
        self.assertIn('mode',txt)
        self.assertIn('github.com/yang0/handraw-style.git',txt)
        self.assertIn('FileExistsError',txt)
        self.assertIn('sparse-checkout',txt)

    def test_handraw_legacy_style_resolution(self):
        self.assertEqual('FH-015', handraw.resolve_style('169')['canonical'])
        self.assertEqual('FH-013', handraw.resolve_style('#167')['canonical'])
        self.assertEqual('FA-018', handraw.resolve_style('FA-018')['canonical'])

    def test_handraw_unknown_style_never_fabricated(self):
        with self.assertRaises(ValueError):
            handraw.resolve_style('370')
        with self.assertRaises(ValueError):
            handraw.resolve_style('auto')

    def test_handraw_prompt_and_provenance(self):
        data=handraw.prompt_data(handraw.resolve_style('169'), 'AI 工具与真实交付', 'cover', 'C-01', '小康新鲜事儿')
        self.assertEqual('2.35:1',data['ratio'])
        self.assertIn('原始 Logo',data['prompt_zh'])
        self.assertIn('不是已生成',data['note'])

    def test_handraw_demo_images_are_real_and_respect_aspects(self):
        from struct import unpack
        examples=ROOT/'examples/handraw-demo'
        for filename in ['cover-169-colored-pencil-2.35x1.png','cover-167-risograph-2.35x1.png',
                         'inline-01-drafts-vs-delivery-4x3.png','inline-02-rework-loop-4x3.png',
                         'inline-03-done-checklist-4x3.png']:
            payload=(examples/filename).read_bytes()
            self.assertTrue(payload.startswith(b'\x89PNG\r\n\x1a\n'))
            w,h=unpack('>II',payload[16:24]); self.assertGreater(w,1000)
            expected=2.35 if filename.startswith('cover-') else 4/3
            self.assertLess(abs(w/h-expected),.03)

    def test_upstream_attribution_is_present(self):
        for fname in ['README.md','references/handraw-integration.md','references/handraw-upstream-license.txt']:
            self.assertIn('yang0', (ROOT/fname).read_text(encoding='utf-8'))

    def test_handraw_illustrated_preview_has_three_embedded_real_images(self):
        page=(ROOT/'examples/demo-article-handraw-illustrated-preview.html').read_text(encoding='utf-8')
        self.assertEqual(page.count('<figure style='), 3)
        self.assertIn('src="handraw-demo/cover-169-colored-pencil-2.35x1.png"', page)
        for stem in ['inline-01-drafts-vs-delivery-4x3.png', 'inline-02-rework-loop-4x3.png', 'inline-03-done-checklist-4x3.png']:
            self.assertIn('src="handraw-demo/' + stem + '"', page)
        self.assertNotIn('src="https://', page)
        self.assertIn('小康新鲜事儿',page)

    def test_handraw_illustrated_markdown_contains_all_images(self):
        txt=(ROOT/'examples/demo-article-illustrated.md').read_text(encoding='utf-8')
        self.assertEqual(txt.count('![手绘'),3)
        for entry in json.loads((ROOT/'examples/handraw-demo/image-map.json').read_text(encoding='utf-8'))['inline_images']:
            self.assertIn(entry['after'],txt)
            self.assertTrue((ROOT/entry['file']).is_file())

    def test_safe_link_protocol_handling(self):
        text = renderer.inline('[危险](javascript:alert(1)) [安全](https://example.com)')
        self.assertNotIn('href="javascript:', text)
        self.assertIn('href="https://example.com"', text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
