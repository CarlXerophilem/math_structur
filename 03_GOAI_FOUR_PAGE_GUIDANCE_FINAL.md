# 四页共用信息（不单独成页）

- **项目标题**：Math Structurer — Convincing, reusable target-matching skills for AI research agents.
- **一句话研究问题**：以 EML 域/分支失效为可运行切片，科研 Agent 能否把自然语言目标结构化为类型化目标、约束、有限基空间和可验证子任务，依据反例主动改变下一次匹配，并把结论修订为带适用域、证据和 `unknown` 的函契约？
- **研究边界**：Math Structurer 是“数学滤镜 + 插件路由”，不是单一 EML 算法。已验证科学切片只含白名单 `eml(x,y)=exp(x)-log(y)` 树和有限自映射；催化由 ReactionDecomposer 先行，EML 只可启发展开合格的标量解析子式且代数结构未确认，3D 独立交给 GeometryPlugin。数值一致、KaTeX 表示和二维/三维投影都不是形式或机制证明。
- **当前成熟度**：E1、E2、E5 已由学员确认，资格闸门有条件通过；Python Demo 12 项、HTML5 面板 11 项测试均通过，真实 Chrome 桌面/移动验收通过且外网请求为 0。已复现论文报告的负实轴分支失效，但自适应策略与随机基线的首次失效中位步数同为 2，尚无新发现或策略优势；固定 Lean 工具链可用，本地义务编译通过，上游 `reconstruct_ln` 仍含 `sorry`，故仅为部分形式化。

---

# 四页正文

## Page 1

## 一、问题与证据

### 1.1 真实问题或需求

Math Structurer 的目标不是一次性回答科研问题，而是把自然语言转换为类型、逻辑、KaTeX 公式、相连空间和可被专业 oracle 逐项否证的机器任务。催化路线先由 ReactionDecomposer 做配平/守恒/中间体槽位/指标，再把可量化子式交给展开器，把坐标交给 GeometryPlugin。当前唯一完成科学校准的展开器切片是 EML：

EML 把初等函数统一写成二叉树：

\[
\operatorname{eml}(x,y)=e^x-\log y,\qquad
S\rightarrow 1\mid\operatorname{eml}(S,S).
\]

统一语法并不自动统一语义。原论文指出：EML 编译式在零点、定义域端点和复对数主分支处会出现困难；实值目标还可能依赖复数中间量（E1）。最小可复查案例是论文给出的 `ln(x)` EML 树：在正实数上与参考函数一致，而在负实轴的符号化主分支计算中得到相反的虚部；`x=0` 则未定义。我们的 Demo 在 `x=-1` 得到编译值约 `−πi`、参考值 `+πi`，误差 `2π`，并保留两个后端的轨迹（P1）。这是对已知问题的复现，不是新定理。

### 1.2 为什么尚未被结构化

Content MathML 已有 `domainofapplication`、`condition` 和 `compose`；规范甚至明确提醒，组成函数的定义域/陪域未必兼容，结果定义域可能为空（E2）。所以“首次给函数加定义域”不成立。当前可探索的窄点是把**表示**变成可反驳的循环：在看结果前登记域与分支，Agent 选择下一边界或子树，oracle 返回反例、未定义或未知，Agent 再缩小适用域。尚未系统排查所有 CAS branch-cut、SMT、refinement type 和证明助手工作，因此只称“候选结构化缺口”。

### 1.3 研究价值与合适切片

科学计算中，公式在语法上合法却在特定域或后端上改变含义，是可复现、可否证的问题。AI 的作用不是猜答案，而是搜索边界点、归纳失败区域、选择下一验证后端并保存修订历史。四小时切片只用 E1 的 `ln(x)` 树验证环境，再以作者公开的软件快照证明材料可得（E5）。后续若环境能在封存的其他 EML 函数中找到新的稳定失败族，才可能形成科学发现；若只能重现已知例子，则产物只是可靠的检查器原型。

- **页面专属字段**：EML 语法树、初始域、对数分支、失效输入、最小反例、当前假设版本。
- **证据编号**：E1、E2、E5；本地运行 P1、T1、L1、B1。
- **建议视觉**：`artifacts/visuals/page1_branch_mismatch.png`，并标注“已知问题复现”。
- **人工确认项**：不得把 `−1` 反例写成新发现；核对公式、主分支约定及“Content MathML ≠ Lean 证明”。
- **建议内容预算**：700–800 汉字，1 幅分支对照图。

---

## Page 2

## 二、环境接口

### 2.1 固定规则

| 固定项 | 落地定义 |
|---|---|
| 目标过滤 | 保存 `user_target, typed_logic, KaTeX, spaces, plugin_route`；公式显示不等于真值。 |
| 插件类型 | ReactionDecomposer 处理反应；GeometryPlugin 处理坐标；EML 只接收白名单标量 AST，代数结构标 `unconfirmed`。 |
| 参考对象 | 当前只比较 E1 的编译 `ln(x)` 与复对数主值 `Log(x)`。 |
| 初始域/分支 | 输入候选池 `{-2,-1,-0.5,0,0.5,1,2}`；`principal_complex_log`。 |
| 判定 | 误差不超过 `1e-10` 为数值一致；否则 `mismatch`；零点为 `undefined`；工具不能决定时为 `unknown`。 |
| 禁止改变 | 运行后不得更换公式、参考函数、分支、候选池、容差、预算或成功标准。 |
| 安全边界 | 不使用 `eval`、`exec`、裸 `sympify` 或任意自然语言执行。 |

### 2.2 观察/行动/反馈

| 类型 | 具体接口 |
|---|---|
| **观察** | `user_target, typed_logic, spaces, plugin_route, expression_ast, declared_domain, branch_policy, counterexamples, budget_left`。 |
| **行动** | `select_basis()`；`route_plugin()`；`probe(point)`；`inspect_subtree(path)`；`revise_domain(diff)`；`emit_lean_obligation()`；`stop(reason)`。 |
| **反馈** | `status, typed_output, compiled/reference_value, absolute_error, failed_subtree, evidence_url, reason, oracle_trace`。 |

最小自适应策略先测 `x=1`；一致后，反馈使下一步改为符号相反点 `x=-1`；发现分支失配后，再测负实轴邻点和零边界。Lean 只作为证明义务出口：E2 的表示可生成 `∀x, D x → D(g x)` 等闭合命题。本地义务已编译；现有 EML 文件虽被 Lean 接受，但 `reconstruct_ln` 含 `sorry`，必须返回 `partial_formalization`，不能伪造已证明。

### 2.3 记录与预算

每一步追加保存 `step, action, feedback, next_action_reason` 到 `events.jsonl`；完整结果、版本和基线写入 `results.json`，源码与产物写入 SHA-256 receipt。自适应预算固定为 5 次查询；随机参照使用同一候选池、同一 5 次预算和 20 个固定种子；无干预参照只测三个正实内部点。有限自映射校准另做三项：恒等根正例、`g²≠f` 反例和 `g(D)⊄D` 闭合失败。

- **页面专属字段**：固定规则表、观察/行动/反馈 API、JSONL 事件、查询预算、状态词表。
- **证据编号**：E1、E2、E5；P1、T1、T2、L1、B1。
- **建议视觉**：`artifacts/visuals/page2_environment_loop.png`。
- **人工确认项**：确认固定候选池和容差没有看结果后修改；Lean 状态必须保留 `partial_formalization / accepted_with_sorry`。
- **建议内容预算**：650–750 汉字 + 2 个小表。

---

## Page 3

## 三、发现信号与参照

### 3.1 什么算发现

预先允许四类发现信号：①在封存 EML 树中出现可跨多个输入复现的域/分支失效族；②找到能定位到最小子树的反例；③稳定负结果，例如某后端始终无法判定某类表达式；④反例迫使把问题从“全域等价”修正为“仅在指定域/分支等价”。每项必须包含输入、表达树、后端版本、轨迹和修订 diff。重现 E1 已报告的负实轴问题只证明环境有效，不计新发现。

### 3.2 平凡解/随机/无干预

| 参照 | 比较方式 |
|---|---|
| **平凡参照** | 只验证 AST/schema；若无数学反例，项目不合格。 |
| **无干预参照** | 固定测试 `1,2,0.5`，不根据反馈改动作；本次预算内未发现失败。 |
| **随机参照** | 同一 7 点池、5 次预算、20 种子；记录首次 `mismatch/undefined` 步数。 |
| **非平凡 baseline** | SymPy `continuous_domain` 分析实连续域；本次参考式与编译式均返回 `(0,∞)`。 |
| **精确校准** | 有限域逐点检查闭合和 `g(g(x))=f(x)`，区分 `invalid` 与 `refuted`。 |

### 3.3 最低成功与失败标准

**技术最低成功**：反馈确实改变下一查询；在 5 步内捕获 E1 已知负实轴失配和零点未定义；所有结果带轨迹；闭合失败先于复合；测试全过。本轮达到：第 2 步首次失效，随后三个负点均失配、零点未定义，12/12 测试通过（P1、T1）。

**探索最低成功**：在预先封存的其他 EML 树上发现至少一个 E1 未直接报告、可复现且能导致契约修订的失败族；同时首次失败步数或有效反例数至少一项严格优于随机中位数。本轮未达到：自适应和随机中位数均为第 2 步。因此结论是“环境技术闸门通过、科学发现闸门未通过”。不得改指标追求胜出；下一轮应扩大封存函数集并加入固定边界策略。若仍不胜随机或只复现已知例子，应把题目降级为验证工具，而非开放发现系统。

- **页面专属字段**：发现类型、首次失效步数、反例族、随机种子、修订次数、明确负结论。
- **证据编号**：E1、E2；P1、T1。
- **建议视觉**：`artifacts/visuals/page3_baseline_result.png`，直接标注“与随机持平”。
- **人工确认项**：保留未胜随机和无新发现的原判；不得用普通 accuracy 代替过程指标。
- **建议内容预算**：700–800 汉字，1 个参照表 + 1 幅结果图。

---

## Page 4

## 四、最小验证计划

### 4.1 一次试跑怎么做

**目标**：先验证数学滤镜不会把反应、目标函数、EML 和几何混为一谈，再验证 EML 切片能从正实反馈转向负实轴反例。**输入**：催化 DSL；冻结的 EML `ln(x)` JSON、7 点池、主分支和 5 次预算。**步骤**：①ReactionDecomposer 返回配平、守恒、`I?` 与欠定目标；②确认 EML=`not_invoked`、GeometryPlugin 独立；③对白名单 EML 运行自适应/随机/SymPy 参照；④保存反馈和有限映射校准；⑤测试、Lean 和双面板验收。**输出**：KaTeX 目标、插件路由、Demo JSON/JSONL、测试收据与截图。催化路线只确认接口，不算发现。实际命令：

```powershell
python demo/run_demo.py
python -m pytest -q demo/test_demo.py
python -m pytest -q panel/test_panel.py
python panel/serve_panel.py   # 浏览器打开 http://127.0.0.1:8766/
```

实际结果为 Demo `12 passed`、面板 `11 passed`；真实 Chrome 验收覆盖双标签、反应守恒、四个文献候选、2D/3D、分支反例、Lean 状态和移动布局。默认内核运行的模型调用与外网请求均为 0。Lean 本地义务通过，上游 EML 文件为 `accepted_with_sorry`。

### 4.2 主要风险与失败路径

- **已知例冒充发现**：分离“环境校准”和“封存新表达式探索”。
- **后端分支差异**：本次 SymPy 符号后数值计算给 `−πi`，递归 `cmath` 轨迹可能受有符号零/逼近方向影响；两条轨迹都保留，不选对自己有利的一条。
- **采样冒充证明**：只写“在测试点数值一致”，形式证明必须另交 Lean/其他证明证书。
- **Agent 伪装**：当前是确定性自适应策略，不是 LLM；若反馈不改下一动作即判失败。
- **基线过弱**：下一轮必须加入固定边界扫描，不只比较随机。
- **跨域夸张**：催化、PDE 和未证明理论只保留适配器字段，不进入当前结论。
- **EML 越权**：若 EML 接收到反应机理或 3D 坐标，路由测试立即失败；其代数结构保持 `unconfirmed`。
- **形式化夸张**：`.lean` 能编译不等于定理完成；任何 `sorry` 都必须保留 `partial_formalization`，不能写成证明。
- **接口候选冒充发现**：催化候选来自已核验摘要或元数据，仍不是活性预测；`@best` 在条件、候选域和测量表未冻结时必须弃权。示意几何与普通存在义务都不进入科学结论。

### 4.3 复现与开源计划

公开 `demo/`、`panel/`、冻结合同、事件日志、结果、测试、浏览器截图、来源 URL 与 SHA-256；不打包不必要的上游仓库或论文 PDF。第三方在 Python 3.14.2、SymPy 1.14.0 下应复现第 2 步失效、随机中位第 2 步、零点未定义、12+11 项测试和本地双面板。Lean 复跑必须使用固定工具链并保留上游 `sorry` 警告。下一实验建立新的封存表达式清单和预注册 JSON，禁止在看到结果后修改。

- **页面专属字段**：目标、输入、逐步命令、输出文件、八类风险、复现版本、开源边界。
- **证据编号**：E1、E2、E5；P1、T1、T2、R1、L1、B1。
- **建议视觉**：`artifacts/visuals/page4_reproduction.png`。
- **人工确认项**：提交前用另一台机器复跑；核对 Lean 版本、`sorry` 警告、截图中文字和所有 receipt 哈希。
- **建议内容预算**：700–800 汉字，1 段命令 + 1 幅复现流程图。

# 制作工作区（不进入四页文档）

## A. 页面—证据对应关系

| 页面 | 外部证据 | 本地证据 | 作用 |
|---|---|---|---|
| Page 1 | E1、E2、E5 | P1、B1 | 问题存在、已有表示、环境可得、已知反例复现 |
| Page 2 | E1、E2、E5 | P1、T1、T2、L1、B1 | 固定规则、接口、日志、Lean 边界 |
| Page 3 | E1、E2 | P1、T1 | 发现信号、参照和负结论 |
| Page 4 | E1、E2、E5 | P1、T1、T2、R1、L1、B1 | 运行、风险、复现与开源 |

正文只使用学员已确认的 E1、E2、E5。E3、E4、E6、E7、E8 仅保留在工作区，等待学员日后核验。

## B. 完整证据台账

### E1

- **状态**：已核验（教练打开；学员确认）
- **主张**：EML 提供统一二叉树语法，但存在零点、端点、复数中间量与主分支问题。
- **标题/作者机构/日期**：*All elementary functions from a single binary operator*；Andrzej Odrzywołek，Jagiellonian University；2026-03-23，v2 2026-04-04。
- **URL/访问日期**：https://arxiv.org/html/2603.21852v2；2026-08-16。
- **原文支持点**：`S→1|eml(S,S)`；4.1 节的 `domain endpoints`、复数内部计算、负实轴 `2πi` 跳跃和手工分支修正。
- **局限**：预印本；只覆盖初等函数；不证明通用 checker 新颖。
- **快照/哈希**：`evidence_captures_v2/core/E1_eml_arxiv_html_v2.html`；`93ab638b...a6c1d`。

### E2

- **状态**：已核验（教练打开；学员确认）
- **主张**：Content MathML 已表示定义域、条件和复合，但不保证组成函数域兼容，结果域可能为空。
- **标题/作者机构/日期**：*MathML 3.0, 2nd Edition*, Chapter 4；W3C，编辑 David Carlisle、Patrick Ion、Robert Miner；2014-04-10。
- **URL/访问日期**：https://www.w3.org/TR/MathML3/chapter4.html；2026-08-16。
- **原文支持点**：`domainofapplication`、`condition`、`compose` 及 `domain ... may be empty`。
- **局限**：表示标准不是求值器或 Lean 证明；不能单独证明 checker 缺口。
- **快照/哈希**：`evidence_captures_v2/core/E2_mathml3_chapter4.html`；`6d01b66e...f9f6f`。

### E3

- **状态**：待学员核验（教练已打开）
- **主张**：OpenMath 已有语义对象和 Content Dictionaries，但明确不规定计算行为。
- **标题/作者机构/日期**：*The OpenMath Standard, Version 2.0 Revision 2*；OpenMath Society，Buswell 等；2019-07。
- **URL/访问日期**：https://openmath.org/standard/om20-2019-07-01/omstd20.html；2026-08-16。
- **原文支持点**：编码对象意义；CD 固定含义；不是查询/编程语言。
- **局限**：不执行证明或域闭合检查；未进入正文。

### E4

- **状态**：待学员核验（教练已打开）
- **主张**：SymPy 有 `continuous_domain/function_range`，但受奇点、极限和临界点算法限制。
- **标题/作者机构/日期**：*Calculus — SymPy 1.14.0 documentation*；SymPy Development Team；2025-04-27。
- **URL/访问日期**：https://docs.sympy.org/latest/modules/calculus/index.html；2026-08-16。
- **原文支持点**：函数定义、能力限制和 `NotImplementedError`。
- **局限**：能力限制不是创新证明；正文只引用本地实际运行 P1。

### E5

- **状态**：已核验（教练打开；学员确认）
- **主张**：原作者提供 EML 软件快照、代码和复现材料。
- **标题/作者机构/日期**：*VA00/SymbolicRegressionPackage: v1.0 — PNAS submission snapshot*；Andrzej Odrzywołek、Jagiellonian University/Zenodo；2026-03-23。
- **URL/访问日期**：https://doi.org/10.5281/zenodo.19183008；2026-08-16。
- **原文支持点**：Software 类型、zip、MIT License、GitHub URL；README 列出 `EML_toolkit/`。
- **局限**：可下载不等于代码已复现；本轮 Demo 为独立最小实现。
- **快照/哈希**：`E5b_eml_zenodo_record.html` `0bdf19bc...04f1`；README `b6c2df45...aa08`。

### E6

- **状态**：待学员核验（教练已打开）
- **主张**：有限自映射上的 `g(g(x))=f(x)` 提供闭合和复合的精确校准。
- **标题/作者机构/日期**：*Iterative square roots of functions*；B. V. Rajarama Bhat、Chaitanya Gopalakrishna，Indian Statistical Institute；2022/2023。
- **URL/访问日期**：https://doi.org/10.1017/etds.2022.35；2026-08-16。
- **原文支持点**：自映射及迭代平方根定义、任意集合与函数图。
- **局限**：只作校准，不支持 EML 新颖性或跨域迁移。

### E7

- **状态**：待学员核验（教练已打开）
- **主张**：SymPy 官方警告 `parse_expr` 使用 `eval`，不应接受未清洗输入。
- **标题/作者机构/日期**：*Parsing — SymPy 1.14.0 documentation*；SymPy Development Team；2025-04-27。
- **URL/访问日期**：https://docs.sympy.org/latest/modules/parsing.html；2026-08-16。
- **原文支持点**：`eval` 警告和默认名称空间行为。
- **局限**：安全工程约束，不是科学发现。

### E8

- **状态**：待学员核验（教练已打开）
- **主张**：JSON Schema 可冻结结构约束，但不证明数学语义。
- **标题/作者机构/日期**：*JSON Schema: A Media Type for Describing JSON Documents*；Austin Wright、Henry Andrews、Ben Hutton、Greg Dennis；2022-06-16。
- **URL/访问日期**：https://json-schema.org/draft/2020-12/json-schema-core；2026-08-16。
- **原文支持点**：结构描述、validation、assertion/annotation。
- **局限**：页面为 Internet-Draft；schema 通过不是数学证明。

### C1（仅支撑广义分析器界面，不进入四页科学主张）

- **状态**：已核验（教练打开；学员未确认）
- **主张**：alphaXiv 提供 Streamable HTTP MCP；原生 MCP 客户端可用 OAuth 2.1/API key，浏览器托管集成需要 bridge；返回论文内容不等于完成领域核验。
- **标题/作者机构/日期**：*MCP Server Documentation*；alphaXiv；页面未标明发布日期。
- **URL/访问日期**：https://www.alphaxiv.org/docs/mcp；2026-08-16。
- **原文支持点**：端点 `https://api.alphaxiv.org/mcp/v1`；`discover_papers` 与 `get_paper_content`；浏览器 CORS 边界。
- **局限**：语料主要围绕 arXiv/alphaXiv；不能假定覆盖全部 ACS、Elsevier 或实验催化论文；本轮未通过界面发起模型检索。

### C2（仅支撑催化候选界面）

- **状态**：已核验摘要（教练打开；学员未确认）
- **主张**：文献报告 Pd 单原子锚定于 Fe3O4 表面的 CO2 加氢制乙醇案例，支持把 Pd1/Fe3O4 放入候选集。
- **标题/作者机构/日期**：*Remarkable Carbon Dioxide Hydrogenation to Ethanol on a Palladium/Iron Oxide Single-Atom Catalyst*；Francisco J. Caparrós 等；2018。
- **URL/访问日期**：https://hdl.handle.net/2117/118190；DOI https://doi.org/10.1002/cctc.201800362；2026-08-16。
- **原文支持点**：机构仓储摘要明确提到 Fe3O4 表面锚定 Pd 单原子、CO2 加氢生成乙醇及金属—氧化物界面。
- **局限**：摘要不能支持跨研究排名；面板坐标是示意图，不是论文结构数据。

### C3（仅支撑催化候选界面）

- **状态**：元数据已核验；正文待核验（学员未确认）
- **主张**：存在题为 *CO2 Hydrogenation to Ethanol over Cu@Na-Beta* 的 2020 年论文，可作为待核验候选入口。
- **作者/机构/日期**：Liping Ding 等；*Chem*；2020。
- **URL/访问日期**：https://doi.org/10.1016/j.chempr.2020.07.001；2026-08-16。
- **原文支持点**：题名、作者、期刊、年份和 DOI 元数据。
- **局限**：出版页正文未打开；不得写温压、选择性、稳定性或最优结论。

### C4（仅支撑催化候选界面）

- **状态**：元数据已核验；正文待核验（学员未确认）
- **主张**：存在题为 *Highly Active and Selective Hydrogenation of CO2 to Ethanol by Ordered Pd–Cu Nanoparticles* 的 2017 年论文。
- **作者/机构/日期**：Shuxing Bai 等；*Journal of the American Chemical Society*；2017。
- **URL/访问日期**：https://doi.org/10.1021/jacs.7b03101；2026-08-16。
- **原文支持点**：题名、作者、期刊、年份和 DOI 元数据。
- **局限**：题名中的 “Highly Active and Selective” 是作者表述，不可改写为跨论文全局最佳；正文未核验。

### C5（仅支撑催化候选界面）

- **状态**：元数据已核验；正文待核验（学员未确认）
- **主张**：存在题为 *Highly Selective Hydrogenation of CO2 to Ethanol via Designed Bifunctional Ir1–In2O3 Single-Atom Catalyst* 的 2020 年论文。
- **作者/机构/日期**：Xue Ye 等；*Journal of the American Chemical Society*；2020。
- **URL/访问日期**：https://doi.org/10.1021/jacs.0c08607；2026-08-16。
- **原文支持点**：题名、作者、期刊、年份和 DOI 元数据。
- **局限**：正文未核验；不能比较条件、选择性定义、稳定性或碳平衡，也不能据此排名。

### C6（设计参考，不进入四页科学主张）

- **状态**：待核验
- **主张**：`alphaXiv/openresearch-cli` 可作为实验树和证据工作流的候选参考。
- **标题/作者机构/日期**：*alphaXiv/openresearch-cli*；alphaXiv；日期待核验。
- **URL/访问日期**：https://github.com/alphaXiv/openresearch-cli；2026-08-16。
- **原文支持点**：待人工打开仓库页面核对。
- **局限**：本机没有 `orx` 命令、仓库 clone 或 Rust/Cargo；不得写成已安装或已集成。

### 本地证据

| 编号 | 状态 | 内容 | 路径 |
|---|---|---|---|
| P1 | 已运行 | 自适应第 2 步失效；随机中位第 2 步；负点失配、零点未定义；SymPy 实域 baseline。 | `artifacts/demo/results.json` |
| T1 | 已运行 | Demo `12 passed in 0.61s`。 | `artifacts/demo/pytest.txt` |
| T2 | 已运行 | 双面板/API/固定 Lean 检查 `11 passed`。 | `artifacts/panel/pytest.txt` |
| R1 | 已核验 | Python/SymPy/Lean 版本、命令、源码与产物 SHA-256。 | `artifacts/demo/provenance_receipt.json`、提交包 manifest |
| L1 | 部分形式化 | `FunctionContract.lean` 编译通过；上游 `eml.lean` 被接受但 `reconstruct_ln` 使用 `sorry`。 | `artifacts/demo/lean_status.txt` |
| B1 | 已运行 | Chrome 桌面/390px 移动验收通过；双标签、2D/3D、催化候选和 EML/Lean 均通过；无控制台错误、无外网请求、无模型调用。 | `artifacts/panel/browser_acceptance.json`、4 幅截图 |
| H1 | 已核验 | Codex CLI 0.147.0 与 alphaXiv MCP 配置存在；DeepSeek cross-verify 脚本存在但当前无密钥；`openresearch-cli` 未安装。验收只检查状态，不发送模型请求。 | `/api/harness/status`、`panel/README.md` |

## C. 术语表

| 术语 | 本项目含义 |
|---|---|
| **函契约** | 表达树加声明域、陪域、分支、假设、失败状态、验证器和来源；不是新数学标准。 |
| **EML** | 本文专指 Exp-Minus-Log：`exp(x)-log(y)`。 |
| **相连空间** | 自然语言、类型逻辑、守恒/基、候选/测量、几何和证明空间；空间之间用带类型的部分映射连接，并非同一个向量空间。 |
| **ReactionDecomposer** | 催化示例的前置插件：配平、守恒、中间体槽位和指标登记；不预测机理。 |
| **GeometryPlugin** | 接收坐标/图 schema 并输出 2D/3D 投影；不经过 EML。 |
| **定义域闭合** | 复合前满足 `x∈D_g ⇒ g(x)∈D_f`；迭代时为 `g(D)⊆D`。 |
| **分支策略** | 对多值复函数选择的单值约定，如复对数主值。 |
| **失效包络** | 一组带支持例、反例和边界的适用域描述。 |
| **unknown** | 当前 oracle 无法决定；既不是 false，也不是反例。 |
| **Lean obligation** | 从契约导出的待证明命题；只有真实编译/证明证书才算完成。 |

## D. 未决问题

1. 在看结果前冻结哪些 EML 函数作为第二轮 holdout？
2. 如何定义“最小失败子树”，按节点数、深度还是语义依赖？
3. 固定边界扫描是否与自适应策略同样有效？本轮尚未比较。
4. 如何区分数学分支差异、IEEE-754 有符号零和 CAS 化简策略？
5. 哪些义务交给 SymPy，哪些导出到 Lean；Lean 复数主对数的语义如何与运行后端对齐？
6. 若未来接催化/PDE，什么领域 oracle 能返回证书而不是单一分数？

## E. 反方评审与已实施修订

1. **“这只是一个 parser。”** 修订：研究对象改为 EML 语义失效包络；parser 只是环境。
2. **“MathML 已经做过。”** 修订：明确 E2 已解决表示，候选贡献只在检查、反例与修订循环。
3. **“已知 `−1` 反例不是发现。”** 修订：将其降为环境校准；科学成功要求 holdout 新失败族。
4. **“Agent 没胜随机。”** 修订：保留第 2 步对第 2 步的平局，结论写未达到探索成功。
5. **“SymPy 已经给出域。”** 修订：把它设为非平凡 baseline；本轮只显示复分支轨迹的补充信息，不声称全面优越。
6. **“Lean 文件就是证明。”** 修订：E2 与 Lean 明确分层；本地义务虽通过，上游仍含 `sorry`，L1 标 `partial_formalization`。
7. **“催化/PDE/理论统一很宏大。”** 修订：只保留广义分析接口；催化输入先做守恒与目标完备性检查，四个候选不排名，全部不进入当前科学结论。

## F. AI 不确定性声明

- 本轮没有系统性完成 branch-cut/CAS/refinement types/SMT/Lean 相关文献综述，不能主张组合 checker 新颖。
- Demo 的负实轴现象由 E1 已报告；我们只复现并记录后端差异。
- 数值容差、7 点池和确定性策略是最小环境选择，不代表通用最佳设置。
- `cmath` 与 SymPy 在分支切线附近可能因有符号零或逼近方向不同；保存轨迹不等于已解释全部机制。
- 未确认 EML 构成何种代数结构，也未实现李代数生成元 oracle；李代数只作“基压缩”类比。
- 未运行原作者完整 EML 软件、催化模拟或 PDE 等价验证；ReactionDecomposer 的 `I?` 不代表机理，催化 2D/3D 仅为示意图。本轮只编译固定 Lean 文件，且上游 EML 重建仍含 `sorry`。
- Word 稿是四页版式草案；最终提交仍需参赛者核对赛事模板、作者信息和图中文字。
