"""
test_inference.py — Tests for prediction pipeline components.
"""

from __future__ import annotations

import tempfile
import shutil
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
import torch


class TestPredictionComponents:
    def setup_method(self):
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))

    def test_postprocessing_mask_processor(self):
        from postprocessing.mask_processor import MaskProcessor
        processor = MaskProcessor(threshold=0.5, min_component_size=10, keep_n_largest=1)

        # Create prob_mask with two regions
        prob_mask = np.zeros((100, 100))
        # Large region
        prob_mask[10:40, 10:40] = 0.9 # 30x30 = 900
        # Small region
        prob_mask[60:65, 60:65] = 0.8 # 5x5 = 25
        # Tiny region - will be thresholded out if probability is low, but we give 0.9, so 2x2=4
        prob_mask[80:82, 80:82] = 0.9

        binary_mask, stats = processor.process(prob_mask)
        # Assuming cv2 is available, otherwise clean_components does nothing
        import postprocessing.mask_processor
        if postprocessing.mask_processor._CV2_AVAILABLE:
            assert stats["stone_area_pixels"] == 900
            assert stats["num_components"] == 1
        else:
            # Fallback
            assert stats["stone_area_pixels"] == 900 + 25 + 4

    def test_prediction_pipeline_init(self):
        # We can't fully mock PredictionPipeline without heavy mocking or real weights,
        # but we can test that the imports work and the basic structure is there.
        from prediction.pipeline import PredictionPipeline
        assert PredictionPipeline is not None
