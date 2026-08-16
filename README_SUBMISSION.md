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

默认催化切片可由 Python 标准库运行；Windows 上已额外以禁用站点包的 `python -I -S -B run.py --check` 核验。符号分支比较才会按需使用可选的 SymPy，缺失时返回明确的不可用状态。

## 默认切片的边界

默认输入是 **CO2gas+H2gas -- CH3CH2OHgas @best**。系统先报告原式不守恒，再给出配平式、\(A\nu=0\)、欠定目标函数、相连空间、未排名文献候选及标有“示意、未经弛豫”的二维／三维构型。

这里没有催化活性数值模拟，没有 DFT 或动力学计算，也没有“最佳催化剂”排名。当前发现信号是：缺少温度、压力、候选域和统一观测表时，无条件排名在数学上欠定，科研代理应拒绝作答并要求补齐条件。文献候选只提供可核验入口，几何图只承担接口与可视化演示。

第二个工作区只调试已声明的基算子
\[
B:\mathbb C\times\mathbb C^\times\to\mathbb C,\qquad B(u,v)=e^u-\operatorname{Log}v,
\]
有限域上的 \(g\circ g=f\) 和一般反逆证明义务；这里的 \(\operatorname{Log}\) 逐点取主值。它不把反应配平或三维坐标送入标量迭代，也不声称存在统一代数。

## 平台与后端状态

- **Windows 11：已实测。** 一行启动、隔离标准库核验、Python 回归测试和真实 Chrome 验收均已运行。
- **Linux／macOS：设计适配，尚未实机验收。** 标准库入口、相对资源定位和回环服务没有操作系统专用调用；在真实平台或 CI 复跑前，不把 Windows 结果表述为跨平台实测。
- 默认精确内核调用模型次数为零。本地 Qwen3-8B、Codex、DeepSeek 和 Lean 均属于可选后端；不可用时必须显式显示“不可用”，不能静默替换或伪造结果。
- 最新测试计数、浏览器网络记录、Word 页数和文件哈希以 `artifacts/` 中与提交包同时生成的收据为准。

## 文件入口

- 四页 Word：`GOAI_四页提交稿_Math_Structurer.docx`
- 指导性 Markdown：`03_GOAI_FOUR_PAGE_GUIDANCE_FINAL.md`
- 交互面板：`panel/`
- 验证截图与收据：`artifacts/`
- 提交压缩包：`AI4R_OPEN_team_id.zip`

压缩包不收录论文 PDF。检索失败不等于研究不存在，元数据不等于实验结论，示意图不等于弛豫结构，有限采样、模型输出或 `sorry` 也不等于证明。
