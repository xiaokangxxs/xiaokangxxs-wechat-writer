# 手绘风格封面与文章插图演示

文章：《AI 工具越用越多，为什么事情反而没做完？》

| 资产 | 风格 | 用途 | 说明 |
|---|---|---|---|
| cover-169-colored-pencil-2.35x1.png | #169/FH-015 | 公众号文章封面（主推） | 源 3D IP 与 Logo 合成，彩铅纸纹与极简标题 |
| cover-167-risograph-2.35x1.png | #167/FH-013 | 备选封面 | 双色套印调性，原始品牌人物 |
| inline-01-drafts-vs-delivery-4x3.png | #169/FH-015 | 开头“看到结果≠完成事情”后 | 生成多份草稿与单项交付的对比示意 |
| inline-02-rework-loop-4x3.png | #169/FH-015 | “反复重来”段落后 | 4 步返工循环 |
| inline-03-done-checklist-4x3.png | #169/FH-015 | “明确终点”段落后 | 三个交付验收问题 |

以上图像通过本地绘图和真实品牌素材合成，不是调用 handraw-style 自带模型或其完整编号参考图。品牌图像随包提供，仅限品牌权利人授权使用。

原风格库：yang0/handraw-style（https://github.com/yang0/handraw-style），风格选择：#169、#167。

- 使用 `image-map.json` 中的段落锚点通过 `scripts/render_illustrated.py` 回填三张图，生成离线图文预览。
