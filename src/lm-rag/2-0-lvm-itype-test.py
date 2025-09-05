#!/usr/bin/env python3
# 6-1-lvm-entity-test.py

import os
import re
import json
import pandas as pd
import importlib.util
import torch
from tqdm import tqdm

# Dynamically load the LVM pipeline (3-0-lvm_pipeline.py)
spec = importlib.util.spec_from_file_location("lvm_pipeline", "3-0-lvm_pipeline.py")
lvm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lvm)

# Extract JSON objects from model responses
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

# Compute Jaccard similarity between two lists (unused here)
def jaccard_similarity_list(list1, list2) -> float:
    try:
        set1 = set(list1)
        set2 = set(list2)
    except TypeError:
        return 0.0
    if not set1 and not set2:
        return 1.0
    return len(set1 & set2) / len(set1 | set2)

# Load prompts from CSV
def load_prompts(csv_path: str) -> list:
    df = pd.read_csv(csv_path)
    return df['prompt'].dropna().astype(str).tolist()

# Load ground truth entities from CSV
def load_ground_truth(csv_path: str) -> dict:
    df = pd.read_csv(csv_path)
    answers = {}
    for _, row in df.iterrows():
        fname = row['file'] if 'file' in row else row['image_file']
        ans = row.get('nodes', row.get('image_type', ''))
        answers[fname] = ans
    return answers

# Main test harness
if __name__ == '__main__':
    prompt_csv = 'data/img-entity/lvm-entity-prompt.csv'
    answer_csv = 'data/img-entity/lvm-test-answer.csv'
    image_folder = 'data/img-entity/lvm-entity-testdata'
    output_csv = 'data/img-entity/img_type_lvm_test_results.csv'

    prompts = load_prompts(prompt_csv)
    answers_map = load_ground_truth(answer_csv)
    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    all_results = []

    # Test Llama-3.2, Phi-3, Phi-3.5
    model_specs = [
        ('llama32', lvm.load_llama_vision_model_and_processor, lvm.process_llama32_image),
        ('phi3',   lvm.load_phi3_model_and_processor,           lvm.process_phi3_image),
        ('phi35',  lvm.load_phi35_model_and_processor,         lvm.process_phi35_image),
    ]
    for name, load_fn, proc_fn in model_specs:
        model, processor = load_fn(device)
        for prompt in tqdm(prompts, desc=f"{name} prompts"):
            for fname in os.listdir(image_folder):
                if not fname.lower().endswith('.jpg'):
                    continue
                img_path = os.path.join(image_folder, fname)
                record = {'entity_prompt': prompt, 'img_path': img_path}
                proc_fn(record, model, processor, device, worker_id=0)
                response_text = record.get(f"{name}_entity", "")
                objs = extract_json_objects(response_text)
                pred_entities = objs[0].get('entities', []) if objs else []
                true_entities = answers_map.get(fname, [])
                sim = jaccard_similarity_list(true_entities, pred_entities)
                all_results.append({
                    'model': name,
                    'prompt': prompt,
                    'image': fname,
                    'jaccard': sim,
                    'response': response_text
                })

    # Test Pixtral
    lvm.start_pixtral_service()
    for prompt in tqdm(prompts, desc="pixtral prompts"):
        for fname in os.listdir(image_folder):
            if not fname.lower().endswith('.jpg'):
                continue
            img_path = os.path.join(image_folder, fname)
            record = {'entity_prompt': prompt, 'img_path': img_path}
            lvm.send_pixtral_request(record, worker_id=0)
            resp = record.get('pixtral_entity', [])
            response_text = json.dumps(resp, ensure_ascii=False)
            pred_entities = resp[0].get('entities', []) if isinstance(resp, list) and resp else []
            true_entities = answers_map.get(fname, [])
            sim = jaccard_similarity_list(true_entities, pred_entities)
            all_results.append({
                'model': 'pixtral',
                'prompt': prompt,
                'image': fname,
                'jaccard': sim,
                'response': response_text
            })

    # Test LlaVA (Ollama)
    ip_port_list = lvm.config.OLLAMA_IP_PORTS
    for prompt in tqdm(prompts, desc="llava prompts"):
        for fname in os.listdir(image_folder):
            if not fname.lower().endswith('.jpg'):
                continue
            img_path = os.path.join(image_folder, fname)
            record = {'entity_prompt': prompt, 'img_path': img_path}
            lvm.ollama_vision_task(record, worker_id=0, ip_port_list=ip_port_list)
            response_text = record.get('llava_entity', '')
            objs = extract_json_objects(response_text)
            pred_entities = objs[0].get('entities', []) if objs else []
            true_entities = answers_map.get(fname, [])
            sim = jaccard_similarity_list(true_entities, pred_entities)
            all_results.append({
                'model': 'llava',
                'prompt': prompt,
                'image': fname,
                'jaccard': sim,
                'response': response_text
            })

    # Save and summarize
    df = pd.DataFrame(all_results)
    df.to_csv(output_csv, index=False)
    print(f'Saved detailed results to {output_csv}')
    summary = df.groupby('model')['jaccard'].mean()
    print('Average Jaccard similarity by model:')
    print(summary)
