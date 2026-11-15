# 测试说明 / Tests

本仓库包含真实可读取的品牌 PNG 和五张测试 PNG（经过文件尺寸与色彩空间优化），以及三个可离线打开的文章预览 HTML。

## 一键检查

```bash
python scripts/validate_public_repo.py
python scripts/validate_skill.py .
python tests/run_tests.py
```

- `validate_public_repo.py`：README 图像/文档链接、公开文件完整性和风格编号。
- `validate_skill.py`：Skill 元数据、默认品牌文件 SHA256、依赖引用和样例完整性。
- `run_tests.py`：文章 HTML、标题长度、版权和用户确认原则、handraw 169/167 编号、PNG 画幅、品牌隔离、三张配图位置，共 26 项回归测试。
- `.github/workflows/validate.yml`：push / PR 时执行上述所有检查，不依赖额外包，不会自动发布公众号。

公开 GitHub 中的图片已经过优化，像素与原始高清附件不同；SHA256 使用 GitHub 仓库现有优化图作为测试基准。原始高清图仍可使用用户历史交付 ZIP 取得。本项目测试成功不等于真实公众号后台发布验证成功。
