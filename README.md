# Sphinx: Multi-dimensional Benchmark for Goal-based Mobile UI Navigation

**Sphinx** is a comprehensive evaluation framework for assessing foundation models' capabilities in goal-based mobile UI navigation tasks. Operating on Android emulators, this benchmark features 244 user tasks spanning 100 popular industrial applications across 17 categories. Through its multi-dimensional assessment system, Sphinx evaluates model capabilities in:
- Goal understanding
- Application knowledge
- Task planning
- UI element grounding
- Instruction following

## Installation Guide

### Android Emulator Setup
1. **Install Android Studio**  
   Download from [here](https://developer.android.com/studio)

2. **Configure Emulator**  
   Create virtual device with specifications:
   - Device: Nexus 4
   - System Image: Android 12.0 (Google APIs) x86_64

3. **Launch & Configure**  
   - Start the emulator
   - Authenticate with Google account (required for app functionality)

### Environment Configuration
```bash
conda create -n sphinx python=3.11.8
conda activate sphinx
pip install -r requirements.txt
```

### Application Package Setup

1. Download [APKs](https://drive.google.com/file/d/1M_vCeNCf3WVLL6-ae4AdIXnl5VNSgiIE/view?usp=sharing).
1. Extract contents to apks/ directory

## Task Execution

### End-to-End UI Navigation Task

1. Use `python run_benchmark.py` to run a single task.
2. Use `python run_evaluation.py` to evaluate the generated result.

### Knowledge Probing Task

1. Change the model config in `knowledege_probing.py` and run `python knowledge_probing.py` to evaluate goal-understanding and app-knowledge capability by MCQs/BQs.
2. If the model can not follow specific output format, change the model config and run `extractor.py` to revise the output format by DeepSeek-v2.


### Completion Judgment Task

Change the model config in `run_complete.py` and use `python run_complete.py` to run model on all completion judgment tasks.

### Grounding Task

1. Change the model config in `run_lowlevel.py` and use `python run_lowlevel.py` to run model on all low-level grounding tasks.
2. If the model can not follow specific output format, change the model config and run `parsed_lowlevel.py` to revise the output format by DeepSeek-v2.

### Instruction Following Task

1. Run end-to-end UI navigation task.
2. Change the model config in `eval_instr.py`.
3. Use `python eval_instr.py`.


