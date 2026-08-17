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
        ("观察", "反应物 R、产物 P\n能量记录 ΔE 或 null\n文献／记录 ID\n带来源的空间坐标"),
        ("行动", "查 DOI／alphaXiv\n查询公共数据库\n筛选与稳定排序\n绘制带记录 ID 坐标"),
        ("反馈", "新增／冲突／不可用\n能量字段是否可比\n几何范围与许可\n接口状态"),
        ("记录", "URL、记录 ID、时间\n单位／类型／方法\n参考态与坐标来源\n失败及下一查询"),
        ("预算", "本地 Qwen ≤ 1 次\n快照外网 0 次\n实时接口逐项留据\n探索最多 6 轮"),
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
            "固定规则：@best 只改变检索顺序；无单位、类型、方法、参考态和来源的能量保持 null；仅绘制带记录 ID 的坐标。",
            color=GRAY, fontsize=7.6)
    save(fig, "page2_environment_interface.png")


def page3_discovery() -> None:
    fig, ax = plt.subplots(figsize=(8.3, 3.25), dpi=210)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.text(.025, .965, "发现信号：同一反应实体下可复核的能量—几何证据关系", color=NAVY, fontsize=12, weight="bold", va="top")
    ax.text(.025, .895,
            r"$\mathcal{R}_{R,P}=\{r:\mathrm{match}(r;R,P)=1,\ \mathrm{source}(r)\neq\emptyset\}$；"
            r"$\Delta E_r=(v,u,k,m,s_0,URL)$，任一字段缺失即记为 unknown。",
            color=BLUE, fontsize=9.2, va="top")

    signals = [
        ("正向", "至少两个独立来源支持同一\n结构—能量关系，且分层后复现"),
        ("稳定负结果", "同预算记录均缺可比能量；\n明确数据缺口与下一接口"),
        ("异常／反例", "同名能量实为不同 kind／\n参考态，或几何仅是体相支撑体"),
        ("问题修正", "反馈把下一轮从性能猜测\n改为指定记录、字段或几何检索"),
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
            "DOI／alphaXiv 与公共接口留收据；未知能量为 null；\n本地合同与人工终审通过；反馈改变下一查询。",
            fontsize=7.0, color=INK, va="top", linespacing=1.35)
    ax.text(.54, .375, "科学发现通过", fontsize=8.6, weight="bold", color=NAVY, va="top")
    ax.text(.54, .315,
            "出现确定性检索基线没有的可核验结构—能量关系，\n或稳定数据缺口；经独立来源与方法／参考态分层复现。",
            fontsize=7.0, color=INK, va="top", linespacing=1.35)

    ax.text(.025, .105,
            "当前试跑：取得体相支撑体几何和文献候选，但无可比反应能量；下一轮转向授权记录查询。",
            fontsize=7.8, color=ORANGE, weight="bold")
    ax.text(.025, .045,
            "明确失败：补写能量、把检索顺序冒充性能最佳、把体相支撑体冒充活性位，或反馈不改变下一查询。",
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
