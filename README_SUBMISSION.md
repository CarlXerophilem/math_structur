# GOAI 四小时提交包

**Math Structurer — Convincing, reusable target-matching skills for AI research agents.**

## 直接打开

- **完整提交包**：`AI4R_OPEN_team_id.zip`
- **四页 Word 稿**：`GOAI_四页提交稿_Math_Structurer.docx`
- **完整指导 Markdown**：`03_GOAI_FOUR_PAGE_GUIDANCE_FINAL.md`
- **资格闸门**：`02_QUALIFICATION_GATE.md`
- **反方与验证**：`04_VALIDATION_AND_RED_TEAM.md`

## 运行 Demo

```powershell
python demo/run_demo.py
python -m pytest -q demo/test_demo.py
python demo/generate_visuals.py
```

## 打开交互面板

```powershell
python panel/serve_panel.py
```

浏览器打开 `http://127.0.0.1:8766/`。界面只含两个标签：

1. **广义分析器**：默认输入 `CO2gas+H2gas -- CH3CH2OHgas @best`；先报告不守恒，再配平并列出四个未排名文献候选、2D/3D 示意构型和 Lean 守恒义务。
2. **迭代・反逆调试**：EML、有限 `g²=f`、一般反逆义务和固定 Lean 检查。

统一路线是：`用户目标 → 类型/逻辑/KaTeX → 相连空间与有限基 → 专业插件/oracle → 证据、反例或 unknown → 2D/3D`。催化先经过 ReactionDecomposer；EML 只接收合格标量解析子式且代数结构仍为 `unconfirmed`；几何坐标不经过 EML。

默认本地精确内核运行 0 次模型。Codex CLI + alphaXiv MCP 和 DeepSeek cross-verify 是单次显式可选后端；本轮浏览器验收没有调用。面板不提供导出或 PDF 下载。

当前验证结果：Demo `12 passed in 0.50s`、面板 `11 passed in 11.31s`；真实 Chrome 桌面/390px 移动验收通过且外网请求、模型调用均为 0；Word 16 实测为 4 页；自适应与随机首次失败中位数均为第 2 步。固定 Lean 工具链存在，本地义务编译通过；上游 `reconstruct_ln` 使用 `sorry`，状态为 `partial_formalization / accepted_with_sorry`。

## 最重要的提交口径

这是一个**数学滤镜与可复用目标匹配插件环境首版**，以定义域/分支失效作为已运行科学切片。它复现已知反例并诚实保留未胜随机的负结果；它不是万能解析器，也没有发现新定理或验证催化/PDE。

## 目录提示

- `demo/`：源码、测试、冻结合同、Lean 导出草案。
- `panel/`：无前端依赖的 HTML5 面板、本地只读 API、测试和浏览器验收脚本。
- `artifacts/demo/`：结果、事件日志、测试与哈希收据。
- `artifacts/panel/`：桌面/移动截图、浏览器验收 JSON 与测试输出。
- `artifacts/visuals/`：Word 内使用的四幅图。
- `evidence_captures_v2/`：原始页面快照和 manifest。
- `archive/`：已被取代的旧 OC20/D3 路线，不得混入当前提交。
