# Import necessary libraries
import argparse
import sys
import logging
import os
import urllib3
import json
from flask import Flask, request
import torch
import time
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer
import torch.nn.functional as F
from torch import Tensor
import traceback

# Disable SSL warnings from urllib3
urllib3.disable_warnings()

# Logging configuration
current_time = time.strftime("%Y-%m-%d_%H-%M-%S")
current_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(current_dir, 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logger = logging.getLogger('multi_gpu_logger')
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler(os.path.join(log_dir, 'embed.log'))
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Initialize Flask app
app = Flask(__name__)

# Model/tokenizer placeholders
pubmedbert_tokenizer = None
pubmedbert_model = None

all_MiniLM_L6_v2_tokenizer = None
all_MiniLM_L6_v2_model = None

bge_large_en_v15_tokenizer = None
bge_large_en_v15_model = None

gte_large_tokenizer = None
gte_large_model = None

# Additional model placeholders (if necessary)
S_PubMedBert_MS_MARCO_tokenizer = None
S_PubMedBert_MS_MARCO_model = None

yes_loc = None

bce_rerank_tokenizer = None
bce_rerank_model = None

bge_reranker_large_tokenizer = None
bge_reranker_large_model = None

bge_reranker_v2_m3_tokenizer = None
bge_reranker_v2_m3_model = None

mxbai_rerank_large_v1_model = None


def load_model(models_to_load=None):
    """
    Load only the models specified in models_to_load. If none are specified, exit the script.
    :param models_to_load: list of model names to load, e.g., ["bge_reranker_large", "gte_large"]
    """
    global pubmedbert_tokenizer, pubmedbert_model, \
           all_MiniLM_L6_v2_tokenizer, all_MiniLM_L6_v2_model, \
           bge_large_en_v15_tokenizer, bge_large_en_v15_model, \
           gte_large_tokenizer, gte_large_model
    if models_to_load is None:
        models_to_load = [
            "pubmedbert", "all_MiniLM_L6_v2", "bge_large_en_v15", "gte_large"
        ]
        sys.exit(1)

    # Load each model based on name
    for model_name in models_to_load:
        try:
            if model_name == "pubmedbert":
                pubmedbert_tokenizer = AutoTokenizer.from_pretrained("microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext")
                pubmedbert_model = AutoModel.from_pretrained("microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract-fulltext", device_map="auto")
                logger.info("Loaded pubmedbert model and tokenizer.")
            elif model_name == "all_MiniLM_L6_v2":
                all_MiniLM_L6_v2_tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
                all_MiniLM_L6_v2_model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2", device_map="auto")
                logger.info("Loaded all_MiniLM_L6_v2 model and tokenizer.")
            elif model_name == "bge_large_en_v15":
                bge_large_en_v15_tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-large-en-v1.5")
                bge_large_en_v15_model = AutoModel.from_pretrained("BAAI/bge-large-en-v1.5", device_map="auto")
                logger.info("Loaded bge_large_en_v15 model and tokenizer.")
            elif model_name == "gte_large":
                gte_large_tokenizer = AutoTokenizer.from_pretrained("thenlper/gte-large")
                gte_large_model = AutoModel.from_pretrained("thenlper/gte-large", device_map="auto")
                logger.info("Loaded gte_large model and tokenizer.")
            # Add more models as needed
        except Exception as e:
            logger.error(f"Error loading {model_name}: {e}")
            traceback.print_exc()


def pubmedbert(sentences):
    inputs = pubmedbert_tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')
    inputs = inputs.to(pubmedbert_model.device)
    with torch.no_grad():
        outputs = pubmedbert_model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1)
    return F.normalize(embeddings, p=2, dim=1).cpu().tolist()


def all_MiniLM_L6_v2(sentences):
    inputs = all_MiniLM_L6_v2_tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')
    inputs = inputs.to(all_MiniLM_L6_v2_model.device)
    with torch.no_grad():
        outputs = all_MiniLM_L6_v2_model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1)
    return F.normalize(embeddings, p=2, dim=1).cpu().tolist()


def bge_large_en_v15(sentences):
    inputs = bge_large_en_v15_tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')
    inputs = inputs.to(bge_large_en_v15_model.device)
    with torch.no_grad():
        outputs = bge_large_en_v15_model(**inputs)
    cls_embeddings = outputs.pooler_output if hasattr(outputs, 'pooler_output') else outputs.last_hidden_state[:,0]
    return F.normalize(cls_embeddings, p=2, dim=1).cpu().tolist()


def gte_large(sentences):
    inputs = gte_large_tokenizer(sentences, padding=True, truncation=True, return_tensors='pt')
    inputs = inputs.to(gte_large_model.device)
    with torch.no_grad():
        outputs = gte_large_model(**inputs)
    embeddings = outputs.last_hidden_state.mean(dim=1)
    return F.normalize(embeddings, p=2, dim=1).cpu().tolist()


@app.route('/v1/embeddings', methods=['POST'])
def embeddings_endpoint():
    try:
        json_data = request.get_json()
        sentences = json_data.get('input', [])
        model_name = json_data.get('model', '')

        model_map = {
            'pubmedbert': pubmedbert,
            'all-MiniLM-L6-v2': all_MiniLM_L6_v2,
            'bge-large-en-v1.5': bge_large_en_v15,
            'gte-large': gte_large,
        }

        if model_name not in model_map:
            return { 'error': f'Model {model_name} not supported.' }, 400

        func = model_map[model_name]
        embeddings = func(sentences)

        return {
            'object': 'list',
            'data': [ { 'sentence': s, 'embedding': e } for s, e in zip(sentences, embeddings)],
            'model': model_name,
            'usage': { 'sentence_count': len(sentences) }
        }
    except Exception as e:
        logger.error(f"Error in /v1/embeddings: {e}")
        traceback.print_exc()
        return { 'error': str(e) }, 500


def main():
    parser = argparse.ArgumentParser(description='Run embedding service')
    parser.add_argument('--port', type=int, default=55443, help='Port to run the service on')
    parser.add_argument('models', nargs='*', help='List of models to load')
    args = parser.parse_args()

    if not args.models:
        default_models = ['pubmedbert', 'all_MiniLM_L6_v2', 'bge_large_en_v15', 'gte_large']
        models_to_load = default_models
    else:
        models_to_load = args.models

    load_model(models_to_load)
    app.run(host='0.0.0.0', port=args.port, debug=False)


if __name__ == '__main__':
    main()
