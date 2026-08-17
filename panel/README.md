# Math Structurer HTML5 工作台

Math Structurer 将自然语言科研目标转换为类型化字段、文献与公共数据库查询、空间表示和可追溯反馈。当前面板是可检查的最小原型，不是催化性能模拟器，也不会把数据库候选包装为科学发现。

## 一行启动

在项目根目录运行：

~~~bash
python3 run.py
~~~

Windows 也可使用 **python run.py**。零模型结构检查为：

~~~bash
python3 run.py --check
~~~

入口只使用相对路径与回环地址。本地 Qwen3-8B-Jailbroken 用于受限目标识别；符号分支调试按需使用 SymPy。后端不可用时必须显示真实状态，不得静默替换。

## 两个工作区

### 广义分析器

默认输入为 **CO2gas+H2gas -- CH3CH2OHgas @best**。主分析显示：

1. 反应物与相态；
2. 产物与相态；
3. 带数值定义、单位、方法和来源的反应能量；若未取得可核验数据则显示 `—`；
4. 来自文献和公共数据库的催化剂候选、记录标识与证据层级；
5. 催化剂二维／三维空间几何及其坐标来源状态。

`@best` 只按 `50*reaction_match + 25*abstract_verified + 15*public_geometry_link + 10*comparable_energy_record` 稳定排列候选，不表示性能最优。温度、压力、候选范围、观测指标和参照方法都是可选 **possibilities**，缺失时不阻止查询。每条候选必须保留可点击来源；只有元数据时只能陈述元数据，不能推断能量、活性、选择性或机理。当前几何来自 Materials Project OPTIMADE `mp-19306` 的 Fe₃O₄ 体相坐标，只标为 `support-only`，不是 Pd 活性位。

### 迭代与反逆调试

当前特定基算子为

\[
B:\mathbb C\times\mathbb C^\times\to\mathbb C,\qquad B(u,v)=e^u-\operatorname{Log}v.
\]

它只在当前测试域和已声明的主值复对数约定下复合，不被包装为统一代数。面板另支持有限域上的函数复合核验和一般反逆义务输出；含公理或证明占位符的结果继续标为“部分形式化”。

## 可选后端

- **本地 Qwen3-8B-Jailbroken**：Ollama 检查点 `hf.co/mradermacher/Qwen3-8B-Jailbroken-GGUF:Q4_K_M`，每次至多一次受限识别；检查点名称不构成可信保证。
- **本机 Codex**：只读模式，可通过已配置的 alphaXiv 接口读取论文记录。
- **DeepSeek**：仅在用户显式选择且本地接入条件齐备时调用。
- **Lean 4**：核验明示的数学命题，不承担化学性能判断。

## 认证连接器

Materials Project 和 alphaXiv 分别从 `MP_API_KEY` 与 `ALPHAXIV_API_KEY` 环境变量读取凭据。运行 `python panel/authenticated_connector_smoke.py --full-text` 只保存 HTTP 状态、返回对象范围、原文长度和 SHA-256，不保存密钥或原文。当前实测观察到 `mp-19306 → mp-aaaabcoo`标识解析与 14 个 Fe₃O₄ 位点，以及 alphaXiv MCP／`fullText=true` HTTP 200；它们均不提供可比反应能或活性位证据。

## 验证边界

Windows 本地收据覆盖双工作区、KaTeX、文献跳转、二维／三维切换、移动视口、特定算子反例和模型调用预算。最新计数以 `artifacts/` 中随提交包生成的收据为准。Linux 与 macOS 使用同一入口，但在真实平台或持续集成复跑前仅标为“设计适配、未实测”。

面板不提供 PDF 保存功能。公共数据库接口不可用不等于记录不存在；能量空值不等于零；排序结果不等于性能结论；支撑体体相坐标不等于活性位结构；有限采样和 **sorry** 也不等于证明。
