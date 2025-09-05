#!/usr/bin/env python3

import os
import re
import json
import argparse
import importlib.util
import torch
from clickhouse_driver import Client
from tqdm import tqdm

# ----------------------
# Helpers
# ----------------------
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

# ----------------------
# Main
# ----------------------
def main(args):
    # 1. Load LVM pipeline module
    spec = importlib.util.spec_from_file_location("lvm_pipeline", args.pipeline)
    lvm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lvm)

    # 2. Read prompts (one per line)
    prompt_path = args.prompts or 'data/img-entity/seleted-prompt.txt'
    if not os.path.isfile(prompt_path):
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompts = [line.strip() for line in f if line.strip()]

    # 3. Initialize ClickHouse client
    client = Client(
        host=args.clickhouse_host,
        port=args.clickhouse_port,
        user=args.clickhouse_user,
        password=args.clickhouse_password,
        database=args.clickhouse_database
    )

    # 4. Fetch rows needing processing
    select_sql = (
        f"SELECT pmcid, graphic, file_path FROM {args.table} "
        "WHERE nodes = ''"
    )
    rows = client.execute(select_sql)
    if not rows:
        print("No rows to process.")
        return

    # 5. Prepare model & processor
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model, processor = lvm.load_phi35_model_and_processor(device)

    # 6. Process each row with each prompt and update ClickHouse
    for pmcid, graphic, file_path in tqdm(rows, desc='Rows'):
        for prompt in prompts:
            record = {'entity_prompt': prompt, 'img_path': file_path}
            lvm.process_phi35_image(record, model, processor, device, worker_id=0)
            resp_text = record.get('phi35_entity', '')
            objs = extract_json_objects(resp_text)
            ents = objs[0].get('entities', []) if objs else []
            nodes_json = json.dumps([{'entities': ents}], ensure_ascii=False)

            update_sql = (
                f"ALTER TABLE {args.table} UPDATE nodes = '{nodes_json}', update_time = now() "
                f"WHERE pmcid = '{pmcid}' AND graphic = '{graphic}' AND file_path = '{file_path}'"
            )
            client.execute(update_sql)

    print("Done! Entities written to ClickHouse table.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Run phi-3.5 entity extraction and write to ClickHouse"
    )
    parser.add_argument(
        '--prompts', type=str,
        help='Path to prompt file (one per line). Defaults to data/img-entity/seleted-prompt.txt.'
    )
    parser.add_argument(
        '--pipeline', type=str, default='3-0-lvm_pipeline.py',
        help='Path to the LVM pipeline module.'
    )
    parser.add_argument(
        '--clickhouse-host', type=str, required=True,
        help='ClickHouse host.'
    )
    parser.add_argument(
        '--clickhouse-port', type=int, default=9000,
        help='ClickHouse port.'
    )
    parser.add_argument(
        '--clickhouse-user', type=str, required=True,
        help='ClickHouse username.'
    )
    parser.add_argument(
        '--clickhouse-password', type=str, required=True,
        help='ClickHouse password.'
    )
    parser.add_argument(
        '--clickhouse-database', type=str, required=True,
        help='ClickHouse database name.'
    )
    parser.add_argument(
        '--table', type=str, default='image_node_lvm_total',
        help='ClickHouse table name.'
    )
    args = parser.parse_args()
    main(args)
