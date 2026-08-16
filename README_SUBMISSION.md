# GOAI 开放探索提交包

**Math Structurer — Convincing, reusable target-matching skills for AI research agents.**

Math Structurer 将自然语言科研目标整理为类型化目标、约束、相连空间、特定基算子和可验证子任务。当前版本是可检查的研究原型：它可以暴露守恒失败、目标欠定、反例和未知状态，但不会把候选文献、示意构型或模型文本冒充科学结论。

## 一行启动

解压后在项目根目录运行。Linux／macOS 入口为：

~~~bash
python3 run.py
~~~

Windows 入口为：

~~~powershell
python run.py
~~~

程序启动回环地址上的本地 HTML5 服务，并在终端打印 `http://127.0.0.1:8766/`；它不会擅自打开浏览器。按 `Ctrl+C` 停止。入口以 `run.py` 自身位置寻找 `panel/`，不依赖调用命令时的当前工作目录；因此也可以从其他目录用脚本绝对路径启动。

### 默认目标识别模型

默认界面使用本机 Ollama 中名称完全匹配下列检查点的模型：

~~~text
hf.co/mradermacher/Qwen3-8B-Jailbroken-GGUF:Q4_K_M
~~~

启动界面前先核对本机模型清单：

~~~bash
ollama list
~~~

清单中必须出现上述完整名称。随后仍使用前述命令启动界面：Linux／macOS 为 `python3 run.py`，Windows 为 `python run.py`。

该模型只做**目标识别**：输出只允许包含受限的任务类型、意图、实体、约束和缺失字段，不生成催化剂排名、机理、证明或其他科学结论。模型返回值始终是不可信的候选结构，随后必须由确定性的类型检查、反应配平、元素守恒、定义域和目标完备性验证器复核；未通过的字段只能标为失败、缺失或未知。

模型不存在、Ollama 未运行、返回格式不合格或验证器拒绝时，界面必须明确失败，不会静默改用 Codex、DeepSeek、其他 Ollama 模型或本地规则来伪装同一次目标识别已经成功。名称中的 **Jailbroken** 只是上游检查点名称，不表示模型可信，不表示安全限制或科学验证已经解除，也不降低任何确定性验证门槛。

### 本次本地识别验收

Windows 11 上已实际调用该 Ollama 模型一次，模型摘要为 `ca6da952658c16e9eafcf68cb6a1719dbdc67891c89cff06f0394a722508a5d8`。默认查询被识别为 `reaction / catalyst_search`，实体为 `CO2gas`、`H2gas` 和 `CH3CH2OHgas`，并列出温度、压力、候选域、观测指标与基线等缺项。确定性闸门随后确认识别域与意图一致，检测到原输入不守恒，补平后得到 \(A\nu=(0,0,0)\)，并继续拒绝无条件排名；这仍不是催化剂发现。完整收据见 `artifacts/qwen_recognition_acceptance.json`。

## 一行核验

Linux／macOS：

~~~bash
python3 run.py --check
~~~

Windows：

~~~powershell
python run.py --check
~~~

`--check` 只在回环地址临时启动服务，固定选择本地精确内核，不调用模型或外网。只有静态页面可访问、失衡输入被识别且配平结果满足 \(A\nu=0\) 时才返回退出码 `0` 和 `"status":"passed"`。任一检查失败都会向标准错误输出 `"status":"failed"` 并返回非零退出码，不会以降级结果冒充通过。

零模型离线核验路径可由 Python 标准库运行；Windows 上已额外以禁用站点包的 `python -I -S -B run.py --check` 核验。该命令不要求 Ollama 或上述检查点。符号分支比较才会按需使用可选的 SymPy，缺失时返回明确的不可用状态。

## 默认切片的边界

默认输入是 **CO2gas+H2gas -- CH3CH2OHgas @best**。系统先报告原式不守恒，再给出配平式、\(A\nu=0\)、欠定目标函数、相连空间、未排名文献候选及标有“示意、未经弛豫”的二维／三维构型。

本地模型在这条链中只识别“反应目标、物种、相态、最佳化意图以及温压和观测表等缺项”；配平结果、守恒判定和拒绝无条件排名的结论不由模型自证。

这里没有催化活性数值模拟，没有 DFT 或动力学计算，也没有“最佳催化剂”排名。当前发现信号是：缺少温度、压力、候选域和统一观测表时，无条件排名在数学上欠定，科研代理应拒绝作答并要求补齐条件。文献候选只提供可核验入口，几何图只承担接口与可视化演示。

第二个工作区只调试已声明的基算子
\[
B:\mathbb C\times\mathbb C^\times\to\mathbb C,\qquad B(u,v)=e^u-\operatorname{Log}v,
\]
有限域上的 \(g\circ g=f\) 和一般反逆证明义务；这里的 \(\operatorname{Log}\) 逐点取主值。它不把反应配平或三维坐标送入标量迭代，也不声称存在统一代数。

## 平台与后端状态

- **Windows 11：已实测。** 一行启动、隔离标准库核验、Python 回归测试和真实 Chrome 验收均已运行。
- **Linux／macOS：设计适配，尚未实机验收。** 标准库入口、相对资源定位和回环服务没有操作系统专用调用；在真实平台或 CI 复跑前，不把 Windows 结果表述为跨平台实测。
- 默认交互界面最多调用一次上述本地 Ollama 检查点，仅用于受限目标识别；确定性验证器负责接受或拒绝其字段。`python3 run.py --check`／`python run.py --check` 始终为零模型离线核验。Codex、DeepSeek 和 Lean 不是默认目标识别的静默后备项。
- 最新测试计数、浏览器网络记录、Word 页数和文件哈希以 `artifacts/` 中与提交包同时生成的收据为准。

## 文件入口

- 四页 Word：`GOAI_四页提交稿_Math_Structurer.docx`
- 指导性 Markdown：`03_GOAI_FOUR_PAGE_GUIDANCE_FINAL.md`
- 交互面板：`panel/`
- 验证截图与收据：`artifacts/`
- 提交压缩包：`AI4R_OPEN_team_id.zip`

压缩包不收录论文 PDF。检索失败不等于研究不存在，元数据不等于实验结论，示意图不等于弛豫结构，有限采样、模型输出或 `sorry` 也不等于证明。
