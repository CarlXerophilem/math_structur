# GOAI 开放探索提交包

**Math Structurer — Convincing, reusable target-matching skills for AI research agents.**

Math Structurer v0.6 将自然语言科研目标整理为类型化对象、来源字段、空间表示和可验证子任务。当前版本聚焦一个最小化学切片：从反应物与产物出发，连接文献分析和公共数据库接口，展示严格六元组反应能量、催化剂候选及来源限定几何。候选记录、Fe₃O₄ 支撑体坐标和模型文本均不是科学发现。

## 一行启动

Linux／macOS：

~~~bash
python3 run.py
~~~

Windows：

~~~powershell
python run.py
~~~

服务只监听回环地址，并在终端给出 `http://127.0.0.1:8766/`；按 `Ctrl+C` 停止。资源均按 `run.py` 所在目录定位，不依赖启动时的工作目录。

## 默认本地识别模型

交互界面默认使用本机 Ollama 中名称完全匹配的检查点：

~~~text
hf.co/mradermacher/Qwen3-8B-Jailbroken-GGUF:Q4_K_M
~~~

模型只负责识别任务域、排序意图、反应物、产物和可选筛选维度。名称中的 **Jailbroken** 只是上游检查点名称，不表示模型可信，也不降低来源核验要求。模型不可用、格式不合格或字段冲突时，界面必须保留明确状态，不会静默切换到其他模型。

Windows 11 上已进行一次本地识别验收，模型摘要为 `ca6da952658c16e9eafcf68cb6a1719dbdc67891c89cff06f0394a722508a5d8`。默认查询被识别为 `reaction / catalyst_search`，反应物为 `CO2gas`、`H2gas`，产物为 `CH3CH2OHgas`。温度、压力、候选范围、观测指标和参照方法只作为 **possibilities** 保存；任何一项为空都不阻止文献和数据库检索。

## 一行核验

Linux／macOS：

~~~bash
python3 run.py --check
~~~

Windows：

~~~powershell
python run.py --check
~~~

`--check` 只在回环地址临时启动服务，以零模型方式检查静态资源、接口字段、空值语义和收据格式；它不调用外网，也不把缺少能量或可选条件判为失败。任一结构检查失败都会返回非零退出码。符号分支调试才按需使用 SymPy。

## 认证接口核验

密钥只通过环境变量 `MP_API_KEY` 和 `ALPHAXIV_API_KEY` 读取，不进入源码、收据或提交包。可运行：

~~~bash
python3 panel/authenticated_connector_smoke.py --full-text
~~~

2026-08-18 实测中，Materials Project 认证查询返回 HTTP 200：请求 `mp-19306` 时返回规范标识 `mp-aaaabcoo`、Fe₃O₄ 和 14 个位点。这是标识解析信号，不把体相支撑体升级为活性位。alphaXiv MCP 认证初始化、11 个工具列表及 `fullText=true` 原文抽取均返回 HTTP 200；原文未在本地保存。Catalysis-Hub 和 DeepSeek 仍需各自的环境变量。

## 默认化学切片

默认输入为 **CO2gas+H2gas -- CH3CH2OHgas @best**。其中 `@best` 仅指定候选排序方式：排序依据必须显示，且不得改写成“性能最佳”或“全局最优”。首屏分析限定为：

- **反应物**：从输入中直接识别并保留相态；
- **产物**：从输入中直接识别并保留相态；
- **反应能量**：只有数值、单位、能量定义、计算或实验方法及来源同时可追溯时才显示；当前缺少可比来源时保持空值 `—`，不能写成零；
- **文献与公共数据库**：保存来源类型、记录标识、标题、作者、年份、链接和证据层级；接口不可用不等于记录不存在；
- **催化剂空间几何**：当前读取 Materials Project OPTIMADE 的 `mp-19306` Fe₃O₄ 体相笛卡尔坐标，二维／三维均标为 `support-only`；这不是 Pd 活性位、吸附界面或反应机理；
- **可选可能性**：温度、压力、候选范围、观测指标和参照方法可用于后续筛选，但缺失时继续返回有来源候选。

Wang 等关于 CO₂ 直接制乙醇的研究讨论了 Na–Fe@C、K–CuZnAl、界面与组分邻近方式，说明候选的结构描述和来源上下文不可省略（Wang et al., 2021，DOI: [10.1021/acscatal.1c01504](https://doi.org/10.1021/acscatal.1c01504)）。本项目只把该记录作为可追溯候选入口，不从标题或元数据推断催化性能。

`@best` 只做稳定排序，固定公式为 `50*reaction_match + 25*abstract_verified + 15*public_geometry_link + 10*comparable_energy_record`。四项均为 0／1 特征；排序不改变证据等级，也不表示催化性能最佳。温度、压力、候选范围、观测指标和基线继续作为非阻断的 **possibilities**。

## 数据接口职责与实测边界

| 接口 | 本项目读取的字段 | 已核验边界 |
|---|---|---|
| [Catalysis-Hub](https://doi.org/10.1038/s41597-019-0081-y) | 反应物、产物、带类型的密度泛函能量、部分原子结构 | GraphQL 模式内省本轮返回 200；无密钥记录查询返回 401；`reaction_energy` 也可能是吸附能；不同论文不可直接按能量排序 |
| [OC20](https://doi.org/10.1021/acscatal.0c04525) | 初始／弛豫结构、能量、力、`bulk_mpid`、Miller 指数、吸附位点 | 数据为 CC-BY-4.0，但不是完整反应网络；吸附能或弛豫能不是实验催化性能 |
| [Materials Project](https://docs.materialsproject.org/downloading-data/using-the-api/getting-started) | 最低能体相晶体、形成能、凸包与平衡分解字段 | 无密钥查询返回 401；认证查询返回 200 并观察到 `mp-19306 → mp-aaaabcoo`标识解析；体相结构仍不是催化界面 |
| [Crossref](https://www.crossref.org/documentation/retrieve-metadata/rest-api/)／[OpenAlex](https://help.openalex.org/data/works/attributes.md) | DOI、题名、作者、日期、落地页、开放状态 | 只作身份核验与跳转；不提供反应能或几何；摘要索引不等于全文 |
| [alphaXiv MCP](https://alphaxiv.org/docs/mcp)／[arXiv API](https://info.arxiv.org/help/api/index.html) | AI 阅读、原文抽取／规范元数据与版本链接 | 无认证返回 401；认证 MCP 和 `fullText=true` 原文抽取已返回 200。默认 AI 中间报告仍不是原文，失败时回退 arXiv 元数据 |

所有能量记录必须写明 `kind`。表面反应密度泛函能、吸附能、弛豫结构能、每原子形成能、凸包能和平衡分解能不得折叠到同一数轴排名。`@best` 只按检索相关性、来源层级、字段完整度与几何可追溯性排序。

第二个工作区独立调试特定基算子

\[
B:\mathbb C\times\mathbb C^\times\to\mathbb C,\qquad B(u,v)=e^u-\operatorname{Log}v,
\]

以及有限域上的函数复合与反逆义务。该工作区不处理反应能量或三维坐标，也不声称存在统一代数。

## 平台与后端状态

- **Windows 11：已实测。** 本地启动、零模型结构检查和 Chrome 验收已有收据。
- **Linux／macOS：设计适配，尚未实机验收。** 在真实平台或持续集成中复跑前，不把 Windows 结果写成跨平台通过。
- Qwen3-8B-Jailbroken 每次至多用于一次受限识别；Codex、DeepSeek 和 Lean 只有在用户显式选择且接口可用时才运行。
- 最新测试计数、浏览器网络记录、Word 页数和文件哈希以 `artifacts/` 中随提交包生成的收据为准。

## 文件入口

- 四页 Word：`GOAI_四页提交稿_Math_Structurer.docx`
- 指导性 Markdown：`03_GOAI_FOUR_PAGE_GUIDANCE_FINAL.md`
- 交互面板：`panel/`
- 验证截图与收据：`artifacts/`
- 提交压缩包：`AI4R_OPEN_team_id.zip`

提交包不保存检索所得论文 PDF。数据库候选不等于发现，元数据不等于实验结论，未知能量不等于零，支撑体体相坐标不等于活性位结构，检索失败也不等于研究不存在。
