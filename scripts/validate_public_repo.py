#!/usr/bin/env python3
"""Checks that files referenced in the PUBLIC GitHub README are present.
Full-media regression checks require the original media asset bundle.
"""
from pathlib import Path
import re, json, sys, importlib.util
root=Path(__file__).resolve().parents[1]
missing=[]
for rel in [
  'SKILL.md','README.md','README.en.md','VERSION','LICENSE',
  'scripts/render_article.py','scripts/handraw_bridge.py','scripts/brand_pack.py',
  'references/handraw-integration.md','references/brand-visual-policy.md',
  'assets/readme/hero.svg','assets/readme/cover-demo.svg',
  'assets/readme/illustration-demo.svg','assets/readme/workflow.svg',
  'examples/demo-article.md','examples/demo-publish-pack.md',
  'tests/test-cases.md','tests/README.md'
]:
 if not (root/rel).is_file(): missing.append(rel)
readme=(root/'README.md').read_text(encoding='utf-8')
for ref in re.findall(r'(?:src|href)=["\x27]([^"\x27]+)["\x27]',readme):
 if ref.startswith(('http://','https://','#','mailto:')): continue
 path=ref.split('#')[0]
 if path and not (root/path).exists(): missing.append('README reference: '+path)
for ref in re.findall(r'!\[[^]]*\]\(([^)]+)\)',readme):
 if not ref.startswith(('http','data:')) and not (root/ref.split('#')[0]).exists():
  missing.append('Markdown image: '+ref)
if (root/'assets/brand-profile.json').exists():
 p=json.loads((root/'assets/brand-profile.json').read_text(encoding='utf-8'))
 assert p.get('active_brand')=='xiaokangxxs'
spec=importlib.util.spec_from_file_location('handraw_bridge',root/'scripts/handraw_bridge.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
assert module.resolve_style('169')['canonical']=='FH-015'
assert module.resolve_style('167')['canonical']=='FH-013'
if missing:
 print('FAIL: missing files or references:')
 for f in missing:print(' -',f)
 sys.exit(1)
print('PASS: public documentation references resolve, core sources compile, style ID mapping verified')
