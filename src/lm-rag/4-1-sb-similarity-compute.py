"""
Calculate Jaccard similarity between extracted JSON entities from model responses and ground-truth answers
for multiple model output files.
"""
import json
import re
import pandas as pd
from pathlib import Path

# Models to process
MODEL_KEYS = ['qwen', 'llama32', 'gemma', 'llama31']

# Regex for extracting JSON entities
JSON_PATTERN_MARKDOWN = re.compile(r'```json\s*\n(.*?)\n```', re.DOTALL)
JSON_PATTERN_INLINE = re.compile(r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}')


def extract_ds_query_entities(text):
    """Extract JSON-like entities from text."""
    # 1) JSON in markdown code block
    m = JSON_PATTERN_MARKDOWN.search(text)
    if m:
        try:
            parsed = json.loads(m.group(1).strip())
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                # flatten dict values
                out = []
                for v in parsed.values():
                    if isinstance(v, list):
                        out.extend(v)
                return out
        except json.JSONDecodeError:
            pass

    # 2) Inline JSON objects
    matches = JSON_PATTERN_INLINE.findall(text)
    objs = []
    for s in matches:
        try:
            objs.append(json.loads(s))
        except json.JSONDecodeError:
            continue
    return objs


def jaccard_similarity(list1, list2):
    """Compute Jaccard similarity between two lists."""
    set1, set2 = set(list1), set(list2)
    if not set1 and not set2:
        return 1.0
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union)


def calculate_key_value_similarity(list_a, list_b, keys):
    """Compute Jaccard similarity for specified keys between two lists of dicts."""
    scores = {}
    for key in keys:
        vals_a = [item.get(key) for item in list_a if isinstance(item, dict) and key in item]
        vals_b = [item.get(key) for item in list_b if isinstance(item, dict) and key in item]
        scores[key] = jaccard_similarity(vals_a, vals_b)
    return scores


def process_model(model_key, sample_df, keys):
    """Compute similarity for one model and save output file."""
    resp_file = Path(f"data/{model_key}.xlsx")
    if not resp_file.exists():
        print(f"[Warning] Response file not found for {model_key}: {resp_file}")
        return
    response_df = pd.read_excel(resp_file)

    # Merge records on caption/content
    merged = sample_df.merge(
        response_df,
        left_on="caption",
        right_on="content",
        how="inner"
    )

    # Initialize similarity columns
    for key in keys:
        merged[f"{key}_similarity"] = None

    # Compute per-record similarity
    for idx, row in merged.iterrows():
        answer_str = row.get("Answer", "")
        response_text = row.get("response", "")

        extracted = extract_ds_query_entities(response_text)
        try:
            gt = json.loads(answer_str)
            ground_truth = gt if isinstance(gt, list) else [gt]
        except json.JSONDecodeError:
            ground_truth = []

        sim_scores = calculate_key_value_similarity(extracted, ground_truth, keys)
        for k, score in sim_scores.items():
            merged.at[idx, f"{k}_similarity"] = score

    # Save per-model similarity
    out_file = Path(f"{model_key}_similarity.xlsx")
    merged.to_excel(out_file, index=False)
    print(f"Similarity results saved to {out_file}")


def main():
    # Load ground truth samples
    sample_path = Path("data/scale-bar/scale-bar-sample.xlsx")
    if not sample_path.exists():
        print(f"Sample file not found: {sample_path}")
        return
    sample_df = pd.read_csv(sample_path)
    print(f"Loaded {len(sample_df)} sample records.")

    keys = ["Descriptor Type", "Value", "Units", "Notes", "Panel"]

    # Process each model
    for mk in MODEL_KEYS:
        print(f"Processing model: {mk}")
        process_model(mk, sample_df, keys)


if __name__ == "__main__":
    main()
