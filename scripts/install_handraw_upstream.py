#!/usr/bin/env python3
"""Optional, explicit install of upstream yang0/handraw-style resources.

Downloads only when user invokes it; never uploads article or brand data.
'catalog' is sparse and does not contain reference images; 'full' may be large.
Requires git on PATH and network to github.com.
"""
from __future__ import annotations
import argparse,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
URL='https://github.com/yang0/handraw-style.git'
CATALOG=[
 'SKILL.md','LICENSE','DEPENDENCIES.md',
 'styles_200_reorganized.md','STYLES.md','LAYOUTS.md','COLORS.md',
 'skills/handdraw-style-prompter/SKILL.md',
 'skills/handdraw-style-prompter/references/style_alias_map.json',
 'skills/article-cover-designer/SKILL.md',
 'skills/article-illustration-planner/SKILL.md',
]

def run(args):
  print('$ '+' '.join(map(str,args)))
  subprocess.run(args,check=True)

def install(destination:Path,mode:str):
  if mode not in ('catalog','full'):
    raise ValueError('mode must be catalog or full')
  if destination.exists():
    raise FileExistsError(f'目录已存在，不会覆盖：{destination}')
  destination.parent.mkdir(parents=True,exist_ok=True)
  if mode=='catalog':
    run(['git','clone','--depth','1','--filter=blob:none','--no-checkout',URL,str(destination)])
    run(['git','-C',str(destination),'sparse-checkout','init','--no-cone'])
    run(['git','-C',str(destination),'sparse-checkout','set','--no-cone',*CATALOG])
    run(['git','-C',str(destination),'checkout','HEAD'])
  else:
    run(['git','clone','--depth','1',URL,str(destination)])
  for rel in ['SKILL.md','LICENSE','styles_200_reorganized.md','skills/handdraw-style-prompter/references/style_alias_map.json']:
    if not (destination/rel).is_file():
      raise RuntimeError(f'安装后未找到关键风格索引: {rel}')
  return destination

def main(argv=None):
  p=argparse.ArgumentParser(description='Opt-in installation of public yang0/handraw-style repo')
  p.add_argument('--mode',choices=['catalog','full'],default='catalog')
  p.add_argument('--dest',type=Path,default=ROOT/'vendor/handraw-style')
  args=p.parse_args(argv)
  try:
    target=install(args.dest.resolve(),args.mode)
    print('[OK] Upstream:',target)
    print('Use: python scripts/handraw_bridge.py --style 169 --theme "topic" --upstream "'+str(target)+'"')
    if args.mode=='catalog':print('[INFO] catalog-only: no numbered reference images; full mode is required for those assets.')
    return 0
  except (FileExistsError,ValueError,RuntimeError,subprocess.CalledProcessError, OSError) as e:
    print('[ERROR]',e,file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
