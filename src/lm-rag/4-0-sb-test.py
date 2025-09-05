"""
Batch testing of FastGPT responses for multiple models, storing outputs in per-model folders with timestamped files,
and then merging all runs into consolidated Excel files per model.
"""
import os
import glob
import json
import uuid
import time
import requests
import pandas as pd
import multiprocessing
from datetime import datetime

# Configuration
API_URL = 'YOUR_API_URL'
API_KEY = 'YOUR_API_KEY'
PROMPT_FILE = '/hra-rag-ftu/scale-bar/scale-bar-prompts.csv'
INPUT_FILE = '/hra-rag-ftu/scale-bar/scale-bar-sample.csv'
CONCURRENCY = 30  # Number of parallel processes

HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

# Models to test
MODEL_MAP = {
    'qwen': 'qwen2.5:72b',
    'llama32': 'llama3.2:latest',
    'gemma': 'gemma2:27b',
    'llama31': 'llama3.1:70b'
}

# ===============================
def read_first_column(csv_path):
    """Read the first column of an CSV file into a list of strings."""
    df = pd.read_csv(csv_path, usecols=[0], header=0)
    col = df.columns[0]
    return df[col].dropna().astype(str).tolist()

# ===============================
def fastgpt_ai(prompt, question, model):
    """Call FastGPT API with given prompt, question and model. Retries until valid response."""
    payload = {
        'messages': [{'id': str(uuid.uuid4()), 'role': 'user', 'content': question}],
        'variables': {'model': model, 'prompt': prompt},
        'chatId': str(uuid.uuid4())
    }
    while True:
        try:
            resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
            resp.raise_for_status()
            data = resp.json()
            if data.get('code') == 200 and 'data' in data:
                choices = data['data'].get('choices', [])
                if choices and 'message' in choices[0]:
                    content = choices[0]['message'].get('content', '').strip()
                    if content:
                        return content
            time.sleep(1)
        except (requests.RequestException, ValueError):
            time.sleep(1)

# ===============================
def process_question(args):
    """Process one (prompt, question, model, key) tuple and return the result dict."""
    prompt, question, model, key = args
    start = time.time()
    response = fastgpt_ai(prompt, question, model)
    runtime = time.time() - start
    return {
        'model': key,
        'prompt': prompt,
        'question': question,
        'response': response,
        'runtime_sec': round(runtime, 3)
    }

# ===============================
def run_for_model(key, model, prompts, inputs):
    """Run batch tests for one model and save results to timestamped Excel."""
    tasks = [(p, q, model, key) for p in prompts for q in inputs]
    out_dir = os.path.join('data', key)
    os.makedirs(out_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = os.path.join(out_dir, f'{key}_{timestamp}.xlsx')

    print(f"Running {key} ({model}): {len(tasks)} tasks -> {out_file}")
    with multiprocessing.Pool(processes=CONCURRENCY) as pool:
        results = pool.map(process_question, tasks)

    df = pd.DataFrame(results)
    df.to_excel(out_file, index=False)
    print(f"Saved results for {key} to {out_file}")

# ===============================
def combine_results():
    """Merge all timestamped Excel files into one per model in data/ folder."""
    for key in MODEL_MAP:
        folder = os.path.join('data', key)
        files = sorted(glob.glob(os.path.join(folder, '*.xlsx')))
        if not files:
            continue
        dfs = [pd.read_excel(f) for f in files]
        combined = pd.concat(dfs, ignore_index=True)
        out_file = os.path.join('data', f'{key}.xlsx')
        combined.to_excel(out_file, index=False)
        print(f"Combined {len(files)} runs for {key} into {out_file}")

# ===============================
if __name__ == '__main__':
    prompt_list = read_first_column(PROMPT_FILE)
    input_list = read_first_column(INPUT_FILE)
    print(f"Loaded {len(prompt_list)} prompts and {len(input_list)} inputs.")

    # Run tests
    for key, model in MODEL_MAP.items():
        run_for_model(key, model, prompt_list, input_list)

    # Combine results
    combine_results()
