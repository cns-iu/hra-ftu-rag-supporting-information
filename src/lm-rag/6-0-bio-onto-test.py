#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
import functools
import json
import multiprocessing
import re
import time
import uuid

import pandas as pd
import requests
from clickhouse_driver import Client

# File paths and table name configuration
file1 = r"data\bio-onto\bio-onto-test-answer.csv"
file2 = r"data\bio-onto\bio-onto-prompt.csv"
table_name = "bio_test"

# ClickHouse client configuration
client = Client(
    host='your_host', port='your_port',
    user='your_username', password='your_password',
    database='your_database'
)

# Expected columns and primary key order fields
expected_cols = [
    'text_type', 'num', 'itype', 'pmcid',
    'content', 'llama31_runtime', 'llama32_runtime', 'gemma_runtime', 'qwen_runtime',
    'llama31_jaccard', 'llama32_jaccard', 'qwen_jaccard', 'gemma_jaccard',
    'answer', 'prompt', 'llama31', 'llama32', 'qwen', 'gemma'
]
order_columds = ['text_type', 'num', 'itype', 'pmcid', 'content', 'prompt']

# FastGPT API key
Authorization = 'your_fastgpt_key'


def create_table():
    """Create the ClickHouse table if it does not already exist."""
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        {' String, '.join(expected_cols)} String,
        update_time DateTime DEFAULT now()
    ) ENGINE = ReplacingMergeTree(update_time)
    ORDER BY ({', '.join(order_columds)});
    """
    client.execute(create_table_query)


def import_data():
    """Import data from Excel files into ClickHouse."""
    df_A = pd.read_csv(file1)
    df_B = pd.read_csv(file2)
    df_A.rename(columns={'type': 'text_type'}, inplace=True)
    # Perform Cartesian product merge
    df_A['key'] = 1
    df_B['key'] = 1
    merged = pd.merge(df_A, df_B, on='key').drop('key', axis=1)
    # Ensure all expected columns exist
    for col in expected_cols:
        if col not in merged.columns:
            merged[col] = ''
    merged[expected_cols] = merged[expected_cols].astype(str)
    merged['update_time'] = datetime.datetime.now()
    # Reorder columns and bulk insert into ClickHouse
    all_cols = expected_cols + ['update_time']
    data = [tuple(row) for row in merged[all_cols].to_numpy()]
    client.execute(f'INSERT INTO {table_name} VALUES', data)


def fetch_data_from_clickhouse(condition):
    """Fetch rows from ClickHouse matching the given SQL condition."""
    query = f"SELECT {', '.join(expected_cols)} FROM {table_name} {condition}"
    rows = client.execute(query)
    return [dict(zip(expected_cols, row)) for row in rows]


def extrac_json_text(text):
    """Extract JSON objects from the model response text."""
    pattern = r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}'
    json_strings = re.findall(pattern, text)
    objs = []
    for js in json_strings:
        try:
            objs.append(json.loads(js))
        except json.JSONDecodeError:
            continue
    return objs


def jaccard_similarity_list(list1, list2):
    """Compute the Jaccard similarity between two lists."""
    try:
        set1 = set(list1)
        set2 = set(list2)
    except:
        return 0
    if not set1 and not set2:
        return 1
    return len(set1 & set2) / len(set1 | set2)


def insert_data(data):
    """Insert or update a single row in ClickHouse."""
    row = [data.get(col, '') for col in expected_cols]
    client.execute(
        f"INSERT INTO {table_name} ({', '.join(expected_cols)}) VALUES",
        [tuple(row)]
    )


def send_request(result, model_name, col_name):
    """Query the FastGPT API for a specific model, save the response and latency."""
    question = result.get('content', '')
    prompt = result.get('prompt', '')
    url = 'your_fastgpt_url'
    headers = {
        'Authorization': f"Bearer {Authorization}",
        'Content-Type': 'application/json'
    }
    payload = {
        'messages': [{'content': question, 'role': 'user'}],
        'variables': {'model': model_name, 'prompt': prompt}
    }
    start = time.time()
    json_rs = []
    for _ in range(10):
        res = requests.post(url, headers=headers, data=json.dumps(payload))
        content = res.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        json_rs = extrac_json_text(content)
        if json_rs:
            break
    runtime = time.time() - start
    result[f'{col_name}_runtime'] = str(round(runtime, 2))
    result[col_name] = json.dumps(json_rs)
    insert_data(result)


def process_entities_jaccard(result, column_name):
    """Compute and write back Jaccard similarity for the 'entities' list."""
    try:
        ans_json = json.loads(result.get('answer', ''))
    except:
        ans_json = {}
    try:
        rs_json = json.loads(result.get(column_name, ''))
    except:
        rs_json = []
    if ans_json and rs_json:
        ans_entities = ans_json.get('entities', [])
        rs_entities = rs_json[0].get('entities', [])
        sim = jaccard_similarity_list(ans_entities, rs_entities)
    else:
        sim = 0
    result[f'{column_name}_jaccard'] = str(sim)
    insert_data(result)


if __name__ == '__main__':
    # Step 1: Create table and import data
    create_table()
    import_data()

    # Step 2: Iterate over models, query and save responses/latencies
    model_map = {
        'qwen': 'qwen2.5:72b',
        'llama32': 'llama3.2:latest',
        'gemma': 'gemma2:27b',
        'llama31': 'llama3.1:70b'
    }
    for col, model in model_map.items():
        condition = f"WHERE {col} = '' AND prompt != ''"
        tasks = fetch_data_from_clickhouse(condition)
        for task in tasks:
            send_request(task, model, col)

    # Step 3: Parallel computation of entity-level Jaccard similarity
    for col in model_map:
        condition = f"WHERE {col} != '' AND {col}_jaccard = ''"
        tasks = fetch_data_from_clickhouse(condition)
        worker = functools.partial(process_entities_jaccard, column_name=col)
        with multiprocessing.Pool(processes=20) as pool:
            pool.map(worker, tasks)
