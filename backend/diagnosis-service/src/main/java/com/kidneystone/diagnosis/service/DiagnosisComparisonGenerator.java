package com.kidneystone.diagnosis.service;

import com.kidneystone.diagnosis.entity.Diagnosis;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Purpose:
 *   Generate a deterministic, composite PNG comparison image for a completed
 *   diagnosis from ACTUAL system outputs only.
 *
 *   The image layout is:
 *
 *   ┌─────────────────────────────────────────────────────────────────────┐
 *   │               KIDNEY STONE — AI ANALYSIS COMPARISON                │
 *   ├──────────────────────┬──────────────────────┬───────────────────────┤
 *   │   ORIGINAL CT IMAGE  │   CLASSIFICATION     │   SEGMENTATION RESULT │
 *   │                      │                      │                       │
 *   │  <actual CT bytes>   │  Class: Stone        │  Detected: No         │
 *   │                      │  Confidence: 98.7%   │  Area: 0 px           │
 *   │                      │                      │  Coverage: 0.0%       │
 *   ├──────────────────────┴──────────────────────┴───────────────────────┤
 *   │   CONSISTENCY / CROSS-VALIDATION                                     │
 *   │   Status: PARTIAL_DISAGREEMENT                                       │
 *   │   Classification predicts kidney stone, but segmentation did not …  │
 *   ├─────────────────────────────────────────────────────────────────────┤
 *   │   GRAD-CAM / EXPLAINABILITY  (if available)                         │
 *   │  <actual heatmap/overlay image>                                      │
 *   └─────────────────────────────────────────────────────────────────────┘
 *
 *   Rules:
 *     - Uses ONLY actual data from the Diagnosis entity.
 *     - Does NOT fabricate medical findings.
 *     - Segmentation and classification are shown independently.
 *     - Disagreement is clearly displayed, not hidden.
 *     - If Grad-CAM is unavailable the panel is omitted cleanly.
 *     - Output is a standard PNG file.
 *
 *   Terminology:
 *     All user-facing text uses "AI prediction / Model confidence" language,
 *     never "confirmed diagnosis / guaranteed result."
 *
 *   Thread safety: stateless — safe for concurrent calls.
 */
@Slf4j
@Component
public class DiagnosisComparisonGenerator {

    // ── Layout constants ─────────────────────────────────────────────────────

    private static final int PANEL_W      = 420;   // width of each top panel
    private static final int PANEL_H      = 340;   // height of image area in top panels
    private static final int NUMERAL_PAD  = 20;    // internal cell padding
    private static final int HEADER_H     = 60;    // top banner height
    private static final int CONSIST_H    = 120;   // consistency panel height
    private static final int GRADCAM_H    = 300;   // Grad-CAM panel height (when present)
    private static final int FOOTER_H     = 36;    // disclaimer footer
    private static final int TOTAL_W      = PANEL_W * 3;

    // ── Colour palette ───────────────────────────────────────────────────────

    private static final Color COL_BG_DARK    = new Color(18,  24,  38);   // canvas background
    private static final Color COL_BG_PANEL   = new Color(28,  36,  54);   // panel background
    private static final Color COL_BG_HEADER  = new Color(12,  16,  28);   // header strip
    private static final Color COL_BORDER     = new Color(55,  72, 110);   // panel border
    private static final Color COL_ACCENT     = new Color(91, 146, 255);   // accent blue
    private static final Color COL_WARN       = new Color(255, 180,  50);  // warning amber
    private static final Color COL_OK         = new Color( 60, 200, 130);  // success green
    private static final Color COL_LABEL      = new Color(160, 180, 220);  // secondary label
    private static final Color COL_VALUE      = new Color(230, 240, 255);  // primary value
    private static final Color COL_SEPARATOR  = new Color(40,  52,  80);   // separator line
    private static final Color COL_DISCLAIMER = new Color(100, 115, 150);  // disclaimer text

    // ── Storage ──────────────────────────────────────────────────────────────

    @Value("${diagnosis.comparison.output-dir:${java.io.tmpdir}/kidneystone-comparisons}")
    private String outputDir;

    // ── Public API ───────────────────────────────────────────────────────────

    /**
     * Purpose:
     *   Generate (or retrieve a cached) comparison image for the given diagnosis.
     *
     *   Cache key: {outputDir}/{diagnosisId}.png
     *   If the file already exists it is returned directly without re-rendering.
     *
     * @param diagnosis       saved, completed Diagnosis entity
     * @param originalCtBytes raw bytes of the original CT image (from Image Service)
     * @param gradCamBytes    raw bytes of the Grad-CAM overlay (may be null)
     * @return absolute Path to the written PNG file
     */
    public Path generateAndCache(Diagnosis diagnosis, byte[] originalCtBytes, byte[] gradCamBytes)
            throws IOException {

        ensureOutputDirExists();

        Path outputPath = buildOutputPath(diagnosis.getId().toString());

        if (Files.exists(outputPath)) {
            log.debug("Comparison image already exists, returning cached: {}", outputPath);
            return outputPath;
        }

        BufferedImage composite = render(diagnosis, originalCtBytes, gradCamBytes);
        try (OutputStream os = Files.newOutputStream(outputPath)) {
            ImageIO.write(composite, "PNG", os);
        }

        log.info("Comparison image written: {}", outputPath);
        return outputPath;
    }

    /**
     * Purpose:
     *   Return the cached PNG path if it exists, otherwise null.
     *   Used by the endpoint to serve without re-generating.
     */
    public Path getCachedPath(String diagnosisId) {
        Path p = buildOutputPath(diagnosisId);
        return Files.exists(p) ? p : null;
    }

    // ── Rendering ────────────────────────────────────────────────────────────

    private BufferedImage render(Diagnosis d, byte[] ctBytes, byte[] gradCamBytes) {

        boolean hasGradCam = gradCamBytes != null && gradCamBytes.length > 0;

        int totalH = HEADER_H + PANEL_H + CONSIST_H + (hasGradCam ? GRADCAM_H : 0) + FOOTER_H;
        BufferedImage canvas = new BufferedImage(TOTAL_W, totalH, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = canvas.createGraphics();

        enableAntiAliasing(g);
        g.setColor(COL_BG_DARK);
        g.fillRect(0, 0, TOTAL_W, totalH);

        int y = 0;

        // 1. Banner header
        y = drawHeader(g, y);

        // 2. Three top panels
        y = drawTopPanels(g, d, ctBytes, y);

        // 3. Consistency bar
        y = drawConsistencyPanel(g, d, y);

        // 4. Grad-CAM panel (conditional)
        if (hasGradCam) {
            y = drawGradCamPanel(g, d, gradCamBytes, y);
        }

        // 5. Footer disclaimer
        drawFooter(g, y);

        g.dispose();
        return canvas;
    }

    // ── Section renderers ─────────────────────────────────────────────────────

    private int drawHeader(Graphics2D g, int y) {
        g.setColor(COL_BG_HEADER);
        g.fillRect(0, y, TOTAL_W, HEADER_H);

        // Accent line
        g.setColor(COL_ACCENT);
        g.fillRect(0, y + HEADER_H - 3, TOTAL_W, 3);

        g.setColor(COL_VALUE);
        g.setFont(boldFont(22));
        String title = "KIDNEY STONE — AI-ASSISTED CT ANALYSIS";
        int tw = g.getFontMetrics().stringWidth(title);
        g.drawString(title, (TOTAL_W - tw) / 2, y + 38);

        return y + HEADER_H;
    }

    private int drawTopPanels(Graphics2D g, Diagnosis d, byte[] ctBytes, int y) {
        drawOriginalCt(g,           0,          y, ctBytes);
        drawClassification(g,  PANEL_W,          y, d);
        drawSegmentation(g, PANEL_W * 2,          y, d);
        return y + PANEL_H;
    }

    /** Panel 1: Original CT image rendered to fit the panel */
    private void drawOriginalCt(Graphics2D g, int x, int y, byte[] ctBytes) {
        drawPanelBackground(g, x, y, PANEL_W, PANEL_H);

        String label = "ORIGINAL CT IMAGE";
        drawPanelLabel(g, x, y, label, COL_ACCENT);

        int imgY = y + 32;
        int imgH = PANEL_H - 40;

        if (ctBytes != null && ctBytes.length > 0) {
            try {
                BufferedImage ct = ImageIO.read(new ByteArrayInputStream(ctBytes));
                if (ct != null) {
                    // Scale preserving aspect ratio
                    int[] dims = scaledDims(ct.getWidth(), ct.getHeight(), PANEL_W - NUMERAL_PAD * 2, imgH - NUMERAL_PAD);
                    int ix = x + (PANEL_W - dims[0]) / 2;
                    int iy = imgY + (imgH - dims[1]) / 2;
                    g.drawImage(ct, ix, iy, dims[0], dims[1], null);
                    return;
                }
            } catch (IOException e) {
                log.warn("Could not decode CT image for comparison panel: {}", e.getMessage());
            }
        }

        // Fallback: placeholder
        drawPlaceholderBox(g, x + NUMERAL_PAD, imgY + NUMERAL_PAD / 2,
                PANEL_W - NUMERAL_PAD * 2, imgH - NUMERAL_PAD, "CT image unavailable");
    }

    /** Panel 2: Classification result — text only, no fabricated imagery */
    private void drawClassification(Graphics2D g, int x, int y, Diagnosis d) {
        drawPanelBackground(g, x, y, PANEL_W, PANEL_H);
        drawPanelLabel(g, x, y, "CLASSIFICATION (AI PREDICTION)", COL_ACCENT);

        int cy = y + 80;
        int cx = x + PANEL_W / 2;

        // Predicted class — large prominent display
        String cls = d.getPredictedClass() != null ? d.getPredictedClass().toUpperCase() : "UNKNOWN";
        Color classColor = classColor(d.getPredictedClass());

        // Class chip
        g.setFont(boldFont(32));
        int cw = g.getFontMetrics().stringWidth(cls);
        int chipPad = 18;
        int chipW   = cw + chipPad * 2;
        int chipH   = 54;
        int chipX   = cx - chipW / 2;
        g.setColor(classColor.darker().darker());
        g.fillRoundRect(chipX, cy, chipW, chipH, 12, 12);
        g.setColor(classColor);
        g.drawRoundRect(chipX, cy, chipW, chipH, 12, 12);
        g.setColor(Color.WHITE);
        g.drawString(cls, chipX + chipPad, cy + 38);

        cy += chipH + 20;

        // Confidence
        if (d.getConfidence() != null) {
            double pct = d.getConfidence() * 100.0;
            String confStr = String.format("%.2f%%", pct);

            drawLabelValue(g, cx, cy, "Model Confidence", confStr, COL_LABEL, COL_VALUE);
            cy += 30;

            // Confidence bar
            int barW = PANEL_W - NUMERAL_PAD * 4;
            int barH = 10;
            int barX = x + NUMERAL_PAD * 2;
            g.setColor(COL_BG_DARK);
            g.fillRoundRect(barX, cy, barW, barH, barH, barH);
            int filled = (int) (barW * d.getConfidence());
            g.setColor(classColor);
            g.fillRoundRect(barX, cy, filled, barH, barH, barH);
        } else {
            drawCentred(g, cx, cy + 14, "Confidence: N/A", COL_LABEL, plainFont(14));
        }

        cy += 36;

        // Terminology disclaimer
        int dW = PANEL_W - NUMERAL_PAD * 2;
        drawWrapped(g, x + NUMERAL_PAD, cy, dW, "AI model prediction only.\nNot a confirmed clinical diagnosis.", COL_DISCLAIMER, plainFont(11));
    }

    /** Panel 3: Segmentation result — strictly from entity metadata, never fabricated */
    private void drawSegmentation(Graphics2D g, int x, int y, Diagnosis d) {
        drawPanelBackground(g, x, y, PANEL_W, PANEL_H);
        drawPanelLabel(g, x, y, "SEGMENTATION RESULT", COL_ACCENT);

        int cx = x + PANEL_W / 2;
        int cy = y + 75;

        boolean detected = Boolean.TRUE.equals(d.getStoneDetected());

        // Detection badge
        String badge = detected ? "STONE REGION DETECTED" : "NO REGION DETECTED";
        Color badgeColor = detected ? COL_WARN : COL_LABEL;

        g.setFont(boldFont(14));
        int bw = g.getFontMetrics().stringWidth(badge);
        int bPad = 12;
        int bW   = bw + bPad * 2;
        int bH   = 34;
        int bX   = cx - bW / 2;
        g.setColor(badgeColor.darker().darker());
        g.fillRoundRect(bX, cy, bW, bH, 8, 8);
        g.setColor(badgeColor);
        g.drawRoundRect(bX, cy, bW, bH, 8, 8);
        g.setColor(Color.WHITE);
        g.drawString(badge, bX + bPad, cy + 22);

        cy += bH + 28;

        // Metadata table
        Object[][] rows = {
            {"Stone Area",      d.getStoneAreaPixels() != null ? d.getStoneAreaPixels() + " px" : "N/A"},
            {"Coverage Ratio",  d.getCoverageRatio()   != null ? String.format("%.4f (%.2f%%)",
                                    d.getCoverageRatio(), d.getCoverageRatio() * 100.0) : "N/A"},
        };

        for (Object[] row : rows) {
            drawLabelValue(g, cx, cy, (String) row[0], (String) row[1], COL_LABEL, COL_VALUE);
            cy += 30;
        }

        cy += 10;
        // Visual note
        String note = detected
                ? "A potential stone region was identified by the segmentation model."
                : "The segmentation model found no stone region above the detection threshold.";
        int noteW = PANEL_W - NUMERAL_PAD * 2;
        drawWrapped(g, x + NUMERAL_PAD, cy, noteW, note, COL_DISCLAIMER, plainFont(11));
    }

    /** Consistency panel — always shown with actual values */
    private int drawConsistencyPanel(Graphics2D g, Diagnosis d, int y) {
        // Separator
        g.setColor(COL_SEPARATOR);
        g.fillRect(0, y, TOTAL_W, 2);

        g.setColor(COL_BG_PANEL);
        g.fillRect(0, y + 2, TOTAL_W, CONSIST_H);

        // Accent side bar
        String status = d.getConsistencyStatus();
        Color sideColor = consistencyColor(status);
        g.setColor(sideColor);
        g.fillRect(0, y + 2, 5, CONSIST_H);

        // Label
        g.setFont(boldFont(13));
        g.setColor(COL_LABEL);
        g.drawString("CONSISTENCY / CROSS-VALIDATION", NUMERAL_PAD + 8, y + 30);

        // Status badge
        String statusDisplay = status != null ? status.replace("_", " ") : "UNKNOWN";
        g.setFont(boldFont(14));
        int sw = g.getFontMetrics().stringWidth(statusDisplay);
        int sX = NUMERAL_PAD + 8;
        int sY = y + 44;
        int sPad = 10;
        int sChipW = sw + sPad * 2;
        int sChipH = 28;
        g.setColor(sideColor.darker().darker());
        g.fillRoundRect(sX, sY, sChipW, sChipH, 6, 6);
        g.setColor(sideColor);
        g.drawRoundRect(sX, sY, sChipW, sChipH, 6, 6);
        g.setColor(Color.WHITE);
        g.drawString(statusDisplay, sX + sPad, sY + 19);

        // Message
        if (d.getConsistencyMessage() != null && !d.getConsistencyMessage().isBlank()) {
            int msgX = NUMERAL_PAD + 8;
            int msgY = sY + sChipH + 14;
            int msgW = TOTAL_W - NUMERAL_PAD * 2;
            drawWrapped(g, msgX, msgY, msgW, d.getConsistencyMessage(), COL_VALUE, plainFont(13));
        }

        return y + CONSIST_H;
    }

    /** Grad-CAM panel — shown only when actual Grad-CAM bytes are available */
    private int drawGradCamPanel(Graphics2D g, Diagnosis d, byte[] gradCamBytes, int y) {
        g.setColor(COL_SEPARATOR);
        g.fillRect(0, y, TOTAL_W, 2);

        g.setColor(COL_BG_PANEL);
        g.fillRect(0, y + 2, TOTAL_W, GRADCAM_H);

        g.setColor(COL_ACCENT);
        g.fillRect(0, y + 2, 5, GRADCAM_H);

        g.setFont(boldFont(13));
        g.setColor(COL_LABEL);
        g.drawString("GRAD-CAM EXPLAINABILITY — Classification Heat Map", NUMERAL_PAD + 8, y + 28);

        g.setFont(plainFont(11));
        g.setColor(COL_DISCLAIMER);
        String method = d.getXaiMethod() != null ? d.getXaiMethod() : "Grad-CAM";
        g.drawString("Method: " + method + "  |  Highlights regions influencing the classification prediction.",
                NUMERAL_PAD + 8, y + 44);

        int imgY    = y + 54;
        int imgH    = GRADCAM_H - 60;
        int maxW    = TOTAL_W - NUMERAL_PAD * 2;

        try {
            BufferedImage gc = ImageIO.read(new ByteArrayInputStream(gradCamBytes));
            if (gc != null) {
                int[] dims = scaledDims(gc.getWidth(), gc.getHeight(), maxW, imgH);
                int ix = NUMERAL_PAD + (maxW - dims[0]) / 2;
                int iy = imgY + (imgH - dims[1]) / 2;
                g.drawImage(gc, ix, iy, dims[0], dims[1], null);
            }
        } catch (IOException e) {
            log.warn("Could not decode Grad-CAM image for comparison: {}", e.getMessage());
            drawPlaceholderBox(g, NUMERAL_PAD, imgY, maxW, imgH, "Grad-CAM image could not be decoded");
        }

        return y + GRADCAM_H;
    }

    private void drawFooter(Graphics2D g, int y) {
        g.setColor(COL_BG_HEADER);
        g.fillRect(0, y, TOTAL_W, FOOTER_H);
        g.setFont(plainFont(11));
        g.setColor(COL_DISCLAIMER);
        String footer = "⚠  Clinical Decision Support Only — AI predictions require physician evaluation before clinical action.";
        int fw = g.getFontMetrics().stringWidth(footer);
        g.drawString(footer, (TOTAL_W - fw) / 2, y + 22);
    }

    // ── Drawing helpers ───────────────────────────────────────────────────────

    private void drawPanelBackground(Graphics2D g, int x, int y, int w, int h) {
        g.setColor(COL_BG_PANEL);
        g.fillRect(x, y, w, h);
        g.setColor(COL_BORDER);
        g.drawRect(x, y, w - 1, h - 1);
    }

    private void drawPanelLabel(Graphics2D g, int x, int y, String label, Color color) {
        g.setColor(color.darker());
        g.fillRect(x, y, PANEL_W, 28);
        g.setFont(boldFont(12));
        g.setColor(Color.WHITE);
        g.drawString(label, x + NUMERAL_PAD, y + 18);
    }

    private void drawLabelValue(Graphics2D g, int cx, int y, String label, String value,
                                 Color labelColor, Color valueColor) {
        g.setFont(plainFont(12));
        g.setColor(labelColor);
        String full = label + ":  ";
        int lw = g.getFontMetrics().stringWidth(full);
        g.drawString(full, cx - lw, y);
        g.setFont(boldFont(12));
        g.setColor(valueColor);
        g.drawString(value, cx, y);
    }

    private void drawCentred(Graphics2D g, int cx, int y, String text, Color color, Font font) {
        g.setFont(font);
        g.setColor(color);
        int w = g.getFontMetrics().stringWidth(text);
        g.drawString(text, cx - w / 2, y);
    }

    private void drawWrapped(Graphics2D g, int x, int y, int maxW, String text, Color color, Font font) {
        g.setFont(font);
        g.setColor(color);
        FontMetrics fm = g.getFontMetrics();
        int lineH = fm.getHeight() + 2;
        for (String line : text.split("\n")) {
            // Simple word-wrap
            String[] words = line.split(" ");
            StringBuilder current = new StringBuilder();
            int cy = y;
            for (String word : words) {
                String test = current.isEmpty() ? word : current + " " + word;
                if (fm.stringWidth(test) > maxW && !current.isEmpty()) {
                    g.drawString(current.toString(), x, cy);
                    cy += lineH;
                    current = new StringBuilder(word);
                } else {
                    current = new StringBuilder(test);
                }
            }
            if (!current.isEmpty()) {
                g.drawString(current.toString(), x, cy);
                cy += lineH;
            }
            y = cy;
        }
    }

    private void drawPlaceholderBox(Graphics2D g, int x, int y, int w, int h, String message) {
        g.setColor(COL_SEPARATOR);
        g.fillRect(x, y, w, h);
        g.setColor(COL_BORDER);
        g.drawRect(x, y, w, h);
        g.setFont(plainFont(12));
        g.setColor(COL_LABEL);
        int tw = g.getFontMetrics().stringWidth(message);
        g.drawString(message, x + (w - tw) / 2, y + h / 2);
    }

    // ── Utilities ─────────────────────────────────────────────────────────────

    private static Color classColor(String cls) {
        if (cls == null) return COL_LABEL;
        return switch (cls.toLowerCase()) {
            case "stone"  -> new Color(255, 140,  40);
            case "tumor"  -> new Color(220,  50,  50);
            case "cyst"   -> new Color(140, 160, 255);
            case "normal" -> COL_OK;
            default       -> COL_LABEL;
        };
    }

    private static Color consistencyColor(String status) {
        if (status == null) return COL_LABEL;
        return switch (status.toUpperCase()) {
            case "CONSISTENT"            -> COL_OK;
            case "PARTIAL_DISAGREEMENT"  -> COL_WARN;
            case "DISAGREEMENT"          -> new Color(220, 60, 60);
            default                      -> COL_LABEL;
        };
    }

    private static int[] scaledDims(int srcW, int srcH, int maxW, int maxH) {
        if (srcW <= 0 || srcH <= 0) return new int[]{maxW, maxH};
        double scale = Math.min((double) maxW / srcW, (double) maxH / srcH);
        return new int[]{Math.max(1, (int)(srcW * scale)), Math.max(1, (int)(srcH * scale))};
    }

    private static Font boldFont(int size)  { return new Font("SansSerif", Font.BOLD,  size); }
    private static Font plainFont(int size) { return new Font("SansSerif", Font.PLAIN, size); }

    private static void enableAntiAliasing(Graphics2D g) {
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING,        RenderingHints.VALUE_ANTIALIAS_ON);
        g.setRenderingHint(RenderingHints.KEY_TEXT_ANTIALIASING,   RenderingHints.VALUE_TEXT_ANTIALIAS_LCD_HRGB);
        g.setRenderingHint(RenderingHints.KEY_RENDERING,           RenderingHints.VALUE_RENDER_QUALITY);
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION,       RenderingHints.VALUE_INTERPOLATION_BICUBIC);
    }

    private void ensureOutputDirExists() throws IOException {
        Path dir = Paths.get(outputDir);
        if (!Files.exists(dir)) {
            Files.createDirectories(dir);
            log.info("Created comparison output directory: {}", dir.toAbsolutePath());
        }
    }

    private Path buildOutputPath(String diagnosisId) {
        return Paths.get(outputDir).resolve(diagnosisId + ".png");
    }
}
