from __future__ import annotations

from pathlib import Path
import json
import shutil

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "visuals"
PANEL_ARTIFACTS = ROOT / "artifacts" / "panel"
OUT.mkdir(parents=True, exist_ok=True)

mpl.rcParams["font.family"] = ["Microsoft YaHei", "DejaVu Sans"]
mpl.rcParams["axes.unicode_minus"] = False

NAVY = "#0D2538"
BLUE = "#245F83"
ORANGE = "#E77859"
GOLD = "#E9C46A"
PALE = "#EDF3F4"
PAPER = "#FBFAF7"
GRAY = "#66727D"
INK = "#182026"


def save(fig: plt.Figure, name: str) -> None:
    fig.savefig(OUT / name, dpi=210, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def box(ax, x, y, w, h, title, body, accent=BLUE):
    patch = FancyBboxPatch(
        (x, y), w, h,
        boxstyle="round,pad=0.012,rounding_size=0.020",
        facecolor=PAPER, edgecolor=accent, linewidth=1.5,
    )
    ax.add_patch(patch)
    ax.text(x + .018, y + h - .052, title, color=NAVY, fontsize=9.1, weight="bold", va="top")
    ax.text(x + .018, y + h - .115, body, color=INK, fontsize=7.4, va="top", linespacing=1.35)


def page1_demo_crop() -> None:
    source = PANEL_ARTIFACTS / "panel_desktop_general_slice.png"
    if source.is_file() and Image.open(source).height >= 500:
        shutil.copyfile(source, OUT / "page1_demo_slice.png")
        return
    fallback = Image.open(PANEL_ARTIFACTS / "panel_desktop_general_2d.png")
    receipt_path = PANEL_ARTIFACTS / "browser_acceptance.json"
    if receipt_path.is_file():
        receipt = json.loads(receipt_path.read_text("utf-8"))
        region = receipt.get("assertions", {}).get("general", {}).get("slice", {})
        x = int(region.get("x", 22))
        y = int(region.get("y", 735))
        width = int(region.get("width", fallback.width - 44))
        height = int(region.get("height", 615))
        crop = fallback.crop((x, y, x + width, y + height))
    else:
        crop = fallback.crop((22, 735, fallback.width - 22, 1350))
    crop.save(OUT / "page1_demo_slice.png", optimize=True)


def page2_environment() -> None:
    fig, ax = plt.subplots(figsize=(8.3, 2.7), dpi=210)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.text(.025, .955, "环境接口：每一步都是带类型的部分映射", color=NAVY, fontsize=12, weight="bold", va="top")
    ax.text(.025, .895, r"$b_i:X_i\rightharpoonup X_j,\quad z_{t+1}=b_{i_t}(z_t)$".replace("\\\\", "\\"), color=BLUE, fontsize=10.5, va="top")

    items = [
        ("观察", "原始目标 q₀\n物种、相态、条件 θ\n候选域 Cθ、来源状态"),
        ("行动", "配平与守恒\n补齐／收缩条件域\n检索、几何、证明义务"),
        ("反馈", "通过／否证／未知\n缺失字段与守恒余量\n来源位置、反例、超时"),
        ("记录", "目标与算子版本\n输入输出哈希、下一动作\n失败状态与证据轨迹"),
        ("预算", "本地 Qwen3-8B ≤ 1 次\n远端后端显式选一\n文献 ≤ 8 次；探索 ≤ 6 轮"),
    ]
    n = len(items)
    gap = .018
    width = (.95 - gap * (n - 1)) / n
    y, h = .38, .40
    for i, (title, body) in enumerate(items):
        x = .025 + i * (width + gap)
        box(ax, x, y, width, h, title, body, ORANGE if title == "反馈" else BLUE)
        if i < n - 1:
            ax.add_patch(FancyArrowPatch(
                (x + width + .002, y + h / 2), (x + width + gap - .002, y + h / 2),
                arrowstyle="-|>", mutation_scale=10, color=GRAY, linewidth=1.1,
            ))

    ax.add_patch(FancyArrowPatch(
        (.765, .325), (.20, .325), connectionstyle="arc3,rad=-.18",
        arrowstyle="-|>", mutation_scale=12, color=ORANGE, linewidth=1.4,
    ))
    ax.text(.485, .16, "反馈必须改变下一轮算子、搜索区域或问题定义", color=ORANGE,
            fontsize=8.5, weight="bold", ha="center")
    ax.text(.025, .045,
            "固定规则：未经配平不得排名；目标欠定不得补写“最佳”；无坐标来源只能显示示意构型；含占位符不得标为证明。",
            color=GRAY, fontsize=7.6)
    save(fig, "page2_environment_interface.png")


def page3_discovery() -> None:
    fig, ax = plt.subplots(figsize=(8.3, 3.25), dpi=210)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.text(.025, .965, "发现不是材料名称，而是可被反驳的条件—结构关系", color=NAVY, fontsize=12, weight="bold", va="top")
    ax.text(.025, .895,
            r"$\mathcal{F}(\theta)=\{c\in C_\theta:A\nu=0,\ h_j(c;\theta)=0,\ q_i(c;\theta)\leq0\}$；"
            r"$\mathcal{F}=\varnothing$ 即无可行解，$|\arg\max J|>1$ 即非唯一。".replace("\\\\", "\\"),
            color=BLUE, fontsize=9.2, va="top")

    signals = [
        ("正向", "冻结 θ、Cθ 与指标后，\n结构关系跨条件扰动复现"),
        ("稳定负结果", "同预算下候选均违反\n同一条已声明约束"),
        ("异常／反例", "预期可行的候选被守恒、\n来源或专业验证器否证"),
        ("问题修正", "@best 因条件和测量缺失\n被改写为下一次可运行查询"),
    ]
    for i, (title, body) in enumerate(signals):
        x = .025 + i * .242
        box(ax, x, .535, .22, .235, title, body, ORANGE if i in {1, 2} else BLUE)

    ax.text(.025, .455, "两级成功标准（不可混同）", color=NAVY, fontsize=8.7, weight="bold", va="top")
    tech = FancyBboxPatch((.025, .165), .455, .245, boxstyle="round,pad=.012,rounding_size=.018",
                          facecolor=PALE, edgecolor=BLUE, linewidth=1.3)
    science = FancyBboxPatch((.52, .165), .455, .245, boxstyle="round,pad=.012,rounding_size=.018",
                             facecolor="#FFF4EE", edgecolor=ORANGE, linewidth=1.3)
    ax.add_patch(tech)
    ax.add_patch(science)
    ax.text(.045, .375, "环境技术通过（不等于科学发现）", fontsize=8.6, weight="bold", color=NAVY, va="top")
    ax.text(.045, .315,
            "文献穿透＋本地结构核验＋人工终审；\n零守恒错误、零无来源性能主张；至少一次反馈改变下一动作。",
            fontsize=7.0, color=INK, va="top", linespacing=1.35)
    ax.text(.54, .375, "科学发现通过", fontsize=8.6, weight="bold", color=NAVY, va="top")
    ax.text(.54, .315,
            "冻结 θ、Cθ、J 与预算后，出现确定性基线没有的\n可核验关系或稳定负结果，并经预注册扰动复现。",
            fontsize=7.0, color=INK, va="top", linespacing=1.35)

    ax.text(.025, .105,
            "当前 @best：只取得问题修正与接口信号；科学发现闸门未通过。",
            fontsize=7.8, color=ORANGE, weight="bold")
    ax.text(.025, .045,
            "明确失败：无条件排名、元数据冒充实验结论、反馈不改动作，或结果不超过同预算确定性基线。",
            fontsize=7.5, color=GRAY)
    save(fig, "page3_discovery_gates.png")


def page4_reproduction() -> None:
    source = PANEL_ARTIFACTS / "panel_desktop_iterate.png"
    shutil.copyfile(source, OUT / "page4_function_space_screenshot.png")


if __name__ == "__main__":
    page1_demo_crop()
    page2_environment()
    page3_discovery()
    page4_reproduction()
    for path in sorted(OUT.glob("*.png")):
        print(path.relative_to(ROOT), path.stat().st_size)
