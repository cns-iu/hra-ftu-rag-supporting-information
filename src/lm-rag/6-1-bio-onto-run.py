#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import datetime
import json
import re
import time

import requests
from clickhouse_driver import Client

# Load configuration from environment variables
FASTGPT_API_URL = 'YOUR_FASTGPT_API_URL'
FASTGPT_API_KEY = 'YOUR_FASTGPT_API_KEY'

# Load fixed prompt from file
with open(r'data\bio-onto\seleted_prompt.txt', 'r', encoding='utf-8') as f:
    FIXED_PROMPT = f.read().strip()

# Initialize ClickHouse client
client = Client(
    host='your_host', port='your_port',
    user='your_username', password='your_password',
    database='your_database'
)

# Table names and schema definitions
TABLE_INFO = 'bio_onto_all_info'
TABLE_ENT = 'bio_onto_entities'
PRIMARY_KEYS_INFO = ['pmcid', 'id', 'type']
EXPECTED_COLS_INFO = ['pmcid', 'id', 'content', 'type', 'answer']

# Regex pattern for nested JSON
JSON_PATTERN = r"\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}"


def create_tables():
    """Create both info and entities tables if they don't exist."""
    ddl_info = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_INFO} (
        pmcid String,
        id String,
        content String,
        type String,
        answer String,
        update_time DateTime DEFAULT now()
    ) ENGINE = ReplacingMergeTree(update_time)
    ORDER BY ({','.join(PRIMARY_KEYS_INFO)});
    """
    ddl_ent = f"""
    CREATE TABLE IF NOT EXISTS {TABLE_ENT} (
        pmcid String,
        id String,
        type String,
        entity String,
        update_time DateTime DEFAULT now()
    ) ENGINE = MergeTree()
    ORDER BY (pmcid,id,type,entity);
    """
    client.execute(ddl_info)
    client.execute(ddl_ent)


def import_data():
    """Import source data into bio_onto_all_info."""
    client.execute(f"""
        INSERT INTO {TABLE_INFO} (pmcid, id, content, type)
        SELECT pmcid, graphic AS id, caption AS content, 'caption' AS type
        FROM ftu_pub_pmc a join vision_llm b on a.pmcid=b.pmcid and a.graphic=b.graphic 
        WHERE micro='Yes' or schema='Yes'
    """)
    client.execute(f"""
        INSERT INTO {TABLE_INFO} (pmcid, id, content, type)
        SELECT pmcid, graphic AS id, nodes AS content, 'figure_node' AS type
        FROM image_node_lvm_total a join vision_llm b on a.pmcid=b.pmcid and a.graphic=b.graphic 
        WHERE micro='Yes' or schema='Yes'
    """)


def fetch_pending_info():
    """Fetch rows from info table where answer is empty."""
    cols = ', '.join(PRIMARY_KEYS_INFO + ['content'])
    sql = f"SELECT {cols} FROM {TABLE_INFO} WHERE answer = ''"
    rows = client.execute(sql)
    return [dict(zip(PRIMARY_KEYS_INFO + ['content'], r)) for r in rows]


def extract_json_objects(text):
    """Extract JSON objects from text using nested-brace regex."""
    matches = re.findall(JSON_PATTERN, text)
    objs = []
    for m in matches:
        try:
            objs.append(json.loads(m))
        except json.JSONDecodeError:
            continue
    return objs


def send_request(row):
    """Call LLM, parse answer JSON, and upsert into info table."""
    payload = {'messages': [{'role': 'user', 'content': row['content']}],
               'variables': {'model': 'gemma2:27b', 'prompt': FIXED_PROMPT}}
    headers = {'Authorization': f"Bearer {FASTGPT_API_KEY}", 'Content-Type': 'application/json'}

    ans_objs = []
    for _ in range(5):
        resp = requests.post(FASTGPT_API_URL, headers=headers, json=payload)
        text = resp.json().get('choices', [{}])[0].get('message', {}).get('content', '')
        ans_objs = extract_json_objects(text)
        if ans_objs:
            break
    answer_val = json.dumps(ans_objs) if ans_objs else text

    vals = (row['pmcid'], row['id'], row['content'], row['type'], answer_val)
    sql = f"INSERT INTO {TABLE_INFO} ({', '.join(EXPECTED_COLS_INFO)}) VALUES"
    client.execute(sql, [vals])


def extract_and_insert_entities():
    """Parse entities from answers and insert into bio_onto_entities."""
    # Fetch all rows with non-empty answer
    sql = f"SELECT pmcid, id, type, answer FROM {TABLE_INFO} WHERE answer != ''"
    rows = client.execute(sql)
    ent_records = []
    for pmcid, id_, type_, ans in rows:
        try:
            data = json.loads(ans)
        except:
            continue
        # Handle list of JSON objects or single
        for obj in (data if isinstance(data, list) else [data]):
            entities = obj.get('entities', [])
            for ent in entities:
                ent_records.append((pmcid, id_, type_, str(ent)))
    # Bulk insert
    if ent_records:
        client.execute(
            f"INSERT INTO {TABLE_ENT} (pmcid, id, type, entity) VALUES",
            ent_records
        )


def main():
    # Step 1: Create tables
    create_tables()
    # Step 2: Import source info
    import_data()
    # Step 3: Query LLM and upsert answers
    pending = fetch_pending_info()
    for row in pending:
        send_request(row)
    # Step 4: Extract entities and insert into entities table
    extract_and_insert_entities()


if __name__ == '__main__':
    main()
