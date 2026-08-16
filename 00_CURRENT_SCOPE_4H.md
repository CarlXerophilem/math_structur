# 四小时范围冻结：Math Structurer

**Project name**：Math Structurer — Convincing, reusable target-matching skills for AI research agents.

**项目接口**：将特定的自然语言科研目标解析为类型化目标、约束、基空间和可验证子任务，调用本地 AI harness 与专业求解插件生成候选，并将结构、公式、证据、反例和不确定性投射到统一的 2D/3D HTML5 工作台。

**当前状态：可交付首版已完成并核验。**  
**下一步：打开四页 Word 与 HTML5 双面板作人工确认后提交；科学发现闸门仍未通过，不得把已知反例、文献候选或示意构型写成新发现。**

## 1. 把“函”说清楚

本项目不把催化、未证明理论和 PDE 强行说成普通的一元函数。这里的“函”是一个**带上下文、适用域和失败状态的部分函数契约**：

```text
FunctionContract = {
  input_symbols,
  declared_domain,
  codomain,
  expression_tree,
  branch_policy,
  assumptions,
  undefined_cases,
  verifier,
  counterexample,
  provenance
}
```

直觉上，普通公式只写“怎样算”；函契约还要写“在什么地方能算、采用哪条分支、何时不能算、怎样举出反例”。

本文的 `EML` 明确指 Exp-Minus-Log 算子

\[
\operatorname{eml}(x,y)=\exp(x)-\log(y),
\]

不是把项目命名为一个新的 EML 标准。

EML 只是标量解析子表达式的**启发展开器**；其代数结构尚未确认。Math Structurer 不把所有对象送进 EML，而是在多个相连但类型不同的空间之间路由：

```text
N 自然语言 → T 类型化逻辑/KaTeX → S/B 守恒核或注册基
             → C/Y 候选与测量 → G 几何商空间 → P 证明义务
```

以催化剂为例，`ReactionDecomposer` 先处理物种、相态、配平、元素守恒、中间体槽位和目标指标；只有可写成评分、约束或迭代更新的标量部分才可交给 EML 或其他展开器，三维坐标只能交给 `GeometryPlugin`。李代数只提供“用有限结构生成元压缩参数搜索”的基选择类比；本轮没有实现李代数 oracle。

## 2. 四小时内唯一主问题

> **在人工固定初始实域或复域及对数分支后，Agent 能否把受限 EML 表达树解析为带类型的部分函数契约，逐层传播可定义条件与值域信息，并在函数复合或迭代前发现“定义域不闭合、分支不一致或语义无法判定”的最小反例？**

最小形式条件是：若要组成 \(f\circ g\)，不仅要会读两棵语法树，还要检查

\[
x\in D_g \quad\Longrightarrow\quad g(x)\in D_f.
\]

若检查失败，系统应返回具体的 \(x\)、失败子树和状态；若现有符号工具不能判定，应返回 `unknown`，不能伪装成 `false` 或“已证明”。

## 3. Agent 的最小探索循环（资格闸门有条件通过）

1. **观察**：当前表达树、人工声明的起始域、分支策略、已知边界点和历史反例。
2. **行动**：选择下一棵子树或边界点；请求符号域分析或数值探测；提出更窄域、分支修正或 `unknown` 标记。
3. **反馈**：合法证书、具体反例，或 `unsupported/unknown`；每条反馈带工具轨迹和来源。
4. **修订**：只允许修改契约的适用域、分支说明和待判定项，不得事后修改固定测试集和成功门槛。

有限自映射的 \(g\circ g=f\) 只作为精确校准：它检查解析器是否先验证 \(g:D\to D\)，再逐点验证复合。它不是 EML 理论的新结果。

## 4. 四小时裁剪

### 必做

- 白名单 EML AST：`1`、显式变量、`eml(left,right)`；不接收任意自然语言。
- 显式 `declared_domain` 和 `branch_policy`；未知域 fail closed。
- `exp/log/eml` 的局部约束传播；复合前做闭合性检查。
- 返回 `valid / invalid / unknown`，并保存反例与工具轨迹。
- 用 SymPy `continuous_domain` 作非平凡 baseline。
- 用有限自映射 \(g^2=f\) 做一个正例和一个穷举反例。

### 只做接口压力测试，不算科学验证

- 广义分析器：LLM 把用户目标写成类型化目标、显式逻辑、KaTeX 公式、相连空间和机器子问题；只能从注册字典提出有限基与插件路由，输出仍须由领域 oracle 核验。
- 催化 Demo：保留原始 `CO2gas+H2gas -- CH3CH2OHgas @best`，但内核先报告原子不守恒，再配平为 `2 CO2 + 6 H2 → C2H5OH + 3 H2O`；`@best` 因缺少冻结条件和测量表而弃权。
- 路由边界：`ReactionDecomposer` 负责反应；`ObjectiveStructurer` 检查目标函数是否在候选集上可计算且非平凡；`GeometryPlugin` 负责 2D/3D；EML 对本次反应为 `not_invoked`。
- 文献候选：Pd1/Fe3O4 摘要已核验；Cu@Na-Beta、有序 Pd-Cu 和 Ir1-In2O3 仅核验元数据。二维/三维图为示意接口构型，不是弛豫结构或机制证明。
- PDE 与未证明理论：只能生成残差或证明义务；不得声称保持完整解空间，也不得把“没找到证明”写成反证。
- HTML5 只保留“广义分析器”和“迭代・反逆调试”两个面板；不存在第三个范畴映射面板或导出入口。

### Harness 边界

- 默认本地精确内核不调用模型；
- 本机 Codex CLI 以 `read-only + ephemeral + approval=never` 接入 alphaXiv MCP，单次运行最多调用一个模型后端；本机配置可能指向远程计费服务，不能写成“免费本地模型”；
- DeepSeek 仅在服务器进程具备密钥且用户主动选择时调用现有 cross-verify harness；当前验收没有调用；
- alphaXiv 通过后端 MCP bridge 读取并返回 URL；浏览器不直连、不保存 PDF；
- `openresearch-cli` 仅作为设计参考，本机未安装，不得伪报已接入。

### 明确删除

- “万能科学解析器”“万物统一为一个函数”；
- 把自然语言到公式的一次转换直接当成可信结论；标准公式必须带类型、逻辑、来源、oracle 和 `unknown`；
- 自动判断未证明命题真伪；
- 自动完成一般 PDE 等价化简；
- 三领域普适性已经得到验证；
- “首次给数学表达式加入定义域/条件/复合”。

## 5. 会迫使我们放弃当前切片的结果

- 原型只会检查 JSON 或语法，不能产生定义域/分支反例；
- 在同一受限表达集上不能提供超出 SymPy 直接调用的任何可审计信息；
- 接受了 \(g(D)\nsubseteq D\) 却继续计算 \(g\circ g\)；
- 把数值采样通过写成恒等式证明；
- `invalid`、`unknown` 和 `false` 无法区分；
- 每加入一个表达式都需要无约束的手工例外，契约比原表达式更难检查。

## 6. 已执行的四小时时间预算

| 用时 | 工作 |
|---:|---|
| 0:00–0:25 | 冻结 schema、测试集、分支策略和不可声称内容 |
| 0:25–1:20 | 白名单 AST 与契约验证 |
| 1:20–2:15 | 域传播、复合闭合与最小反例 |
| 2:15–2:55 | EML、SymPy baseline、有限迭代根对照 |
| 2:55–3:20 | 失败注入与反方检查 |
| 3:20–4:00 | 四页指导稿、证据工作区和压缩修订 |
