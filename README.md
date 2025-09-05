# AI-Supported Extraction of Functional Tissue Unit Properties for Human Reference Atlas Construction


---

The Human Reference Atlas (HRA) effort brings together experts from more than 25 international consortia to capture the multiscale organization of the human body—from large anatomical organ systems (macro) to the single-cell level (micro). Functional tissue units (FTU, meso) in 10 organs have been detailed and 2D illustrations have been created by experts. Comprehensive FTU property characterization is essential for the HRA, but manual review of the vast number of scholarly publications is impractical. Here, we introduce Large-Model Retrieval-Augmented Generation for HRA FTUs (HRAftu-LM-RAG), an AI-driven framework for scalable and automated extraction of FTU-relevant properties from scholarly publications. This validated framework integrates Large Language Models for textual reasoning, Large Vision Models for visual interpretation, and Retrieval Augmented Generation for knowledge grounding, offering a balanced trade-off between accuracy and processing efficiency. We retrieved 244,640 PubMed Central publications containing 1,389,168 figures for 22 FTUs and identified 617,237 figures with microscopy and schematic images. From these images and associated text, we automatically extracted 331,189 scale bars and 1,719,138 biological entity mentions, along with donor metadata such as sex and age. 


## Introduction
This repository provides the supporting code and data for "AI-Supported Extraction of Functional Tissue Unit Properties for Human Reference Atlas Construction" paper, detailing the robust and scalable computation of scholarly evidence for the size, structure, and demographic differences of FTUs, facilitating the design and approval of future FTU illustrations during HRA construction.

### Workflow Diagram
<p align="center">
 <img src="vis/workflows.svg" alt="Example Image" width="700"/>
</p>

### Workflow Summary

<table>
  <tr>
    <th>Workflow</th>
    <th>Input</th>
    <th>Algorithm/Script</th>
    <th>Output</th>
  </tr>
  
  <tr>
    <td><b>WF1: Image-type categorization</b></td>
    <td>
      - <code>ftu_pub_pmc</code> table: <i>pmcid</i>, <i>graphic</i>, <i>caption</i>, <i>label</i>, <i>file_path</i><br>
      - <code>image_refs</code> table: <i>ref_text</i>
    </td>
    <td><a href="src/lm-rag/2-3-itype-run.py"><code>2-3-itype-run.py</code></a></td>
    <td>
      - Raw outputs from vision models: <i>llama</i>, <i>llava</i>, <i>phi3</i>, <i>phi35</i>, <i>pixtral</i><br>
      - Final image-type labels stored in <code>vision_llm</code> table: <i>micro</i>, <i>statis</i>, <i>schema</i>, <i>3d</i>, <i>chem</i>, <i>math</i>
    </td>
  </tr>
  
  <tr>
    <td><b>WF2: In-image text-term extraction</b></td>
    <td>
      - <code>image_node_lvm_total</code> table: <i>pmcid</i>, <i>graphic</i>, <i>file_path</i>
    </td>
    <td><a href="src/lm-rag/3-2-lvm-entity-run.py"><code>3-2-lvm-entity-run.py</code></a></td>
    <td>
      - Extracted in-image text terms stored in <code>image_node_lvm_total</code> table under <i>nodes</i> field
    </td>
  </tr>
  
  <tr>
    <td><b>WF3: Scale-bar extraction</b></td>
    <td>
      - <code>ftu_pub_pmc</code> table: <i>pmcid</i>, <i>graphic</i>, <i>caption</i><br>
      - <code>image_refs</code> table: <i>ref_text</i><br>
      - Filter: <code>vision_llm.micro = "Yes"</code>
    </td>
    <td><a href="src/lm-rag/4-2-sb-run.py"><code>4-2-sb-run.py</code></a></td>
    <td>
      - Scale bar information stored in <code>scale_bar_all_info</code> table:<br>
      <i>Descriptor Type</i>, <i>Value</i>, <i>Units</i>, <i>Notes</i>, <i>Panel</i>
    </td>
  </tr>
  
  <tr>
    <td><b>WF4: Donor-metadata extraction</b></td>
    <td>
      - <code>ftu_pub_pmc</code> table: <i>pmcid</i>, <i>graphic</i>, <i>caption</i><br>
      - <code>publication_summary</code> table: <i>abstract</i><br>
      - Filter: <code>vision_llm.micro = "Yes"</code> or <code>vision_llm.schema = "Yes"</code><br>
      - <code>image_node_lvm_total</code> table: <i>nodes</i>
    </td>
    <td><a href="src/lm-rag/5-1-donor-run.py"><code>5-1-donor-run.py</code></a></td>
    <td>
      - Donor metadata stored in <code>donor_meta_all_info</code> table:<br>
      <i>species</i>, <i>sex</i>, <i>age</i>, <i>BMI</i>, <i>height</i>, <i>weight</i>
    </td>
  </tr>
  
  <tr>
    <td><b>WF5: AS+CT+B extraction</b></td>
    <td>
      - <code>ftu_pub_pmc</code> table: <i>pmcid</i>, <i>graphic</i>, <i>caption</i><br>
      - <code>image_node_lvm_total</code> table: <i>nodes</i><br>
      - Filter: <code>vision_llm.micro = "Yes"</code> or <code>vision_llm.schema = "Yes"</code>
    </td>
    <td><a href="src/lm-rag/6-1-bio-onto-run.py"><code>6-1-bio-onto-run.py</code></a></td>
    <td>
      - Biological entity terms stored in <code>bio_onto_all_info</code> table:<br>
      <i>entity</i> (AS, CT, B)
    </td>
  </tr>
  
</table>

## Repository Structure

```plain
├── data      # Input and output datasets, plus test data for validation
├── docs      # Detailed documentation (architecture, deployment, usage)
├── src       # Source code for data fetching, LLM/Vision pipelines, similarity scripts
├── vis       # Generated SVG figures used in the paper
```

* **data/**: Store raw and processed input data, output results, and any test datasets required to reproduce experiments.
* **docs/**: Markdown guides covering architecture (architecture.md), installation (installation.md), LLM deployment (llm\_deployment.md), vision-language model deployment (lvm\_deployment.md), and usage (usage.md).
* **src/**: Organized into submodules:

  * **data-fetching/**: Scripts for retrieving and preprocessing data from [BioPortal](https://bioportal.bioontology.org/), [OLS](https://www.ebi.ac.uk/ols4/), and [PMC](https://pmc.ncbi.nlm.nih.gov/), including fetching FTU descriptions, downloading and extracting PMC articles, and extracting image paths and metadata.
  * **lm-rag/**: Integrated Large Language Models (LLMs) and Large Vision Models (LVMs) pipelines covering Retrieval-Augmented Generation (RAG), evaluations and batch running of FTU-related tasks, including image-type classification, image-entity extraction, scale bar extraction, donor metadata extraction and biology entities extraction.
  * **process-donor/** & **process-scale-bar/**: Post-processing scripts for cleaning and standardizing donor metadata metrics and extracted scale bar values.
* **vis/**: Contains SVG images from analysis results, presented in the paper.

## Installation

For full installation instructions, environment setup, and dependency management, see [docs/installation.md](docs/installation.md).

**Quick Start**:

1. Clone the repository:

   ```bash
   git clone https://github.com/cns-iu/hra-ftu-rag-supporting-information.git
   cd HRAftu-LM-RAG
   ```
2. Follow the steps in `docs/installation.md` to install system dependencies (Docker, Python, CUDA), set up containers, and verify services.

## Usage

Usage examples, command-line options, and configuration details are provided in [docs/usage.md](docs/usage.md).

**Common Workflows**:

* **Data Import**: Load PDF, TXT, DOCX files into FastGPT collections.
* **FTU Extraction**: Run LLM-RAG pipelines to extract scale bars and biological entities from images.
* **Similarity Evaluation**: Execute similarity scripts to compare model outputs with ground truth.

## Documentation

Access architectural diagrams, deployment guides, and model-specific instructions in the `docs/` folder:

* **Architecture**: `docs/architecture.md` Provides an overview of the system architecture, including module interactions, data flow diagrams, and component responsibilities.
* **LLM Deployment**: `docs/llm_deployment.md` Step-by-step instructions for environment setup, dependency installation, Docker and CUDA configuration, and verification tests.
* **Vision-Language Model Deployment**: `docs/lvm_deployment.md` Demonstrates common workflows with example commands, configuration parameters, and expected outputs for core functionalities such as data import, FTU extraction, and similarity evaluation.
* **Installation Guide**: `docs/installation.md` Covers deployment of Large Language Models, including model selection criteria, API configuration, and performance optimization strategies.
* **Usage Guide**: `docs/usage.md` Explains the vision-language model pipeline setup, detailing image preprocessing, model integration, and inference procedures.

## Data

The `data/` directory contains the following subdirectories and files:

* **bio-onto/**

  * `bio-onto-prompt.csv`: Prompts for biological ontology extraction.
  * `bio-onto-test-answer.csv`: Expected answers for ontology tests.
  * `selected_prompt.txt`: The chosen prompt template.

* **donor-meta/**

  * `prompt-donor.csv`: Prompts for donor metadata extraction.
  * `donor-test-answer.csv`: Expected donor metadata answers.
  * `selected_prompt.txt`: Chosen prompt template.
  * `age/`, `age_yearold/`, `bmi/`, `sex/`, `species/`: Each contains `<metric>_1.csv` (sample data) and `round.csv` (processing scripts for rounding values).

* **emb/**

  * `test_questions.csv`: Embedding-based similarity test questions.

* **img-entity/**

  * `lvm-entity-prompt.csv`: Prompts for LVM-based entity extraction.
  * `lvm-entity-testdata.tar.gz`: Compressed test images for entity extraction.
  * `lvm-test-answer.csv`: Expected outputs for image-entity tasks.
  * `selected-prompt.txt`: The chosen image-entity prompt template.

* **img-type/**

  * `prompt.txt`: Prompt template for image type classification.
  * `test_img_info.json.gz`: JSON test file with image metadata.
  * `img-type-test-answer.csv`: Expected classification results.

* **input-data/**

  * `0-0-ftu-pmc-total.tar.gz`: Complete FTU–PMC dataset archive.
  * `0-1-oa-comm-ftu-pmcid-filepath.tar.gz`: Subset with FTU–PMC ID to filepath mappings.
  * `ftu-description-from-bioportal.csv`: FTU descriptions imported from BioPortal.
  * `organ-ftu-uberon.csv`: Mapping of organs to UBERON FTU terms.
  * **ftu-pmc-manual/**: Manually curated PMC search results for 22 FTUs, e.g., `pmc_result_<FTU name>.txt`.

* **scale-bar/**

  * `scale-bar-prompts.csv`: Prompts for scale bar detection and extraction.
  * `scale-bar-sample.csv`: Sample output file illustrating extracted scale bar values.
  * `selected_prompt.txt`: The chosen scale-bar prompt template.
  * **units-expression/**: CSV files for unit normalization (e.g., `um.csv`, `cm.csv`, `m.csv`, etc.).

* **vis-source-data/**

  * Source datasets (CSV, JSON, spreadsheets) used to generate the SVG figures in `vis/`. Follow the processing pipelines in `docs/usage.md` to regenerate visualizations.

> **Note**: Due to size constraints, raw data files are not stored in this repository. Please follow the data preparation steps in [`docs/installation.md`](docs/installation.md) to download and extract the required archives.

## Visualization

The `vis/` directory holds SVG images generated from analysis results, matching the figures in the paper. These include scale bar overlays, FTU schematics, and demographic plots.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
