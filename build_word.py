from __future__ import annotations

from pathlib import Path
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "GOAI_四页提交稿_Math_Structurer.docx"
VIS = ROOT / "artifacts" / "visuals"

NAVY = "17324D"
BLUE = "2E6F95"
PALE = "EAF2F5"
PALE_ORANGE = "FBECE7"
GRAY = "66727D"
LIGHT_GRAY = "F2F4F5"
WHITE = "FFFFFF"


def shade(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=45, start=65, bottom=45, end=65):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    tcMar = tcPr.first_child_found_in("w:tcMar")
    if tcMar is None:
        tcMar = OxmlElement("w:tcMar")
        tcPr.append(tcMar)
    for m, v in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tcMar.find(qn(f"w:{m}"))
        if node is None:
            node = OxmlElement(f"w:{m}")
            tcMar.append(node)
        node.set(qn("w:w"), str(v))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row):
    trPr = row._tr.get_or_add_trPr()
    tblHeader = OxmlElement("w:tblHeader")
    tblHeader.set(qn("w:val"), "true")
    trPr.append(tblHeader)


def set_keep_with_next(paragraph, keep=True):
    pPr = paragraph._p.get_or_add_pPr()
    node = pPr.find(qn("w:keepNext"))
    if keep and node is None:
        pPr.append(OxmlElement("w:keepNext"))
    elif not keep and node is not None:
        pPr.remove(node)


def set_cant_split(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(OxmlElement("w:cantSplit"))


def font_run(run, size=8.6, bold=False, color=None, font="Microsoft YaHei"):
    run.font.name = font
    run._element.rPr.rFonts.set(qn("w:eastAsia"), font)
    run.font.size = Pt(size)
    run.bold = bold
    if color:
        run.font.color.rgb = RGBColor.from_string(color)


def setup_styles(doc: Document):
    normal = doc.styles["Normal"]
    normal.font.name = "Microsoft YaHei"
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    normal.font.size = Pt(8.6)
    pf = normal.paragraph_format
    pf.space_after = Pt(1.8)
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE

    for name, size, color in (("Title", 16, NAVY), ("Heading 1", 13, NAVY), ("Heading 2", 10.3, BLUE), ("Heading 3", 9.2, NAVY)):
        style = doc.styles[name]
        style.font.name = "Microsoft YaHei"
        style._element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = RGBColor.from_string(color)
        style.paragraph_format.space_before = Pt(2.5 if name != "Title" else 0)
        style.paragraph_format.space_after = Pt(1.8)
        style.paragraph_format.keep_with_next = True


def add_page_number(section):
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run("GOAI 开放探索  •  ")
    font_run(r, 7.3, color=GRAY)
    fldChar1 = OxmlElement("w:fldChar"); fldChar1.set(qn("w:fldCharType"), "begin")
    instrText = OxmlElement("w:instrText"); instrText.set(qn("xml:space"), "preserve"); instrText.text = " PAGE "
    fldChar2 = OxmlElement("w:fldChar"); fldChar2.set(qn("w:fldCharType"), "end")
    r._r.append(fldChar1); r._r.append(instrText); r._r.append(fldChar2)


def configure_section(section):
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(1.25)
    section.bottom_margin = Cm(1.15)
    section.left_margin = Cm(1.35)
    section.right_margin = Cm(1.35)
    section.header_distance = Cm(0.45)
    section.footer_distance = Cm(0.45)
    add_page_number(section)


def add_h(doc, text, level=1):
    p = doc.add_paragraph(text, style=f"Heading {level}")
    set_keep_with_next(p)
    return p


def add_p(doc, text, *, bold_lead=None, align=None, size=8.6, color=None, space_after=1.8):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    if bold_lead and text.startswith(bold_lead):
        r1 = p.add_run(bold_lead); font_run(r1, size=size, bold=True, color=color)
        r2 = p.add_run(text[len(bold_lead):]); font_run(r2, size=size, color=color)
    else:
        r = p.add_run(text); font_run(r, size=size, color=color)
    return p


def add_bullets(doc, items, size=8.3):
    for item in items:
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.left_indent = Cm(.42)
        p.paragraph_format.first_line_indent = Cm(-.22)
        p.paragraph_format.space_after = Pt(1.1)
        r = p.add_run(item)
        font_run(r, size=size)


def add_table(doc, headers, rows, widths=None, font_size=7.7):
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.style = "Table Grid"
    hdr = table.rows[0]
    set_repeat_table_header(hdr); set_cant_split(hdr)
    for i, h in enumerate(headers):
        c = hdr.cells[i]; shade(c, NAVY); c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER; set_cell_margins(c)
        if widths: c.width = Cm(widths[i])
        p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
        r = p.add_run(h); font_run(r, size=font_size, bold=True, color=WHITE)
    for ri, row in enumerate(rows):
        cells = table.add_row().cells; set_cant_split(table.rows[-1])
        for i, value in enumerate(row):
            c = cells[i]; c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER; set_cell_margins(c)
            if widths: c.width = Cm(widths[i])
            if ri % 2 == 1: shade(c, LIGHT_GRAY)
            p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(value)); font_run(r, size=font_size, bold=(i == 0))
    doc.add_paragraph().paragraph_format.space_after = Pt(0)
    return table


def add_meta(doc, evidence, visual, human, budget):
    rows = [
        ("证据编号", evidence, "建议视觉", visual),
        ("人工确认", human, "内容预算", budget),
    ]
    table = doc.add_table(rows=2, cols=4)
    table.style = "Table Grid"; table.alignment = WD_TABLE_ALIGNMENT.CENTER; table.autofit = False
    widths = [1.8, 6.7, 1.8, 6.7]
    for ri, row in enumerate(rows):
        set_cant_split(table.rows[ri])
        for ci, value in enumerate(row):
            c = table.rows[ri].cells[ci]; c.width = Cm(widths[ci]); set_cell_margins(c, top=30, bottom=30)
            if ci in (0, 2): shade(c, PALE); bold = True
            else: bold = False
            p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(0)
            r = p.add_run(value); font_run(r, size=6.9, bold=bold, color=NAVY if bold else GRAY)
    return table


def add_picture(doc, filename, width_cm=17.7):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(1.2)
    run = p.add_run()
    run.add_picture(str(VIS / filename), width=Cm(width_cm))


def page_break(doc):
    p = doc.add_paragraph()
    p.add_run().add_break(WD_BREAK.PAGE)


def build():
    doc = Document()
    setup_styles(doc)
    configure_section(doc.sections[0])
    props = doc.core_properties
    props.title = "Math Structurer — Convincing, reusable target-matching skills for AI research agents"
    props.subject = "GOAI AI for Research 开放探索四页问题定义"
    props.author = "GOAI 参赛团队"
    props.keywords = "GOAI, Math Structurer, EML, target matching, basis, FunctionContract, Agent"

    # PAGE 1
    p = doc.add_paragraph(style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("Math Structurer").bold = True
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = sub.add_run("Convincing, reusable target-matching skills for AI research agents.\n数学滤镜 + 多空间插件路由；EML 域/分支为最小科学切片")
    font_run(r, size=9, color=BLUE)
    add_table(doc, ["共用信息", "冻结内容"], [
        ("一句话问题", "Agent 能否把自然语言科研目标转换为类型、逻辑、约束、相连基空间与可否证子任务，并依据 oracle 反馈改变下一行动？"),
        ("研究边界", "这是数学滤镜与插件路由，不是万能 EML 解析器；催化只压测接口，EML 域/分支才是已运行科学切片；KaTeX 与 2D/3D 均非证明。"),
        ("当前成熟度", "E1/E2/E5 已确认；Demo 12 项、面板 11 项和 Chrome 验收通过；环境技术闸门通过、科学发现闸门未通过；Lean 为部分形式化。"),
    ], widths=[2.6, 14.9], font_size=7.45)
    add_h(doc, "一、问题与证据", 1)
    add_h(doc, "1.1 真实问题或需求", 2)
    add_p(doc, "Math Structurer 先把 qNL 写成类型、逻辑、约束、基空间、机器任务和 KaTeX 视图，再用带验证器的部分映射连接多个空间。催化输入先交 ReactionDecomposer：默认式被判不守恒，补为 2CO2+6H2→C2H5OH+3H2O，得到 ν∈kerZ(A)；因条件化测量缺失，@best 弃权。EML 未被调用，3D 独立交给 GeometryPlugin——这里只压测路由，不宣称催化发现。")
    add_p(doc, "当前唯一科学校准切片是 EML 的 eml(x,y)=exp(x)−log(y) 树。原论文记录零点、域端点和复对数主分支困难（E1）；Demo 在 x=−1 得到编译值约 −πi、参考值 +πi、误差 2π，x=0 未定义（P1）。这是已知复现，不是新定理。", size=8.2)
    add_h(doc, "1.2 为什么尚未被结构化", 2)
    add_p(doc, "Content MathML 已能表示 domain、condition 与 compose（E2），类型系统、化学配平和几何工具也各自成熟；所以“统一表示”或“写一个 parser”不是创新。尚未结构化的是可审计循环：哪种目标先进入哪个专业插件，何时必须弃权，以及反例如何改变下一空间、基、oracle 或问题边界。系统性新颖性检索仍未完成。")
    add_h(doc, "1.3 研究价值与合适切片", 2)
    add_p(doc, "AI 的价值是把模糊目标降到可检查的机器问题，并依据守恒失败、欠定目标、反例或 unknown 改变下一行动。四小时只以催化例检查多空间路由，以 E1 的 ln 树校准反例循环，并由 E5 支撑材料可得；只有在封存的新 EML 树上找到稳定新失败族，才算科学发现。")
    add_picture(doc, "page1_branch_mismatch.png", 17.0)
    add_meta(doc, "E1、E2、E5；P1、T1、B1", "分支虚部图（标“已知复现”）", "催化仅接口压测；不得把 x=−1 写成新发现。", "750–850 汉字；1 图")

    page_break(doc)

    # PAGE 2
    add_h(doc, "二、环境接口", 1)
    add_h(doc, "2.1 固定规则", 2)
    add_table(doc, ["固定项", "可执行定义"], [
        ("目标记录", "保存 user_target、typed_logic、KaTeX、constraints、basis、spaces、plugin_route；显示公式不等于真值。"),
        ("相连空间", "催化固定为 N→S→C→Y→G→P；映射逐个带输入/输出类型和 oracle，不假定它们是同一向量空间。"),
        ("插件路由", "ReactionDecomposer 管反应；ObjectiveStructurer 管标量目标；GeometryPlugin 管坐标；Lean 只查明示命题。"),
        ("EML 闸门", "只接收合格标量解析 AST；代数结构标 unconfirmed；科学切片固定主分支、7 点池、1e−10 与 5 次预算。"),
        ("状态/安全", "solved / mismatch / undefined / unknown / abstain；不用 eval、exec、裸 sympify，运行后不得换指标。"),
    ], widths=[3.1, 14.4], font_size=7.5)
    add_h(doc, "2.2 观察/行动/反馈", 2)
    add_table(doc, ["接口", "字段/函数"], [
        ("观察", "typed_target, spaces, plugin_route, AST/domain/branch, conditioned_data, counterexamples, budget_left"),
        ("行动", "decompose_reaction(), choose_basis(), probe(), inspect_subtree(), revise(diff), project_geometry(), emit_lean()"),
        ("反馈", "balance/Aν, objective_status, evidence_span, mismatch/undefined/unknown, failed_subtree, proof_status, oracle_trace"),
    ], widths=[3.1, 14.4], font_size=7.4)
    add_p(doc, "反馈必须改变行动：输入不守恒→补齐计量空间；@best 欠定→弃权并索取条件化观测；标量 AST 才可进 EML；x=1 一致→下一步改测 x=−1；失配→检查负轴与零边界。固定 Lean 义务通过，但上游 EML reconstruct_ln 含 sorry，只能返回 partial_formalization。", size=8.1)
    add_h(doc, "2.3 记录与预算", 2)
    add_p(doc, "每步向 events.jsonl 写 step/action/feedback/next_action_reason，并记录模型、插件、来源 URL、unknown 与 SHA-256。当前验收模型调用/外网请求均为 0；可选 Harness 每次最多 1 个模型。EML 随机参照共享 5 次预算、20 固定种子；有限映射另测恒等根、g²≠f 与 g(D)⊄D。", size=8.05)
    add_picture(doc, "page2_environment_loop.png", 17.0)
    add_meta(doc, "E1、E2、E5；P1、T1、T2、L1、B1", "类型过滤→插件→oracle→修订；N/S/C/Y/G/P", "确认插件边界、预算与上游 sorry。", "700–800 汉字；2 表1图")

    page_break(doc)

    # PAGE 3
    add_h(doc, "三、发现信号与参照", 1)
    add_h(doc, "3.1 什么算发现", 2)
    add_p(doc, "科学发现须在探索前定义：①封存树中可跨多个输入复现的域/分支失效族；②能定位到最小子树的反例；③稳定 unknown/后端失败；④反例迫使把“全域等价”改成带域、分支和弃权项的契约。每项须保存输入、树、后端版本、轨迹和修订 diff。催化路由与 E1 已报告的负实轴问题都只算环境校准。")
    add_h(doc, "3.2 平凡解/随机/无干预", 2)
    add_table(doc, ["参照", "同预算比较"], [
        ("平凡", "只过 AST/schema；若不给数学反例则不合格。"),
        ("无干预", "固定 1,2,0.5，不按反馈改动作；本轮未发现失败。"),
        ("随机", "同一 7 点池、5 次、20 种子；统计首次失败步数。"),
        ("非平凡", "SymPy continuous_domain；两式实连续域均为 (0,∞)。"),
        ("精确校准", "有限域先查闭合，再逐点查 g(g(x))=f(x)。"),
    ], widths=[3.1, 14.4], font_size=7.45)
    add_h(doc, "3.3 最低成功与失败标准", 2)
    add_p(doc, "技术门槛：反馈改变查询；5 步内捕获已知分支失配与零点未定义；轨迹齐全；闭合先验；测试全过。本轮第2步首次失效、三个负点失配、零点未定义，12/12 测试通过（P1/T1）。")
    add_p(doc, "探索门槛：在封存的其他 EML 树中找到至少一个 E1 未直接报告的稳定失败族，且首次失败步数或有效反例数至少一项严格优于随机中位数。本轮自适应=2、随机中位=2，未达门槛；结论是“环境技术通过，科学发现未通过”。若扩大封存集后仍不胜随机，只能降级为验证工具。", size=8.25)
    add_picture(doc, "page3_baseline_result.png", 17.0)
    add_meta(doc, "E1、E2；P1、T1", "首次失败步数对照，显式标平局", "保留未胜随机、无新发现原判。", "700–800 汉字；1 表1图")

    page_break(doc)

    # PAGE 4
    add_h(doc, "四、最小验证计划", 1)
    add_h(doc, "4.1 一次试跑怎么做", 2)
    add_p(doc, "目标：先验证数学滤镜不把反应、标量目标与几何混为一谈，再验证反馈能从正实一致转向负实反例。输入：默认催化 DSL；冻结 EML ln JSON、7 点池、主分支与 5 次预算。步骤：ReactionDecomposer 配平/守恒/中间体槽位→ObjectiveStructurer 对欠定 @best 弃权→确认 EML not_invoked、GeometryPlugin 独立→运行 EML 自适应/随机/SymPy→保存日志、Lean 与浏览器证据。")
    code = doc.add_paragraph()
    code.paragraph_format.left_indent = Cm(.35); code.paragraph_format.space_after = Pt(2)
    shade_dummy = None
    for i, line in enumerate(("python demo/run_demo.py", "python -m pytest -q demo/test_demo.py panel/test_panel.py", "python panel/serve_panel.py  # open :8766")):
        r = code.add_run(("" if i == 0 else "\n") + line)
        font_run(r, size=7.5, font="Consolas", color=NAVY)
    add_p(doc, "实际结果：Demo 12 项、双面板 11 项及真实 Chrome 桌面/移动验收通过；输出含 KaTeX、N/S/C/Y/G/P、未排名文献候选与示意 2D/3D；默认内核无外网请求、无模型调用。Lean 本地义务通过，上游文件 accepted_with_sorry。", bold_lead="实际结果：", size=8.0)
    add_h(doc, "4.2 主要风险与失败路径", 2)
    add_bullets(doc, [
        "已知例冒充发现：校准集与 holdout 新表达式严格分离。",
        "后端分支差异：SymPy 与递归 cmath 轨迹都保存，不挑有利后端。",
        "采样冒充证明：数值一致不是恒等证明；Lean 含 sorry 即部分形式化。",
        "Agent 伪装：当前是确定性策略；反馈不改变动作即判失败。",
        "基线过弱：下一轮加入固定边界扫描；不得只和随机比。",
        "插件越权：EML 若接到配平、机理或 3D 坐标，路由测试立即失败。",
        "跨域夸张：催化候选/示意构型和 PDE/理论适配器不进入当前科学结论。",
    ], size=7.9)
    add_h(doc, "4.3 复现与开源计划", 2)
    add_p(doc, "公开 demo/、panel/、冻结合同、日志、结果、测试、截图、来源 URL 和 SHA-256；不打包论文 PDF。第三方在 Python 3.14.2 / SymPy 1.14.0 下应复现配平与弃权、EML 第2步失效、随机中位第2步、12+11 项测试和本地 2D/3D 面板。Lean 复跑须保留上游 sorry。", size=8.0)
    add_picture(doc, "page4_reproduction.png", 17.0)
    add_meta(doc, "E1、E2、E5；P1、T1、T2、R1、L1、B1", "输入→运行→日志→测试→Lean/面板", "异机复跑；核对 sorry、截图与哈希。", "700–800 汉字；命令+1图")

    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    build()
