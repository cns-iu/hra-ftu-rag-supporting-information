# LVM Deployment Guide (lvm_deployment.md)

This document provides detailed instructions on how to deploy and run various vision-language models (LVMs) supported by **HRAftu-LM-RAG**. Each subsection covers model-specific prerequisites, pull commands, run commands, and example inference requests.

---

## 1. Overview

HRAftu-LM-RAG integrates the following LVMs:

1. **LLaVa:34B** (via Ollama)  
2. **Llama-3.2-11B-Vision** (via vLLM)  
3. **Phi-3-Vision-128k-Instruct** (via vLLM)  
4. **Phi-3.5-Vision-Instruct** (via vLLM)  
5. **Pixtral-12B-2409** (via vLLM)  

These models are queried separately from standard LLM (text-only) queries. Each model exposes its own HTTP endpoint. The recommended setup uses **Ollama** for LLaVa and **vLLM** for the remaining models.

---

## 2. Common Prerequisites

Before deploying any LVM, ensure the following prerequisites are met:

- **GPU Drivers & CUDA Toolkit**  
  - For optimal performance, install NVIDIA drivers and CUDA (version compatible with your GPU and PyTorch).  
- **Python Environment**  
  - Ensure Python 3.8+ is installed.  
  - Activate your virtual environment (`venv` or `conda`).  
- **vLLM**  
  - Install via `pip install vllm`.  
  - Verify installation by running `vllm --help`.  
- **Ollama (for LLaVa)**  
  - Download & install the Ollama CLI from [ollama.com](https://ollama.com/) or via Homebrew on macOS:  
    ```bash
    brew install ollama
    ```  
  - Verify via `ollama --help`.  

---

## 3. LLaVa:34B (Ollama)

LLaVa:34B is a large-scale vision-language model provided through the Ollama registry.

### 3.1 Pull Command

```bash
ollama pull llava:34b
````

* This command downloads and caches the LLaVa:34B model locally.
* Verify by running:

  ```bash
  ollama list
  ```

  You should see `llava:34b` in the model list.

### 3.2 Run Command

```bash
ollama run llava:34b
```

* By default, Ollama will start a local HTTP server on port `11434`.
* To specify a custom port, use:

  ```bash
  ollama run llava:34b --port 12345
  ```

### 3.3 Inference Examples

* **Endpoint**: `POST http://localhost:11434/completions`
* **Request Payload** (example):

  ```json
  {
    "prompt": "Describe this image: <Base64-encoded-image-data>"
  }
  ```
* **`curl` Example**:

  ```bash
  curl -X POST http://localhost:11434/completions \
    -H "Content-Type: application/json" \
    -d '{
      "prompt": "Describe this image: <Base64-encoded-image>"
    }'
  ```
* **Expected Response**:

  ```json
  {
    "id": "abc123",
    "choices": [
      { "text": "A dog is playing in a grassy field.", "finish_reason": "stop" }
    ]
  }
  ```

---

## 4. Llama-3.2-11B-Vision (vLLM)

Llama-3.2-11B-Vision is an open-source vision-language model accessible via Hugging Face.

### 4.1 Pull or Reference Model

No explicit pull is required for vLLM; vLLM will download weights at first serve. Ensure you have network access to Hugging Face.

### 4.2 Run Command

```bash
vllm serve "meta-llama/Llama-3.2-11B-Vision" --port 8000
```

* By default, vLLM listens on `http://0.0.0.0:8000`.
* To specify GPU device (e.g., `cuda:0`):

  ```bash
  vllm serve "meta-llama/Llama-3.2-11B-Vision" --port 8000 --device cuda:0
  ```

### 4.3 Inference Examples

* **Endpoint**: `POST http://localhost:8000`
* **Request Payload** (example):

  ```json
  {
    "inputs": [
      { "type": "image", "data": "<Base64-encoded-image>" },
      { "type": "text", "text": "What objects do you see in this image?" }
    ]
  }
  ```
* **`curl` Example**:

  ```bash
  curl -X POST http://localhost:8000 \
    -H "Content-Type: application/json" \
    -d '{
      "inputs": [
        { "type": "image", "data": "<Base64-encoded-image>" },
        { "type": "text", "text": "What objects do you see in this image?" }
      ]
    }'
  ```
* **Expected Response**:

  ```json
  {
    "id": "req-456",
    "outputs": [
      { "text": "I see a cat sitting on a windowsill.", "entities": [] }
    ]
  }
  ```

---

## 5. Phi-3-Vision-128k-Instruct (vLLM)

Phi-3-Vision-128k-Instruct is a specialized vision-language model from Microsoft.

### 5.1 Run Command

```bash
vllm serve "microsoft/Phi-3-vision-128k-instruct" --port 8001
```

* Ensure GPU availability; add `--device cuda:1` if needed.

### 5.2 Inference Examples

* **Endpoint**: `POST http://localhost:8001`
* **Request Payload**:

  ```json
  {
    "inputs": [
      { "type": "image", "data": "<Base64>" },
      { "type": "text", "text": "Identify any medical anomalies in this X-ray image." }
    ]
  }
  ```
* **`curl` Example**:

  ```bash
  curl -X POST http://localhost:8001 \
    -H "Content-Type: application/json" \
    -d '{
      "inputs": [
        { "type": "image", "data": "<Base64>" },
        { "type": "text", "text": "Identify any medical anomalies in this X-ray image." }
      ]
    }'
  ```
* **Expected Response**:

  ```json
  {
    "id": "req-789",
    "outputs": [
      {
        "text": "There is a small opacity in the lower right lung field.",
        "entities": [{ "label": "Anomaly", "text": "opacity", "confidence": 0.92 }]
      }
    ]
  }
  ```

---

## 6. Phi-3.5-Vision-Instruct (vLLM)

Phi-3.5-Vision-Instruct is an enhanced version for broader vision-language tasks.

### 6.1 Run Command

```bash
vllm serve "microsoft/Phi-3.5-vision-instruct" --port 8002
```

* Add `--device cuda:2` if using a specific GPU.

### 6.2 Inference Examples

* **Endpoint**: `POST http://localhost:8002`
* **Request Payload**:

  ```json
  {
    "inputs": [
      { "type": "image", "data": "<Base64>" },
      { "type": "text", "text": "Extract any chemical structures from this image." }
    ]
  }
  ```
* **`curl` Example**:

  ```bash
  curl -X POST http://localhost:8002 \
    -H "Content-Type: application/json" \
    -d '{
      "inputs": [
        { "type": "image", "data": "<Base64>" },
        { "type": "text", "text": "Extract any chemical structures from this image." }
      ]
    }'
  ```
* **Expected Response**:

  ```json
  {
    "id": "req-012",
    "outputs": [
      {
        "text": "I see ethanol and benzene rings.",
        "entities": [
          { "label": "Molecule", "text": "ethanol", "confidence": 0.87 },
          { "label": "Molecule", "text": "benzene", "confidence": 0.90 }
        ]
      }
    ]
  }
  ```

---

## 7. Pixtral-12B-2409 (vLLM)

Pixtral-12B-2409 is a Mistral-based model optimized for multimodal tasks.

### 7.1 Run Command

```bash
vllm serve "mistralai/Pixtral-12B-2409" --port 8003
```

* Use `--device cuda:3` to specify GPU if required.

### 7.2 Inference Examples

* **Endpoint**: `POST http://localhost:8003`
* **Request Payload**:

  ```json
  {
    "inputs": [
      { "type": "image", "data": "<Base64>" },
      { "type": "text", "text": "Describe the scene and list any textual labels visible." }
    ]
  }
  ```
* **`curl` Example**:

  ```bash
  curl -X POST http://localhost:8003 \
    -H "Content-Type: application/json" \
    -d '{
      "inputs": [
        { "type": "image", "data": "<Base64>" },
        { "type": "text", "text": "Describe the scene and list any textual labels visible." }
      ]
    }'
  ```
* **Expected Response**:

  ```json
  {
    "id": "req-345",
    "outputs": [
      {
        "text": "A street sign says 'Main St.' and a traffic light is green.",
        "entities": [ { "label": "Text", "text": "Main St.", "confidence": 0.95 } ]
      }
    ]
  }
  ```

---

## 8. Tips & Troubleshooting

* **Memory Constraints**:

  * Vision-language models are large (≥11B parameters). Ensure at least 16GB of GPU memory is available.
  * If you encounter out-of-memory errors, consider using a smaller batch size or switching to CPU (with performance trade-offs).

* **Port Conflicts**:

  * If the default ports (`11434`, `8000-8003`) are in use, specify alternative ports via the `--port` flag.

* **Model Download Issues**:

  * Check internet connectivity and Hugging Face credentials (if private).
  * For Ollama, ensure you have sufficient disk space and proper permissions.

* **CUDA Compatibility**:

  * Verify that your PyTorch and vLLM installations match your CUDA version.
  * Use `nvidia-smi` to confirm GPU availability and driver version.

* **API Validation**:

  * Test simple `curl` requests to verify the model service is responding before integrating into downstream pipelines.

