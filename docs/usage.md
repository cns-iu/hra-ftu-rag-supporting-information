# Usage Guide (usage.md)

This document provides step-by-step instructions for using the main components of **HRAftu-LM-RAG**. Each section covers how to run scripts and services in the `src/` directory, along with example commands.

---

## Prerequisites

1. **Configuration File**  
   Before invoking any script, ensure you have copied and edited `config/example_config.yaml` to `config/config.yaml`, filling in:  
   - `fastgpt.api_key` & `fastgpt.host`  
   - Vision model device/port settings  
   - ClickHouse connection details (if using similarity evaluation)  

2. **Environment Activation**  
   ```bash
   cd HRAftu-LM-RAG
   source venv/bin/activate       # or: conda activate hraftu
    ````

---

## 1. Data Import

The **Data Import** script (`import_data_to_knowledge_datatabase.py`) uploads a directory of local files (PDF, TXT, DOCX, etc.) into a FastGPT dataset/collection.

### 1.1 Command Syntax

```bash
python src/import_data/import_data_to_knowledge_datatabase.py \
  --directory_path <PATH_TO_FILES> \
  --database <FASTGPT_DATASET_NAME> \
  [--collect_name <COLLECTION_NAME>] \
  [--parm <create|update|delete>] \
  [--parentId <PARENT_COLLECTION_ID>]
```

* `--directory_path` (required): Absolute or relative path to the folder containing documents.
* `--database` (required): The FastGPT dataset/collection name under which to import.
* `--collect_name` (optional): A human-readable name for the collection; if omitted, defaults to the directory name.
* `--parm` (optional):

  * `create` (default) → add all new documents, skip existing ones.
  * `update` → replace documents that already exist.
  * `delete` → remove documents matching names in the folder.
* `--parentId` (optional): If you want to nest this collection under an existing parent collection ID.

### 1.2 Example

```bash
python src/import_data/import_data_to_knowledge_datatabase.py \
  --directory_path ./data/technical_papers \
  --database ResearchCorpus \
  --collect_name “TechPapers” \
  --parm create
```

This will:

1. Read every file under `./data/technical_papers`.
2. Create or update the FastGPT collection named `ResearchCorpus/TechPapers`.
3. Skip any files that are already indexed.

---

## 2. Embedding Service

The **Embedding Service** (`embedding_web.py`) is a Flask-based HTTP server that loads multiple embedding models. Clients send text and specify which model to use, and the service returns normalized vectors.

### 2.1 Starting the Service

```bash
python src/embedding_service/embedding_web.py --port 55443
```

* `--port` (optional): Port number on which Flask will listen (default: `55443`).

#### Logs

When the service starts, you’ll see console output similar to:

```
[INFO] Loading model: pubmedbert
[INFO] Loading model: all-MiniLM-L6-v2
[INFO] Loading model: bge-large-en-v1.5
[INFO] Loading model: gte-large
[INFO] Flask server running on http://0.0.0.0:55443
```

### 2.2 API Endpoint

* **URL**: `POST http://<host>:<port>/v1/embeddings`
* **Request body** (JSON):

  ```json
  {
    "input": ["Text sentence 1", "Text sentence 2", ...],
    "model": "all-MiniLM-L6-v2"
  }
  ```
* **Response body** (JSON array):

  ```json
  [
    [0.123, -0.456, ...],   // normalized vector for "Text sentence 1"
    [0.789,  0.012, ...]    // normalized vector for "Text sentence 2"
  ]
  ```

### 2.3 Example `curl` Request

```bash
curl -X POST http://localhost:55443/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "input": ["The quick brown fox jumps over the lazy dog."],
    "model": "all-MiniLM-L6-v2"
  }'
```

You should receive a JSON array containing one embedding vector.

---

## 3. LLM Batch Query

The **LLM Batch Query** script (`llm_query.py`) sends multiple prompts in parallel to FastGPT’s Chat Completions endpoint and collects responses.

### 3.1 Command Syntax

```bash
python src/llm_query/llm_query.py \
  --input_file <PATH_TO_PROMPTS_FILE> \
  --output_file <PATH_TO_OUTPUT_JSON> \
  [--max_workers <NUM_THREADS>] \
  [--timeout <SECONDS>]
```

* `--input_file` (required): Path to a CSV or JSON file containing a list of prompts.
* `--output_file` (required): Path where the script will write the aggregated JSON responses.
* `--max_workers` (optional): Number of parallel threads to use (default: `4`).
* `--timeout` (optional): Timeout in seconds per request (default: `30`).

#### Input File Format

* **CSV**:

  ```csv
  id,prompt
  1,"What is the capital of France?"
  2,"Explain the theory of relativity in simple terms."
  ```
* **JSON**:

  ```json
  [
    {"id": "1", "prompt": "What is the capital of France?"},
    {"id": "2", "prompt": "Explain the theory of relativity in simple terms."}
  ]
  ```

### 3.2 Example

```bash
python src/llm_query/llm_query.py \
  --input_file examples/sample_prompts.csv \
  --output_file output/llm_responses.json \
  --max_workers 8
```

* The script will read each `prompt`, submit it to FastGPT’s `/v1/chat/completions`, and write a list of objects like:

  ```json
  [
    {"id": "1", "response": "Paris is the capital of France."},
    {"id": "2", "response": "The theory of relativity, developed by Einstein, states that ..."}
  ]
  ```

---

## 4. LVM Query

**LVM Query** refers to querying vision-language models separately from the LLM batch query. Each model (LLaVa, Llama-3.2-Vision, Phi-3-Vision, Phi-3.5-Vision, Pixtral) exposes its own RESTful endpoint. Below are example commands for each.

> **Note:** Ensure you have already started the relevant LVM service (see `docs/installation.md`).

### 4.1 LLaVa:34B (Ollama)

* **Endpoint**: `POST http://localhost:11434/completions`
* **Example `curl`**:

  ```bash
  curl -X POST http://localhost:11434/completions \
    -H "Content-Type: application/json" \
    -d '{
      "prompt": "Describe this image: <Base64-encoded-image-data>"
    }'
  ```
* **Response**:

  ```json
  {
    "id": "abc123",
    "choices": [
      {"text": "A dog is running in a grassy field.", "finish_reason": "stop"}
    ]
  }
  ```

### 4.2 Llama-3.2-11B-Vision (vLLM)

* **Endpoint**: `POST http://localhost:8000`
* **Payload Format**:

  ```json
  {
    "inputs": [
      {"type": "image", "data": "<Base64-or-URL>"},
      {"type": "text", "text": "What objects do you see in this image?"}
    ]
  }
  ```
* **Example `curl`**:

  ```bash
  curl -X POST http://localhost:8000 \
    -H "Content-Type: application/json" \
    -d '{
      "inputs": [
        {"type": "image", "data": "<Base64-encoded-image>"},
        {"type": "text", "text": "What objects do you see in this image?"}
      ]
    }'
  ```
* **Response**:

  ```json
  {
    "id": "req-456",
    "outputs": [
      {"text": "I see a cat sitting on a windowsill.", "entities": []}
    ]
  }
  ```

### 4.3 Phi-3-Vision-128k-Instruct (vLLM)

* **Endpoint**: `POST http://localhost:8001`
* **Example `curl`**:

  ```bash
  curl -X POST http://localhost:8001 \
    -H "Content-Type: application/json" \
    -d '{
      "inputs": [
        {"type": "image", "data": "<Base64>"},
        {"type": "text", "text": "Identify any medical anomalies in this X-ray image."}
      ]
    }'
  ```
* **Response**:

  ```json
  {
    "id": "req-789",
    "outputs": [
      {"text": "There is a small opacity in the lower right lung field.", "entities": [{"label":"Anomaly","text":"opacity","confidence":0.92}]}
    ]
  }
  ```

### 4.4 Phi-3.5-Vision-Instruct (vLLM)

* **Endpoint**: `POST http://localhost:8002`
* **Example `curl`**:

  ```bash
  curl -X POST http://localhost:8002 \
    -H "Content-Type: application/json" \
    -d '{
      "inputs": [
        {"type": "image", "data": "<Base64>"},
        {"type": "text", "text": "Extract any chemical structures from this image."}
      ]
    }'
  ```
* **Response**:

  ```json
  {
    "id": "req-012",
    "outputs": [
      {"text": "I see ethanol and benzene rings.", "entities": [{"label":"Molecule","text":"ethanol","confidence":0.87}, {"label":"Molecule","text":"benzene","confidence":0.90}]}
    ]
  }
  ```

### 4.5 Pixtral-12B-2409 (vLLM)

* **Endpoint**: `POST http://localhost:8003`
* **Example `curl`**:

  ```bash
  curl -X POST http://localhost:8003 \
    -H "Content-Type: application/json" \
    -d '{
      "inputs": [
        {"type": "image", "data": "<Base64>"},
        {"type": "text", "text": "Describe the scene and list any textual labels visible."}
      ]
    }'
  ```
* **Response**:

  ```json
  {
    "id": "req-345",
    "outputs": [
      {"text": "A street sign says 'Main St.' and a traffic light is green.", "entities": [{"label":"Text","text":"Main St.","confidence":0.95}]}
    ]
  }
  ```

---

## 5. Similarity Evaluation

The **Similarity Evaluation** script (`jaccard_similarity.py`) compares LVM outputs against ground truth annotations and writes an Excel report containing Jaccard similarity (and optional EMD) scores.

### 5.1 Command Syntax

```bash
python src/similarity/jaccard_similarity.py \
  --ground_truth <PATH_TO_GROUND_TRUTH_XLSX> \
  --clickhouse_table <CLICKHOUSE_TABLE_NAME> \
  --output <PATH_TO_OUTPUT_XLSX> \
  [--host <CLICKHOUSE_HOST>] \
  [--port <CLICKHOUSE_PORT>] \
  [--user <CLICKHOUSE_USER>] \
  [--password <CLICKHOUSE_PASSWORD>] \
  [--database <CLICKHOUSE_DB>]
```

* `--ground_truth` (required): Excel file with annotated entities/relations (e.g., `schema-test.xlsx`).
* `--clickhouse_table` (required): Table where LVM outputs are stored (e.g., `clkg.vision_outputs`).
* `--output` (required): Path to the resulting Excel report (e.g., `results_with_all_similarity_and_emd5.xlsx`).
* ClickHouse connection parameters default to those in `config/config.yaml` if not provided.

### 5.2 Ground Truth Format

Your ground truth Excel should have columns such as:

```text
id    | entity_name    | entity_label    | relation_type    | ...
---------------------------------------------------------------
img_1 | “cat”          | “Animal”        | “has_tail”       | ...
img_2 | “benzene”      | “Molecule”      | “...”            | ...
```

Each row corresponds to one entity or relation annotation for a specific `id`.

### 5.3 Example

```bash
python src/similarity/jaccard_similarity.py \
  --ground_truth data/schema-test.xlsx \
  --clickhouse_table clkg.vision_outputs \
  --output results_with_all_similarity_and_emd5.xlsx
```

* The script will:

  1. Connect to ClickHouse (`host`, `port`, `user`, `password`, `database` from `config/config.yaml` by default).
  2. Query all rows in `clkg.vision_outputs` and parse the `output_json` column into entity/relation sets.
  3. Compare against the `schema-test.xlsx` annotations.
  4. Compute Jaccard similarity for each record and write results to `results_with_all_similarity_and_emd5.xlsx`.

---

## 6. Example Workflow

1. **Import Data**

   ```bash
   python src/import_data/import_data_to_knowledge_datatabase.py \
     --directory_path ./data/technical_papers \
     --database ResearchCorpus
   ```
2. **Start Embedding Service**

   ```bash
   python src/embedding_service/embedding_web.py --port 55443
   ```
3. **Verify Embedding API**

   ```bash
   curl -X POST http://localhost:55443/v1/embeddings \
     -H "Content-Type: application/json" \
     -d '{
       "input": ["Deep learning for NLP."],
       "model": "all-MiniLM-L6-v2"
     }'
   ```
4. **Run LLM Batch Query**

   ```bash
   python src/llm_query/llm_query.py \
     --input_file examples/sample_prompts.csv \
     --output_file output/llm_responses.json
   ```
5. **Query LVM (LLaVa Example)**

   ```bash
   curl -X POST http://localhost:11434/completions \
     -H "Content-Type: application/json" \
     -d '{
       "prompt": "Describe the following image: <Base64-encoded-image>"
     }'
   ```
6. **Store LVM Output in ClickHouse**

   * Assuming your inference client writes to `clkg.vision_outputs` in ClickHouse.
7. **Run Similarity Evaluation**

   ```bash
   python src/similarity/jaccard_similarity.py \
     --ground_truth data/schema-test.xlsx \
     --clickhouse_table clkg.vision_outputs \
     --output results_with_all_similarity_and_emd5.xlsx
   ```

After following these steps, you should have:

* Documents indexed in FastGPT.
* Embedding Service running and returning float vectors.
* LLM responses saved to JSON.
* LVM inferences stored in ClickHouse.
* Similarity scores exported to an Excel report.

