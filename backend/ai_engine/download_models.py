"""
Download and cache all models locally for offline use.
Run this script once to download all required models.

Usage: python download_models.py
"""
import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def download_embedding_model():
    """Download paraphrase-mpnet-base-v2 embedding model."""
    print("\n" + "="*80)
    print("📥 DOWNLOADING EMBEDDING MODEL")
    print("="*80)
    print("Model: paraphrase-mpnet-base-v2 (768 dimensions)")
    print("Size: ~420MB")
    print("Purpose: Text embeddings for RAG and similarity search")
    print("-"*80)
    
    from sentence_transformers import SentenceTransformer
    
    # Download to local cache directory
    models_dir = Path(__file__).parent / "models" / "embeddings"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / "paraphrase-mpnet-base-v2"
    
    if model_path.exists():
        print(f"✅ Model already cached at: {model_path}")
        print("   Verifying model loads correctly...")
        model = SentenceTransformer(str(model_path))
        test_embedding = model.encode("test", show_progress_bar=False)
        print(f"   ✅ Model verified (embedding shape: {test_embedding.shape})")
    else:
        print("⏬ Downloading model from HuggingFace...")
        model = SentenceTransformer('paraphrase-mpnet-base-v2')
        
        print(f"💾 Saving model to: {model_path}")
        model.save(str(model_path))
        
        print(f"✅ Model downloaded and cached successfully!")
        print(f"   Location: {model_path}")

def download_setfit_classifier():
    """Verify SetFit classifier is available."""
    print("\n" + "="*80)
    print("📥 CHECKING SETFIT CLASSIFIER")
    print("="*80)
    print("Model: SetFit Intent Classifier (paraphrase-mpnet-base-v2 base)")
    print("Size: ~100MB")
    print("Purpose: Fast intent classification for supervisor routing")
    print("-"*80)
    
    model_path = Path(__file__).parent / "models" / "setfit_intent_classifier"
    
    if model_path.exists():
        print(f"✅ SetFit model found at: {model_path}")
        print("   Verifying model loads correctly...")
        
        from setfit import SetFitModel
        model = SetFitModel.from_pretrained(str(model_path))
        print(f"   ✅ Model verified successfully!")
    else:
        print(f"⚠️  SetFit model not found at: {model_path}")
        print("   This model needs to be trained first.")
        print("   Run: python -m ai_engine.supervisor.classifier")

def download_cache_models():
    """Download semantic cache embedding model."""
    print("\n" + "="*80)
    print("📥 DOWNLOADING CACHE EMBEDDING MODEL")
    print("="*80)
    print("Model: all-MiniLM-L6-v2 (384 dimensions)")
    print("Size: ~90MB")
    print("Purpose: Semantic cache for query matching")
    print("-"*80)
    
    from sentence_transformers import SentenceTransformer
    
    models_dir = Path(__file__).parent / "models" / "embeddings"
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / "all-MiniLM-L6-v2"
    
    if model_path.exists():
        print(f"✅ Cache model already downloaded at: {model_path}")
    else:
        print("⏬ Downloading cache model from HuggingFace...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        print(f"💾 Saving model to: {model_path}")
        model.save(str(model_path))
        
        print(f"✅ Cache model downloaded successfully!")

def main():
    """Download all required models."""
    print("\n" + "="*80)
    print("🚀 MODEL DOWNLOADER FOR OFFLINE USE")
    print("="*80)
    print("This script will download all required models to local cache.")
    print("After completion, the application will load models instantly.")
    print("="*80)
    
    try:
        # 1. Download main embedding model
        download_embedding_model()
        
        # 2. Check SetFit classifier
        download_setfit_classifier()
        
        # 3. Download cache embedding model
        download_cache_models()
        
        print("\n" + "="*80)
        print("✅ ALL MODELS DOWNLOADED SUCCESSFULLY")
        print("="*80)
        print("\nModels saved in:")
        print(f"  {Path(__file__).parent / 'models'}")
        print("\nNext steps:")
        print("  1. If SetFit model is missing, train it:")
        print("     python -m ai_engine.supervisor.classifier")
        print("  2. Restart Django server to use cached models:")
        print("     python manage.py runserver")
        print("\n✅ Setup complete! Models will now load instantly.\n")
        
    except KeyboardInterrupt:
        print("\n⚠️  Download interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during download: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
