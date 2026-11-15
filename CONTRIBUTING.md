# 贡献指南

欢迎完善微信公众号写作、风格选择、事实核查、公众号排版兼容性等功能。

贡献者应遵守：作者原意优先；不凭空制造亲历、新闻或统计；不将用户未确认的大纲当作最终方案；不把标题冲突感变成标题党；不擅自复用专有 Logo 或人物。

对 SKILL/references 的改动请同步更新测试用例；对图片渲染、字号、裁切的改动需要提供前后截图和手机尺寸检查。引用 handraw-style 规则时必须保留 yang0 与上游仓库链接。

提交前运行：

~~~bash
python scripts/validate_skill.py .
python -m unittest discover -s tests -p 'test_*.py'
~~~

PR 最好说明：修改前的问题、修改后的可验证行为、示例输入和输出、版权与隐私影响。