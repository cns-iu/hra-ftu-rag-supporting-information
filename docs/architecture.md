# Project Architecture

This document describes the overall architecture of **HRAftu-LM-RAG**, detailing each component and how they interact to form a Retrieval-Augmented Generation (RAG) and multimodal inference pipeline.

---

## 1. High-Level Overview

HRAftu-LM-RAG leverages the **FastGPT** platform as its central knowledge base and retrieval engine, integrating multiple submodules:

- **Data Import**: Batch ingestion of documents into FastGPT.
- **Embedding Service**: HTTP-based service offering multiple embedding models.
- **LLM Batch Query**: Parallelized queries to FastGPT’s Chat Completions API.
- **LVM Query**: Separate querying of vision-language models for image-based inference.
- **Intermediate Storage/Message Bus**: ClickHouse or Kafka for downstream data consumption.
- **Similarity Evaluation**: Jaccard and other distance metrics to compare model outputs against ground truth.

Below is a simplified block diagram illustrating the main data flow:

```

┌────────────────────────────────────────────────────────────────────────┐
│                              HRAftu-LM-RAG                             │
│                                                                        │
│  ┌─────────────┐       ┌───────────────────┐       ┌───────────────┐   │
│  │             │       │                   │       │               │   │
│  │  Data Import│───▶  │  FastGPT Knowledge│  ◀─── │  Embedding    │   │
│  │  (import)   │       │     Base (DB)     │       │  Service      │   │
│  │             │       │                   │       │               │   │
│  └─────────────┘       └───────────────────┘       └───────────────┘   │
│         │                     │                             │          │
│         │                     │                             │          │
│         │                     ▼                             │          │
│         │             ┌───────────────────┐                 │          │
│         │             │                   │                 │          │
│         └───────────▶ │  LLM Batch Query  │  ◀─────────────┘          │
│                       │                   │                            │
│                       └───────────────────┘                            │
│                                     │                                  │
│                                     │                                  │
│                                     ▼                                  │
│  ┌─────────────┐       ┌────────────────────────────┐                  │
│  │             │       │                            │                  │
│  │   LVM Query │───▶   │  Intermediate Storage /   │                  │
│  │             │       │  Message Bus (ClickHouse / │                  │
│  │             │       │         Kafka)             │                  │
│  └─────────────┘       └────────────────────────────┘                  │
│                                     │                                  │
│                                     │                                  │
│                                     ▼                                  │  │                       ┌───────────────────────────┐                    │
│                       │                           │                    │
│                       │  Similarity Evaluation    │                    │
│                       │   (Jaccard, EMD, etc.)    │                    │
│                       │                           │                    │
│                       └───────────────────────────┘                    │
└────────────────────────────────────────────────────────────────────────┘
```

### Key Subsystems

1. **Data Import (src/import_data/import_data_to_knowledge_datatabase.py)**
   - Batch uploads local files to a specified FastGPT dataset/collection.
   - Supports create, update, delete operations and skips duplicates.
   - Logs progress and errors.

2. **FastGPT Knowledge Base**
   - Stores uploaded documents, builds vector indices, and supports hybrid retrieval.
   - Exposes endpoints such as:
     - `POST /v1/embeddings` (called by Embedding Service)
     - `POST /v1/search` (semantic or hybrid search)
     - `POST /v1/chat/completions` (LLM queries)
   - See FastGPT official documentation for deployment details.

3. **Embedding Service (src/embedding_service/embedding_web.py)**
   - A Flask-based HTTP service that loads multiple pretrained embeddings:
     - `pubmedbert`
     - `all-MiniLM-L6-v2`
     - `bge-large-en-v1.5`
     - `gte-large`
   - Endpoint: `POST /v1/embeddings`
     - Request: JSON with fields `input: List[str]`, `model: str`
     - Response: JSON array of normalized embedding vectors.
   - Used by test scripts to compare retrieval performance across models.

4. **LLM Batch Query (src/llm_query/llm_query.py)**
   - Concurrently sends prompts to FastGPT’s Chat Completions API.
   - Designed for large-scale evaluation or data collection.
   - Input: CSV/JSON of questions or documents; Output: aggregated responses in JSON or CSV.

5. **LVM Query**
   - Integrates several vision-language models, each deployed separately:
     - **LLaVa:34B** (via Ollama)
     - **Llama-3.2-11B-Vision** (via vLLM)
     - **Phi-3-Vision-128k-Instruct** (via vLLM)
     - **Phi-3.5-Vision-Instruct** (via vLLM)
     - **Pixtral-12B-2409** (via vLLM)
   - Each model:
     - Is “pulled” or downloaded through a CLI (Ollama or vLLM).
     - Served via a HTTP endpoint.
     - Accepts mixed inputs (e.g., Base64-encoded image + text prompt).
     - Produces structured outputs (e.g., image caption, entity/relation JSON).
   - Queries to these models are performed separately from LLM queries.
   - Detailed deployment instructions appear in **docs/lvm_deployment.md**.

6. **Intermediate Storage / Message Bus**
   - LVM outputs and other high-volume data need persistent storage or streaming:
     - **ClickHouse**: high-performance columnar database for big data analytics.
     - **Kafka**: distributed streaming platform for real-time data pipelines.
   - Downstream analytics or similarity evaluation scripts read from these sources.

7. **Similarity Evaluation (src/similarity/jaccard_similarity.py)**
   - Compares model outputs against human-labeled ground truth.
   - Computes:
     - Jaccard similarity for node/entity sets.
     - Additional metrics (e.g., EMD distance if applicable).
   - Input:
     - Excel file with ground truth entity/relationship annotations.
     - JSON outputs from ClickHouse queries.
   - Output:
     - Consolidated Excel report (`results_with_all_similarity_and_emd5.xlsx`) with similarity scores per model.

---

## 2. Module Interaction Flow

1. **Data Import → FastGPT Knowledge Base**
   - `import_data_to_knowledge_datatabase.py` loads local docs into FastGPT.
   - FastGPT processes each document: tokenizes, generates embeddings (via built-in or external service), and indexes.

2. **Embedding Service → FastGPT Retrieval**
   - A client (e.g., `test_embedding_model.py`) sends raw text to the Embedding Service.
   - Embedding Service returns a vector according to the specified model.
   - Client then queries FastGPT’s `/v1/search` with that vector to retrieve relevant documents.
   - Results help evaluate which embedding model yields the best retrieval performance.

3. **FastGPT → LLM Batch Query**
   - The LLM query script constructs prompts (possibly concatenating retrieved documents from step 2).
   - Sends each prompt to FastGPT’s Chat Completions endpoint.
   - Aggregates and stores responses for further analysis or direct use.

4. **LVM Query → Intermediate Storage / Message Bus**
   - Users or automated pipelines send images (plus optional text prompts) to each Vision+Language model endpoint.
   - The model processes the image+text pair and outputs structured data (e.g., JSON with detected entities or answers).
   - Outputs are either:
     - Written directly into a ClickHouse table for batch analytics.
     - Published to a Kafka topic for real-time consumption by other services.

5. **ClickHouse / Kafka → Similarity Evaluation**
   - The Jaccard similarity script extracts model outputs from ClickHouse (or consumes from Kafka).
   - Compares against ground truth from an Excel file.
   - Computes per-model similarity metrics and writes a final report in Excel.

---

## 3. Key Components and Responsibilities

### 3.1 FastGPT Knowledge Base
- **Deployment**: Docker-based installation following the FastGPT Docker Guide (see `docs/installation.md`).
- **Primary Functions**:
  - Document indexing and hybrid search.
  - LLM inference endpoint.
- **Endpoints**:
  - `POST /v1/embeddings` (for external embedding services).
  - `POST /v1/search` (semantic or hybrid search).
  - `POST /v1/chat/completions` (ChatGPT-style LLM queries).

### 3.2 Embedding Service
- **Framework**: Flask.
- **Models Supported**:
  - `pubmedbert`
  - `all-MiniLM-L6-v2`
  - `bge-large-en-v1.5`
  - `gte-large`
- **Endpoint**: 

```
POST /v1/embeddings
Request body:
{
"input": \["text1", "text2", ...],
"model": "all-MiniLM-L6-v2"
}
Response body:
\[
\[0.123, -0.456, ...],   // normalized vector for "text1"
\[0.789,  0.012, ...]    // normalized vector for "text2"
]
```

### 3.3 LLM Batch Query
- **Script**: `src/llm_query/llm_query.py`
- **Function**:  
- Reads a list of prompts or documents from a CSV or JSON file.
- Sends concurrent requests to FastGPT’s Chat Completions endpoint.
- Outputs responses to a unified JSON/CSV for further analysis.

### 3.4 LVM Query
- **Models & Deployment**:
1. **LLaVa:34B**  
   - Pull command: `ollama pull llava:34b`  
   - Run command: `ollama run llava:34b`  
2. **Llama-3.2-11B-Vision**  
   - Dependencies: `vllm` (install via `pip install vllm`)  
   - Run command: `vllm serve "meta-llama/Llama-3.2-11B-Vision"`
3. **Phi-3-Vision-128k-Instruct**  
   - Run command: `vllm serve "microsoft/Phi-3-vision-128k-instruct"`
4. **Phi-3.5-Vision-Instruct**  
   - Run command: `vllm serve "microsoft/Phi-3.5-vision-instruct"`
5. **Pixtral-12B-2409**  
   - Run command: `vllm serve "mistralai/Pixtral-12B-2409"`

- **Input/Output Formats**:  
- Accepts mixed JSON payloads with Base64-encoded image data and text prompts.  
- Returns JSON structured responses, e.g.:  
  ```json
  {
    "id": "request-xyz",
    "outputs": [
      {
        "text": "A cat sitting on a wooden floor.",
        "entities": [
          { "label": "Animal", "text": "cat", "confidence": 0.98 },
          …
        ]
      }
    ]
  }
  ```

- **Result Delivery**:  
- Write results to a ClickHouse table named (e.g.) `vision_outputs`, or  
- Publish to a Kafka topic called `vision_inference`.

### 3.5 Similarity Evaluation
- **Script**: `src/similarity/jaccard_similarity.py`
- **Workflow**:
1. **Load Ground Truth**: Read Excel file (e.g., `schema-test.xlsx`) containing annotated entities and relations.
2. **Fetch Model Outputs**: Query ClickHouse table to retrieve model inference JSON.
3. **Compute Sets**: Parse JSON to extract entity/relation sets.
4. **Calculate Similarity**:
   - Jaccard similarity for set overlap:  
     
     \[
       \text{Jaccard}(A, B) = \frac{|A \cap B|}{|A \cup B|}
     \]
   - Optionally compute EMD (Earth Mover’s Distance) for embeddings if needed.
5. **Export Results**: Combine per-model, per-record scores into `results_with_all_similarity_and_emd5.xlsx`.

---

## 4. Extensibility and Customization

- **Adding New Embedding Models**  
1. In `src/embedding_service/embedding_web.py`, add model-loading logic and define its API method.  
2. Update documentation in `docs/usage.md` to show how to request the new model.

- **Integrating Additional Multimodal Models**  
1. Add a new deployment section in `docs/lvm_deployment.md` with pull/run instructions.  
2. If desired, create a Python wrapper in `src/vision_models/` for that model to standardize input/output handling.

- **Switching Intermediate Storage**  
- If you want to replace ClickHouse with another analytics database (e.g., PostgreSQL or MongoDB), modify data ingestion and query logic in `src/similarity/jaccard_similarity.py`.  
- Update the “Intermediate Storage” section in this architecture file to reflect the new data store.

- **Custom Evaluation Metrics**  
- Extend `jaccard_similarity.py` or write new scripts under `src/similarity/` to compute additional metrics (e.g., BLEU scores, ROUGE, or cosine similarity between embedding vectors).

---

## 5. References

- FastGPT Official Documentation (for Docker deployment and API specification).  
- Source code files:  
- `src/import_data/import_data_to_knowledge_datatabase.py`  
- `src/embedding_service/embedding_web.py`  
- `src/llm_query/llm_query.py`  
- `src/similarity/jaccard_similarity.py`  
- Multimodal Model Deployment Guide: `docs/lvm_deployment.md`  
