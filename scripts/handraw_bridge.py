#!/usr/bin/env python3
"""Resolve numbered handraw-style prompts without guessing unindexed styles.

This tool does not invoke a remote image model or send private article assets anywhere.
If you separately installed yang0/handraw-style, pass --upstream PATH to access
its full canonical numbering map and style catalog. A small verified offline
subset is built in for demonstrations.
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

# Verified against yang0/handraw-style, STYLES.md / styles_200_reorganized.md (2026-11-15).
OFFLINE={
 "169":{"canonical":"FH-015","name":"Colored Pencil Diary · 彩铅日记","traits":"铅笔轮廓、轻柔彩铅、纸纹、生活记录","en":"soft colored pencil strokes, subtle sketch contours, warm textured paper, diary-like editorial illustration"},
 "167":{"canonical":"FH-013","name":"Two-Color Risograph Drawing · 双色孔版手绘","traits":"双色套印、轻微错版、粗颗粒、纸张质感","en":"two-ink risograph printing, subtle offset registration, coarse grain, tactile paper"},
 "175":{"canonical":"FH-021","name":"Ink with Flat Spot Color · 墨线点色","traits":"黑墨主体 + 单一强调色、极简但醒目","en":"expressive black ink drawing with one restrained flat spot color"},
 "018":{"canonical":"FA-018","name":"Minimal Deadpan Dialogue Cartoon · 冷面简笔漫画","traits":"极简圆头人物、面无表情、简单动物、灰蓝与米色小色块","en":"deadpan editorial cartoon with minimal clean lines, calm figures and restrained spot colors"},
 "013":{"canonical":"FA-013","name":"Bold Flat Everyday Satire · 日常社论插画","traits":"粗黑轮廓、扁平色块、现代人物、互联网生活讽刺","en":"bold black outlines, flat colors, minimal contemporary editorial satire"},
}
PALETTE={"C-01":"克莱因蓝","C-03":"普鲁士蓝","C-04":"钴蓝","C-10":"鼠尾草绿"}

def upstream_paths(base: Path):
  return base/'styles_200_reorganized.md',base/'skills/handdraw-style-prompter/references/style_alias_map.json'

def load_full(base:Path):
  styles,aliases=upstream_paths(base)
  if not styles.is_file() or not aliases.is_file():
    raise FileNotFoundError('无法找到上游完整风格索引，请提供完整 handraw-style 仓库 --upstream 路径。')
  mapping=json.loads(aliases.read_text(encoding='utf-8'))['legacy_to_new']
  entries={}
  for line in styles.read_text(encoding='utf-8').splitlines():
    m=re.match(r'^\|\s*((?:FA|FB|FC|FD|FE|FF|FG|FH|FI)-\d{3})\s*·\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|',line)
    if m:
      entries[m.group(1)]={'canonical':m.group(1),'name':m.group(3).strip(),'traits':m.group(4).strip()}
  return mapping,entries

def resolve_style(style:str,upstream:Path|None=None):
  s=style.strip().lstrip('#').upper()
  if not s or s=='AUTO':
    raise ValueError('AUTO 应由 Agent 根据文章主题、读者、品牌和当前美学目标动态选风格，不可硬编码关键词映射。')
  canonical=re.fullmatch(r'F[A-I]-\d{3}',s)
  number=s.zfill(3) if s.isdigit() else None
  if number in OFFLINE:
    return {'legacy':number,**OFFLINE[number], 'source':'verified_bundled_subset'}
  for k,v in OFFLINE.items():
    if canonical and s==v['canonical']:
      return {'legacy':k,**v, 'source':'verified_bundled_subset'}
  if not upstream:
    raise ValueError(f'风格 {style} 不在随包离线精选库内；请提供 --upstream 完整上游仓库目录，不要猜测对应风格。')
  mapping,entries=load_full(upstream)
  cid=(mapping.get(number) if number else s)
  if not cid or cid not in entries:
    raise ValueError(f'未在上游权威索引找到风格编号 {style}')
  inv={v:k for k,v in mapping.items()}
  return {'legacy':inv.get(cid),**entries[cid], 'source':'full_upstream_index'}

def prompt_data(style:dict,title:str,usage:str,color:str,brand:str):
  if not title.strip(): raise ValueError('title / 文章主题不可空')
  ck=PALETTE.get(color.upper(),color)
  if usage=='cover':
    aspect='2.35:1'
    task='公众号主封面：先用一个有张力的视觉隐喻表达文章核心结论。主标题醒目，少字，高级留白，能在手机缩略图辨认。'
  else:
    aspect='4:3'
    task='公众号正文信息图：服务文章论点，标清插入锚点，保留原文关键事实与数字，不制造额外数据。'
  return {
    'style_id':style['canonical'],'legacy_id':style['legacy'],'style_name':style['name'],
    'style_traits':style['traits'],'theme_color':f'{color} {ck}', 'ratio':aspect,
    'prompt_zh':f'主题：{title}。{task} 风格：{style["canonical"]} {style["name"]}；视觉要素：{style["traits"]}；主题色：{color} {ck}，同时尊重当前品牌主蓝色。画幅 {aspect}。启用品牌：{brand}。封面使用品牌当前真实 3D 人物素材作为主体参考，后期叠加原始 Logo/字标原图以防重画变形；正文插图按需少量品牌化。不要堆霓虹、机械手、聊天窗口、咖啡杯等无关 AI 万能装饰。',
    'prompt_en':f'Topic: {title}. {"WeChat article cover" if usage=="cover" else "WeChat inline editorial illustration"}; ratio {aspect}. Visual style {style["canonical"]} {style["name"]}. Traits: {style.get("en",style["traits"])}. Palette: {ck} with the active brand blue. Preserve the real brand character reference, composite the source logo as an untouched asset. Design a clear visual metaphor with ample negative space and no generic tech clutter.',
    'note':'这是提示词与风格数据，不是已生成的 AI 图片；实际生图依赖宿主图像工具及权限。'
  }

def main(argv=None):
  p=argparse.ArgumentParser(description='Prompt bridge for yang0/handraw-style')
  p.add_argument('--style',required=True,help='169, FH-015, or any upstream indexed style ID')
  p.add_argument('--theme',required=True,help='Article core theme/title')
  p.add_argument('--usage',choices=['cover','inline'],default='cover')
  p.add_argument('--color',default='C-01')
  p.add_argument('--brand',default='小康新鲜事儿')
  p.add_argument('--upstream',type=Path,help='Local clone of https://github.com/yang0/handraw-style')
  a=p.parse_args(argv)
  try:
    data=prompt_data(resolve_style(a.style,a.upstream),a.theme,a.usage,a.color,a.brand)
    print(json.dumps(data,ensure_ascii=False,indent=2))
    return 0
  except (OSError,ValueError,KeyError,json.JSONDecodeError) as exc:
    print('[ERROR]',exc,file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
