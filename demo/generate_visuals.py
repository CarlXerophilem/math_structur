from pathlib import Path
import json
import math

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "visuals"
OUT.mkdir(parents=True, exist_ok=True)

COLORS = {
    "navy": "#17324D",
    "blue": "#2E6F95",
    "cyan": "#59A5B3",
    "orange": "#E07A5F",
    "gold": "#E9C46A",
    "paper": "#F7F5F0",
    "ink": "#182026",
    "gray": "#66727D",
}


def base(figsize=(8.0, 2.25)):
    fig, ax = plt.subplots(figsize=figsize, dpi=180)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    return fig, ax


def save(fig, name):
    fig.savefig(OUT / name, bbox_inches="tight", facecolor="white", dpi=180)
    plt.close(fig)


def page1_branch_plot():
    data = json.loads((ROOT / "artifacts" / "demo" / "results.json").read_text("utf-8"))
    events = data["adaptive"]["events"]
    xs, compiled, reference = [], [], []
    for e in events:
        f = e["feedback"]
        if f["status"] == "undefined":
            continue
        xs.append(f["input"])
        compiled.append(f["compiled_value"]["imag"])
        reference.append(f["reference_value"]["imag"])
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    xs = [xs[i] for i in order]
    compiled = [compiled[i] for i in order]
    reference = [reference[i] for i in order]
    fig, ax = base((8.0, 2.15))
    ax.plot(xs, reference, "o-", lw=2.2, color=COLORS["blue"], label="principal log(x)")
    ax.plot(xs, compiled, "s--", lw=2.2, color=COLORS["orange"], label="EML-compiled ln(x)")
    ax.axhline(0, color="#CBD2D9", lw=1)
    ax.axvline(0, color="#CBD2D9", lw=1)
    ax.fill_between([-2.2, -0.01], -3.45, 3.45, color=COLORS["gold"], alpha=.16)
    ax.text(-1.95, 0.25, "negative-real branch mismatch", color=COLORS["ink"], fontsize=9)
    ax.set(xlim=(-2.2, 1.2), ylim=(-3.55, 3.55), xlabel="input x", ylabel="imaginary part")
    ax.set_yticks([-math.pi, 0, math.pi], ["−π", "0", "+π"])
    ax.legend(frameon=False, ncol=2, loc="upper right", fontsize=8.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Known EML branch failure reproduced by the demo", loc="left", color=COLORS["navy"], weight="bold")
    save(fig, "page1_branch_mismatch.png")


def flow_boxes(name, title, boxes, accent_indices=()):
    fig, ax = base((8.0, 1.75))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    n = len(boxes); gap = .025; width = (1 - .08 - gap * (n - 1)) / n
    y, h = .25, .43
    for i, text in enumerate(boxes):
        x = .04 + i * (width + gap)
        face = "#EAF2F5" if i not in accent_indices else "#FBECE7"
        edge = COLORS["blue"] if i not in accent_indices else COLORS["orange"]
        patch = FancyBboxPatch((x, y), width, h, boxstyle="round,pad=0.012,rounding_size=0.025", fc=face, ec=edge, lw=1.5)
        ax.add_patch(patch)
        ax.text(x + width/2, y + h/2, text, ha="center", va="center", fontsize=9, color=COLORS["ink"], wrap=True)
        if i < n-1:
            ax.add_patch(FancyArrowPatch((x+width+.004, y+h/2), (x+width+gap-.004, y+h/2), arrowstyle="-|>", mutation_scale=10, color=COLORS["gray"], lw=1.2))
    ax.text(.04, .86, title, fontsize=11, color=COLORS["navy"], weight="bold", va="center")
    save(fig, name)


def page2_loop():
    fig, ax = base((8.0, 2.05))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    ax.text(.04, .91, "Typed multi-space environment: routing precedes solving", fontsize=11,
            color=COLORS["navy"], weight="bold", va="center")

    boxes = [
        ("NL TARGET", "reaction / theorem\n/ PDE"),
        ("MATH FILTER", "types + logic\n+ basis"),
        ("PLUGIN ROUTE", "reaction / scalar\n/ geometry"),
        ("ORACLE", "evidence / proof\n/ unknown"),
        ("REVISE", "next task\n+ 2D/3D"),
    ]
    gap = .018
    width = (1 - .08 - gap * (len(boxes) - 1)) / len(boxes)
    y, h = .42, .30
    for i, (heading, detail) in enumerate(boxes):
        x = .04 + i * (width + gap)
        accent = i == 3
        patch = FancyBboxPatch(
            (x, y), width, h,
            boxstyle="round,pad=0.009,rounding_size=0.020",
            fc="#FBECE7" if accent else "#EAF2F5",
            ec=COLORS["orange"] if accent else COLORS["blue"],
            lw=1.45,
        )
        ax.add_patch(patch)
        ax.text(x + width / 2, y + .19, heading, ha="center", va="center",
                fontsize=8.4, weight="bold", color=COLORS["navy"])
        ax.text(x + width / 2, y + .090, detail, ha="center", va="center",
                fontsize=6.25, color=COLORS["ink"], linespacing=1.05)
        if i < len(boxes) - 1:
            ax.add_patch(FancyArrowPatch(
                (x + width + .002, y + h / 2),
                (x + width + gap - .002, y + h / 2),
                arrowstyle="-|>", mutation_scale=9, color=COLORS["gray"], lw=1.0,
            ))

    labels = [
        ("N", "language"), ("S", "stoich."), ("C", "candidates"),
        ("Y", "measure."), ("G", "geometry"), ("P", "proof"),
    ]
    chip_gap = .012
    chip_w = (1 - .08 - chip_gap * (len(labels) - 1)) / len(labels)
    for i, (symbol, label) in enumerate(labels):
        x = .04 + i * (chip_w + chip_gap)
        patch = FancyBboxPatch((x, .13), chip_w, .14,
                               boxstyle="round,pad=0.005,rounding_size=0.012",
                               fc="#F7F5F0", ec="#CBD2D9", lw=.9)
        ax.add_patch(patch)
        ax.text(x + .018, .20, symbol, ha="left", va="center", fontsize=8.0,
                weight="bold", color=COLORS["blue"])
        ax.text(x + chip_w - .012, .20, label, ha="right", va="center",
                fontsize=6.6, color=COLORS["gray"])
    ax.text(.04, .045, "Typed partial maps connect spaces; KaTeX and geometry are views, not proofs.",
            fontsize=7.0, color=COLORS["gray"])
    save(fig, "page2_environment_loop.png")


def page3_baselines():
    data = json.loads((ROOT / "artifacts" / "demo" / "results.json").read_text("utf-8"))
    adaptive = 2
    random_median = data["random_baseline"]["median_first_failure_step"]
    values = [adaptive, random_median, 6]
    labels = ["adaptive", "random\nmedian", "no intervention"]
    colors = [COLORS["blue"], COLORS["cyan"], "#B8C1C8"]
    fig, ax = base((8.0, 2.15))
    bars = ax.bar(labels, values, color=colors, width=.56)
    for i, (bar, value) in enumerate(zip(bars, values)):
        label = "missed within budget" if i == 2 else f"step {value}"
        ax.text(bar.get_x()+bar.get_width()/2, value+.12, label, ha="center", fontsize=9, color=COLORS["ink"])
    ax.axhline(5, color=COLORS["orange"], lw=1.2, ls="--")
    ax.text(2.35, 5.08, "budget = 5", fontsize=8.5, color=COLORS["orange"], ha="right")
    ax.set_ylim(0, 6.6); ax.set_ylabel("first failure step (lower is earlier)")
    ax.set_title("Pilot result: adaptive ties the random median; no superiority claim", loc="left", color=COLORS["navy"], weight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "page3_baseline_result.png")


def page4_reproduce():
    flow_boxes(
        "page4_reproduction.png",
        "Reproducible minimum run: interface stress test + scientific slice",
        ["frozen\nreaction + EML", "demo + panel\nlocal kernel", "JSON / JSONL\nscreenshots", "pytest\n12 + 11 pass", "Lean boundary\nlocal pass\nupstream sorry"],
        accent_indices=(4,),
    )


if __name__ == "__main__":
    page1_branch_plot()
    page2_loop()
    page3_baselines()
    page4_reproduce()
    for p in sorted(OUT.glob("*.png")):
        print(p.relative_to(ROOT), p.stat().st_size)
