#!/usr/bin/env python3
# 6-3-fastgpt-imgtype-test.py

import os
import re
import json
import uuid
import time
import requests
import threading
import argparse
import pandas as pd
from tqdm import tqdm

# ===== Configuration via CLI args =====
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--token', type=str, required=True, help='FastGPT auth token')
    parser.add_argument('--api-url', type=str, required=True, help='FastGPT API URL (e.g., http://host:port/api/v1/chat/completions)')
    parser.add_argument('--prompt-file', type=str, default='data/img-type/prompt.txt', help='Path to single prompt file')
    parser.add_argument('--fig-info', type=str, default='data/img-type/all_figures_info.json', help='Path to figures info JSON')
    parser.add_argument('--vision-responses-csv', type=str, default='data/img-entity/img_type_lvm_test_results.csv', help='CSV with vision model responses (must include image_file and response columns)')
    parser.add_argument('--image-root', type=str, default='data/img-type/test-data', help='Root dir of test images')
    parser.add_argument('--answer-csv', type=str, default='data/img-type/img-type-test-answer.csv', help='CSV with image_file,image_type')
    parser.add_argument('--output-csv', type=str, default='data/img-entity/img_type_hybrid_test_results.csv', help='Path to output CSV')
    parser.add_argument('--max-threads', type=int, default=5, help='Max concurrent threads per model')
    return parser.parse_args()

# ===== FastGPT API Call =====
def fastgpt_call(api_url, token, model, question, prompt):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    payload = {
        'messages': [{'role': 'user', 'content': question}],
        'variables': {'model': model, 'prompt': prompt},
        'chatId': str(uuid.uuid4())
    }
    try:
        resp = requests.post(api_url, headers=headers, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        if data.get('code') in (500, 403):
            return ''
        choices = data.get('data', {}).get('choices', [])
        if choices:
            return choices[0].get('message', {}).get('content', '').strip()
    except Exception:
        return ''
    return ''

# ===== JSON extraction =====
def extract_json_objects(text: str) -> list:
    pattern = r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}'
    matches = re.findall(pattern, text)
    objs = []
    for m in matches:
        try:
            objs.append(json.loads(m))
        except json.JSONDecodeError:
            continue
    return objs

# ===== Load inputs =====
def load_prompt(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().strip()


def collect_images(root):
    image_list = []
    for dirpath, _, files in os.walk(root):
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_list.append((f, os.path.join(dirpath, f)))
    return image_list

# ===== Thread worker =====
def model_worker(model, prompt, api_url, token, img_item, answer_map, figure_map, responses_map, results, lock):
    fname, path = img_item
    # Retrieve metadata for this figure
    refname = os.path.splitext(fname)[0]
    info = figure_map.get(refname, {})
    caption = info.get('caption', '')
    references = info.get('references', []) or []
    label = info.get('label', '')
    # Build descriptions from prior vision model responses
    responses = responses_map.get(fname, [])
    descriptions = "".join([f"Description #{i+1} for this figure: {r}" for i, r in enumerate(responses)]) if responses else ''
    # Combine into question
    question = (
        f"Classify the type of figure for the caption and references provided for {label}.\n"
        f"Caption: {caption}\n"
        f"References: {references}\n"
        f"Label: {label}\n"
        f"{descriptions}\n"
        f"Prompt: {prompt}\n"
    )

    # Call FastGPT and capture response
    resp = fastgpt_call(api_url, token, model, question, prompt)

    # Parse JSON for types
    objs = extract_json_objects(resp)
    types = []
    if objs:
        o = objs[0]
        if isinstance(o.get('types'), list):
            types = o['types']
        elif isinstance(o.get('type'), str):
            types = [o['type']]

    # Ground truth and correctness
    gt = answer_map.get(fname, '')
    correct = 1 if gt and gt in types else 0

    # Append result including raw response
    with lock:
        results.append({
            'model': model,
            'image_file': fname,
            'correct': correct,
            'response': resp
        })

# ===== Main =====
if __name__ == '__main__':
    args = parse_args()
    prompt = load_prompt(args.prompt_file)
    # Load figure info JSON
    with open(args.fig_info, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Flatten figure_map by refname
    figure_map = {}
    for pmcid, figs in data.items():
        for fig_key, info in figs.items():
            ref = info.get('refname')
            if ref:
                figure_map[ref] = info

    # Load prior vision model responses
    vis_df = pd.read_csv(args.vision_responses_csv)
    responses_map = {}
    for fname, group in vis_df.groupby('image_file'):
        responses_map[fname] = group['response'].astype(str).tolist()

    # Load ground truth answers
    answer_df = pd.read_csv(args.answer_csv)
    answer_map = {row['image_file']: row['image_type'] for _, row in answer_df.iterrows()}
    # Collect images recursively
    images = collect_images(args.image_root)

    models = ['qwen2.5:72b', 'llama3.2:latest', 'gemma2:27b', 'llama3.1:70b']
    all_results = []
    lock = threading.Lock()

    for model in models:
        print(f"Running model {model}...")
        threads = []
        results = []
        for img_item in images:
            # throttle max threads
            while threading.active_count() > args.max_threads:
                time.sleep(0.1)
            t = threading.Thread(
                target=model_worker,
                args=(model, prompt, args.api_url, args.token,
                      img_item, answer_map, figure_map, responses_map, results, lock)
            )
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        all_results.extend(results)

    # Save and summarize
    df = pd.DataFrame(all_results)
    df.to_csv(args.output_csv, index=False)
    summary = df.groupby('model')['correct'].mean()
    print(f"Saved results to {args.output_csv}")
    print("Accuracy by model:")
    print(summary)
