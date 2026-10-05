# Canine Disease NLP Architecture & Process Flow Blueprint

This document specifies the technical architecture, neural network design, end-to-end data transformation pipeline, and conversational state machine for the **Canivue Canine Disease NLP Symptom Parser & Intake Agent**.

---

## 🏛️ 1. Clean Architecture System Structure

The NLP module is organized into **Feature-Based Clean Architecture** inside a **Modular Monolith**. It adheres to the **Inward Dependency Rule**: outer layers depend on inner layers, and the Domain layer has zero framework dependencies.

```mermaid
graph TB
    subgraph Presentation ["1. Presentation Layer (HTTP / REST)"]
        Router["router.py<br/>• POST /symptoms/parse<br/>• POST /symptoms/intake/sessions<br/>• POST /symptoms/intake/sessions/{id}/turns<br/>• POST /symptoms/intake/sessions/{id}/complete"]
        Schemas["schemas.py<br/>• SymptomParseRequest / Response<br/>• StartIntakeRequest<br/>• IntakeTurnRequest"]
        Deps["dependencies.py<br/>• get_symptom_engine()<br/>• get_intake_session_repository()<br/>• Use Case Providers"]
    end

    subgraph Application ["2. Application Layer (Use Cases & DTOs)"]
        ParseUC["ParseSymptomTextUseCase<br/>Single-turn parsing coordinator"]
        StartUC["StartIntakeSessionUseCase<br/>Session initialization & slot extraction"]
        TurnUC["ConductIntakeTurnUseCase<br/>Multi-turn context synthesis"]
        CompleteUC["CompleteIntakeSessionUseCase<br/>Final evidence freeze"]
        DTOs["dtos.py<br/>• ParseSymptomInputDTO / OutputDTO<br/>• StartIntakeInputDTO / OutputDTO<br/>• ConductTurnInputDTO"]
    end

    subgraph Domain ["3. Domain Layer (Pure Business Core)"]
        Entities["entities.py<br/>• SymptomParseResult<br/>• IntakeSession & IntakeMessage<br/>• BodyLocation, DurationEntity, ExtractedSpan"]
        Protocols["repositories.py (Protocols)<br/>• NLPSymptomEngineProtocol<br/>• IntakeSessionRepositoryProtocol"]
        Rules["intake_rules.py<br/>• evaluate_missing_slots()<br/>• generate_clarifying_prompt()"]
        Exceptions["exceptions.py<br/>• EmptySymptomTextException<br/>• IntakeSessionNotFoundException<br/>• IntakeSessionClosedException"]
    end

    subgraph Infrastructure ["4. Infrastructure Layer (Adapters & Serving)"]
        SessionRepo["session_repository.py<br/>InMemoryIntakeSessionRepository"]
        ServingEngines["ml/engine.py<br/>• StubNLPSymptomEngine (Fast CI/tests)<br/>• TrainedNLPSymptomEngine (PyTorch inference)"]
        Preproc["ml/preprocessing.py<br/>• check_emergency_triage()<br/>• calculate_text_quality_score()<br/>• calculate_modality_reliability()"]
    end

    subgraph MachineLearning ["5. Machine Learning Core (ml/nlp/)"]
        Pipeline["pipeline.py<br/>SymptomParserPipeline"]
        MultiTask["model.py<br/>MultiTaskSymptomTransformer"]
        TrainEval["train.py & evaluate.py<br/>• Dog-level splitting (pet_id)<br/>• Macro-F1 across 4 conditions<br/>• Expected Calibration Error (ECE)"]
    end

    %% Dependency Arrows
    Router --> Schemas
    Router --> Deps
    Router --> ParseUC
    Router --> StartUC
    Router --> TurnUC
    Router --> CompleteUC

    ParseUC --> Protocols
    ParseUC --> DTOs
    StartUC --> Protocols
    StartUC --> Rules
    StartUC --> DTOs
    TurnUC --> Protocols
    TurnUC --> Rules
    TurnUC --> DTOs
    CompleteUC --> Protocols
    CompleteUC --> DTOs

    ServingEngines -.->|implements| Protocols
    SessionRepo -.->|implements| Protocols
    TrainedEngine --> Pipeline
    Pipeline --> MultiTask
    Pipeline --> Preproc
```

> [!NOTE]
> **Zero ML Framework Leakage:** `torch` and `transformers` are isolated entirely inside `infrastructure/ml/engine.py` and `ml/nlp/`. The application and domain layers depend solely on [`NLPSymptomEngineProtocol`](file:///c:/Users/indun/OneDrive/Desktop/canivue-api/app/features/symptom_nlp/domain/repositories.py).

---

## ⚡ 2. Dual-Engine Serving Topology

To guarantee that unit tests, local development, and CI execute in milliseconds without requiring GPUs or gigabyte model downloads, the application employs a **Dual-Engine Pattern**:

```mermaid
graph LR
    subgraph ClientRequest ["Client Intake Request"]
        Req["POST /api/v1/symptoms/*"]
    end

    subgraph DependencyInjection ["dependencies.py: get_symptom_engine()"]
        CheckConfig{"USE_REAL_ML_MODELS<br/>is True AND Checkpoint Exists?"}
    end

    subgraph Stubs ["Fast Mode (Development & CI)"]
        Stub["StubNLPSymptomEngine<br/>• Zero framework imports<br/>• Deterministic regex & lexicon rules<br/>• Execution time: < 1ms"]
    end

    subgraph RealML ["Production Mode (Inference Serving)"]
        Trained["TrainedNLPSymptomEngine<br/>• Loads weights from model_registry/nlp/<br/>• Delegates to SymptomParserPipeline<br/>• Multi-task Transformer inference"]
    end

    Req --> CheckConfig
    CheckConfig -- No --> Stub
    CheckConfig -- Yes --> Trained
```

---

## 🧠 3. Multi-Task Neural Network Architecture

The neural core in [`MultiTaskSymptomTransformer`](file:///c:/Users/indun/OneDrive/Desktop/canivue-api/ml/nlp/model.py) uses a **single shared Transformer backbone** with **two concurrent prediction heads**.

```mermaid
graph TD
    Text["Owner Symptom Text<br/>'My dog has been scratching its left ear for three days and it is becoming red.'"]
    
    subgraph Tokenization ["Subword Tokenization"]
        Tok["DistilBERT Tokenizer<br/>Produces Input IDs, Attention Mask, Offset Mappings"]
    end

    subgraph Backbone ["Shared Contextual Encoder"]
        DistilBERT["6-Layer DistilBERT Encoder<br/>768 Hidden Dimensions<br/>Output Matrix: H ∈ ℝ^(seq_len × 768)"]
    end

    subgraph HeadA ["Task A: Token Classification (NER)"]
        SeqTokens["Token Representations<br/>H_seq ∈ ℝ^(seq_len × 768)"]
        DropoutA["Dropout (p=0.2)"]
        LinearA["Linear Projection<br/>768 → K_NER"]
        SoftmaxA["Token Softmax"]
        LabelsA["BIO Entity Labels:<br/>• B-symptom ('scratching')<br/>• B-body_location ('left')<br/>• I-body_location ('ear')<br/>• B-duration ('three')<br/>• I-duration ('days')<br/>• B-symptom ('red')"]
    end

    subgraph HeadB ["Task B: Sequence Classification (Condition)"]
        CLS["Pooled [CLS] Representation<br/>h_CLS ∈ ℝ^768"]
        DropoutB["Dropout (p=0.2)"]
        LinearB["Linear Projection<br/>768 → 4 Classes"]
        SoftmaxB["Sequence Softmax"]
        ProbsB["Canonical Condition Probabilities:<br/>• ear_inflammation: 0.82<br/>• skin_condition: 0.11<br/>• eye_condition: 0.02<br/>• other: 0.05"]
    end

    Text --> Tok
    Tok --> DistilBERT
    DistilBERT --> SeqTokens
    DistilBERT --> CLS
    
    SeqTokens --> DropoutA --> LinearA --> SoftmaxA --> LabelsA
    CLS --> DropoutB --> LinearB --> SoftmaxB --> ProbsB
```

### Multi-Task Loss Formulation
During offline training ([`ml/nlp/train.py`](file:///c:/Users/indun/OneDrive/Desktop/canivue-api/ml/nlp/train.py)), both heads are optimized simultaneously with loss weighting:
$$\mathcal{L}_{\text{total}} = 0.6 \cdot \mathcal{L}_{\text{NER}}(\text{CrossEntropy}) + 0.4 \cdot \mathcal{L}_{\text{condition}}(\text{CrossEntropy})$$

---

## 🔄 4. End-to-End Symptom Processing Pipeline

The following flowchart details the sequential stages that an input string passes through:

```mermaid
flowchart TD
    Raw["Raw Owner Utterance"] --> Step1["1. Input Sanitization & Unicode Normalization"]
    
    Step1 --> Step2{"2. Emergency Red-Flag Interceptor<br/>check_emergency_triage()"}
    
    Step2 -- Emergency Triggered --> Divert["Emergency Alert Activated<br/>• is_critical = True<br/>• reason: 'Sudden collapse / blue gums / respiratory distress'<br/>• recommendation: 'Immediate emergency veterinary clinic'<br/>• Routine intake halted"]
    
    Step2 -- Safe / Non-Critical --> Step3["3. Multi-Task Transformer Inference<br/>• Token BIO span predictions<br/>• 4-class condition probability distribution"]
    
    Step3 --> Step4["4. Negation Scoping Analyzer<br/>• Scans for 'no', 'not', 'stopped', 'ceased'<br/>• Routes negated entities to negated_symptoms history"]
    
    Step4 --> Step5["5. Deterministic Temporal Normalizer<br/>• Extracts value and unit regex patterns<br/>• 'for three days' → {value: 3, unit: 'days'}"]
    
    Step5 --> Step6["6. Anatomical Laterality Resolution<br/>• Links 'left', 'right', 'both' to matching bilateral body parts"]
    
    Step6 --> Step7["7. Text Quality Rubric (0.0 to 1.0)<br/>• Symptoms present: +0.30<br/>• Body location present: +0.20<br/>• Duration present: +0.20<br/>• Progression/severity: +0.15<br/>• Syntax & length (≥8 words): +0.15"]
    
    Step7 --> Step8["8. Modality Reliability Scoring<br/>Reliability = (2 × Quality × Confidence) / (Quality + Confidence)"]
    
    Step8 --> Output["9. Output Standardized Envelope<br/>Returns SymptomParseResult ready for Multimodal Fusion"]
    Divert --> Output
```

---

## 💬 5. Conversational Clinical Intake Agent Process Flow

When an owner engages in a multi-turn consultation, the agent coordinates context accumulation and targeted clarifying prompt generation:

```mermaid
sequenceDiagram
    autonumber
    actor Owner as Dog Owner
    participant API as FastAPI Router
    participant SessionRepo as IntakeSessionRepository
    participant UseCase as ConductIntakeTurnUseCase
    participant Engine as NLPSymptomEngine
    participant Rules as Intake Slot Rules
    participant Fusion as Adaptive Multimodal Fusion

    Note over Owner,API: Turn 1: Initial Presentation
    Owner->>API: POST /symptoms/intake/sessions {"text": "My dog is scratching its ear"}
    API->>UseCase: StartIntakeSessionUseCase.execute()
    UseCase->>Engine: parse("My dog is scratching its ear")
    Engine-->>UseCase: SymptomParseResult (symptoms=['scratching'], location=['ear'], side=null, duration=null)
    UseCase->>Rules: evaluate_missing_slots()
    Rules-->>UseCase: missing = ["body_location_side", "duration"]
    UseCase->>Rules: generate_clarifying_prompt()
    Rules-->>UseCase: "Which ear is affected (left, right, or both), and how long has this been going on?"
    UseCase->>SessionRepo: save(session: turn=1, status='in_progress')
    UseCase-->>API: IntakeSessionResponseData
    API-->>Owner: Agent Question: "Which ear is affected, and for how long?"

    Note over Owner,API: Turn 2: Follow-up Clarification
    Owner->>API: POST /symptoms/intake/sessions/{id}/turns {"message": "It's the left ear, started 3 days ago. Getting worse."}
    API->>UseCase: ConductIntakeTurnUseCase.execute()
    UseCase->>SessionRepo: get(session_id)
    SessionRepo-->>UseCase: session (turn=1)
    UseCase->>UseCase: Synthesize cumulative dialogue narrative
    UseCase->>Engine: parse("My dog is scratching its ear. It's the left ear, started 3 days ago. Getting worse.")
    Engine-->>UseCase: Updated Parse (locations=[{part: 'ear', side: 'left'}], duration={3, 'days'}, progression='worsening')
    UseCase->>Rules: evaluate_missing_slots()
    Rules-->>UseCase: missing = [] (All satisfied!)
    UseCase->>Rules: generate_clarifying_prompt()
    Rules-->>UseCase: "Thank you. I have captured the full clinical picture. Would you like to finalize?"
    UseCase->>SessionRepo: save(session: turn=2, is_complete=True)
    API-->>Owner: Response with resolved entities and completion prompt

    Note over Owner,Fusion: Final Consultation Complete
    Owner->>API: POST /symptoms/intake/sessions/{id}/complete
    API->>UseCase: CompleteIntakeSessionUseCase.execute()
    UseCase->>SessionRepo: update(status='completed')
    UseCase-->>API: Final SymptomParseResult
    API->>Fusion: Ingest Condition Probabilities + Modality Reliability Score
```

---

## 🔀 6. Integration with Multimodal Fusion & DPRPE

The NLP module acts as a **clinical evidence translator** for the other canine diagnostic engines:

```mermaid
graph TD
    subgraph NLPEvidence ["NLP Symptom Parser Output"]
        Probs["Condition Probabilities<br/>• ear_inflammation: 0.82<br/>• skin_condition: 0.11<br/>• eye_condition: 0.02<br/>• other: 0.05"]
        Reliability["Modality Reliability Score<br/>Harmonic mean of Quality & Confidence"]
        Temporal["Temporal Dynamics<br/>• duration: {value: 3, unit: 'days'}<br/>• progression: 'worsening'<br/>• severity_cues: ['redness', 'odor']"]
        EntitiesList["Categorical Clinical Features<br/>• symptoms: ['scratching', 'head_shaking']<br/>• negated_symptoms: ['vomiting']<br/>• body_locations: [{part: 'ear', side: 'left'}]"]
    end

    subgraph Modalities ["Other Modalities"]
        Vision["Vision Diagnosis Module<br/>Photographic lesion classification"]
        Sensors["Behavioural IMU Sensor<br/>ESP32 / MPU6050 accelerometer analysis"]
    end

    subgraph DownstreamEngines ["Downstream Diagnostic Engines"]
        FusionEngine["Confidence-Weighted Adaptive Multimodal Fusion<br/>Balances modality weights by reliability:<br/>Weight_text = f(Reliability_text)"]
        DPRPEEngine["Disease Progression & Risk Prediction Engine (DPRPE)<br/>Forecasts disease risk trajectory using duration & progression"]
        VetPortal["Veterinary Clinical Portal<br/>Displays exact text spans highlighted for clinician review"]
    end

    Probs --> FusionEngine
    Reliability --> FusionEngine
    Vision --> FusionEngine
    Sensors --> FusionEngine

    Temporal --> DPRPEEngine
    EntitiesList --> DPRPEEngine

    EntitiesList --> VetPortal
    Temporal --> VetPortal
```

---

## 📊 Summary of Architectural Guarantees

| Capability | Architectural Seam | Verification Method |
|---|---|---|
| **Stateless Single-Turn Parsing** | `POST /api/v1/symptoms/parse` | Tested via `test_api.py` with schema and span validation |
| **Multi-Turn Clinical Intake** | `POST /api/v1/symptoms/intake/*` | Tested via `test_intake_api.py` across full dialogue turns |
| **Emergency Triage Red-Flag** | `check_emergency_triage()` | Immediate diversion tested on Turn 1 and Turn $N$ |
| **Zero-GPU Testing Discipline** | `StubNLPSymptomEngine` | Executed in CI without GPU drivers or network access |
| **Leak-Free ML Dataset** | `get_dog_level_splits(pet_id)` | Tested in `test_nlp_pipeline.py` preventing patient overlap |
