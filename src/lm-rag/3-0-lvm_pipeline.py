"""
Language Vision Model (LVM) pipelines for Llama-3.2, Phi-3, Phi-3.5, Pixtral, and LlaVA/Ollama.
Each pipeline loads its model/processor (or service endpoints), processes an image record, and sends results to Kafka.
"""
import time
import traceback
import base64
import json
import random
import subprocess
import re
import requests

import torch
from PIL import Image
from transformers import (MllamaForConditionalGeneration, AutoProcessor,
                          AutoModelForCausalLM)

import config  
from kafka_producer import produce_record_to_kafka
from logger import logger

# ---- Llama-3.2 Pipeline ----
def load_llama_vision_model_and_processor(device: str):
    """Load Llama-3.2 vision model and processor."""
    model = MllamaForConditionalGeneration.from_pretrained(
        "meta-llama/Llama-3.2-11B-Vision-Instruct",
        device_map="auto" if torch.cuda.is_available() and device.startswith("cuda") else None
    )
    processor = AutoProcessor.from_pretrained("meta-llama/Llama-3.2-11B-Vision-Instruct")
    return model, processor


def process_llama32_image(record: dict, model, processor, device: str, worker_id: int):
    """Process one image record through Llama-3.2 vision-instruct."""
    start = time.time()
    try:
        prompt = record["entity_prompt"]
        img = Image.open(record["img_path"]).convert("RGB")
        chat = processor.apply_chat_template(images=img, prompt=prompt)
        inputs = processor(
            text=chat["text"], images=chat["images"], return_tensors="pt"
        ).to(device)
        outputs = model.generate(**inputs, max_new_tokens=3000)
        answer = processor.decode(outputs, skip_special_tokens=True)
        record["llama32_entity"] = answer
        produce_record_to_kafka(config.KAFKA_TOPIC, record, worker_id)
    except Exception:
        logger.error("Llama-3.2 pipeline error", exc_info=True)
    finally:
        logger.info(f"Llama-3.2 done in {time.time() - start:.2f}s")

# ---- Phi-3 Pipeline ----
def load_phi3_model_and_processor(device: str):
    """Load Phi-3 vision model and processor."""
    model = AutoModelForCausalLM.from_pretrained(
        "microsoft/Phi-3-vision-128k-instruct",
        trust_remote_code=True,
        device_map="auto" if torch.cuda.is_available() and device.startswith("cuda") else None
    )
    processor = AutoProcessor.from_pretrained("microsoft/Phi-3-vision-128k-instruct")
    return model, processor


def process_phi3_image(record: dict, model, processor, device: str, worker_id: int):
    """Process one image record through Phi-3 vision-instruct."""
    start = time.time()
    try:
        prompt = f"<|image_1|>{record['entity_prompt']}"
        img = Image.open(record['img_path']).convert('RGB')
        inputs = processor(prompt, images=[img], return_tensors='pt').to(device)
        outputs = model.generate(**inputs, do_sample=False)
        answer = processor.batch_decode(outputs, skip_special_tokens=True)[0]
        record['phi3_entity'] = answer
        produce_record_to_kafka(config.KAFKA_TOPIC, record, worker_id)
    except Exception:
        logger.error("Phi-3 pipeline error", exc_info=True)
    finally:
        logger.info(f"Phi-3 done in {time.time() - start:.2f}s")

# ---- Phi-3.5 Pipeline ----
def load_phi35_model_and_processor(device: str):
    """Load Phi-3.5 vision model and processor."""
    model = AutoModelForCausalLM.from_pretrained(
        "microsoft/Phi-3.5-vision-instruct",
        trust_remote_code=True,
        device_map="auto" if torch.cuda.is_available() and device.startswith("cuda") else None
    )
    processor = AutoProcessor.from_pretrained(
        "microsoft/Phi-3.5-vision-instruct",
        num_crops=4
    )
    return model, processor


def process_phi35_image(record: dict, model, processor, device: str, worker_id: int):
    """Process one image record through Phi-3.5 vision-instruct."""
    start = time.time()
    try:
        prompt = f"<|image_1|>{record['entity_prompt']}"
        img = Image.open(record['img_path']).convert('RGB')
        inputs = processor(prompt, images=[img], return_tensors='pt').to(device)
        outputs = model.generate(**inputs, max_new_tokens=2048)
        answer = processor.decode(outputs, skip_special_tokens=True)
        record['phi35_entity'] = answer
        produce_record_to_kafka(config.KAFKA_TOPIC, record, worker_id)
    except Exception:
        logger.error("Phi-3.5 pipeline error", exc_info=True)
    finally:
        logger.info(f"Phi-3.5 done in {time.time() - start:.2f}s")

# ---- Pixtral Service ----
def file_to_data_url(file_path: str) -> str:
    """Convert a file to a base64 data URL."""
    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    return f"data:image/png;base64,{b64}"


def extract_json_text(text: str) -> list:
    """Extract JSON objects from a text string."""
    matches = re.findall(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    results = []
    for m in matches:
        try:
            results.append(json.loads(m))
        except json.JSONDecodeError:
            continue
    return results


def send_pixtral_request(record: dict, worker_id: int):
    """Send image and prompt to Pixtral service, extract JSON response."""
    start = time.time()
    while True:
        try:
            host = random.choice(config.PIXTRAL_HOSTS)
            port = random.choice(config.PIXTRAL_PORTS)
            url = f"http://{host}:{port}/v1/generate"
            payload = {
                "prompt": record['entity_prompt'],
                "image": file_to_data_url(record['img_path'])
            }
            resp = requests.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            content = resp.text
            entities = extract_json_text(content)
            if entities:
                record['pixtral_entity'] = entities
                produce_record_to_kafka(config.KAFKA_TOPIC, record, worker_id)
                break
        except Exception:
            logger.error("Pixtral request error, retrying...", exc_info=True)
            time.sleep(5)
    logger.info(f"Pixtral done in {time.time() - start:.2f}s")

# ---- LlaVA (Ollama) Pipeline ----
def ollama_vision_task(record: dict, worker_id: int, ip_port_list: list):
    """Send image and prompt to Ollama LlaVA service, retry until success."""
    image_path = record.get('img_path', '')
    prompt = record.get('entity_prompt', '')
    start_time = time.time()
    while True:
        try:
            ip_port = random.choice(ip_port_list)
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode("utf-8")
            url = f"http://{ip_port}/api/generate"
            data = {
                "model": "llava:34b",
                "prompt": prompt,
                "stream": False,
                "images": [base64_image]
            }
            res = requests.post(url, json=data, timeout=60).json()
            response_text = res.get('response', '')
            if response_text:
                break
            else:
                logger.error(f"worker-{worker_id}, ip:{ip_port} - {res.get('error','')}")
                time.sleep(5)
        except Exception as e:
            logger.error(f"Ollama LlaVA error: {e}")
            return
    record['llava_entity'] = response_text


def start_pixtral_service(continued: bool = False):
    """Start Pixtral services on remote hosts via SSH and verify connectivity."""
    if continued and os.path.exists(config.VISION_FILENAME):
        return
    services = []
    for host in config.PIXTRAL_HOSTS:
        for gpu, port in enumerate(config.PIXTRAL_PORTS):
            cmd = (
                f"ssh {host} 'nohup vllm serve {config.PIXTRAL_MODEL} "
                f"--device cuda:{gpu} --port {port} > /dev/null 2>&1 &'"
            )
            subprocess.Popen(cmd, shell=True)
            services.append((host, port))
    time.sleep(400)
    available = []
    for host, port in services:
        try:
            subprocess.check_call([
                "curl", "--connect-timeout", "5",
                f"http://{host}:{port}/healthz"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            available.append((host, port))
        except subprocess.CalledProcessError:
            continue
    with open(config.VISION_FILENAME, 'w') as f:
        for host, port in available:
            f.write(f"{host}:{port}\n")
    logger.info("Pixtral services available at: %s", available)

# Example usage in main
if __name__ == '__main__':
    record = {'entity_prompt': 'Extract entities from this image.', 'img_path': 'path/to/image.png'}
    device = config.DEVICE

    # Llama-3.2
    llama_model, llama_processor = load_llama_vision_model_and_processor(device)
    process_llama32_image(record.copy(), llama_model, llama_processor, device, worker_id=0)

    # Phi-3
    phi_model, phi_processor = load_phi3_model_and_processor(device)
    process_phi3_image(record.copy(), phi_model, phi_processor, device, worker_id=0)

    # Phi-3.5
    phi35_model, phi35_processor = load_phi35_model_and_processor(device)
    process_phi35_image(record.copy(), phi35_model, phi35_processor, device, worker_id=0)

    # Pixtral
    start_pixtral_service()
    send_pixtral_request(record.copy(), worker_id=0)

    # LlaVA (Ollama)
    ollama_vision_task(record.copy(), worker_id=0, ip_port_list=config.OLLAMA_IP_PORTS)
    produce_record_to_kafka(config.KAFKA_TOPIC, record, worker_id=0)
