# 安装与 Agent 兼容

## 推荐：Skills CLI

~~~bash
npx skills add xiaokangxxs/xiaokangxxs-wechat-writer
~~~

通过 npx 启动 Skills CLI，从 GitHub 安装此目录 Skill；**不意味着发布到 npm**。

## Windows / macOS / Linux 手动安装

~~~bash
git clone https://github.com/xiaokangxxs/xiaokangxxs-wechat-writer.git
~~~

将完整目录放到你的 Agent 支持的 Skill 路径（不要只复制 SKILL.md）。例如部分 Codex 配置会从 ~/.agents/skills/ 扫描。

Windows PowerShell 示例：

~~~powershell
$target = Join-Path $HOME '.agents\skills'
New-Item -ItemType Directory -Force -Path $target | Out-Null
Copy-Item -Recurse -Force .\xiaokangxxs-wechat-writer $target
~~~

实际自动发现规则以所用宿主和其当前版本为准；不支持目录 Skill 的客户端可以直接读取 SKILL.md 并按其引用工作。

## 自检

~~~bash
python scripts/validate_skill.py .
python -m unittest discover -s tests -p "test_*.py"
~~~

校验使用 Python 标准库，无需额外网络调用或登录任何平台。

## 可选 handraw-style 完整目录

本 Skill 提供历史编号映射规则与精选常见风格，完整的 370 种风格定义应以原仓库为准。

~~~bash
git clone --depth 1 https://github.com/yang0/handraw-style.git
~~~

下载前请注意上游图库体积可能较大，且其资源按原始许可证分发。本 Skill 不会偷偷下载参考图或发布到上游社区。

## 用户品牌包

「小康新鲜事儿」的源 PNG / 3D IP 属于用户独立授权资产，若当前安装包中未附带，须由用户提供并放入 assets/brands/xiaokangxxs/。不能把缺失的素材说成已安装成功，也不得替用户重绘真实 Logo。

## 使用边界

图像提示词生成不等于生成图片；在线生图必须有实际可用的工具/额度。
HTML 离线预览不是公众号官方编辑器，正式发布前要在移动端做人工复核。