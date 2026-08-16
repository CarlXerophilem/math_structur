# 函契约解析器证据台账（证据检查点已完成）

**项目**：Math Structurer — Convincing, reusable target-matching skills for AI research agents.

**当前状态：E1、E2、E5 已由学员确认；其余条目保持待学员核验。**  
**下一步：资格闸门、最小验证、四页指导稿和反方修订均已完成；不得把未确认条目写进四页事实正文。**

访问日期统一为 **2026-08-16**。所有网页均已由教练实际打开并保存快照；这不等于学员已经打开，也不等于来源中的主张已被独立复现。

## A. 当前候选问题与证据需求

候选问题：

> 在人工固定初始域和对数分支后，Agent 能否解析受限 EML 表达树，传播可定义条件与值域信息，并在复合或迭代前找出域不闭合、分支不一致或无法判定的最小反例？

证据覆盖：

| 核心类别 | 台账条目 |
|---|---|
| 真实问题确实存在（至少 2 条） | E1、E2、E4 |
| 已有方法与候选结构化缺口（至少 2 条） | E2、E3、E4、E7、E8 |
| 环境/代码/精确校准可得（至少 1 条） | E5、E6；E4 亦可作 baseline |

> 注意：“候选结构化缺口”不是新颖性结论。尚未系统排查 refinement types、SMT/证明助手、CAS branch-cut 分析及 design-by-contract 文献，因此不得写“此前无人研究”。

---

## E1｜EML 的统一树结构同时暴露真实的域与分支问题

- **状态**：已核验（教练已打开；学员已确认）
- **类别**：真实问题；方法起点；环境可得性辅助证据
- **主张**：`eml(x,y)=exp(x)-ln(y)` 能把标准初等函数编译为统一二叉树，但作者明确报告零点、定义域端点、复数中间量和对数主分支跳跃；因此“树能表示”不等于“在指定实域上语义安全”。
- **标题**：*All elementary functions from a single binary operator*
- **作者/机构**：Andrzej Odrzywołek；Jagiellonian University
- **日期**：初投 2026-03-23；v2 2026-04-04
- **URL**：https://arxiv.org/html/2603.21852v2
- **访问日期**：2026-08-16
- **原文支持点**：
  1. 摘要给出语法 `S → 1 | eml(S,S)`，说明可形成统一表达树。
  2. 4.1 节写明编译表达式在实轴上除少数点外工作，问题尤其出现在零点和定义域端点；三角函数内部计算必须进入复数域。
  3. 使用复对数主分支时，负实轴会出现 `2πi` 跳跃；某些公式需重定义 EML 分支或手工修正符号。
  4. 同节列出 Python 原型编译器及 NumPy/PyTorch 等执行路径。
- **局限**：arXiv 预印本，不等于同行评审定论；对象是标准初等函数，不支持催化、未证明理论或一般 PDE 已被统一；作者将边界问题描述为常见计算困难，并未证明本文候选 checker 的新颖性。
- **本地快照**：`evidence_captures_v2/core/E1_eml_arxiv_html_v2.html`
- **SHA-256**：`93ab638b7357b44c22001a7f734343bdda040cfe269257f3b66cc7034e4a6c1d`

## E2｜Content MathML 已能表示域、条件和复合，但明确不保证复合兼容

- **状态**：已核验（教练已打开；学员已确认）
- **类别**：真实问题；关键先行工作；候选结构化缺口
- **主张**：数学表达的定义域、条件和复合已有标准表示；但 MathML 明确不假设组成函数的定义域/陪域兼容，复合后的定义域甚至可能为空。可辩护的窄点是**检查与反例**，不是重新发明表示。
- **标题**：*Mathematical Markup Language (MathML) Version 3.0, 2nd Edition*, Chapter 4: Content Markup
- **作者/机构**：W3C；编辑 David Carlisle、Patrick Ion、Robert Miner
- **日期**：W3C Recommendation，2014-04-10
- **URL**：https://www.w3.org/TR/MathML3/chapter4.html
- **访问日期**：2026-08-16
- **原文支持点**：
  1. `domainofapplication` 与 `condition` 用于限制绑定变量。
  2. `compose` 表示函数复合。
  3. 规范明确说 MathML 不对组成函数的 domain/codomain 作假设，结果复合的定义域可能为空。
- **局限**：这是表示标准，不负责证明公式为真，也不负责自动生成反例；该条反驳“首次加入定义域”主张，但单凭它不能证明尚无现成 checker。
- **本地快照**：`evidence_captures_v2/core/E2_mathml3_chapter4.html`
- **SHA-256**：`6d01b66ed24ddb5a3b30e977743cc6db518599c6ea5810e88e1cac38022f9f6f`

## E3｜OpenMath 已有语义对象与 Content Dictionaries，但不是求值器

- **状态**：已核验（教练已打开；待学员确认）
- **类别**：关键先行工作；结构化边界
- **主张**：OpenMath 已提供机器可读数学对象、应用、绑定、错误、Content Dictionaries、签名字典及 JSON/XML 等编码；项目不能把“数学语义 AST”包装成首次提出。其标准又明确说 OpenMath 对象不规定计算行为，给外部 verifier 留出了空间。
- **标题**：*The OpenMath Standard, Version 2.0 Revision 2*
- **作者/机构**：S. Buswell、O. Caprotti、D. P. Carlisle、M. C. Dewar、M. Gaëtano、M. Kohlhase、J. H. Davenport、P. D. F. Ion、T. Wiesing；The OpenMath Society
- **日期**：2019-07
- **URL**：https://openmath.org/standard/om20-2019-07-01/omstd20.html
- **访问日期**：2026-08-16
- **原文支持点**：
  1. OpenMath 允许编码对象的意义，而非仅视觉表现。
  2. Content Dictionaries 独立于应用固定对象含义。
  3. 标准明确说 OpenMath 对象“不规定任何计算行为”，且 OpenMath 不是查询或编程语言。
- **局限**：OpenMath 能承载语义不代表接收程序会执行、证明或检查域闭合；本轮不实现完整 OpenMath 兼容，只把它作为表达后端和 prior art。
- **本地快照**：`evidence_captures_v2/core/E3_openmath20r2.html`
- **SHA-256**：`45d00a3f6fbc953127913fa14e4e41fb8648275fb72bdc489f45b0d66f3c3c36`

## E4｜SymPy 已有连续域和值域分析，但能力明确有限

- **状态**：已核验（教练已打开；待学员确认）
- **类别**：真实问题；非平凡 baseline；环境可得
- **主张**：SymPy 的 `continuous_domain` 和 `function_range` 已能处理一部分实函数域/值域，因此必须作为 baseline；文档同时明确其结果受奇点、不连续点、极限与临界点算法能力限制，未实现时抛出 `NotImplementedError`。
- **标题**：*Calculus — SymPy 1.14.0 documentation*
- **作者/机构**：SymPy Development Team
- **日期**：最后更新 2025-04-27
- **URL**：https://docs.sympy.org/latest/modules/calculus/index.html
- **访问日期**：2026-08-16
- **原文支持点**：
  1. `continuous_domain(f, symbol, domain)` 返回表达式连续的域。
  2. 文档写明该函数受识别奇点和不连续点能力限制，未开发相应方法时抛 `NotImplementedError`。
  3. `function_range` 同样受奇点、极限和临界点求解能力限制。
- **局限**：文档中的能力限制不等于形成了新研究问题；候选系统若只是包装两个函数，就没有贡献。SymPy 也不是完备的复分析分支证明器。
- **本地快照**：`evidence_captures_v2/core/E4_sympy_calculus.html`
- **SHA-256**：`4c28165774bc30fb97f97de765debedec10cb8ad5ac25727bab76028175eefe8`

## E5｜原作者提供可下载的 EML 编译器与复现实验软件

- **状态**：已核验（教练已打开；学员已确认）
- **类别**：环境/代码可得性
- **主张**：EML 论文的原作者提供版本化软件快照和仓库；四小时原型可复用其表达式/测试材料作参考，而不必重新制造整套函数表。
- **标题**：*VA00/SymbolicRegressionPackage: v1.0 — PNAS submission snapshot*
- **作者/机构**：Andrzej Odrzywołek；Jagiellonian University；Zenodo
- **日期**：2026-03-23
- **URL**：https://doi.org/10.5281/zenodo.19183008
- **访问日期**：2026-08-16
- **原文支持点**：
  1. Zenodo 条目标为 Software，包含约 308.9 kB 的 v1.0 zip、MIT License 和 GitHub repository URL。
  2. 仓库 README 列出 `EML_toolkit/`，含 Python EML compiler、NumPy/PyTorch/mpmath 测试、符号验证笔记本等。
  3. 论文的数据可得性段把该快照指为精确投稿版本。
- **局限**：代码可得不等于所有公式、分支和平台都正确；本轮尚未执行该软件。GPU/CUDA 搜索工具不适合当前 CPU 时间盒，也不是首版所需。
- **本地快照**：`evidence_captures_v2/core/E5b_eml_zenodo_record.html`；辅助 README：`E5a_eml_original_repo_readme.md`
- **SHA-256**：Zenodo 页面 `0bdf19bca68af737ddaa87b4c5dba53449be938955ea4043466d0ebe9eb304f1`；README `b6c2df459afdddfb0eda5face408b8a0144ce3600b7d5feb62b55eabe008aa08`

## E6｜迭代平方根给出域固定、复合精确可判的校准环境

- **状态**：已核验（教练已打开；待学员确认）
- **类别**：精确校准环境；真实数学背景
- **主张**：迭代平方根问题明确要求自映射 \(f:X\to X\) 与 \(g:X\to X\)，并逐点满足 \(g(g(x))=f(x)\)。有限集合上可穷举验证，适合检查“先验域—复合—反例—状态修订”管道。
- **标题**：*Iterative square roots of functions*
- **作者/机构**：B. V. Rajarama Bhat、Chaitanya Gopalakrishna；Indian Statistical Institute
- **日期**：2022 在线发表；*Ergodic Theory and Dynamical Systems* 43 (2023), 2201–2227
- **URL**：https://doi.org/10.1017/etds.2022.35
- **访问日期**：2026-08-16
- **原文支持点**：
  1. 摘要与定义给出：自映射 \(f\) 的迭代平方根是满足 \(g(g(\cdot))=f(\cdot)\) 的自映射 \(g\)。
  2. 论文研究任意集合上的自映射，并用函数有向图分析存在/不存在条件。
  3. 对有限 \(X\)，候选 \(g\) 的闭合和等式可逐点精确检查并返回首个反例。
- **局限**：论文的主要结果远强于首版所需，但它不证明 EML checker 新颖或可迁移到催化/PDE；有限映射只作单元校准，不能作为科学发现。
- **本地保存**：无；按最终接口约束只保留 DOI 跳转，不保存或打包论文 PDF。

## E7｜SymPy 官方警告 `parse_expr` 会调用 `eval`

- **状态**：已核验（教练已打开；待学员确认）
- **类别**：实现边界；安全约束
- **主张**：首版不能直接把任意字符串交给 `parse_expr`；应使用白名单 AST 和显式符号表，否则“广义解析器”会同时失去安全性与语义可控性。
- **标题**：*Parsing — SymPy 1.14.0 documentation*
- **作者/机构**：SymPy Development Team
- **日期**：最后更新 2025-04-27
- **URL**：https://docs.sympy.org/latest/modules/parsing.html
- **访问日期**：2026-08-16
- **原文支持点**：`parse_expr` 文档警告该函数使用 `eval`，不应处理未清洗输入；默认 global dictionary 还会导入 SymPy 名称空间。
- **局限**：这是软件安全与可复现性理由，不是科学创新证据；白名单 AST 也不会自动赋予公式正确的领域含义。
- **本地快照**：`evidence_captures_v2/core/E7_sympy_parsing.html`
- **SHA-256**：`480203a7e6d8be57751a33fb728230956c544c5584b9fa15f7691784dd5cb56e`

## E8｜JSON Schema 能检查结构，但不能证明数学语义

- **状态**：已核验（教练已打开；待学员确认）
- **类别**：实现先行工作；负边界
- **主张**：JSON Schema 适合冻结函契约字段、类型和条件子模式；它检查 JSON 实例约束，不会证明表达式等价、定义域闭合或命题为真。
- **标题**：*JSON Schema: A Media Type for Describing JSON Documents*
- **作者/机构**：Austin Wright、Henry Andrews、Ben Hutton、Greg Dennis；IETF/JSON Schema
- **日期**：2022-06-16（2020-12 规范族的 core 草案文本）
- **URL**：https://json-schema.org/draft/2020-12/json-schema-core
- **访问日期**：2026-08-16
- **原文支持点**：规范把 JSON Schema 定义为描述 JSON 数据结构的媒体类型，并说明其用途包含 validation、documentation 等；关键词可对 JSON 实例断言约束或添加注释。
- **局限**：该页面自身标明 Internet-Draft/working document；schema 通过仅表示数据结构合规，不是数学证明。若项目只交 schema，开放探索资格不通过。
- **本地快照**：`evidence_captures_v2/core/E8_jsonschema_core.html`
- **SHA-256**：`b0f0ac09cb8ba67a4ca1e8ec7e6ddd444869e47115c9bc9d3d38cf89397f53e6`

---

## B. 当前证据结论（不是资格闸门结论）

### 已能支持

1. EML 的统一表达树是一个真实、可运行的起点；域端点和复对数分支问题由原作者明确记录（E1）。
2. 定义域、条件、复合和数学语义对象已有 MathML/OpenMath 先行标准，不能把“表示层”当创新（E2、E3）。
3. 现成 CAS 有域/值域分析但并不完备，SymPy 是必须击败或增补的 baseline（E4）。
4. 原作者代码与有限自映射精确 oracle 可支撑消费级最小环境（E5、E6）。
5. 白名单 AST 和结构 schema 是必要工程约束，但不是发现（E7、E8）。

### 仍不能支持

- “通用函解析器”已适用于催化、理论判定和 PDE；
- “首次表示带定义域的函数”；
- 现有工具从未检查过复合域或 branch cuts；
- EML 编译后的所有公式在所有域、分支和数值后端都语义等价；
- 四小时内可证明一个新的广义数学理论。

## C. 学员确认记录

- 学员回复：`确认 E1、E2、E5。E2 若和 Lean 有关最好。`
- 处理：E1、E2、E5 进入四页正文；E3、E4、E6、E7、E8 保持“教练已核验、学员待核验”。
- E2 边界：E2 是 Content MathML 规范，不是 Lean 论文。项目只把 MathML 函数/域表示转换成 Lean 待证明义务；Lean 编译结果另记为本地证据 L1。
- 检查点结论：问题存在、现有方法/候选缺口、环境可得三类各有至少一条学员确认的已核验证据，允许进入资格闸门。

## D. 捕获清单

机器可读的 URL、HTTP 状态、最终跳转、文件大小与 SHA-256 位于：

`evidence_captures_v2/core_manifest.json`
