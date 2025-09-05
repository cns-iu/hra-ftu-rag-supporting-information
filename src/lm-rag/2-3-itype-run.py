"""
Batch pipeline: read ftu_pub_pmc records, run vision models, store responses in ClickHouse,
then run LLM classification (llama3.2:latest) and store classification flags.
"""
import os
import re
import json
import time
import uuid
import argparse
import requests
from clickhouse_driver import Client
from tqdm import tqdm

# ===== Helpers =====
def extract_json_objects(text: str) -> list:
    pattern = r'\{(?:[^{}]|\{(?:[^{}]|\{[^{}]*\})*\})*\}'
    objs = []
    for m in re.findall(pattern, text):
        try:
            objs.append(json.loads(m))
        except json.JSONDecodeError:
            continue
    return objs

# FastGPT/LLM call for classification
def fastgpt_call(api_url, token, model, question, prompt):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
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

# ===== CLI args =====
def parse_args():
    p = argparse.ArgumentParser(description='Batch run vision+LLM pipelines')
    p.add_argument('--pipeline', type=str, default='3-0-lvm_pipeline.py', help='Path to vision pipeline module')
    p.add_argument('--clickhouse-host', required=True)
    p.add_argument('--clickhouse-port', type=int, default=9000)
    p.add_argument('--clickhouse-user', required=True)
    p.add_argument('--clickhouse-password', required=True)
    p.add_argument('--clickhouse-database', required=True)
    p.add_argument('--vision-table', default='hra_rag_ftu.vision_results')
    p.add_argument('--llm-table', default='hra_rag_ftu.vision_llm')
    p.add_argument('--entity-prompt', required=True, help='Prompt text for vision models')
    p.add_argument('--classify-prompt', required=True, help='Prompt file for LLM classification')
    p.add_argument('--image-refs-table', default='image_refs')
    p.add_argument('--ftu-table', default='ftu_pub_pmc')
    p.add_argument('--fastgpt-api-url', required=True)
    p.add_argument('--fastgpt-token', required=True)
    return p.parse_args()

# ===== Main =====
def main(args):
    # Load vision pipeline module
    import importlib.util
    spec = importlib.util.spec_from_file_location('lvm_pipeline', args.pipeline)
    lvm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lvm)

    # Connect ClickHouse
    client = Client(
        host=args.clickhouse_host,
        port=args.clickhouse_port,
        user=args.clickhouse_user,
        password=args.clickhouse_password,
        database=args.clickhouse_database
    )

    # 1. Create vision_results table
    vision_ddl = f"""
CREATE TABLE IF NOT EXISTS {args.vision_table} (
    img_name String,
    llama String,
    llava String,
    phi3 String,
    phi35 String,
    pixtral String,
    file_path String,
    pmcid String,
    ext String,
    graphic String,
    created_at DateTime DEFAULT now()
) ENGINE = ReplacingMergeTree(created_at)
PARTITION BY toYYYYMM(created_at)
ORDER BY file_path
"""
    client.execute(vision_ddl)

    # 2. Insert base records from ftu_pub_pmc (only jpg/jpeg)
    insert_sql = f"""
INSERT INTO {args.vision_table} (img_name,llama,llava,phi3,phi35,pixtral,file_path,pmcid,ext,graphic)
SELECT
    concat(
      arrayElement(splitByChar('/', file_path), -2), '/', arrayElement(splitByChar('/', file_path), -1)
    ) AS img_name,
    '' AS llama,
    '' AS llava,
    '' AS phi3,
    '' AS phi35,
    '' AS pixtral,
    file_path,
    pmcid,
    substringAfterLast(file_path, '.') AS ext,
    graphic
FROM {args.ftu_table}
WHERE lower(substringAfterLast(file_path, '.')) IN ('jpg','jpeg')
"""
    client.execute(insert_sql)

    # 3. Query records for vision models
    vision_rows = client.execute(
        f"SELECT img_name,file_path,pmcid,graphic,ext FROM {args.vision_table}"
    )

    # 4. Run vision pipelines and update responses (only jpg/jpeg)
    for img_name, file_path, pmcid, graphic, ext in tqdm(vision_rows, desc='Vision models'):
        # Prepare record
        rec = {'entity_prompt': args.entity_prompt, 'img_path': file_path}
        # Llama-3.2
        llama_model, llama_proc = lvm.load_llama_vision_model_and_processor(rec['entity_prompt'])
        lvm.process_llama32_image(rec, llama_model, llama_proc, rec['entity_prompt'], worker_id=0)
        resp_llama = rec.get('llama32_entity', '')
        # LlaVA
        lvm.ollama_vision_task(rec, worker_id=0, ip_port_list=lvm.config.OLLAMA_IP_PORTS)
        resp_llava = rec.get('llava_entity', '')
        # Phi-3
        phi3_model, phi3_proc = lvm.load_phi3_model_and_processor(rec['entity_prompt'])
        lvm.process_phi3_image(rec, phi3_model, phi3_proc, rec['entity_prompt'], worker_id=0)
        resp_phi3 = rec.get('phi3_entity', '')
        # Phi-3.5
        phi35_model, phi35_proc = lvm.load_phi35_model_and_processor(rec['entity_prompt'])
        lvm.process_phi35_image(rec, phi35_model, phi35_proc, rec['entity_prompt'], worker_id=0)
        resp_phi35 = rec.get('phi35_entity', '')
        # Pixtral
        lvm.send_pixtral_request(rec, worker_id=0)
        resp_pixtral = json.dumps(rec.get('pixtral_entity', []), ensure_ascii=False)
        # Escape single quotes
        def esc(s): return s.replace("'", "''")
        upd = f"""
ALTER TABLE {args.vision_table}
UPDATE
    llama='{esc(resp_llama)}',
    llava='{esc(resp_llava)}',
    phi3='{esc(resp_phi3)}',
    phi35='{esc(resp_phi35)}',
    pixtral='{esc(resp_pixtral)}'
WHERE
    file_path='{file_path}' AND pmcid='{pmcid}' AND graphic='{graphic}'
"""
        client.execute(upd)

    # 5. Create vision_llm table
    llm_ddl = f"""
CREATE TABLE IF NOT EXISTS {args.llm_table} (
    pmcid String,
    graphic String,
    ext String,
    llama32 String,
    run_time String,
    update_time DateTime DEFAULT now(),
    micro String,
    statis String,
    schema String,
    `3d` String,
    chem String,
    math String
) ENGINE = ReplacingMergeTree(update_time)
PRIMARY KEY (pmcid,graphic,ext)
ORDER BY (pmcid,graphic,ext)
"""
    client.execute(llm_ddl)

    # 6. Load metadata from ftu_pub_pmc and image_refs
    ftu_rows = client.execute(f"SELECT pmcid,graphic,caption,label FROM {args.ftu_table}")
    meta = {(pmcid,graphic): {'caption': cap, 'label': lab} for pmcid,graphic,cap,lab in ftu_rows}
    ref_rows = client.execute(f"SELECT pmcid,rid,ref_text FROM {args.image_refs_table} WHERE ref_type='fig'")
    refs = {}
    for pmcid,rid,txt in ref_rows:
        refs.setdefault((pmcid,str(rid)), []).append(txt)

    # 7. Load classification prompt
    with open(args.classify_prompt, 'r', encoding='utf-8') as f:
        class_prompt = f.read().strip()

    # 8. Fetch vision_results for classification
    vr_rows = client.execute(
        f"SELECT pmcid,graphic,ext,llama,llava,phi3,phi35,pixtral FROM {args.vision_table}"
    )
    for pmcid,graphic,ext,rlama,rllava,rphi3,rphi35,rpix in tqdm(vr_rows, desc='Classification'):
        if ext.lower() not in ('jpg','jpeg'):
            continue
        # Metadata
        key = (pmcid,graphic)
        md = meta.get(key, {})
        caption = md.get('caption','')
        label = md.get('label','')
        # Descriptions from vision responses
        resp_list = [rlama, rllava, rphi3, rphi35, rpix]
        descs = [f"Description #{i+1} for this figure: {r}" for i,r in enumerate(resp_list)]
        descriptions = '\n'.join(descs)
        references = refs.get(key, [])
        question = (
            f"Classify the type of figure for the caption and references provided for {label}.\n"
            f"Caption: {caption}\n"
            f"References: {references}\n"
            f"Label: {label}\n"
            f"{descriptions}\n"
            f"Prompt: {class_prompt}\n"
        )
        # Call LLM
        start = time.time()
        out = fastgpt_call(args.fastgpt_api_url, args.fastgpt_token, 'llama3.2:latest', question, class_prompt)
        runtime = f"{time.time()-start:.2f}s"
        # Parse classification
        obj = extract_json_objects(out)
        cl = obj[0] if obj else {}
        def decide(k):
            v = cl.get(k, False)
            if isinstance(v, bool): return 'Yes' if v else 'No'
            return 'Yes' if str(v).lower() in ('yes','true') else 'No'
        vals = (
            pmcid, graphic, ext, out.replace("'","''"), runtime,
            decide('micro'), decide('statis'), decide('schema'),
            decide('3d'), decide('chem'), decide('math')
        )
        insert_llm = (
            f"INSERT INTO {args.llm_table} "
            f"(pmcid,graphic,ext,llama32,run_time,micro,statis,schema,`3d`,chem,math) VALUES "
            + str([vals])
        )
        client.execute(insert_llm)

    print('Batch run complete.')

if __name__ == '__main__':
    main(parse_args())
