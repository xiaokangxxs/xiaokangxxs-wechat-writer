#!/usr/bin/env python3
"""Create a fully offline article preview with exact-position embedded local images.

Standard library only; source images must exist and be local PNG/JPEG/WebP.
The original article Markdown is left unchanged.
"""
from __future__ import annotations
import argparse,base64,html,json,mimetypes
from pathlib import Path
import render_article

def local_data_uri(path:Path):
    kinds={'.png': 'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp'}
    typ=kinds.get(path.suffix.lower())
    if not typ or not path.is_file():raise ValueError(f'图片文件不存在或不支持: {path}')
    if path.stat().st_size>30*1024*1024:raise ValueError(f'图片超过30MB: {path}')
    return f'data:{typ};base64,'+base64.b64encode(path.read_bytes()).decode('ascii')

def resolve_project_path(root:Path, relative:str)->Path:
    p=(root/relative).resolve()
    if not p.is_relative_to(root.resolve()): raise ValueError('配图只能引用本 Skill 目录中的文件')
    return p

def build(article:Path, manifest:Path, root:Path, output:Path):
    data=json.loads(manifest.read_text(encoding='utf-8'))
    cover=resolve_project_path(root,data['cover'])
    body=article.read_text(encoding='utf-8')
    page=render_article.render_document(body,cover_data_uri=local_data_uri(cover))
    entries=data['inline_images']
    for entry in entries:
        anchor=html.escape(entry['after'],quote=True)
        # Anchor may occur inside <strong> content, but sentence itself should be uninterrupted.
        spot=page.find(anchor)
        if spot<0:raise ValueError('文章中找不到图片插入锚点: '+entry['after'])
        close=page.find('</p>',spot)
        if close<0:raise ValueError('图片锚点未处于段落中: '+entry['after'])
        uri=local_data_uri(resolve_project_path(root,entry['file']))
        alt=html.escape(entry['alt'],quote=True)
        fig=f'\n<figure style="margin:26px 0 35px"><img src="{uri}" alt="{alt}" loading="lazy" style="width:100%;height:auto;display:block;border-radius:9px;border:1px solid #e7e9ee"/></figure>\n'
        page=page[:close+4]+fig+page[close+4:]
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(page,encoding='utf-8')
    return output

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('article',type=Path)
    parser.add_argument('--image-map',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    a=parser.parse_args(argv)
    try:
        path=build(a.article,a.image_map,a.root,a.output)
        print('[OK]',path,path.stat().st_size,'bytes')
        return 0
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as e:
        parser.error(str(e))
if __name__=='__main__':raise SystemExit(main())
