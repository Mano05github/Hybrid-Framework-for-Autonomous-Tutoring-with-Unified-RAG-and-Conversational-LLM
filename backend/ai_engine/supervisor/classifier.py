"""
SetFit Intent Classifier - Fast few-shot learning for routing
Target: 12ms inference, 99% cost reduction vs LLM
"""
import os
import json
from typing import Dict, List, Tuple
from pathlib import Path

import torch
from setfit import SetFitModel, SetFitTrainer, TrainingArguments
from sentence_transformers import SentenceTransformer
from datasets import Dataset
import numpy as np


class IntentClassifier:
    """
    SetFit-based intent classifier for supervisor routing.
    
    Performance Targets:
    - Inference: <15ms (87% faster than LLM)
    - Accuracy: >85% on 5-class problem
    - Cost: $0 (vs $0.002/query for LLM)
    """
    
    INTENT_LABELS = {
        0: "teacher",   # Concept explanation, learning content
        1: "coder",     # Code debugging, implementation help
        2: "examiner",  # Quiz generation, assessment
        3: "visionary", # Diagram analysis, visual validation
        4: "empath"     # Emotional support, encouragement
    }
    
    def __init__(self, model_path: str = None):
        """
        Initialize classifier with pretrained or new model.
        
        Args:
            model_path: Path to saved SetFit model (None to train new)
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if model_path and os.path.exists(model_path):
            print(f"Loading trained model from {model_path}")
            self.model = SetFitModel.from_pretrained(model_path)
        else:
            print("Initializing new SetFit model (paraphrase-mpnet-base-v2)")
            # Best base model for sentence classification
            self.model = SetFitModel.from_pretrained(
                "sentence-transformers/paraphrase-mpnet-base-v2",
                labels=list(self.INTENT_LABELS.keys())
            )
        
        self.model.to(self.device)
        self.is_trained = model_path is not None
    
    def train(
        self, 
        training_data_path: str,
        num_epochs: int = 1,
        batch_size: int = 16,
        learning_rate: float = 2e-5
    ) -> Dict[str, float]:
        """
        Train SetFit model on labeled intent data.
        
        Args:
            training_data_path: Path to JSON file with examples
            num_epochs: Training epochs (SetFit needs just 1-3)
            batch_size: Training batch size
            learning_rate: Learning rate for fine-tuning
        
        Returns:
            Training metrics dict
        """
        # Load training data
        with open(training_data_path, 'r') as f:
            data = json.load(f)
        
        examples = data['examples']
        print(f"Loaded {len(examples)} training examples")
        
        # Prepare data for SetFit
        texts = [ex['query'] for ex in examples]
        labels = [self._intent_to_label(ex['intent']) for ex in examples]
        
        # Create train/val split (90/10)
        from sklearn.model_selection import train_test_split
        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=0.1, random_state=42, stratify=labels
        )
        
        print(f"Training on {len(train_texts)} examples, validating on {len(val_texts)}")
        
        # Create dataset
        train_dataset = Dataset.from_dict({"text": train_texts, "label": train_labels})
        
        
        
        trainer = SetFitTrainer(
            model = self.model,
            batch_size=batch_size,
            num_epochs=num_epochs,
            train_dataset=train_dataset,
        )
        
        # Train SetFit (contrastive learning + classification head)
        trainer.train()
        
        # Evaluate on validation set
        val_predictions = self.model.predict(val_texts)
        accuracy = np.mean(np.array(val_predictions) == np.array(val_labels))
        
        # Calculate per-class metrics
        from sklearn.metrics import classification_report
        report = classification_report(
            val_labels, 
            val_predictions,
            target_names=list(self.INTENT_LABELS.values()),
            output_dict=True
        )
        
        self.is_trained = True
        
        return {
            'accuracy': accuracy,
            'val_samples': len(val_texts),
            'per_class_f1': {
                intent: report[intent]['f1-score'] 
                for intent in self.INTENT_LABELS.values()
            }
        }
    
    def predict(self, query: str) -> Tuple[str, float]:
        """
        Classify query intent with confidence score.
        
        Args:
            query: User query string
        
        Returns:
            (intent_name, confidence) tuple
            
        Example:
            >>> classifier.predict("Explain binary search")
            ('teacher', 0.94)
        """
        if not self.is_trained:
            raise ValueError("Model not trained. Call train() first or load pretrained model.")
        
        # Get prediction (SetFit returns label index)
        import time
        start = time.perf_counter()
        
        prediction = self.model.predict([query])[0]
        
        latency = (time.perf_counter() - start) * 1000  # ms
        
        # Get confidence from embeddings
        embeddings = self.model.model_body.encode([query])
        # Use distance to class prototypes as confidence proxy
        confidence = self._calculate_confidence(embeddings[0], prediction)
        
        intent = self.INTENT_LABELS[prediction]
        
        print(f"[Classifier] Query: '{query[:50]}...' -> {intent} ({confidence:.2f}) [{latency:.1f}ms]")
        
        return intent, confidence
    
    def predict_batch(self, queries: List[str]) -> List[Tuple[str, float]]:
        """
        Classify multiple queries efficiently.
        
        Args:
            queries: List of query strings
        
        Returns:
            List of (intent, confidence) tuples
        """
        if not self.is_trained:
            raise ValueError("Model not trained.")
        
        predictions = self.model.predict(queries)
        embeddings = self.model.model_body.encode(queries)
        
        results = []
        for i, pred in enumerate(predictions):
            intent = self.INTENT_LABELS[pred]
            confidence = self._calculate_confidence(embeddings[i], pred)
            results.append((intent, confidence))
        
        return results
    
    def save(self, save_path: str):
        """Save trained model to disk."""
        os.makedirs(save_path, exist_ok=True)
        self.model.save_pretrained(save_path)
        print(f"Model saved to {save_path}")
    
    def _intent_to_label(self, intent: str) -> int:
        """Convert intent string to numeric label."""
        label_map = {v: k for k, v in self.INTENT_LABELS.items()}
        return label_map[intent]
    
    def _calculate_confidence(self, embedding: np.ndarray, predicted_label: int) -> float:
        """
        Calculate confidence score based on embedding distance.
        
        Uses cosine similarity to class centroid as confidence proxy.
        """
        # For now, use a simple heuristic (can be improved with calibration)
        # In production, use class prototypes from SetFit head
        return 0.85  # Placeholder - implement proper confidence calibration


def train_intent_classifier():
    """Training script to create production model."""
    # Paths
    base_dir = Path(__file__).parent.parent
    training_data = base_dir / "data" / "intent_training.json"
    model_save_path = base_dir / "models" / "setfit_intent_classifier"
    
    # Initialize and train
    classifier = IntentClassifier()
    
    print("=" * 60)
    print("Training SetFit Intent Classifier")
    print("=" * 60)
    
    metrics = classifier.train(
        training_data_path=str(training_data),
        num_epochs=1,  # SetFit converges fast
        batch_size=16,
        learning_rate=2e-5
    )
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"Validation Accuracy: {metrics['accuracy']:.2%}")
    print("\nPer-Class F1 Scores:")
    for intent, f1 in metrics['per_class_f1'].items():
        print(f"  {intent:12s}: {f1:.2%}")
    
    # Save model
    classifier.save(str(model_save_path))
    
    # Test inference speed
    print("\n" + "=" * 60)
    print("Performance Benchmarks")
    print("=" * 60)
    
    test_queries = [
        "Explain how binary search works",
        "Debug my sorting function",
        "Give me 5 questions on trees",
        "Is this binary tree correct?",
        "I'm stuck and frustrated"
    ]
    
    import time
    latencies = []
    
    for query in test_queries:
        start = time.perf_counter()
        intent, confidence = classifier.predict(query)
        latency = (time.perf_counter() - start) * 1000
        latencies.append(latency)
        print(f"{intent:12s} ({confidence:.2f}) - {latency:.1f}ms - '{query}'")
    
    print(f"\nAverage Latency: {np.mean(latencies):.1f}ms")
    print(f"Target: <15ms ✓" if np.mean(latencies) < 15 else f"Target: <15ms ✗")
    
    return classifier


if __name__ == "__main__":
    train_intent_classifier()
