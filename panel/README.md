# Math Structurer

**Convincing, reusable target-matching skills for AI research agents.**

将特定的自然语言科研目标解析为类型化目标、约束、基空间和可验证子任务，调用本地 AI harness 与专业求解插件生成候选，并将结构、公式、证据、反例和不确定性投射到统一的 2D/3D HTML5 工作台。EML 域/分支反例是当前已运行的最小科学切片；催化界面是广义接口压力测试。

## 启动

```powershell
Set-Location "D:\MATHs\scripts\公众号文章\分析\前沿探索AI for Research"
python panel\serve_panel.py
```

打开 `http://127.0.0.1:8766/`。页面必须由本地服务器提供；不支持直接双击 `index.html`。

## 两个面板

统一管线：

```text
用户目标
  → AI 标准化：类型 + 逻辑 + KaTeX 公式
  → 相连空间：N → S/B → C/Y → G → P
  → 专业插件与 oracle
  → 证据 / 反例 / unknown
  → 2D/3D 投影
```

`N` 是自然语言空间，`S/B` 是化学计量核或注册基空间，`C/Y` 是候选与条件化测量空间，`G` 是几何商空间，`P` 是 Lean 命题空间。映射必须带类型和验证器；可视化不承担证明。

### 广义分析器

默认输入：

```text
CO2gas+H2gas -- CH3CH2OHgas @best
```

本地精确内核首先返回 `input_balance=invalid`，再构造：

```text
2 CO2(g) + 6 H2(g) -> C2H5OH(g) + 3 H2O(g)
ν=(-2,-6,+1,+3), Aν=0
```

`@best` 在没有冻结反应条件、候选空间和测量表时返回 `abstain`。界面列出四个真实文献候选，不作性能排名；只有 Pd1/Fe3O4 条目核对过摘要，其余三条仅核对元数据。2D/3D 图是可复现的示意界面构型，不是弛豫结构或机制证明。扩展固体不伪造 SMILES。

插件顺序固定为：

1. `ReactionDecomposer`：解析物种/相态/指令，配平，检查元素守恒，登记中间体槽位和目标指标；未知机理保持 `I?`。
2. `ObjectiveStructurer`：只把可量化的评分、约束或迭代更新写成 (J(c;\theta))；没有条件化测量表时，“非平凡性”保持未验证并弃权。
3. `alphaXiv/Codex`：可选地读取来源并返回 URL。
4. `GeometryPlugin`：独立处理 `R^(3n)/SE(3)` 的坐标和 2D/3D 投影。
5. `Lean4`：只核验明示假设下的固定命题。

EML 不处理反应配平、中间体或 3D 构型。它只可接收已经被前序插件判定为合格的标量解析子表达式；当前 Exp-Minus-Log 树仅作启发展开，代数结构尚未确认。

非注册问题由选定 Harness 分解为有限基、机器问题、oracle、Lean 义务和几何 schema。所有输出使用 `textContent` 或 Canvas/SVG 渲染。

### 迭代・反逆调试

- EML 白名单：`Log(x)`、`exp(x)`、恒等映射；
- 有限 `g²=f`：先检查 `g(D)⊆D`，再穷举复合；
- 一般 `f⁻¹` 或 `gⁿ=f`：只生成义务，不能判定时保持 `unknown`；
- `x=-1` 的 EML `Log` 校准返回误差 `2π`；
- 固定 Lean 检查包含反应守恒、本地函契约和上游 EML 文件。上游 `reconstruct_ln` 仍使用 `sorry`，整体状态为 `partial_formalization`。

李代数只作为基选择类比：用有限结构生成元把搜索压到更小参数空间。界面保留 `Lie generator basis` 选项，但本轮没有实现李代数 oracle，也不把类比写成验证结果。

## Harness

| 选项 | 当前接口 | 边界 |
|---|---|---|
| local exact kernel | Python 固定算子 | 默认；0 次模型调用 |
| local Codex CLI + alphaXiv MCP | `codex exec`，read-only、ephemeral、approval=never | 单次运行最多 1 次模型调用；模型后端沿用本机 Codex 配置，可能是远程/计费端点 |
| DeepSeek cross-verify harness | `SolveIterativeFunctions\harness\hooks\cross-verify.sh` | 仅在服务器进程具有 `DEEPSEEK_API_KEY` 时启用；选择后可能产生费用 |
| auto | Codex → DeepSeek → local | 只选择一个后端，不做模型链 |

alphaXiv 使用 Codex MCP bridge，端点为 `https://api.alphaxiv.org/mcp/v1`。浏览器不直接连接 alphaXiv；本项目不下载或保存论文 PDF，只显示可点击的 alphaXiv、机构页或 DOI URL。`openresearch-cli` 仅是设计参考，本机尚未安装，界面不会伪报可用。

## 验证

```powershell
python -m py_compile panel\serve_panel.py
node --check panel\app.js
python -m pytest -q panel\test_panel.py
```

真实 Chrome 验收：

```powershell
npm install --no-save playwright@1.61.0  # 仅验收脚本需要；面板运行不需要 Node 包
node panel\browser_smoke.cjs
```

验收覆盖双标签、反应配平、`Aν=0`、四个候选、可点击来源、Pd/Fe/O 2D 图、可拖动 3D Canvas、EML `2π` 反例、Lean 的 `accepted_with_sorry` 边界、390 px 布局、控制台错误和外网请求。面板没有导出或下载操作。
