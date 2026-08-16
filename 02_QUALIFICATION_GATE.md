# 开放探索资格闸门

**判定：有条件通过。**  
**日期：2026-08-16**

**项目名**：Math Structurer — Convincing, reusable target-matching skills for AI research agents.

## 1. 已确认的最低证据组合

- **问题存在：E1（用户已确认）**。EML 原论文直接记录零点、定义域端点、复数中间量和复对数主分支问题。
- **现有方法/结构化缺口：E2（用户已确认）**。Content MathML 已能表示定义域、条件和复合，但明确不保证组成函数的 domain/codomain 兼容。
- **环境可得：E5（用户已确认）**。原作者提供版本化软件快照和 EML 工具代码。

E3、E4、E6、E7、E8 保持“教练已核验、学员待核验”，不作为四页正文中的外部事实主证据；它们只用于设计 baseline、实现安全边界和制作工作区。

## 2. 题目重写

不合格版本：

> 把催化、未证明理论和 PDE 都归纳成函数，制造万能解析器。

通过闸门的最窄版本：

> **在人工固定初始域和对数分支的受限 EML 表达树集合中，Agent 能否主动选择下一子树、边界点或后端，发现直接 EML 编译与参考函数之间可复现的域/分支失效，并把假设修订为带适用域、分支策略、反例和 `unknown` 状态的函契约？**

这研究的是**失效包络如何被发现和修订**，不是“创造一种 JSON 格式”，也不是提高成熟 benchmark 的最终分数。

## 3. 开放探索资格三问

### Agent 下一轮能改变什么？

- 选择下一输入点：内部点、定义域边界、分支切线或上一反例的邻域；
- 选择下一待展开的 EML 子树；
- 选择符号分析、复数数值探测或精确有限映射 oracle；
- 把当前规则从“所有非零实数成立”修订为“正实数成立；负实轴需分支修正；零点未定义”。

它不能改变冻结的 EML 定义、参考函数、测试池、容差、预算和成功/失败标准。

### 哪种反馈会改变下一轮行动或问题定义？

```text
status = equivalent | mismatch | undefined | unknown
input
compiled_value
reference_value
failed_subtree
domain_or_branch_reason
oracle_trace
```

- `equivalent` 后转向符号相反点或最近边界；
- `mismatch` 后搜索同一连通区域的支持例和最小反例；
- `undefined` 后把点加入排除域；
- `unknown` 后保留未决状态，换 oracle，而不是判假。

### 什么结果迫使承认当前切片不成立？

- 只能检查 AST/JSON，无法输出数学反例；
- 反馈后查询顺序不变，所谓 Agent 只是固定脚本；
- 所有有效信息都由一次 SymPy `continuous_domain` 调用完整给出；
- 在同预算下不比随机/固定边界探测更早发现失效，且不能给出更好的解释；
- 把数值近似一致写成恒等证明；
- 无法区分 `mismatch`、`undefined` 与 `unknown`；
- 扩大表达式库后每个公式都需要不受约束的手工例外。

## 4. 闸门限制

本轮只允许声称：

1. 建立了一个可运行、可反例驱动修订的最小环境；
2. 复现 E1 已知的负实轴分支反例，证明环境能捕捉真实问题；
3. 比较自适应、随机、无干预和符号域 baseline；
4. 有限迭代根只校准闭合与精确复合。

本轮不允许声称：发现了新的 EML 定理、建立了通用科学解析器、验证了催化/PDE/未证明理论，或证明该方法优于现有 CAS。

## 5. E2 与 Lean 的关系

E2 是 **W3C Content MathML**，不是 Lean 文献，不能改写成“Lean 已证明”。合理连接是：

```text
Content MathML / FunctionContract（交换与表示）
        ↓ 生成待证明条件
Lean obligation（证明或拒绝闭合/等价）
```

例如复合前生成：

```lean
def ClosedUnder {α : Type} (D : α → Prop) (g : α → α) : Prop :=
  ∀ x, D x → D (g x)
```

固定工具链 `leanprover/lean4:v4.29.0-rc6` 实际存在。本地 `demo/lean/FunctionContract.lean` 已编译通过；上游 `prime_loop_verification/eml_verification/eml.lean` 可被 Lean 接受，但 `reconstruct_ln` 使用 `sorry`。因此 L1 只能标为 `partial_formalization / accepted_with_sorry`，不能写“已完成证明”；Python/SymPy 轨迹仍是本轮数值反例证据。

## 6. HTML5 确认面板的边界

`panel/` 只保留两个入口，且不扩大本轮科学主张：

1. **广义分析器**：用户目标先变成类型化目标、逻辑和 KaTeX 公式，再通过相连空间路由。催化输入由 `ReactionDecomposer` 处理配平、守恒、中间体槽位和指标；目标函数的非平凡性因无条件化测量表而保持未验证。界面给出四个真实 URL，但不排名。`GeometryPlugin` 独立处理 `nodes+edges`；EML 对反应与 3D 均为 `not_invoked`。
2. **迭代・反逆调试**：白名单 EML 和有限 `g²=f` 可由固定 oracle 检查；一般反逆问题只生成 `unknown/obligation`。EML 只是代数结构尚未确认的启发展开器，不是跨域核心。Lean 只核验固定命题，并保留上游 `sorry`。

默认本地内核运行 0 次模型。Codex CLI + alphaXiv MCP 与 DeepSeek cross-verify 是显式可选后端，每次点击最多选择并调用一个；真实 Chrome 验收没有调用任何模型或外网。alphaXiv 只返回可点击 URL，不在本地保存 PDF。`openresearch-cli` 本机未安装，仅作为工作流设计参考。
