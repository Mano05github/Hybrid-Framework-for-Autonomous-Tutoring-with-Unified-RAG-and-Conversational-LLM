# Sentiment Analysis Strategy: Speech Emotion Recognition (SER)

## The Shift
We are moving from simple "Text Sentiment" (VADER) to "Acoustic Emotion Recognition" (SER).
This allows the AI to detect *how* the student is speaking (Frustrated? Bored? Excited?), even if the words are neutral.

## Selected Architecture: Hybrid CNN-LSTM Ensemble
**Why?**
*   **Best Production Choice**: As noted in your research [IJECE 2025], it offers ~96% accuracy.
*   **Balance**: CNN captures spatial patterns (Spectrograms), LSTM captures temporal evolution (changes in tone over time).
*   **Feasibility**: Can be trained/run on a standard backend without the extreme weight of a ViT.

## Implementation Plan

### Phase 1: Feature Extraction Pipeline ( The "Ear")
We need to turn raw audio into numbers the AI can read.
**Tool**: `librosa` (Python standard for audio).
**Features**:
1.  **MFCC (40 coeffs)**: Captures the "texture" of the sound.
2.  **Chroma**: Captures pitch classes (musicality/tone).
3.  **Mel-Spectrogram**: Visual representation of the audio frequency.

```python
def extract_features(audio_path):
    y, sr = librosa.load(audio_path, duration=3, offset=0.5)
    
    # 1. MFCC
    mfcc = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40).T, axis=0)
    
    # 2. Mel Spectrogram (for CNN)
    mel = librosa.feature.melspectrogram(y=y, sr=sr)
    
    return mfcc, mel
```

### Phase 2: The Model (The "Amydala")
We will build a PyTorch / TensorFlow model that fuses two branches:
1.  **CNN Branch**: Takes the Mel-Spectogram images.
2.  **LSTM Branch**: Takes the MFCC time-series.
3.  **Fusion Layer**: Concatenates them -> Dense Layer -> Output (Neutral, Happy, Sad, Angry, Frustrated).

### Phase 3: Integration (Real-Time Loop)
1.  **Frontend**:
    *   `MediaRecorder` API captures audio chunks (every 3 seconds).
    *   Sends `Blob` to WebSocket.
2.  **Backend (Consumer)**:
    *   Receives `bytes`.
    *   Saves to temp `.wav`.
    *   Runs `model.predict()`.
3.  **Orchestrator**:
    *   Updates `user_state.emotion`.
    *   If `emotion == "frustrated"`, injects prompt: *"The user sounds frustrated. Be calm."*

## Data Requirements
To make this work, we need a pre-trained model. We will use:
*   **RAVDESS** (Ryerson Audio-Visual Database of Emotional Speech and Song).
*   **TESS** (Toronto emotional speech set).
*   *Note*: We will start with a pre-trained model from HuggingFace (`facebook/wav2vec2-large-xlsr-53-emotion`) or build a simpler CNN-LSTM tailored to our needs if custom training is desired.

## Proposed "Quick Path"
1.  **Immediate**: Use `speechbrain` or `transformers` (HuggingFace) to run a pre-trained **Wav2Vec2 Emotion model**.
    *   *Why?* It matches your "Phase 2" optimization but is actually easier to implement *first* because we don't need to manually train a CNN-LSTM from scratch just yet. It gives instant SOTA results.
2.  **Optimization**: If latency is too high, we switch to the lightweight custom CNN-LSTM.
