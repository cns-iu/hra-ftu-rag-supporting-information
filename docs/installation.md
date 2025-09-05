# Installation Guide

This document outlines the steps required to install and configure all components needed for **HRAftu-LM-RAG**, including FastGPT, Python environment, ClickHouse, Kafka (optional), and vision-language model dependencies.

---

## 1. Prerequisites

1. **Operating System**: Ubuntu 20.04 or 22.04 (or any Linux distribution with Docker support).  
2. **Hardware**:  
   - CPU: 4+ cores recommended  
   - RAM: 16GB+  
   - GPU (optional for LVM inference): NVIDIA GPU with CUDA support  
3. **Docker & Docker Compose**: Required for FastGPT deployment.  
   - Install via:  
     ```
     sudo apt-get update
     sudo apt-get install -y docker.io docker-compose
     sudo usermod -aG docker $USER  # Allow non-root docker usage
     ```  
4. **Python**: Version 3.8 or newer.  
5. **Ollama (optional)**: For LLaVa model deployments.  
   - Download & install from [Ollama official site](https://ollama.com/) or via Homebrew (macOS)  
6. **pip / venv / conda**: For Python virtual environment management.  
7. **ClickHouse (optional)**: For similarity evaluation storage.  
8. **Kafka (optional)**: If streaming LVM outputs via message bus.  

---

## 2. FastGPT Setup

HRAftu-LM-RAG relies on FastGPT as its knowledge base and retrieval engine. Follow these steps to deploy FastGPT using Docker.

1. **Clone FastGPT repository or download the Docker Compose file**  
   You can either pull the official FastGPT Docker Compose setup or refer to the Docker YAML configuration.

2. **Create a directory for FastGPT**  
   ```bash
   mkdir fastgpt && cd fastgpt
   ````

3. **Download `docker-compose.yml`**
   Get the latest `docker-compose.yml` from FastGPT’s documentation or GitHub:

   ```bash
   curl -O https://raw.githubusercontent.com/fastgpt/fastgpt/main/docker-compose.yml
   ```
4. **Configure Environment Variables**
   Create a file named `.env` in the same directory with the following content (update values as needed):

   ```ini
   # FastGPT environment variables
   FASTGPT_HOST=0.0.0.0
   FASTGPT_PORT=3000
   FASTGPT_ADMIN_USER=admin
   FASTGPT_ADMIN_PASSWORD=your_password
   ```
5. **Start FastGPT Services**

   ```bash
   docker-compose up -d
   ```

   * This will launch the FastGPT API server, vector indexer, and any supporting components (PostgreSQL, Redis, etc.).
6. **Verify FastGPT**

   * Open a browser and navigate to `http://localhost:3000`.
   * Log in using the admin credentials (`admin` / `your_password`).
   * Confirm that you can access the FastGPT web UI and API endpoints.

> **Note:** For production deployments or custom configurations (TLS, load balancing), refer to the official FastGPT documentation: [https://doc.tryfastgpt.ai/docs/development/docker/](https://doc.tryfastgpt.ai/docs/development/docker/)

---

## 3. Python Environment & Dependencies

Create an isolated Python environment and install all required packages for HRAftu-LM-RAG.

1. **Clone HRAftu-LM-RAG Repository**

   ```bash
   git clone https://github.com/YourUsername/HRAftu-LM-RAG.git
   cd HRAftu-LM-RAG
   ```
2. **Create a Virtual Environment**
   Using `venv`:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   Or using `conda`:

   ```bash
   conda create -n hraftu python=3.8 -y
   conda activate hraftu
   ```
3. **Install Python Dependencies**

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

   The `requirements.txt` should include (but not be limited to):

   ```text
   torch>=2.0.0
   transformers>=4.30.0
   flask>=2.2.0
   pandas>=1.5.0
   requests>=2.28.0
   clickhouse-driver>=0.2.1
   Pillow>=9.0.0
   openpyxl>=3.0.0
   vllm>=0.5.0
   ```
4. **Environment Configuration File**
   Copy the example configuration file and update fields:

   ```bash
   mkdir config
   cp config/example_config.yaml config/config.yaml
   ```

   Edit `config/config.yaml` and set:

   ```yaml
   fastgpt:
     api_key: "YOUR_FASTGPT_API_KEY"
     host: "http://localhost:3000"

   vision:
     llama32_device: "cuda:0"
     phi3_device: "cuda:1"
     phi35_device: "cuda:2"
     pixtral:
       ip_list_file: "config/vision_nodes.txt"
       ports: [34444, 44445, 44446, 44449]

   clickhouse:
     host: "localhost"
     port: 9000
     user: "default"
     password: ""
     database: "clkg"
   ```

   * Replace `YOUR_FASTGPT_API_KEY` with the key obtained from your FastGPT instance.
   * Adjust device IDs or ports as per your hardware and network setup.

---

## 4. ClickHouse Installation (Optional)

If you plan to run **Similarity Evaluation** with ClickHouse, install and configure ClickHouse server:

1. **Install ClickHouse**

   ```bash
   # Official Debian/Ubuntu repository
   sudo apt-get install -y apt-transport-https ca-certificates dirmngr
   sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv E0C56BD4
   echo "deb https://repo.clickhouse.com/deb/stable/ main/" | sudo tee /etc/apt/sources.list.d/clickhouse.list
   sudo apt-get update
   sudo apt-get install -y clickhouse-server clickhouse-client
   ```
2. **Start ClickHouse Service**

   ```bash
   sudo service clickhouse-server start
   ```
3. **Verify Installation**

   ```bash
   clickhouse-client --query="SELECT version();"
   ```
4. **Database & Table Setup**

   * Create a database (if not using `clkg`):

     ```sql
     CREATE DATABASE clkg;
     ```
   * Create a table for storing LVM outputs (example schema):

     ```sql
     CREATE TABLE clkg.vision_outputs (
       id String,
       model String,
       output_json String,
       timestamp DateTime
     ) ENGINE = MergeTree()
     ORDER BY (model, id);
     ```
   * Adjust schema as needed for your JSON structure.

> **Note:** Kafka can also be used for streaming data. If you choose Kafka, install via:
>
> ```bash
> sudo apt-get install -y kafka
> # Configure server.properties (broker.id, zookeeper.connect, etc.)
> sudo service kafka start
> ```
>
> Then create a topic (e.g., `vision_inference`):
>
> ```bash
> kafka-topics.sh --create --topic vision_inference --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
> ```

---

## 5. LVM Prerequisites (Ollama & vLLM)

To deploy and query vision-language models (LLaVa, Llama-3.2-Vision, Phi-3-Vision, Phi-3.5-Vision, Pixtral), follow these steps:

### 5.1 Ollama (LLaVa:34B)

1. **Install Ollama CLI**

   * macOS (Homebrew):

     ```bash
     brew install ollama
     ```
   * Ubuntu/Debian: Download the `.deb` from [Ollama Releases](https://ollama.com/download) and install:

     ```bash
     sudo dpkg -i ollama_<version>_linux_amd64.deb
     ```
2. **Pull LLaVa Model**

   ```bash
   ollama pull llava:34b
   ```
3. **Verify Model**

   ```bash
   ollama list
   ```
4. **Run LLaVa Service**

   ```bash
   ollama run llava:34b
   ```

   * By default, Ollama listens on `http://localhost:11434` (check CLI docs for custom port).
   * Example request:

     ```bash
     curl -X POST http://localhost:11434/completions \
       -H "Content-Type: application/json" \
       -d '{"prompt": "Describe this image: <Base64-encoded data>"}'
     ```

### 5.2 vLLM (Other Vision-Language Models)

1. **Install vLLM**

   ```bash
   pip install vllm
   ```

2. **Pull or Reference Model**
   Ensure you have access to Hugging Face or other model repositories.

3. **Llama-3.2-11B-Vision**

   ```bash
   vllm serve "meta-llama/Llama-3.2-11B-Vision" --port 8000
   ```

   * The service exposes an HTTP endpoint at `http://localhost:8000` by default.
   * Example payload (JSON):

     ```json
     {
       "inputs": [
         { "type": "image", "data": "<Base64 or URL>" },
         { "type": "text", "text": "Describe this scene." }
       ]
     }
     ```

4. **Phi-3-Vision-128k-Instruct**

   ```bash
   vllm serve "microsoft/Phi-3-vision-128k-instruct" --port 8001
   ```

5. **Phi-3.5-Vision-Instruct**

   ```bash
   vllm serve "microsoft/Phi-3.5-vision-instruct" --port 8002
   ```

6. **Pixtral-12B-2409**

   ```bash
   vllm serve "mistralai/Pixtral-12B-2409" --port 8003
   ```

7. **Verify Services**

   * Check logs to confirm that models are loaded and listening on respective ports.
   * Use a test request via `curl` or a simple Python HTTP client to validate inference.

> **Tip:** For GPU acceleration, ensure your drivers and CUDA toolkit are properly installed. Add `--device cuda:0` (or appropriate device) to the `vllm serve` command if needed.

---

## 6. Final Verification

1. **FastGPT**: Visit `http://localhost:3000` and confirm the web UI is accessible.
2. **Embedding Service**: In a separate terminal, run:

   ```bash
   python src/embedding_service/embedding_web.py --port 55443
   ```

   Then test with:

   ```bash
   curl -X POST http://localhost:55443/v1/embeddings \
     -H "Content-Type: application/json" \
     -d '{"input": ["Test sentence"], "model": "all-MiniLM-L6-v2"}'
   ```

   Expect a JSON array of embedding vectors.
3. **LLM Batch Query**: Prepare a sample CSV/JSON of prompts and run:

   ```bash
   python src/llm_query/llm_query.py --input_file examples/sample_prompts.csv --output_file output_llm.json
   ```

   Verify `output_llm.json` contains responses.
4. **LVM Query**: Send a test request to each vision-language endpoint (e.g., LLaVa)

   ```bash
   curl -X POST http://localhost:11434/completions \
     -H "Content-Type: application/json" \
     -d '{"prompt": "<Base64 image> Describe this image."}'
   ```

   Ensure a structured JSON response is returned.
5. **ClickHouse**:

   ```bash
   clickhouse-client --query="SHOW DATABASES;"
   ```

   Confirm that the `clkg` database exists and the `vision_outputs` table is present.
6. **Similarity Script**: Run:

   ```bash
   python src/similarity/jaccard_similarity.py --ground_truth schema-test.xlsx --clickhouse_table vision_outputs --output results_with_all_similarity_and_emd5.xlsx
   ```

   Check that `results_with_all_similarity_and_emd5.xlsx` is generated.

Upon successful verification of each component, your HRAftu-LM-RAG environment is ready for downstream tasks.
