"""
Turn-Type Classifier — Phase 2 SetFit
======================================
Classifies the *style* of a student message (not which agent handles it).

4 classes:
  small_talk     — greetings, casual chat, off-topic
  academic_hint  — wants to learn a CS topic
  help_seeking   — confused, stuck, needs specific help
  emotional      — expressing a feeling (tired, frustrated, bored)

Reuses the same SetFit infrastructure as IntentClassifier.
Base model: paraphrase-mpnet-base-v2 (already downloaded).

Training: run  python -m ai_engine.supervisor.turn_type_classifier
"""
import os
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

TURN_TYPE_LABELS = {
    0: "small_talk",
    1: "academic_hint",
    2: "help_seeking",
    3: "emotional",
}
LABEL_TO_INT = {v: k for k, v in TURN_TYPE_LABELS.items()}

_DEFAULT_MODEL_PATH = Path(__file__).parent.parent / "models" / "setfit_turn_type_classifier"
_TRAINING_DATA_PATH = Path(__file__).parent.parent / "data" / "turn_type_training.json"


class TurnTypeClassifier:
    """
    Lightweight SetFit classifier for detecting turn type.
    Falls back to None if model not yet trained (agents.py keyword fallback takes over).
    """

    def __init__(self, model_path: Optional[Path] = None):
        self.model = None
        self.is_ready = False
        path = model_path or _DEFAULT_MODEL_PATH

        if path.exists():
            try:
                from setfit import SetFitModel
                self.model = SetFitModel.from_pretrained(str(path))
                self.is_ready = True
                logger.info(f"✅ TurnTypeClassifier loaded from {path}")
            except Exception as e:
                logger.warning(f"TurnTypeClassifier: could not load model — {e}")
        else:
            logger.info(
                "TurnTypeClassifier: no trained model found. "
                "Run 'python -m ai_engine.supervisor.turn_type_classifier' to train."
            )

    def predict(self, query: str) -> Optional[str]:
        """
        Returns turn type string or None if model not ready.
        None → callers fall back to keyword detection.
        """
        if not self.is_ready or self.model is None:
            return None
        try:
            prediction = self.model.predict([query])[0]
            label_int = int(prediction)
            turn_type = TURN_TYPE_LABELS.get(label_int, "small_talk")
            logger.debug(f"[TurnType] '{query[:50]}' → {turn_type}")
            return turn_type
        except Exception as e:
            logger.warning(f"TurnTypeClassifier prediction failed: {e}")
            return None


# ── Singleton ──────────────────────────────────────────────────────────────────
_classifier_instance: Optional[TurnTypeClassifier] = None


def get_turn_type_classifier() -> TurnTypeClassifier:
    """Return the singleton TurnTypeClassifier (loaded once at startup)."""
    global _classifier_instance
    if _classifier_instance is None:
        _classifier_instance = TurnTypeClassifier()
    return _classifier_instance


# ── Training Script ────────────────────────────────────────────────────────────
def train_turn_type_classifier():
    """
    Train the SetFit turn-type classifier on the 32-example dataset.
    Run:  python -m ai_engine.supervisor.turn_type_classifier
    Time: ~5 min on CPU, ~1 min on GPU.
    """
    import numpy as np
    from setfit import SetFitModel, SetFitTrainer
    from datasets import Dataset
    from sklearn.metrics import classification_report

    print("=" * 60)
    print("Training SetFit Turn-Type Classifier")
    print("=" * 60)

    # Load training data
    with open(_TRAINING_DATA_PATH) as f:
        data = json.load(f)

    examples = data["examples"]
    texts  = [ex["query"]     for ex in examples]
    labels = [LABEL_TO_INT[ex["turn_type"]] for ex in examples]

    print(f"Loaded {len(texts)} examples across {len(TURN_TYPE_LABELS)} classes")

    # With only 32 examples we use them all for training (no val split —
    # it's a tiny dataset). Real accuracy validated by manual testing.
    train_dataset = Dataset.from_dict({"text": texts, "label": labels})

    # Reuse already-downloaded base model
    model = SetFitModel.from_pretrained(
        "sentence-transformers/paraphrase-mpnet-base-v2",
        labels=list(TURN_TYPE_LABELS.keys()),
    )

    trainer = SetFitTrainer(
        model=model,
        train_dataset=train_dataset,
        num_epochs=3,       # More epochs — small dataset, fast to train
        batch_size=8,
    )

    trainer.train()

    # Quick self-test on training data
    preds = model.predict(texts)
    acc = np.mean(np.array(preds) == np.array(labels))
    print(f"\nTraining accuracy (self-test): {acc:.2%}")

    report = classification_report(
        labels, preds,
        target_names=list(TURN_TYPE_LABELS.values()),
    )
    print(report)

    # Save
    save_path = str(_DEFAULT_MODEL_PATH)
    os.makedirs(save_path, exist_ok=True)
    model.save_pretrained(save_path)
    print(f"\n✅ Model saved → {save_path}")
    print("Restart the server for the classifier to load automatically.")


if __name__ == "__main__":
    train_turn_type_classifier()
