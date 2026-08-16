# 反方评审与交付核验

**项目**：Math Structurer — Convincing, reusable target-matching skills for AI research agents.

**当前状态：四页稿与 Demo 已完成。**  
**结论：可提交为“有条件通过、最小环境已跑通、科学发现尚未通过”的诚实首版。**

## 1. 运行收据

```text
python demo/run_demo.py
adaptive first failure = 2
random median first failure = 2
statuses = equivalent, mismatch, mismatch, mismatch, undefined
Lean = partial_formalization
```

```text
python -m pytest -q demo/test_demo.py
12 passed in 0.50s

python -m pytest -q panel/test_panel.py
11 passed in 11.31s
```

- Python：3.14.2
- SymPy：1.14.0
- Lean：`leanprover/lean4:v4.29.0-rc6`；本地义务通过，上游 EML 文件 `accepted_with_sorry`
- 完整结果：`artifacts/demo/results.json`
- 测试输出：`artifacts/demo/pytest.txt`
- 源码/产物哈希：`artifacts/demo/provenance_receipt.json`

### HTML5 双面板实机验收

- 系统 Chrome 通过隔离 profile 启动，不接管或终止已有浏览器。
- 两标签切换、本地 KaTeX、`N→S→C→Y→G→P` 六个相连空间、ReactionDecomposer/EML/Geometry 类型路由、反应守恒、四个可点击候选、Pd/Fe/O 二维图、可拖动三维 Canvas、EML `x=-1` 的 `6.283185e+0` 失配及 Lean `partial_formalization` 均通过。
- 390×844 移动视口无横向溢出；控制台错误、页面错误、请求失败均为 0。
- 浏览器页面只访问 `127.0.0.1`；外部网络请求为 0；默认本地内核模型调用为 0。
- Codex CLI + alphaXiv MCP 与 DeepSeek cross-verify 均为显式可选后端，每次最多选择一个；本轮未调用。DeepSeek 因服务器进程无密钥显示 `off`；`openresearch-cli` 本机未安装。
- 收据与四幅截图：`artifacts/panel/browser_acceptance.json`、`artifacts/panel/panel_*.png`。

## 2. Word 核验

- 文件：`GOAI_四页提交稿_Math_Structurer.docx`
- Microsoft Word 16 实际打开：成功。
- `ComputeStatistics` 页数：**4**。
- 文档结构：3 个显式分页、4 幅内嵌视觉、1.1–4.3 十二个必需小节全部存在。
- DOCX ZIP 完整性：通过。
- SHA-256：`d9d8a5bdfeb9537f006a967f9dbc594de9d27a3d62ef84376e60707849f67416`
- 机器收据：`artifacts/word_validation.json`
- 交付边界：按要求只交 DOCX 与 Markdown，不生成 PDF；文献检索也不保存论文 PDF。

## 3. 反方问题与修订

| 反方质疑 | 最终处理 |
|---|---|
| 只是写了一个 parser | 把系统重构为“类型化数学滤镜 + 多空间插件路由”；已运行科学对象仍限定为 EML 编译的域/分支失效包络。 |
| MathML 已能表示定义域 | 正文承认 E2 prior art；候选贡献缩为检查、反例和修订循环。 |
| `x=-1` 已在论文里 | 明确标为环境校准，不计新发现。 |
| Agent 没胜随机 | 保留 2 vs 2 平局；科学发现门槛判未通过。 |
| SymPy 已能分析实域 | 设为非平凡 baseline；只声称补充了复分支/后端轨迹。 |
| `.lean` 文件等于证明 | 本地义务虽编译，上游 `reconstruct_ln` 仍用 `sorry`；L1 明确为部分形式化。 |
| 催化/PDE/理论判定被硬统一 | ReactionDecomposer 先处理配平、守恒、中间体槽位和指标；只有合格标量子式可进 EML，3D 独立进 GeometryPlugin。默认例只列未排名候选，不进入科学结论。 |
| 数值采样被写成证明 | 状态只写“测试点数值一致”；形式证明必须有独立证书。 |

## 4. 最终可说与不可说

### 可说

- 建成了白名单、定义域先行、保存反例与 `unknown` 的最小探索环境。
- 环境复现了 E1 已知的负实轴分支问题，并区分零点未定义。
- 反馈确实把下一动作从 `x=1` 改为 `x=-1`。
- 有限映射精确区分闭合失败与等式反例。
- 当前策略没有优于随机；这是保留的负结果。
- 双面板可交互运行；默认反应字符串会被配平，`@best` 因欠定而弃权；本轮没有发送外部请求或真实模型调用。

### 不可说

- 发现了新的 EML 定理或普适规律；
- 建成万能科学函数解析器；
- 已验证催化、PDE 或未证明理论；
- E2 是 Lean 证明；
- Lean 已完成 EML 重建证明；
- 数值通过等于恒等式证明；
- 当前 Agent 优于随机或 SymPy。

## 5. 提交前最后人工操作

1. 按赛事账号信息补充团队/作者字段；正文与分页无需再改。
2. 人工确认图中文字在目标电脑上没有字体替换。
3. 若提及 Lean，只能写“固定工具链可用、本地义务通过、上游含 `sorry` 的部分形式化”；不得删掉警告或改写为完成证明。
