# KidneyStoneAI Segmentation Experiment Framework

This framework provides a rigorous, manually-controlled ablation study environment. It ensures that the baseline configuration remains immutable, output artifacts are perfectly isolated, and any experimental modification is strictly controlled and verified.

## Core Philosophy
- **NO Automatic Sweeps**: Deep learning is resource-intensive. Parameter searches are manual.
- **Isolated State**: Every experiment loads the unmodified `segmentation_config.yaml` as the source of truth, applies exactly one dictionary override, and saves the effective config to a dedicated output folder.
- **Zero Inheritance**: Running `EXP02` does NOT inherit changes from `EXP01`.

## Available Experiments
| ID | Description | Requires Training | Overrides |
|---|---|---|---|
| `EXP00_BASELINE` | Default configuration | Yes | None |
| `EXP01_LOSS_DICE_BCE` | Dice + BCE Loss | Yes | `loss.name` |
| **`EXP02_LOSS_TVERSKY` | Tversky Loss | Yes | `loss.name` |
| `EXP03_LEARNING_RATE` | Learning Rate Ablation | Yes | `training.learning_rate` |
| **`EXP04_AUGMENTATION` | Data Augmentation Ablation | Yes | `augmentation` |
| **`EXP05_INPUT_RESOLUTION`| Input Resolution | Yes | `input.size` |
| `EXP06_NORMALIZATION` | Normalization method | Yes | `preprocessing.normalization` |
| `EXP07_BATCH_SIZE` | Batch Size Ablation | Yes | `training.batch_size` |
| `EXP08_SCHEDULER` | Learning Rate Scheduler | Yes | `training.scheduler` |
| *`EXP09_THRESHOLD` | Threshold Optimization | **No (Inference)** | `evaluation.threshold` |
| *`EXP10_POSTPROCESSING` | Morphological Filtering | **No (Inference)** | `inference.postprocessing` |
| `EXP11_ENCODER` | Backbone Setup | Yes | `model.encoder` |
| **`EXP12_ARCHITECTURE` | Segmentation Arch | Yes | `model.name` |
| `EXP13_ERROR_ANALYSIS` | Worst-case Visualization | **No (Inference)** | Extends evaluator |
| `EXP14_SMALL_STONE_ANALYSIS` | Size-stratified metrics | **No (Inference)** | Extends evaluator |
| `EXP15_2_5D` | Multi-Slice Adjoining Input | Yes | `model.in_channels` |

## Usage

**Method 1 (Recommended): Python Edit**
1. Open `ai-engine/experiments/run_segmentation_experiment.py`.
2. Edit the constant at the top:
   ```python
   EXPERIMENT = "EXP01_LOSS_DICE_BCE"
   ```
3. Run the script:
   ```bash
   python ai-engine/experiments/run_segmentation_experiment.py
   ```

**Method 2: CLI Override**
Run any valid EXP ID directly via terminal:
```bash
python ai-engine/experiments/run_segmentation_experiment.py --experiment EXP03_LEARNING_RATE
```

## How Results are Logged
When you run a training experiment:
1. The model will optimize and save weights to `ai-engine/weights/segmentation/<EXP_ID>`.
2. It will evaluate on the isolated `test` split.
3. It will write performance deltas explicitly into `outputs/segmentation/experiments/experiment_results.csv`.
4. Visualizations will be automatically generated in `outputs/segmentation/experiments/<EXP_ID>/test_results/visualizations/`.

For inference experiments (e.g., `EXP09_THRESHOLD`), the script will autonomously load the already trained `EXP00_BASELINE` model weights, run evaluations over validation sets to find best heuristics, and test them on the split without mutating baseline checkpoints.
