#!/usr/bin/env python3
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

# Compute Jaccard similarity between two lists
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
        fname = row['file']
        try:
            js = json.loads(row['nodes'])
        except (json.JSONDecodeError, TypeError):
            js = row['nodes']
        if isinstance(js, dict):
            ents = js.get('entities', [])
        elif isinstance(js, list) and js and isinstance(js[0], dict):
            ents = js[0].get('entities', [])
        else:
            ents = []
        answers[fname] = ents
    return answers

# Generic model tester for vision pipelines
def test_model(model_name: str, load_fn, process_fn, prompts: list, image_dir: str, answers_map: dict, device: str) -> list:
    model, processor = load_fn(device)
    results = []
    for prompt in tqdm(prompts, desc=f"{model_name} prompts"):
        for fname in os.listdir(image_dir):
            if not fname.lower().endswith('.jpg'):
                continue
            img_path = os.path.join(image_dir, fname)
            record = {'entity_prompt': prompt, 'img_path': img_path}
            process_fn(record, model, processor, device, worker_id=0)
            answer_text = record.get(f"{model_name}_entity", "")
            objs = extract_json_objects(answer_text)
            pred_entities = objs[0].get('entities', []) if objs else []
            true_entities = answers_map.get(fname, [])
            sim = jaccard_similarity_list(true_entities, pred_entities)
            results.append({
                'model': model_name,
                'prompt': prompt,
                'image': fname,
                'jaccard': sim
            })
    return results

# Tester for Pixtral
def test_pixtral(prompts: list, image_dir: str, answers_map: dict) -> list:
    lvm.start_pixtral_service()
    results = []
    for prompt in tqdm(prompts, desc="pixtral prompts"):
        for fname in os.listdir(image_dir):
            if not fname.lower().endswith('.jpg'):
                continue
            img_path = os.path.join(image_dir, fname)
            record = {'entity_prompt': prompt, 'img_path': img_path}
            lvm.send_pixtral_request(record, worker_id=0)
            resp = record.get('pixtral_entity', [])
            pred_entities = resp[0].get('entities', []) if isinstance(resp, list) and resp else []
            true_entities = answers_map.get(fname, [])
            sim = jaccard_similarity_list(true_entities, pred_entities)
            results.append({
                'model': 'pixtral',
                'prompt': prompt,
                'image': fname,
                'jaccard': sim
            })
    return results

# Tester for LlaVA (Ollama)
def test_llava(prompts: list, image_dir: str, answers_map: dict) -> list:
    ip_port_list = lvm.config.OLLAMA_IP_PORTS
    results = []
    for prompt in tqdm(prompts, desc="llava prompts"):
        for fname in os.listdir(image_dir):
            if not fname.lower().endswith('.jpg'):
                continue
            img_path = os.path.join(image_dir, fname)
            record = {'entity_prompt': prompt, 'img_path': img_path}
            lvm.ollama_vision_task(record, worker_id=0, ip_port_list=ip_port_list)
            answer_text = record.get('llava_entity', '')
            objs = extract_json_objects(answer_text)
            pred_entities = objs[0].get('entities', []) if objs else []
            true_entities = answers_map.get(fname, [])
            sim = jaccard_similarity_list(true_entities, pred_entities)
            results.append({
                'model': 'llava',
                'prompt': prompt,
                'image': fname,
                'jaccard': sim
            })
    return results

# Main test harness
if __name__ == '__main__':
    prompt_csv = 'data/img-entity/lvm-entity-prompt.csv'
    answer_csv = 'data/img-entity/lvm-test-answer.csv'
    image_folder = 'data/img-entity/lvm-entity-testdata'

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
        all_results.extend(test_model(name, load_fn, proc_fn, prompts, image_folder, answers_map, device))

    # Test Pixtral
    all_results.extend(test_pixtral(prompts, image_folder, answers_map))

    # Test LlaVA (Ollama)
    all_results.extend(test_llava(prompts, image_folder, answers_map))

    # Save and summarize
    df = pd.DataFrame(all_results)
    df.to_csv('data/img-entity/test_results.csv', index=False)
    print('Saved detailed results to data/img-entity/test_results.csv')
    summary = df.groupby('model')['jaccard'].mean()
    print('Average Jaccard similarity by model:')
    print(summary)
