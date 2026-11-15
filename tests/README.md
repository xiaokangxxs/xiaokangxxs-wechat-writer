# 测试与验收 / Tests

本仓库包含两类验证，**不可混为一谈**。

## A. GitHub 公开源码检查（CI 自动执行）
运行 `python scripts/validate_public_repo.py`：
- 检查 README 中引用的图像、徽章目标、主要页面和文档链接；
- 检查主要源码入口及 Handraw 编号映射；
- Python 语法检查；
- 不依赖生成式图像模型，不访问微信公众号后台。

## B. 完整高清资源包回归（本地执行）
从作者提供的完整 v1.3.0 ZIP 中取得四份原始品牌 PNG、七张真实测试 PNG 及独立 HTML 预览文件，复制到仓库对应位置，再执行：

```bash
python scripts/validate_skill.py .
python tests/run_tests.py
```

本套回归约束原始 PNG SHA256、4:3 和 2.35:1 图片比例、离线 HTML 的数据嵌入以及 26 项综合测试。

**重要说明**：GitHub 中 `assets/readme/*.svg` 是用于 README 的可公开展示的原创 SVG 示意图；它们不是原始 AI 出图，也不替代品牌真实 3D PNG。未经用户授权不要将品牌素材进行二次开源。

测试示例文章只用于工作流演示，不表示作者亲身经历，也未验证微信公众平台后台的实际发布。
