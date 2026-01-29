---
tags:
- setfit
- sentence-transformers
- text-classification
- generated_from_setfit_trainer
widget:
- text: Implement a circular buffer
- text: What is a Fenwick tree?
- text: Implement LRU cache in Python
- text: Create quiz for comparison-based sorting
- text: I feel overwhelmed by all the concepts
metrics:
- accuracy
pipeline_tag: text-classification
library_name: setfit
inference: true
base_model: sentence-transformers/paraphrase-mpnet-base-v2
---

# SetFit with sentence-transformers/paraphrase-mpnet-base-v2

This is a [SetFit](https://github.com/huggingface/setfit) model that can be used for Text Classification. This SetFit model uses [sentence-transformers/paraphrase-mpnet-base-v2](https://huggingface.co/sentence-transformers/paraphrase-mpnet-base-v2) as the Sentence Transformer embedding model. A [LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html) instance is used for classification.

The model has been trained using an efficient few-shot learning technique that involves:

1. Fine-tuning a [Sentence Transformer](https://www.sbert.net) with contrastive learning.
2. Training a classification head with features from the fine-tuned Sentence Transformer.

## Model Details

### Model Description
- **Model Type:** SetFit
- **Sentence Transformer body:** [sentence-transformers/paraphrase-mpnet-base-v2](https://huggingface.co/sentence-transformers/paraphrase-mpnet-base-v2)
- **Classification head:** a [LogisticRegression](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html) instance
- **Maximum Sequence Length:** 512 tokens
- **Number of Classes:** 5 classes
<!-- - **Training Dataset:** [Unknown](https://huggingface.co/datasets/unknown) -->
<!-- - **Language:** Unknown -->
<!-- - **License:** Unknown -->

### Model Sources

- **Repository:** [SetFit on GitHub](https://github.com/huggingface/setfit)
- **Paper:** [Efficient Few-Shot Learning Without Prompts](https://arxiv.org/abs/2209.11055)
- **Blogpost:** [SetFit: Efficient Few-Shot Learning Without Prompts](https://huggingface.co/blog/setfit)

### Model Labels
| Label | Examples                                                                                                                                              |
|:------|:------------------------------------------------------------------------------------------------------------------------------------------------------|
| 3     | <ul><li>'Check if my trie is structured correctly'</li><li>'Verify my tree structure'</li><li>'Check if this is a DAG'</li></ul>                      |
| 1     | <ul><li>'Implement a trie data structure'</li><li>'Write function to validate BST'</li><li>"Code doesn't handle negative numbers"</li></ul>           |
| 0     | <ul><li>'Help me understand recursion'</li><li>'How does a B-tree work?'</li><li>'What is a Fenwick tree?'</li></ul>                                  |
| 4     | <ul><li>'This is too hard for me'</li><li>"I'm under too much pressure"</li><li>"I'm afraid I'm wasting my time"</li></ul>                            |
| 2     | <ul><li>'Give me problems on two pointers'</li><li>'Create assessment on shortest path algorithms'</li><li>'Quiz me about topological sort'</li></ul> |

## Uses

### Direct Use for Inference

First install the SetFit library:

```bash
pip install setfit
```

Then you can load this model and run inference.

```python
from setfit import SetFitModel

# Download from the 🤗 Hub
model = SetFitModel.from_pretrained("setfit_model_id")
# Run inference
preds = model("What is a Fenwick tree?")
```

<!--
### Downstream Use

*List how someone could finetune this model on their own dataset.*
-->

<!--
### Out-of-Scope Use

*List how the model may foreseeably be misused and address what users ought not to do with the model.*
-->

<!--
## Bias, Risks and Limitations

*What are the known or foreseeable issues stemming from this model? You could also flag here known failure cases or weaknesses of the model.*
-->

<!--
### Recommendations

*What are recommendations with respect to the foreseeable issues? For example, filtering explicit content.*
-->

## Training Details

### Training Set Metrics
| Training set | Min | Median | Max |
|:-------------|:----|:-------|:----|
| Word count   | 2   | 5.3483 | 10  |

| Label | Training Sample Count |
|:------|:----------------------|
| 0     | 53                    |
| 1     | 53                    |
| 2     | 53                    |
| 3     | 54                    |
| 4     | 54                    |

### Training Hyperparameters
- batch_size: (16, 16)
- num_epochs: (1, 1)
- max_steps: -1
- sampling_strategy: oversampling
- num_iterations: 20
- body_learning_rate: (2e-05, 2e-05)
- head_learning_rate: 2e-05
- loss: CosineSimilarityLoss
- distance_metric: cosine_distance
- margin: 0.25
- end_to_end: False
- use_amp: False
- warmup_proportion: 0.1
- l2_weight: 0.01
- seed: 42
- eval_max_steps: -1
- load_best_model_at_end: False

### Training Results
| Epoch  | Step | Training Loss | Validation Loss |
|:------:|:----:|:-------------:|:---------------:|
| 0.0015 | 1    | 0.3753        | -               |
| 0.0749 | 50   | 0.1834        | -               |
| 0.1497 | 100  | 0.0404        | -               |
| 0.2246 | 150  | 0.0026        | -               |
| 0.2994 | 200  | 0.0015        | -               |
| 0.3743 | 250  | 0.0011        | -               |
| 0.4491 | 300  | 0.0008        | -               |
| 0.5240 | 350  | 0.0007        | -               |
| 0.5988 | 400  | 0.0007        | -               |
| 0.6737 | 450  | 0.0006        | -               |
| 0.7485 | 500  | 0.0005        | -               |
| 0.8234 | 550  | 0.0005        | -               |
| 0.8982 | 600  | 0.0005        | -               |
| 0.9731 | 650  | 0.0005        | -               |

### Framework Versions
- Python: 3.11.9
- SetFit: 1.1.3
- Sentence Transformers: 5.2.0
- Transformers: 4.57.3
- PyTorch: 2.9.1+cpu
- Datasets: 4.5.0
- Tokenizers: 0.22.2

## Citation

### BibTeX
```bibtex
@article{https://doi.org/10.48550/arxiv.2209.11055,
    doi = {10.48550/ARXIV.2209.11055},
    url = {https://arxiv.org/abs/2209.11055},
    author = {Tunstall, Lewis and Reimers, Nils and Jo, Unso Eun Seo and Bates, Luke and Korat, Daniel and Wasserblat, Moshe and Pereg, Oren},
    keywords = {Computation and Language (cs.CL), FOS: Computer and information sciences, FOS: Computer and information sciences},
    title = {Efficient Few-Shot Learning Without Prompts},
    publisher = {arXiv},
    year = {2022},
    copyright = {Creative Commons Attribution 4.0 International}
}
```

<!--
## Glossary

*Clearly define terms in order to be accessible across audiences.*
-->

<!--
## Model Card Authors

*Lists the people who create the model card, providing recognition and accountability for the detailed work that goes into its construction.*
-->

<!--
## Model Card Contact

*Provides a way for people who have updates to the Model Card, suggestions, or questions, to contact the Model Card authors.*
-->