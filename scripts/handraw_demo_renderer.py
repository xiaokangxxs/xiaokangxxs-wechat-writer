from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import numpy as np, cv2, math, random
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'examples/handraw-demo';OUT.mkdir(parents=True,exist_ok=True)
CHAR=ROOT/'assets/brands/xiaokangxxs/character-3d.png'
LOGO=ROOT/'assets/brands/xiaokangxxs/logo-lockup.png'
MARK=ROOT/'assets/brands/xiaokangxxs/logo-mark.png'
F_SANS='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
F_SERIF='/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
F_REG='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
BLUE=(39,88,211);INK=(22,43,69);GOLD=(236,172,78);PAPER=(252,250,246)
rnd=random.Random(169)

def font(sz,bold=False,serif=False):return ImageFont.truetype(F_SERIF if serif else (F_SANS if bold else F_REG),sz)

def paper(w,h,style='pencil'):
  y,x=np.mgrid[:h,:w]
  rng=np.random.default_rng(169 if style=='pencil' else 167)
  noise=rng.normal(0,1.8,(h,w,1))
  if style=='pencil':
    base=np.empty((h,w,3),float); base[:,:,:]=PAPER
    base[:,:,2]+=2.2*np.sin((x+y)/240)
    base[:,:,0]-=4*np.exp(-((x-w*.86)**2+(y-h*.54)**2)/(w*h*.12))
  else:
    base=np.empty((h,w,3),float);base[:,:,:]=(248,246,238)
    base[:,:,2]+=2.5*np.sin(x/150)
  return Image.fromarray(np.clip(base+noise,0,255).astype(np.uint8),'RGB').convert('RGBA')

def pencil_line(d, points, color=INK,width=5,seed=20):
  r=random.Random(seed)
  shifted=[(int(x+r.uniform(-3,3)),int(y+r.uniform(-3,3))) for x,y in points]
  d.line(shifted, fill=tuple(color)+(150,),width=width+2,joint='curve')
  d.line(points,fill=tuple(color)+(245,),width=width,joint='curve')

def poly_circle(im, cx,cy, rx,ry,fill,stroke,width=6,seed=169):
  r=random.Random(seed);pts=[]
  for i in range(130):
    a=2*math.pi*i/130
    wobble=1+r.uniform(-.014,.014)+.016*math.sin(i/12)
    pts.append((int(cx+rx*wobble*math.cos(a)),int(cy+ry*wobble*math.sin(a))))
  l=Image.new('RGBA',im.size,(0,0,0,0));d=ImageDraw.Draw(l)
  d.polygon(pts,fill=fill)
  d.line(pts+[pts[0]], fill=stroke, width=width, joint='curve')
  im.alpha_composite(l)

def make_char():
  im=Image.open(CHAR).convert('RGB')
  a=np.array(im)
  nonwhite=np.max(255-a,axis=2)>24
  num, labels,stats,_=cv2.connectedComponentsWithStats(nonwhite.astype('uint8'),8)
  comps=sorted(range(1,num),key=lambda z:stats[z,cv2.CC_STAT_AREA],reverse=True)
  mask=np.zeros(nonwhite.shape,dtype='uint8')
  for c in comps[:4]:
    if stats[c,cv2.CC_STAT_AREA]>2000: mask[labels==c]=255
  cnts,_=cv2.findContours(mask,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
  fill=np.zeros(mask.shape,dtype='uint8');cv2.drawContours(fill,cnts,-1,255,-1)
  # feather outer edge only
  fill=cv2.GaussianBlur(fill,(5,5),1.0)
  rgba=im.convert('RGBA'); rgba.putalpha(Image.fromarray(fill));
  bbox=rgba.getbbox()
  return rgba.crop(bbox)

CIMG=make_char()

def place_sticker(canvas, image, box, border=14,shadow=True):
  x,y,w,h=box
  obj=image.copy(); obj.thumbnail((w,h),Image.Resampling.LANCZOS)
  mx=x+(w-obj.width)//2; my=y+(h-obj.height)//2
  if shadow:
    a=obj.getchannel('A')
    under=Image.new('RGBA',canvas.size,(0,0,0,0))
    under.paste((32,52,93,75),(mx+25,my+28,mx+25+obj.width,my+28+obj.height),a.filter(ImageFilter.GaussianBlur(24)))
    canvas.alpha_composite(under)
  if border:
    a=np.array(obj.getchannel('A'))
    thick=cv2.dilate(a,np.ones((2*border+1,2*border+1),np.uint8))
    layer=Image.new('RGBA',obj.size, (255,255,255,0))
    layer.putalpha(Image.fromarray(thick))
    canvas.alpha_composite(layer,(mx,my))
  canvas.alpha_composite(obj,(mx,my))

def place_logo(canvas,x,y,desired_w=480):
  im=Image.open(LOGO).convert('RGBA')
  rgb=np.array(im.convert('RGB'))
  # offwhite background alpha -> preserve true original colored symbol and text RGB without AI repaint
  delta=np.abs(rgb-np.array([250,250,248]))
  mk=(delta.max(2)>33).astype(np.uint8)*255
  mk=cv2.dilate(mk,np.ones((2,2),np.uint8));mk=cv2.GaussianBlur(mk,(3,3),.5)
  im.putalpha(Image.fromarray(mk))
  bb=im.getbbox(); im=im.crop(bb);im.thumbnail((desired_w,200),Image.Resampling.LANCZOS)
  canvas.alpha_composite(im,(x,y))

def place_mark(canvas,x,y,sz=82,opacity=190):
  im=Image.open(MARK).convert('RGBA')
  im=im.crop(im.getbbox()); im.thumbnail((sz,sz),Image.Resampling.LANCZOS)
  a=im.getchannel('A').point(lambda x:int(x*opacity/255));im.putalpha(a)
  canvas.alpha_composite(im,(x,y))

def draw_check(d,x,y,s=72,checked=False,blue=BLUE):
  pts=[(x,y),(x+s,y+4),(x+s+2,y+s),(x,y+s-2),(x,y)]
  pencil_line(d,pts,blue,4,int(x+y))
  if checked:
    pencil_line(d,[(x+12,y+s//2),(x+32,y+s-18),(x+s+10,y+14)],(32,128,100),8,int(x+y+10))

def cover(which='pencil'):
  W,H=2350,1000
  im=paper(W,H,which);ld=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(ld)
  if which=='pencil':
    poly_circle(im,1940,555,425,415,(221,235,246,230),(153,184,222,210),5)
    for i in range(20):
      x=1650+i*37; y=140+i*3
      d.line([(x,y),(x+160,y-45)],fill=(104,153,199,36),width=3)
    d.rounded_rectangle((157,55,610,185),radius=24,fill=(255,255,255,0))
    pencil_line(d,[(159,208),(600,211)],(163,181,204),4,501)
    d.text((160,260),'AI 工具越多，',font=font(125,serif=True),fill=INK,stroke_width=0)
    d.text((160,435),'事情反而',font=font(125,serif=True),fill=INK)
    d.text((655,435),'没做完？',font=font(125,serif=True),fill=BLUE)
    pencil_line(d,[(665,591),(729,598),(813,590),(895,595),(1023,589)],GOLD,13,209)
    d.text((165,686),'生成得快，不代表交付得快。',font=font(56),fill=(80,98,118))
    d.rounded_rectangle((165,825,1095,922),radius=37,fill=(239,244,250,220),outline=(199,215,232,200),width=2)
    draw_check(d,190,852,48,True)
    d.text((268,846),'初稿',font=font(45,bold=True),fill=INK)
    d.text((402,846),'→',font=font(45),fill=BLUE)
    draw_check(d,510,852,48,True)
    d.text((586,846),'修改',font=font(45,bold=True),fill=INK)
    d.text((719,846),'→',font=font(45),fill=BLUE)
    draw_check(d,820,852,48,False)
    d.text((892,846),'交付',font=font(45,bold=True),fill=INK)
  else:
    # a genuinely different but disciplined 2-color risograph editorial scheme
    poly_circle(im,1920,520,435,435,(220,232,248,243),(62,108,197,255),7,167)
    d.polygon([(125,235),(1405,235),(1360,755),(125,755)], fill=(232,237,244,120))
    d.text((155,272),'AI 工具越多，',font=font(125,serif=True),fill=INK)
    d.text((155,465),'事情反而没做完？',font=font(111,serif=True),fill=BLUE)
    pencil_line(d,[(170,625),(1130,630)],GOLD,9,167)
    d.text((163,712),'问题不在生成速度，而在完成这件事。',font=font(44),fill=(78,94,118))
    d.text((166,875),'观点 · 工具效率 · 真实交付',font=font(36),fill=(125,146,175))
  im.alpha_composite(ld)
  place_sticker(im,CIMG,(1470,110,770,920),border=9,shadow=True)
  place_logo(im,163,76,desired_w=500)
  # small hand-drawn motifs near center/right, behind the brand character but not near the title
  fn='cover-169-colored-pencil-2.35x1.png' if which=='pencil' else 'cover-167-risograph-2.35x1.png'
  im.convert('RGB').save(OUT/fn,optimize=True)
  print('cover',fn)

def body_base():
  W,H=1600,1200
  im=paper(W,H)
  ld=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(ld)
  d.text((105,83),'小康新鲜事儿',font=font(38,bold=True),fill=(94,113,140))
  pencil_line(d,[(105,147),(1490,149)],(210,217,224),3,20)
  place_mark(ld,1425,61,72,160)
  im.alpha_composite(ld)
  return im

def footer(im):
  l=Image.new('RGBA',im.size);d=ImageDraw.Draw(l)
  d.text((108,1107),'XIAOKANG  ·  EDITORIAL NOTES',font=font(25),fill=(122,139,158))
  im.alpha_composite(l)

def body_intro():
  im=body_base();ld=Image.new('RGBA',im.size);d=ImageDraw.Draw(ld)
  d.text((110,206),'生成很多 ≠ 完成很多',font=font(82,serif=True),fill=INK)
  d.text((115,330),'满屏都是初稿，真正完成的却很少。',font=font(36),fill=(90,107,126))
  # stack of handdraw loose leaf papers, NOT photoreal objects
  for k in range(4):
    x=180+k*70;y=525-k*30
    angle=(-3+k*3)
    sheet=Image.new('RGBA',(410,470),(0,0,0,0));p=ImageDraw.Draw(sheet)
    p.rounded_rectangle((15,22,390,455),radius=19,fill=(255,255,254,246),outline=(75,105,145,195),width=5)
    for n in range(5):
      p.line([(60,104+n*58),(304-(n%2)*40,104+n*58)],fill=(139,162,184,140),width=5)
    sheet=sheet.rotate(angle,expand=True)
    ld.alpha_composite(sheet,(x,y))
  # arrow between drafts and task outcome
  pencil_line(d,[(980,730),(1100,717),(1193,721)],BLUE,7,200)
  pencil_line(d,[(1167,685),(1202,724),(1166,751)],BLUE,7,201)
  d.rounded_rectangle((1250,535,1493,800),radius=29,fill=(245,249,253,255),outline=(52,106,178,190),width=5)
  draw_check(d,1329,595,72,False)
  d.text((1286,712),'交付?',font=font(55,bold=True),fill=INK)
  im.alpha_composite(ld); footer(im)
  im.convert('RGB').save(OUT/'inline-01-drafts-vs-delivery-4x3.png',optimize=True)

def body_cycle():
  im=body_base();ld=Image.new('RGBA',im.size,(0,0,0,0));d=ImageDraw.Draw(ld)
  d.text((110,205),'反复重做，是怎样浪费时间的？',font=font(69,serif=True),fill=INK)
  items=[('01','生成方案',(145,430)),('02','不够满意',(878,430)),('03','换工具重做',(878,770)),('04','问题还在',(145,770))]
  for num,txt,(x,y) in items:
    d.rounded_rectangle((x,y,x+550,y+205),radius=35,fill=(248,249,249,245),outline=(126,159,195,195),width=5)
    d.rounded_rectangle((x+28,y+28,x+110,y+104),radius=22,fill=(226,238,252,255))
    d.text((x+42,y+35),num,font=font(40,bold=True),fill=BLUE)
    d.text((x+143,y+67),txt,font=font(52,bold=True),fill=INK)
  # arrows clockwise
  pencil_line(d,[(715,526),(820,526)],BLUE,7,300)
  pencil_line(d,[(800,508),(825,526),(800,547)],BLUE,7,301)
  pencil_line(d,[(1160,660),(1160,730)],BLUE,7,302)
  pencil_line(d,[(1142,713),(1160,741),(1176,711)],BLUE,7,303)
  pencil_line(d,[(839,867),(728,867)],BLUE,7,304)
  pencil_line(d,[(750,845),(723,867),(752,887)],BLUE,7,305)
  pencil_line(d,[(428,747),(428,665)],BLUE,7,306)
  pencil_line(d,[(410,682),(428,657),(448,682)],BLUE,7,307)
  im.alpha_composite(ld);footer(im)
  im.convert('RGB').save(OUT/'inline-02-rework-loop-4x3.png',optimize=True)

def body_checklist():
  im=body_base();ld=Image.new('RGBA',im.size,(0,0,0,0));d=ImageDraw.Draw(ld)
  d.text((110,207),'开始前，先写清楚这 3 件事',font=font(74,serif=True),fill=INK)
  d.text((112,322),'把“完成”定义清楚，再让 AI 帮你做。',font=font(38),fill=(90,107,126))
  things=['要解决什么问题？','怎么验证已经完成？','这次结果能不能复用？']
  for i,t in enumerate(things):
    y=440+i*196
    d.rounded_rectangle((144,y,1457,y+154),radius=34,fill=(252,253,252,255),outline=(131,169,205,220),width=5)
    draw_check(d,191,y+44,64,True)
    d.text((314,y+41),t,font=font(60,bold=True),fill=INK)
    d.text((1345,y+47),'0'+str(i+1),font=font(36,bold=True),fill=(143,168,198))
  im.alpha_composite(ld);footer(im)
  im.convert('RGB').save(OUT/'inline-03-done-checklist-4x3.png',optimize=True)

if __name__=='__main__':
 cover();cover('risograph');body_intro();body_cycle();body_checklist();
 print('files',[(x.name,x.stat().st_size) for x in sorted(OUT.glob('*.png'))])
