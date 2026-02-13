import re
import json
import ast
import unicodedata
from collections import defaultdict
from typing import Any, Dict, List, Set, Tuple

import pandas as pd


# -----------------------------
# 1) Normalization helpers
# -----------------------------
_GREEK_MAP = {
    "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta",
    "ε": "epsilon", "κ": "kappa", "λ": "lambda", "μ": "mu",
    "π": "pi", "ρ": "rho", "σ": "sigma", "τ": "tau",
    "φ": "phi", "ω": "omega"
}

def normalize_text(s: str) -> str:
    """
    Normalize a term for robust matching:
    - Unicode normalize + strip diacritics
    - lower case
    - remove parenthetical content
    - replace Greek letters
    - remove all non-alphanumeric chars
    """
    if s is None:
        return ""
    s = str(s).strip()
    if not s:
        return ""

    # Unicode normalize + remove diacritics
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))

    # Replace Greek letters
    for g, rep in _GREEK_MAP.items():
        s = s.replace(g, rep)

    # Remove content in parentheses (often qualifiers)
    s = re.sub(r"\([^)]*\)", " ", s)

    s = s.lower()

    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()

    # Remove special characters (keep only a-z0-9)
    s = re.sub(r"[^a-z0-9]+", "", s)

    return s


def split_entity_variants(ent: str) -> List[str]:
    """
    Try a few conservative splits to salvage matches:
    - split by ; , /
    - also try removing trailing qualifiers after ' of ' (common in long phrases)
    """
    if ent is None:
        return []
    ent = str(ent).strip()
    if not ent:
        return []

    variants = [ent]

    # Split by separators
    parts = re.split(r"[;,/]", ent)
    parts = [p.strip() for p in parts if p.strip()]
    variants.extend(parts)

    # Try shortening "X of Y" -> Y (often the real anatomy term)
    # e.g., "cortical region of the collecting duct" -> "collecting duct"
    m = re.search(r"\bof\b(.+)$", ent, flags=re.IGNORECASE)
    if m:
        tail = m.group(1).strip()
        # remove leading articles
        tail = re.sub(r"^(the|a|an)\s+", "", tail, flags=re.IGNORECASE).strip()
        if tail:
            variants.append(tail)

    # Deduplicate while preserving order
    seen = set()
    out = []
    for v in variants:
        if v not in seen:
            out.append(v)
            seen.add(v)
    return out


# -----------------------------
# 2) Parsing helpers (cells -> entities list)
# -----------------------------
def _try_parse_obj(s: str) -> Any:
    """
    Try parsing a string into Python object:
    - json.loads
    - ast.literal_eval (for single quotes, etc.)
    """
    s = s.strip()
    if not s:
        return None

    # Some CSV cells may contain escaped quotes or be wrapped
    # Try JSON first
    try:
        return json.loads(s)
    except Exception:
        pass

    # Try Python literal
    try:
        return ast.literal_eval(s)
    except Exception:
        return None


def extract_entities(cell: Any) -> List[str]:
    """
    Robustly extract entities list from a cell like:
      - {"entities": [...]}
      - [{"entities": [...]}]
      - stringified versions of the above
    """
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return []

    # If already a Python object (rare)
    obj = cell
    if isinstance(cell, str):
        obj = _try_parse_obj(cell)
        if obj is None:
            # fallback: treat raw string as a single entity
            return [cell.strip()] if cell.strip() else []

    # Unwrap if it's a list of dicts
    if isinstance(obj, list):
        ents = []
        for item in obj:
            if isinstance(item, dict) and "entities" in item:
                ents.extend(item.get("entities") or [])
            elif isinstance(item, str):
                ents.append(item)
        return [str(e).strip() for e in ents if str(e).strip()]

    # Dict with entities
    if isinstance(obj, dict):
        ents = obj.get("entities", [])
        if isinstance(ents, list):
            return [str(e).strip() for e in ents if str(e).strip()]
        # if entities is a string, split conservatively
        if isinstance(ents, str):
            return [e.strip() for e in re.split(r"[;,]", ents) if e.strip()]

    # Fallback: if parsed into string/other
    if isinstance(obj, str):
        return [obj.strip()] if obj.strip() else []

    return []


# -----------------------------
# 3) Build UBERON synonym index
# -----------------------------
def build_uberon_index(uberon_csv_path: str) -> Dict[str, Set[str]]:
    uberon = pd.read_csv(uberon_csv_path)

    # Try to be tolerant to column name variations
    col_id = None
    col_label = None
    col_syn = None
    for c in uberon.columns:
        lc = c.strip().lower()
        if lc in {"class id", "classid", "id", "iri"}:
            col_id = c
        elif lc in {"preferred label", "label", "preferredlabel"}:
            col_label = c
        elif lc in {"synonyms", "synonym"}:
            col_syn = c

    if col_id is None or col_label is None:
        raise ValueError(f"Cannot find required columns in UBERON CSV. "
                         f"Found columns={list(uberon.columns)}. "
                         f"Need at least 'Class ID' and 'Preferred Label'.")

    index = defaultdict(set)

    for _, row in uberon.iterrows():
        uberon_id = str(row[col_id]).strip()
        label = str(row[col_label]).strip() if not pd.isna(row[col_label]) else ""

        candidates = []
        if label:
            candidates.append(label)

        if col_syn is not None and (not pd.isna(row[col_syn])):
            syn_field = str(row[col_syn]).strip()
            if syn_field:
                # UBERON exports often use '|' delimiter
                syns = [s.strip() for s in syn_field.split("|") if s.strip()]
                candidates.extend(syns)

        for term in candidates:
            key = normalize_text(term)
            if key:
                index[key].add(uberon_id)

    return dict(index)


# -----------------------------
# 4) Map entities -> UBERON IDs
# -----------------------------
def map_entities_to_uberon_ids(entities: List[str], index: Dict[str, Set[str]]) -> Set[str]:
    out_ids: Set[str] = set()

    for ent in entities:
        # Try multiple variants (splits, tail after "of", etc.)
        for variant in split_entity_variants(ent):
            key = normalize_text(variant)
            if not key:
                continue
            if key in index:
                out_ids |= index[key]

    return out_ids


# -----------------------------
# 5) Metrics
# -----------------------------
def prf1(pred: Set[str], gold: Set[str]) -> Tuple[float, float, float, int, int, int]:
    tp = len(pred & gold)
    fp = len(pred - gold)
    fn = len(gold - pred)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return precision, recall, f1, tp, fp, fn


# -----------------------------
# 6) Main pipeline
# -----------------------------
def evaluate_uberon_id_level(
    uberon_csv_path: str,
    predictions_csv_path: str,
    out_csv_path: str = "uberon_id_level_eval.csv",
    gt_col: str = "answer",
    model_cols: List[str] = None,
) -> None:
    if model_cols is None:
        model_cols = ["llama31", "llama32", "qwen", "gemma"]

    df = pd.read_csv(predictions_csv_path)

    missing = [c for c in [gt_col] + model_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns in predictions CSV: {missing}. "
                         f"Found columns={list(df.columns)}")

    index = build_uberon_index(uberon_csv_path)

    # Prepare output columns
    df_out = df.copy()

    # Per-row mapped ID sets (stored as sorted, ';'-joined strings)
    gt_ids_list = []
    model_ids_map = {m: [] for m in model_cols}

    # Per-row metrics
    metrics_map = {m: {"P": [], "R": [], "F1": [], "TP": [], "FP": [], "FN": []} for m in model_cols}

    for _, row in df.iterrows():
        gt_entities = extract_entities(row[gt_col])
        gt_ids = map_entities_to_uberon_ids(gt_entities, index)
        gt_ids_list.append(";".join(sorted(gt_ids)))

        for m in model_cols:
            pred_entities = extract_entities(row[m])
            pred_ids = map_entities_to_uberon_ids(pred_entities, index)
            model_ids_map[m].append(";".join(sorted(pred_ids)))

            p, r, f1, tp, fp, fn = prf1(pred_ids, gt_ids)
            metrics_map[m]["P"].append(p)
            metrics_map[m]["R"].append(r)
            metrics_map[m]["F1"].append(f1)
            metrics_map[m]["TP"].append(tp)
            metrics_map[m]["FP"].append(fp)
            metrics_map[m]["FN"].append(fn)

    df_out["answer_UBERON_IDs"] = gt_ids_list
    for m in model_cols:
        df_out[f"{m}_UBERON_IDs"] = model_ids_map[m]
        df_out[f"{m}_P_id"] = metrics_map[m]["P"]
        df_out[f"{m}_R_id"] = metrics_map[m]["R"]
        df_out[f"{m}_F1_id"] = metrics_map[m]["F1"]
        df_out[f"{m}_TP_id"] = metrics_map[m]["TP"]
        df_out[f"{m}_FP_id"] = metrics_map[m]["FP"]
        df_out[f"{m}_FN_id"] = metrics_map[m]["FN"]

    df_out.to_csv(out_csv_path, index=False)

    # Summary: micro + macro
    print("=== ID-level evaluation (UBERON) ===")
    for m in model_cols:
        # Micro
        TP = sum(metrics_map[m]["TP"])
        FP = sum(metrics_map[m]["FP"])
        FN = sum(metrics_map[m]["FN"])
        micro_p = TP / (TP + FP) if (TP + FP) else 0.0
        micro_r = TP / (TP + FN) if (TP + FN) else 0.0
        micro_f1 = (2 * micro_p * micro_r / (micro_p + micro_r)) if (micro_p + micro_r) else 0.0

        # Macro (mean of per-row)
        macro_p = sum(metrics_map[m]["P"]) / len(metrics_map[m]["P"]) if metrics_map[m]["P"] else 0.0
        macro_r = sum(metrics_map[m]["R"]) / len(metrics_map[m]["R"]) if metrics_map[m]["R"] else 0.0
        macro_f1 = sum(metrics_map[m]["F1"]) / len(metrics_map[m]["F1"]) if metrics_map[m]["F1"] else 0.0

        print(f"\nModel: {m}")
        print(f"  Micro  P/R/F1: {micro_p:.4f} / {micro_r:.4f} / {micro_f1:.4f}")
        print(f"  Macro  P/R/F1: {macro_p:.4f} / {macro_r:.4f} / {macro_f1:.4f}")
        print(f"  Totals TP/FP/FN: {TP} / {FP} / {FN}")

    print(f"\nSaved detailed results to: {out_csv_path}")

    # -----------------------------
    # Summary: micro + macro table (for plotting)
    # -----------------------------
    summary_rows = []
    for m in model_cols:
        # Micro
        TP = int(sum(metrics_map[m]["TP"]))
        FP = int(sum(metrics_map[m]["FP"]))
        FN = int(sum(metrics_map[m]["FN"]))
        micro_p = TP / (TP + FP) if (TP + FP) else 0.0
        micro_r = TP / (TP + FN) if (TP + FN) else 0.0
        micro_f1 = (2 * micro_p * micro_r / (micro_p + micro_r)) if (micro_p + micro_r) else 0.0

        # Macro
        n = len(metrics_map[m]["P"])
        macro_p = (sum(metrics_map[m]["P"]) / n) if n else 0.0
        macro_r = (sum(metrics_map[m]["R"]) / n) if n else 0.0
        macro_f1 = (sum(metrics_map[m]["F1"]) / n) if n else 0.0

        summary_rows.append({
            "model": m,
            "micro_P": micro_p,
            "micro_R": micro_r,
            "micro_F1": micro_f1,
            "macro_P": macro_p,
            "macro_R": macro_r,
            "macro_F1": macro_f1,
            "TP_total": TP,
            "FP_total": FP,
            "FN_total": FN,
            "n_samples": n,
        })

    summary_df = pd.DataFrame(summary_rows).sort_values("model")
    print("\n=== UBERON ID-level summary (micro/macro) ===")
    print(summary_df.to_string(index=False))

    summary_path = out_csv_path.replace(".csv", "_summary.csv")
    summary_df.to_csv(summary_path, index=False)
    print(f"\nSaved summary to: {summary_path}")


if __name__ == "__main__":
    # TODO: replace these paths with your actual files
    UBERON_PATH = r"data\bio-onto\cl.csv"            # your UBERON table
    PRED_PATH = r"data\bio-onto\biology-ontology-test-results.csv"         # your combined CSV with answer + model columns

    evaluate_uberon_id_level(
        uberon_csv_path=UBERON_PATH,
        predictions_csv_path=PRED_PATH,
        out_csv_path=r"data\vis-source-data\sf-7b-cl_level_eval.csv",
        gt_col="answer",
        model_cols=["llama31", "llama32", "qwen", "gemma"],
    )
