import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial'],
    'font.size': 10,
    'axes.labelsize': 10,
    'axes.titlesize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'axes.linewidth': 0.5,
    'xtick.major.width': 0.5,
    'ytick.major.width': 0.5,
    'xtick.major.size': 2,
    'ytick.major.size': 2
})


MODELS = ["llama31", "llama32", "qwen", "gemma"]
CATS = [("AS", "AS"), ("CT", "CT"), ("B", "B")]  # (label, column-name-in-plot)

def _compute_micro_from_tp_fp_fn(tp: int, fp: int, fn: int):
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * p * r / (p + r)) if (p + r) else 0.0
    return p, r, f1

def load_micro_table(path: str, category_label: str, models=MODELS) -> pd.DataFrame:
    """
    Returns a DataFrame with columns: model, category, P, R, F1
    Works for:
      (A) summary CSV: columns like model, micro_P, micro_R, micro_F1
      (B) detailed CSV: columns like llama31_TP_id, llama31_FP_id, llama31_FN_id ...
    """
    df = pd.read_csv(path)

    # Case A: summary format
    if ("model" in df.columns) and any(c in df.columns for c in ["micro_P", "micro_R", "micro_F1"]):
        # Try best-effort column mapping
        def pick(col_candidates):
            for c in col_candidates:
                if c in df.columns:
                    return c
            raise ValueError(f"Cannot find any of {col_candidates} in {path}. Columns={list(df.columns)}")

        colP = pick(["micro_P", "Micro_P", "P_micro", "P"])
        colR = pick(["micro_R", "Micro_R", "R_micro", "R"])
        colF = pick(["micro_F1", "Micro_F1", "F1_micro", "F1"])

        out = df[["model", colP, colR, colF]].copy()
        out.columns = ["model", "P", "R", "F1"]
        out["category"] = category_label
        return out[["model", "category", "P", "R", "F1"]]

    # Case B: detailed eval format with TP/FP/FN per model
    rows = []
    for m in models:
        tp_col = f"{m}_TP_id"
        fp_col = f"{m}_FP_id"
        fn_col = f"{m}_FN_id"
        if tp_col not in df.columns or fp_col not in df.columns or fn_col not in df.columns:
            raise ValueError(
                f"Detailed CSV is missing TP/FP/FN columns for model={m} in {path}. "
                f"Need: {tp_col}, {fp_col}, {fn_col}. Columns={list(df.columns)}"
            )

        tp = int(df[tp_col].fillna(0).sum())
        fp = int(df[fp_col].fillna(0).sum())
        fn = int(df[fn_col].fillna(0).sum())
        p, r, f1 = _compute_micro_from_tp_fp_fn(tp, fp, fn)

        rows.append({"model": m, "category": category_label, "P": p, "R": r, "F1": f1})

    return pd.DataFrame(rows)

def plot_metric(all_micro: pd.DataFrame, metric: str, outfile: str = None):
    """
    all_micro columns: model, category, P, R, F1
    metric in {"P","R","F1"}
    """
    # pivot: index=model, columns=category, values=metric
    pivot = all_micro.pivot_table(index="model", columns="category", values=metric, aggfunc="mean")

    # ensure order
    pivot = pivot.reindex(MODELS)
    for cat, _ in CATS:
        if cat not in pivot.columns:
            pivot[cat] = np.nan
    pivot = pivot[[c[0] for c in CATS]]

    x = np.arange(len(pivot.index))
    width = 0.25

    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    for i, (cat, cat_display) in enumerate(CATS):
        ax.bar(x + (i - 1) * width, pivot[cat].values, width, label=cat_display)

    ax.set_xticks(x)
    ax.set_xticklabels(pivot.index)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel(metric)
    ax.set_title(f"Micro {metric} (ID-level) across AS / CT / B by model")
    ax.legend()
    plt.tight_layout()

    if outfile:
        plt.savefig(outfile, dpi=300)
    plt.show()

if __name__ == "__main__":
    # ====== TODO: 改成你自己的三个CSV路径 ======
    AS_CSV = r"data\vis-source-data\sf-7a-uberon_id_level_eval_summary.csv"   # 可以是 as_summary.csv 或 as_eval.csv（详细TP/FP/FN那种也行）
    CT_CSV = r"data\vis-source-data\sf-7b-cl_level_eval_summary.csv"
    B_CSV  = r"data\vis-source-data\sf-7c-b_level_eval_summary.csv"
    # ========================================

    as_micro = load_micro_table(AS_CSV, "AS")
    ct_micro = load_micro_table(CT_CSV, "CT")
    b_micro  = load_micro_table(B_CSV,  "B")

    all_micro = pd.concat([as_micro, ct_micro, b_micro], ignore_index=True)

    # 打印数值表（方便你检查）
    print("\n=== Micro P/R/F1 table ===")
    print(all_micro.sort_values(["category", "model"]).to_string(index=False))

    # 画三张图：P / R / F1
    plot_metric(all_micro, "P",  outfile="micro_precision_as_ct_b.png")
    plot_metric(all_micro, "R",  outfile="micro_recall_as_ct_b.png")
    plot_metric(all_micro, "F1", outfile="micro_f1_as_ct_b.png")
