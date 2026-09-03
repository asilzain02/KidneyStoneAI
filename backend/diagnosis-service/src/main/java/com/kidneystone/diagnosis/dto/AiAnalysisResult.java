package com.kidneystone.diagnosis.dto;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.Data;

import java.util.Map;

/**
 * Purpose:
 *   Java representation of the JSON response returned by the Python AI Engine
 *   POST /api/v1/ai/analyze endpoint.
 *
 *   @JsonIgnoreProperties(ignoreUnknown = true) ensures that if the AI Engine
 *   adds new fields in a future version, Spring does not fail to deserialise.
 *
 *   Field names match the Python Pydantic schema (camelCase) exactly.
 */
@Data
@JsonIgnoreProperties(ignoreUnknown = true)
public class AiAnalysisResult {

    private String inferenceId;
    private Classification classification;
    private Segmentation segmentation;
    private Explainability explainability;
    private Consistency consistency;
    private Models models;
    private Metadata metadata;

    // ── Nested DTOs ───────────────────────────────────────────────────────────

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Classification {
        /** Predicted class name: Normal / Cyst / Stone / Tumor */
        private String predictedClass;
        /** Softmax confidence 0.0 - 1.0 */
        private Double confidence;
        /** Probabilities for all 4 classes */
        private Map<String, Double> probabilities;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Segmentation {
        private Boolean detected;
        private Integer stoneAreaPixels;
        private Integer totalPixels;
        private Double coverageRatio;
        private Integer numComponents;
        private BoundingBox boundingBox;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class BoundingBox {
        private Integer x;
        private Integer y;
        private Integer width;
        private Integer height;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Explainability {
        /** Always "Grad-CAM" in this version */
        private String method;
        private String description;
        private String targetClass;
        private String targetLayer;
        /** Relative path to heatmap PNG on AI Engine filesystem */
        private String heatmapPath;
        /** Relative path to overlay PNG on AI Engine filesystem */
        private String overlayPath;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Consistency {
        /** CONSISTENT | PARTIAL_DISAGREEMENT | DISAGREEMENT */
        private String status;
        private String message;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Models {
        private String classificationCheckpoint;
        private String segmentationCheckpoint;
        private String segmentationExperiment;
    }

    @Data
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class Metadata {
        /** "cuda" or "cpu" */
        private String device;
        private Integer processingTimeMs;
        private String timestamp;
    }
}
