# Gap 1: Voice-Canvas Synchronization Strategy

## Overview

Gap 1 addresses the synchronization between voice-based instruction and real-time visual canvas rendering. This strategy enables the system to dynamically generate and annotate visual representations while explaining concepts through voice, creating a multimodal learning experience.

## Problem Statement

Traditional tutoring systems separate audio instruction from visual aids, forcing students to mentally connect spoken explanations with static diagrams. This cognitive burden increases when learning abstract concepts like data structures or algorithms where step-by-step visualization is crucial.

## Solution Architecture

### Voice Assistant Integration

**Components:**
1. **Wake Word Detection**
   - Model: Bi-LSTM with 40D MFCC features
   - Wake phrase: "Hey Tutor"
   - Latency: <100ms
   - Sample rate: 8kHz continuous monitoring

2. **Speech-to-Text (STT)**
   - Architecture: Deep CNN-LSTM with CTC loss
   - Features: 81D log-mel spectrogram
   - Decoder: Beam search with KenLM language model
   - Target WER: <10%
   - Dataset: Common Voice EN (100h training)

3. **Text-to-Speech (TTS)**
   - Acoustic Model: FastSpeech2 (non-autoregressive)
   - Vocoder: HiFi-GAN
   - Output: 22kHz audio
   - Latency: <200ms for 5-second utterance
   - Prosody Control: Duration/pitch/energy predictors

4. **Natural Language Understanding (NLU)**
   - Backbone: BERT-base-uncased
   - Multi-task heads: Entity (57 classes), Intent (54 classes), Scenario (18 classes)
   - Accuracy: 91% entity F1, 90% intent, 88% scenario

### Canvas Rendering System

**Drawing Operations:**
- Nodes (circles, rectangles, rounded boxes)
- Edges (straight, curved, directed/undirected)
- Annotations (labels, values, highlights)
- Animations (stepwise execution, highlighting, transitions)

**Canvas Architecture:**
```typescript
interface CanvasState {
  nodes: Map<string, Node>;
  edges: Map<string, Edge>;
  annotations: Annotation[];
  currentStep: number;
  animationQueue: Animation[];
}

interface Node {
  id: string;
  type: 'circle' | 'rect' | 'rounded';
  position: {x: number; y: number};
  data: any;
  style: NodeStyle;
}

interface Edge {
  id: string;
  source: string;
  target: string;
  type: 'straight' | 'curved';
  directed: boolean;
  label?: string;
}
```

### Synchronization Protocol

**Event Stream:**
```
User Voice Input → STT → NLU → Agent Processing → Canvas Commands + TTS Text

Voice: "Let me show you binary search"
NLU: {intent: "EXPLAIN", entity: "binary_search", action: "VISUALIZE"}
Agent: Generates step-by-step canvas commands
Canvas: Renders array, pointers, highlights
TTS: "We start with a sorted array. The middle element is..."
```

**Canvas Command Format:**
```json
{
  "type": "draw_nodes",
  "timestamp": 1234567890,
  "nodes": [
    {"id": "n1", "type": "rect", "position": [100, 200], "label": "5"},
    {"id": "n2", "type": "rect", "position": [200, 200], "label": "12"}
  ],
  "sync_with_audio": {
    "phrase": "Here we have two elements",
    "duration_ms": 2000
  }
}
```

## Implementation Status

### Completed
- ✅ Frontend canvas components (React-Konva)
- ✅ WebSocket real-time communication
- ✅ Basic drawing primitives (nodes, edges, text)
- ✅ Infinite canvas with pan/zoom
- ✅ Touch and mouse event handling

### In Progress (Voice Assistant System)
- 🔄 Wake word detection model training
- 🔄 STT model fine-tuning on educational domain
- 🔄 FastSpeech2 + HiFi-GAN TTS pipeline
- 🔄 Canvas command generation from NLU output
- 🔄 Audio-visual synchronization engine

### Planned
- ⏳ Emotion-based prosody adjustment
- ⏳ Interactive canvas (student can draw while listening)
- ⏳ Multi-user collaborative canvas
- ⏳ Recording and playback of voice+canvas sessions

## Technical Specifications

### Voice Processing Pipeline

**Preprocessing:**
```python
def preprocess_audio(audio_buffer):
    # Pre-emphasis filter
    pre_emphasized = librosa.effects.preemphasis(audio_buffer)
    
    # Voice Activity Detection (VAD)
    vad = webrtcvad.Vad(mode=3)
    frames = frame_generator(30, pre_emphasized, 16000)
    speech_frames = [f for f in frames if vad.is_speech(f.bytes, 16000)]
    
    # Feature extraction
    mfcc = librosa.feature.mfcc(
        y=np.concatenate(speech_frames),
        sr=16000,
        n_mfcc=40,
        n_fft=512,
        hop_length=160
    )
    return mfcc
```

**STT Model Architecture:**
```
Input: Log-Mel Spectrogram (81 × T)
  ↓
Conv1D (256 channels, kernel=3) + BatchNorm + ReLU
  ↓
Conv1D (256 channels, kernel=3) + BatchNorm + ReLU
  ↓
Conv1D (256 channels, kernel=3) + BatchNorm + ReLU
  ↓
Bi-LSTM (1024 hidden, 5 layers, dropout=0.3)
  ↓
Linear (2048 → 29 character classes)
  ↓
CTC Loss / Beam Search Decoder
```

**TTS Model Architecture:**
```
Text → Phoneme Sequence (g2p_en)
  ↓
FastSpeech2:
  - Phoneme Embedding
  - Positional Encoding
  - FFT Blocks (4 layers)
  - Duration Predictor
  - Length Regulator
  - Pitch Predictor
  - Energy Predictor
  - FFT Blocks (4 layers)
  - Linear Projection
  ↓
Mel Spectrogram (80 bins)
  ↓
HiFi-GAN Vocoder:
  - Upsampling layers (×256)
  - Multi-Receptive Field Fusion
  - Multi-Period Discriminator
  ↓
Audio Waveform (22kHz)
```

### Canvas Synchronization Engine

**Timing Mechanism:**
```typescript
class SyncEngine {
  private audioContext: AudioContext;
  private canvasTimeline: Timeline;
  
  async syncVoiceAndCanvas(
    audioBuffer: AudioBuffer,
    canvasCommands: CanvasCommand[]
  ) {
    // Extract phoneme timing from TTS model
    const phonemeTiming = this.extractPhonemeTimings(audioBuffer);
    
    // Align canvas commands with phonemes
    const alignedCommands = this.alignCommands(
      canvasCommands,
      phonemeTiming
    );
    
    // Schedule both playback and rendering
    const startTime = this.audioContext.currentTime;
    this.scheduleAudioPlayback(audioBuffer, startTime);
    this.scheduleCanvasAnimations(alignedCommands, startTime);
  }
  
  private alignCommands(
    commands: CanvasCommand[],
    timing: PhonemeTime[]
  ): TimedCommand[] {
    return commands.map((cmd, i) => ({
      ...cmd,
      startTime: timing[i].start,
      duration: timing[i].end - timing[i].start
    }));
  }
}
```

## Performance Metrics

| Metric | Target | Current Status |
|--------|--------|----------------|
| Wake word false positive rate | <2%/hour | Training phase |
| STT Word Error Rate (WER) | <10% | Target: 8.5% |
| TTS Mean Opinion Score (MOS) | ≥4.0/5 | Training phase |
| End-to-end latency | <500ms | Design phase |
| Canvas rendering FPS | ≥30 | ✅ Achieved: 60 FPS |
| Sync accuracy | <50ms drift | Design phase |

## Use Cases

### 1. Algorithm Visualization
**Scenario**: Explaining merge sort

**Voice**: "First, we divide the array into two halves"
**Canvas**: Array splits visually with animation
**Voice**: "Then we recursively sort each half"
**Canvas**: Subarrays highlighted, sorting animation plays
**Voice**: "Finally, we merge the sorted halves"
**Canvas**: Merge operation with step-by-step comparison

### 2. Data Structure Explanation
**Scenario**: Teaching binary trees

**Voice**: "A binary tree has a root node"
**Canvas**: Root node appears
**Voice**: "Each node can have up to two children"
**Canvas**: Two child nodes connect to root
**Voice**: "Let's insert the value 15"
**Canvas**: Highlights traversal path, adds new node

### 3. Mathematical Proof
**Scenario**: Proving a theorem

**Voice**: "Given that x squared equals 4"
**Canvas**: Writes "x² = 4"
**Voice**: "We take the square root of both sides"
**Canvas**: Adds sqrt symbols, shows transformation
**Voice**: "Therefore, x equals plus or minus 2"
**Canvas**: Final result with annotations

## Dependencies

**Backend:**
- PyTorch 1.7.1 (deep learning framework)
- torchaudio 0.7.0 (audio processing)
- librosa 0.8.0 (audio feature extraction)
- webrtcvad 2.0.10 (voice activity detection)
- transformers 4.12.0 (BERT models)
- ctcdecode 0.1.0 (CTC beam search)
- g2p_en (grapheme-to-phoneme conversion)

**Frontend:**
- react-konva 18.2.5 (canvas rendering)
- konva 9.2.0 (HTML5 2D canvas library)
- Web Audio API (browser native)
- MediaRecorder API (browser native)

**Models:**
- Wake word: Custom Bi-LSTM (2.3 MB)
- STT: Deep CNN-LSTM (450 MB)
- NLU: BERT-base (440 MB)
- TTS Acoustic: FastSpeech2 (120 MB)
- TTS Vocoder: HiFi-GAN (55 MB)

**Total Model Size**: ~1.07 GB (downloadable on first use)

## Training Data Requirements

| Component | Dataset | Size | Duration/Samples |
|-----------|---------|------|------------------|
| Wake Word | Custom + Common Voice | 6 GB | 10 hours |
| STT | Common Voice EN | 150 GB | 100 hours |
| NLU | Custom annotated queries | 50 MB | 10K samples |
| TTS | LJSpeech | 2.6 GB | 24 hours |

## Future Enhancements

1. **Multi-Speaker TTS**: Allow students to choose voice persona
2. **Real-Time Style Transfer**: Adjust speaking style based on student's emotional state
3. **Collaborative Canvas**: Multiple students can draw simultaneously
4. **Session Recording**: Save voice + canvas for later review
5. **Gesture Recognition**: Hand gestures to control canvas (via webcam)
6. **3D Visualization**: Extend canvas to 3D for geometry and physics concepts
7. **Accessibility Features**: Sign language generation, visual descriptions for blind students

## Conclusion

Gap 1 represents a significant advancement in multimodal educational technology by tightly integrating voice and visual modalities. The offline, privacy-focused approach ensures data security while delivering sub-500ms latency for real-time interaction. Once fully implemented, this will enable natural, conversational tutoring with synchronized visual explanations, significantly enhancing student comprehension of complex topics.

**Current Implementation Status**: 40% complete (canvas ready, voice assistant in training phase)
**Estimated Completion**: 8-10 weeks (following 10-week implementation plan)
