from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.shared import Cm, Pt, RGBColor
from docx.text.run import Run


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "GOAI_四页提交稿_Math_Structurer.docx"
VIS = ROOT / "artifacts" / "visuals"

NAVY = "0D2538"
BLUE = "245F83"
ORANGE = "E77859"
PALE = "EDF3F4"
PALE_ORANGE = "FBECE7"
GRAY = "66727D"
LIGHT = "F7F8F7"
WHITE = "FFFFFF"


# Author-year references are real external hyperlinks in the generated Word file.
# Keep the longest aliases first so a shorter label cannot split a longer citation.
CITATION_LINKS = sorted(
    [
        ("Güngör, arXiv:1901.01543v11, 2025", "https://arxiv.org/abs/1901.01543"),
        ("Mialon et al., 2023（arXiv v2, 2024）", "https://arxiv.org/abs/2307.05432"),
        ("Murugan & Palanivel, 2021", "https://doi.org/10.1007/s00010-020-00739-w"),
        ("Deng, Hani & Ma, 2025", "https://arxiv.org/abs/2408.07818"),
        ("Brandstetter et al., 2022", "https://proceedings.mlr.press/v162/brandstetter22a.html"),
        ("Wang et al., 2021", "https://doi.org/10.1021/acscatal.1c01504"),
        ("Wang et al. (2021)", "https://doi.org/10.1021/acscatal.1c01504"),
        ("Kozyra, 2021", "https://doi.org/10.20429/tag.2021.080108"),
        ("Murugan–Palanivel 2021", "https://doi.org/10.1007/s00010-020-00739-w"),
        ("Deng–Hani–Ma 2025", "https://arxiv.org/abs/2408.07818"),
        ("Brandstetter 2022", "https://proceedings.mlr.press/v162/brandstetter22a.html"),
        ("Mialon 2023／v2 2024", "https://arxiv.org/abs/2307.05432"),
        ("Güngör v11 2025", "https://arxiv.org/abs/1901.01543"),
        ("Kozyra 2021", "https://doi.org/10.20429/tag.2021.080108"),
        ("Wang 2021", "https://doi.org/10.1021/acscatal.1c01504"),
    ],
    key=lambda item: len(item[0]),
    reverse=True,
)


def font_run(run, size=8.0, bold=False, color=None, font="Microsoft YaHei"):
    run.font.name = font
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), font)
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def add_hyperlink(paragraph, text, url, size=8.0, color=BLUE, bold=False, font="Microsoft YaHei"):
    """Append a real external Word hyperlink and return its Run wrapper."""
    relationship_id = paragraph.part.relate_to(url, RT.HYPERLINK, is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), relationship_id)
    hyperlink.set(qn("w:history"), "1")
    run_element = OxmlElement("w:r")
    hyperlink.append(run_element)
    paragraph._p.append(hyperlink)
    run = Run(run_element, paragraph)
    font_run(run, size, bold, color, font)
    run.font.underline = True
    return run


def add_text_with_links(paragraph, text, size=8.0, color=None, bold=False, font="Microsoft YaHei"):
    """Append text while turning every registered author-year label into a hyperlink."""
    cursor = 0
    while cursor < len(text):
        matches = []
        for label, url in CITATION_LINKS:
            index = text.find(label, cursor)
            if index >= 0:
                matches.append((index, -len(label), label, url))
        if not matches:
            run = paragraph.add_run(text[cursor:])
            font_run(run, size, bold, color, font)
            break
        index, _, label, url = min(matches)
        if index > cursor:
            run = paragraph.add_run(text[cursor:index])
            font_run(run, size, bold, color, font)
        add_hyperlink(paragraph, label, url, size, BLUE, bold, font)
        cursor = index + len(label)


def shade(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    node = tc_pr.find(qn("w:shd"))
    if node is None:
        node = OxmlElement("w:shd")
        tc_pr.append(node)
    node.set(qn("w:fill"), fill)


def cell_margins(cell, top=32, start=55, bottom=32, end=55):
    tc_pr = cell._tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def cant_split(row):
    row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))


def keep_next(paragraph):
    paragraph._p.get_or_add_pPr().append(OxmlElement("w:keepNext"))


def setup(doc):
    normal = doc.styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.font.size = Pt(7.9)
    normal.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    normal.paragraph_format.space_after = Pt(1.5)

    for name, size, color in (
        ("Title", 16.5, NAVY),
        ("Heading 1", 12.5, NAVY),
        ("Heading 2", 9.8, BLUE),
        ("Heading 3", 8.7, NAVY),
    ):
        style = doc.styles[name]
        style.font.name = "Microsoft YaHei"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)
        style.paragraph_format.space_before = Pt(2.0)
        style.paragraph_format.space_after = Pt(1.4)
        style.paragraph_format.keep_with_next = True

    section = doc.sections[0]
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(1.05)
    section.bottom_margin = Cm(1.00)
    section.left_margin = Cm(1.25)
    section.right_margin = Cm(1.25)
    section.header_distance = Cm(0.35)
    section.footer_distance = Cm(0.35)

    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = footer.add_run("GOAI 开放探索  •  ")
    font_run(r, 6.8, color=GRAY)
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    r._r.append(begin)
    r._r.append(instr)
    r._r.append(end)


def add_h(doc, text, level):
    p = doc.add_paragraph(text, style=f"Heading {level}")
    keep_next(p)
    return p


def add_p(doc, text, size=7.9, color=None, bold_lead=None, after=1.5):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(after)
    if bold_lead and text.startswith(bold_lead):
        r = p.add_run(bold_lead)
        font_run(r, size, True, color)
        add_text_with_links(p, text[len(bold_lead):], size, color)
    else:
        add_text_with_links(p, text, size, color)
    return p


def add_formula(doc, text, size=9.0):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0.8)
    p.paragraph_format.space_after = Pt(1.4)
    r = p.add_run(text)
    font_run(r, size, False, NAVY, "Cambria Math")
    return p


def add_table(doc, headers, rows, widths, font_size=7.1):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    header = table.rows[0]
    cant_split(header)
    for index, value in enumerate(headers):
        cell = header.cells[index]
        cell.width = Cm(widths[index])
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        cell_margins(cell)
        shade(cell, NAVY)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(value)
        font_run(r, font_size, True, WHITE)
    for row_index, values in enumerate(rows):
        cells = table.add_row().cells
        cant_split(table.rows[-1])
        for index, value in enumerate(values):
            cell = cells[index]
            cell.width = Cm(widths[index])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            cell_margins(cell)
            if row_index % 2:
                shade(cell, LIGHT)
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(value))
            font_run(r, font_size, index == 0)
    spacer = doc.add_paragraph()
    spacer.paragraph_format.space_after = Pt(0)
    spacer.paragraph_format.line_spacing = Pt(1)
    return table


def add_picture(doc, name, width_cm):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(0.7)
    p.paragraph_format.space_after = Pt(1.0)
    p.add_run().add_picture(str(VIS / name), width=Cm(width_cm))


def add_meta(doc, fields, citations, visual, human, budget):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0.5)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.left_indent = Cm(0.15)
    p.paragraph_format.right_indent = Cm(0.15)
    entries = [
        ("页面字段：", fields),
        ("  文献依据：", citations),
        ("  建议视觉：", visual),
        ("  人工确认：", human),
        ("  内容预算：", budget),
    ]
    for lead, body in entries:
        r = p.add_run(lead)
        font_run(r, 6.45, True, BLUE)
        add_text_with_links(p, body, 6.45, GRAY)


def page_break(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def build():
    doc = Document()
    setup(doc)
    props = doc.core_properties
    props.title = "Math Structurer — GOAI 开放探索四页问题定义"
    props.subject = "特定基算子与迭代、类型化科研目标、发现信号"
    props.author = "GOAI 参赛团队"
    props.keywords = "GOAI, Math Structurer, basis operator, iteration, catalyst, Lie symmetry, verification"

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = title.add_run("Math Structurer")
    font_run(r, 16.5, True, NAVY)
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.paragraph_format.space_after = Pt(2)
    r = subtitle.add_run("Convincing, reusable target-matching skills for AI research agents.")
    font_run(r, 8.4, True, BLUE)

    add_table(
        doc,
        ["四页共用信息", "冻结表述"],
        [
            ("一句话问题", "科研代理能否把自然语言科研目标转换为带定义域、状态空间、约束、特定基算子和验证义务的机器问题，并依据失败反馈改变下一轮行动？"),
            ("研究边界", "首版只运行 CO2gas+H2gas -- CH3CH2OHgas @best 与 B(u,v)=eᵘ−Log(v) 调试；不声称发现新催化剂、统一代数、自动 PDE 约化或任意半迭代证明。"),
            ("当前成熟度", "交互原型 v0.5；配平、守恒、类型化路由、特定算子调试与固定 Lean 义务通过。科学发现闸门未通过。"),
        ],
        [2.7, 15.6],
        6.9,
    )

    add_h(doc, "一、问题与证据", 1)
    add_h(doc, "1.1 真实问题或需求", 2)
    add_p(doc, "化学实验与数学研究都可能表现为“固定对象与约束—由有限结构生成候选—以反馈修订”的过程；相似之处是工作流，而非统一代数。CO₂ 加氢制乙醇的候选必须携带组分邻近方式、温压、进料和测量口径。Wang 等组合 Na–Fe@C 与 K–CuZnAl；ACS Figshare 官方记录写明，原位表征与 DFT 计算提示催化界面、组件邻近方式及醛类中间体具有重要作用。这支持按条件组织候选，却不支持脱离条件的全局最佳排名（Wang et al., 2021）。")
    add_p(doc, "半迭代是在指定 X 上寻找 g:X→X 使 g∘g=f。Kozyra 给出有限自映射的函数图判据；Murugan 与 Palanivel 仅在非单调性高度为 1 的连续非分段单调函数类中获得存在性结果，并另行研究 Hyers–Ulam 稳定性；二者均不能外推到任意光滑函数（Kozyra, 2021；Murugan & Palanivel, 2021）。Güngör 综述说明 PDE 对称可减少独立变量、ODE 对称可降低阶数；所引两项代表工作分别将李对称用于数据增强和自监督表征，但不解决通用生成元、边界兼容或精确约化（Güngör, arXiv:1901.01543v11, 2025；Brandstetter et al., 2022；Mialon et al., 2023（arXiv v2, 2024））。")
    add_p(doc, "本地数论族 fₖ(n)=kP⁺(n)+(P⁺(n) mod k) 可生成轨道并检查素性、最大质因子、同余与闭合；旧 Lean 原型把本应参数化的模数固化为 10，最终命题仍以 sorry 占位，说明生成必须与定义检查和否证器绑定。这些场景都由有限结构生成候选，但缺少经验证的 AI 工具接口；该缺口仍是待检验假设。", 7.7)
    add_h(doc, "1.2 为什么尚未被结构化", 2)
    add_p(doc, "困难不在万能展开公式，而在不同算子的定义域、陪域和验证义务。首版只统一带类型接口 bᵢ:Xᵢ⇀Xⱼ、zₜ₊₁=bᵢₜ(zₜ)：配平属于整数核 kerℤ(A)，构型属于 R³ⁿ/SE(3)，半迭代属于自映射空间，PDE 约化还需延拓、边界与不变量。Deng、Hani 与 Ma 的硬球—Boltzmann 长时推导用时间分层、累积量、部分展开、分子图和切割算法控制误差（Deng, Hani & Ma, 2025，pp. 9–12）。这说明专业参数、结构表示和误差口径必须一起嵌入，公式与三维投影才可复核；该预印本仅作复杂度例证，不证明本工具能完成 PDE 约化、分子模拟或通用函数生成。")
    add_h(doc, "1.3 研究价值与合适切片", 2)
    add_p(doc, "默认查询先被判为不守恒，再补成下式。由于 θ、候选域和观测表未冻结，arg max J(c;θ) 不可审计；系统只返回未排名文献候选、缺失参数、相连空间和示意构型。这一问题修正而非材料名称，构成首版可检查的负结果。")
    add_formula(doc, "2CO₂(g)+6H₂(g) → C₂H₅OH(g)+3H₂O(g),   ν=(−2,−6,1,3),   Aν=0")
    add_picture(doc, "page1_demo_slice.png", 17.6)
    add_meta(
        doc,
        "原始目标、配平、Aν、θ、Cθ、目标完备性、拒绝原因。",
        "Wang 2021；Kozyra 2021；Murugan–Palanivel 2021；Güngör v11 2025；Brandstetter 2022；Mialon 2023／v2 2024；Deng–Hani–Ma 2025。",
        "演示截图：守恒、欠定目标与相连空间。",
        "候选未写成最优；构型标为示意；共享接口缺口仍是待检验假设。",
        "约 900 字＋1 图。",
    )

    page_break(doc)

    add_h(doc, "二、环境接口", 1)
    add_h(doc, "2.1 固定规则", 2)
    add_p(doc, "每次运行先冻结原始目标、物种与相态、条件向量 θ、候选集合 Cθ、指标和允许调用的特定基算子。催化路线固定经过反应解析、元素矩阵、整数核配平、目标完备性、文献检索和几何投影；未经配平不得排名，指标欠定不得补写“最佳”，无来源坐标只能画示意构型，含 sorry 的 Lean 文件不得标为已证明。")
    add_formula(doc, "θlit={T=320 °C, P=5.0 MPa, 进料=(3.25% Ar, 26.5% CO₂, 70.25% H₂), 反应器=内径 6 mm 固定床}")
    add_p(doc, "该参数截面来自 Wang et al. (2021) 的补充材料，只说明专业比较所需的粒度，不自动成为演示环境的条件，也不能与其他论文横向排名。", 7.6)
    add_h(doc, "2.2 观察/行动/反馈", 2)
    add_table(
        doc,
        ["接口", "落地字段或操作", "反馈如何改变下一步"],
        [
            ("观察", "原目标、标准数学式、θ 完整度、Cθ、来源层级、相连空间、反例、预算", "形成当前可判定问题切片"),
            ("行动", "配平；补齐/收缩条件域；换候选子集；调用文献、几何、Lean；生成反例；停止", "选择下一特定算子或插件"),
            ("反馈", "通过／否证／未知／证据不足／超时；守恒余量、失败字段、来源位置、轨迹", "不守恒→配平；欠定→索取条件或拒绝排名；仅元数据→读摘要/原文"),
        ],
        [2.2, 8.4, 7.7],
        6.8,
    )
    add_h(doc, "2.3 记录与预算", 2)
    add_p(doc, "日志保存目标版本、算子签名、输入输出哈希、反馈、下一动作理由、模型/插件版本、来源链接和失败状态。默认精确内核不调用模型；本地 Qwen3-8B 每次至多用于一次语义解析，输出仍须精确复核。Codex 或 DeepSeek 仅在用户显式选择时二选一、最多一次；文献接口至多八次，几何输出至多一幅二维和一幅三维图，探索至多六轮。后端不可用必须明示，不得静默替换。")
    add_picture(doc, "page2_environment_interface.png", 17.6)
    add_meta(
        doc,
        "固定规则、观察字段、动作枚举、反馈状态、日志与模型/文献/几何/轮数预算。",
        "Wang 2021 补充材料 pp. 3–4；Deng–Hani–Ma 2025 仅作复杂度参照。",
        "带类型部分映射与反馈闭环。",
        "专业参数标明来源；Qwen3-8B 不是验证器；Linux/macOS 未宣称实测。",
        "约 700 字＋1 表1图。",
    )

    page_break(doc)

    add_h(doc, "三、发现信号与参照", 1)
    add_h(doc, "3.1 什么算发现", 2)
    add_p(doc, "输出一个材料名称不算发现。正向发现必须是条件化、可反驳的结构关系：冻结温压、进料、候选域和指标后，某类组件邻近关系或构型形成稳定可行候选；按预注册方式扰动一个条件，候选集合或可行性发生可解释变化；关系同时通过守恒、来源和专业插件。稳定负结果是同预算下候选均违反同一冻结约束；异常/反例是预期可行候选被守恒、原文或验证器否证；问题修正则是识别 θ、Cθ 与测量表缺失并生成下一次可运行查询。当前演示环境只取得最后一种信号，尚未构成催化发现。")
    add_h(doc, "3.2 平凡解/随机/无干预", 2)
    add_formula(doc, "F(θ)={c∈Cθ : Aν=0, hⱼ(c;θ)=0, qᵢ(c;θ)≤0},   c*∈arg max[c∈F(θ)] J(c;θ)")
    add_p(doc, "解只可能从冻结后的非空可行域出现：F(θ)=∅ 即无可行解；极值集合含多个元素即非唯一。当目标与约束对某个非平凡群作用不变时，唯一性应在等价类商空间中讨论，或在固定规范后讨论代表元的唯一性。验证依次经过类型/单位、守恒、原文、专业求解器、条件扰动或反例、人工复核；有限采样只算检验。")
    add_table(
        doc,
        ["参照", "同预算操作", "比较指标"],
        [
            ("平凡", "直接让语言模型回答", "类型错误、无来源主张"),
            ("无干预", "不修正输入的关键词检索", "是否发现欠定并改变行动"),
            ("随机", "随机选择基算子或候选", "有效反例、正确拒答率"),
            ("非平凡", "确定性配平＋目标完备性＋结构化检索", "可复查结论与失败轨迹"),
        ],
        [2.3, 7.3, 8.7],
        6.8,
    )
    add_h(doc, "3.3 最低成功与失败标准", 2)
    add_p(doc, "环境技术通过：alphaXiv＋DOI 接口快速核验完成，并分层记录 DOI 解析、元数据、摘要和实际打开的正文层级；本地无数值验证器对类型、配平与 Aν=0 零错误通过，且不伪造催化数值；人工终审公式、链接、构型标签和结论边界；至少一次反馈确实改变下一查询、候选域或动作。", 7.65, bold_lead="环境技术通过：", after=0.8)
    add_p(doc, "科学发现通过：冻结 θ、Cθ、J 与预算后，得到确定性基线没有给出的、可复现的条件—结构关系或稳定负结果，并通过预注册扰动与专业验证。当前 @best 仅达到问题修正／接口验证，科学发现闸门未通过。", 7.65, bold_lead="科学发现通过：", after=0.8)
    add_p(doc, "任一情形直接失败：无条件排名；元数据冒充实验结论；示意图冒充弛豫结构；有限采样或 sorry 冒充证明；检索失败冒充“不存在”；反馈不改变动作。条件化试跑若仍只得到标题且不优于确定性基线，就应承认切片不成立并缩小问题。", 7.55)
    add_picture(doc, "page3_discovery_gates.png", 17.6)
    add_meta(
        doc,
        "发现类型、预注册条件、可行域、扰动、四类参照、三道闸门、成功/失败判据。",
        "Wang 2021；alphaXiv 读取收据；本地精确内核与浏览器收据。",
        "四类发现信号与三道核验闸门。",
        "保留 ACS 主页面 403、无催化数值模拟、当前无催化发现。",
        "约 800 字＋1 表1图。",
    )

    page_break(doc)

    add_h(doc, "四、最小验证计划", 1)
    add_h(doc, "4.1 一次试跑怎么做", 2)
    add_p(doc, "解压后在项目根目录执行同一行命令：", 7.9)
    code = doc.add_paragraph()
    code.alignment = WD_ALIGN_PARAGRAPH.CENTER
    code.paragraph_format.space_after = Pt(2.0)
    r = code.add_run("python3 run.py")
    font_run(r, 10.2, True, NAVY, "Consolas")
    add_p(doc, "浏览器打开终端给出的本地地址，保留默认查询并点击一次“运行”。应看到原输入不守恒、配平方程与 Aν=0、目标因条件和测量缺失而欠定、六个相连空间、未排名文献候选及“示意、未经弛豫”的二维/三维构型。离线检查为 python3 run.py --check。默认启动只用相对路径与 Python 标准库；特定算子的符号分支比较才需要 SymPy。Windows 已实测；Linux/macOS 仍须真实复跑。")
    add_h(doc, "4.2 主要风险与失败路径", 2)
    add_p(doc, "核心风险不是报错，而是失败后仍生成可信语气。系统实行“拒绝冒充性失败”：配平失败不排名；条件欠定不输出最佳；仅有元数据不推断实验性能；无坐标只画示意；数值一致不声称形式证明；含占位符只返回部分形式化。本地参数化记录使用 p mod k，旧 Lean 原型却固定为 p mod 10 且最终命题仍含 sorry；因此，对 k≠10 的整齐输出也不能支持原问题。模型超时、接口受限、文献矛盾和几何失败均须保存触发字段、原始状态与下一修复动作。")
    add_h(doc, "4.3 复现与开源计划", 2)
    add_p(doc, "开源包包含单行入口、冻结查询、特定基算子签名、结果 JSON、事件日志、测试收据、来源链接和源码哈希，不收录论文 PDF。复现截图须显示 Aν=0、J(c;θ) 在 θ/Cθ/测量表冻结前未定义、Gₙ=R³ⁿ/SE(3)，以及六个空间之间的带类型映射。发布前在 Ubuntu 与 macOS 各运行 python3 run.py --check；未实测的平台继续标为未验证。")
    add_formula(doc, "B: ℂ×ℂ^×→ℂ,  B(u,v)=eᵘ−Log(v),  E(x)=B(1, B(B(1,x),1))", 8.7)
    add_p(doc, "每个 B 节点都检查第二参数非零，并约定 Arg(v)∈(−π,π]、逐点采用主值复对数。测试 x=−1 时，E(−1)=−iπ 而 Log(−1)=+iπ，故 E(−1)−Log(−1)=−2πi；该反例保留为“不匹配”。这只是特定基算子复合表达树，不代表统一代数。", 7.35, after=1.0)
    add_picture(doc, "page4_function_space_screenshot.png", 15.0)
    add_meta(
        doc,
        "单行命令、冻结输入、预期输出、拒绝冒充规则、平台状态、源码/日志哈希、开源边界。",
        "Kozyra 2021；本地数论生成—否证记录；测试、浏览器与 Lean 收据。",
        "含 B:ℂ×ℂ^×→ℂ、E(x)=B(1,B(B(1,x),1))、反例和 Lean 状态的工作台截图。",
        "核对命令、平台记录、来源跳转、示意标签与提交哈希；不把设计适配写成跨平台实测。",
        "约 650 字＋1 行命令1图。",
    )

    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
