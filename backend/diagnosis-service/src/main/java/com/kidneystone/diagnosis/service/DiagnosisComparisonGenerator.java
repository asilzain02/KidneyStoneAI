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
 *   Generate a highly professional, 3-panel clinical composite PNG comparison image.
 *   
 *   Design Architecture:
 *   1| Original CT               - Exact unmodified source
 *   2| Segmentation mask         - Localization Evidence ("WHERE")
 *   3| GradCam heatmap           - Classification Explainability ("WHY")
 *   
 *   Followed by Consistency block, then fully expanded 4-column metadata tracking.
 */
@Slf4j
@Component
public class DiagnosisComparisonGenerator {

    private static final int PANEL_W      = 640;
    private static final int PANEL_H      = 640;
    private static final int NUMERAL_PAD  = 30;
    private static final int HEADER_H     = 100;
    private static final int CONSIST_H    = 140;
    private static final int STATS_H      = 220;
    private static final int FOOTER_H     = 50;
    private static final int TOTAL_W      = PANEL_W * 3; // 1920

    private static final Color COL_BG_DARK    = new Color(20,  24,  32);
    private static final Color COL_BG_PANEL   = new Color(30,  36,  48);
    private static final Color COL_BG_HEADER  = new Color(14,  18,  26);
    private static final Color COL_BORDER     = new Color(55,  72, 110);
    private static final Color COL_ACCENT     = new Color(91, 146, 255);
    private static final Color COL_WARN       = new Color(255, 160,  40);
    private static final Color COL_OK         = new Color( 60, 200, 130);
    private static final Color COL_ERROR      = new Color(235,  80,  80);
    private static final Color COL_LABEL      = new Color(170, 190, 230);
    private static final Color COL_VALUE      = new Color(240, 245, 255);
    private static final Color COL_SEPARATOR  = new Color(42,  54,  82);
    private static final Color COL_DISCLAIMER = new Color(110, 125, 160);

    @Value("${diagnosis.comparison.output-dir:${java.io.tmpdir}/kidneystone-comparisons}")
    private String outputDir;

    public Path generateAndCache(Diagnosis diagnosis, byte[] originalCtBytes, byte[] gradCamBytes, byte[] segOverlayBytes)
            throws IOException {

        ensureOutputDirExists();
        Path outputPath = buildOutputPath(diagnosis.getId().toString());

        if (Files.exists(outputPath)) {
            log.debug("Comparison image already exists, returning cached: {}", outputPath);
            return outputPath;
        }

        log.info("Generating comparison PNG. OriginalCT: {} bytes, GradCam: {} bytes, SegOverlay: {} bytes",
                originalCtBytes != null ? originalCtBytes.length : 0, 
                gradCamBytes != null ? gradCamBytes.length : 0, 
                segOverlayBytes != null ? segOverlayBytes.length : 0);

        BufferedImage composite = render(diagnosis, originalCtBytes, gradCamBytes, segOverlayBytes);
        try (OutputStream os = Files.newOutputStream(outputPath)) {
            ImageIO.write(composite, "PNG", os);
        }

        log.info("Comparison image successfully written: {}", outputPath);
        return outputPath;
    }

    public Path getCachedPath(String diagnosisId) {
        Path p = buildOutputPath(diagnosisId);
        return Files.exists(p) ? p : null;
    }

    private BufferedImage render(Diagnosis d, byte[] ctBytes, byte[] gradCamBytes, byte[] segOverlayBytes) {
        int totalH = HEADER_H + PANEL_H + CONSIST_H + STATS_H + FOOTER_H;
        BufferedImage canvas = new BufferedImage(TOTAL_W, totalH, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = canvas.createGraphics();

        enableAntiAliasing(g);
        
        // Deep background layer
        g.setColor(COL_BG_DARK);
        g.fillRect(0, 0, TOTAL_W, totalH);

        int y = 0;
        y = drawHeader(g, y);
        y = drawTopPanels(g, d, ctBytes, gradCamBytes, segOverlayBytes, y);
        y = drawConsistencyPanel(g, d, y);
        y = drawStatsGrid(g, d, y);
        drawFooter(g, y);

        g.dispose();
        return canvas;
    }

    private int drawHeader(Graphics2D g, int y) {
        g.setColor(COL_BG_HEADER);
        g.fillRect(0, y, TOTAL_W, HEADER_H);
        
        g.setColor(COL_ACCENT);
        g.fillRect(0, y + HEADER_H - 4, TOTAL_W, 4);
        
        g.setColor(COL_VALUE);
        g.setFont(boldFont(28));
        String title = "KIDNEY STONE — AI-ASSISTED CT ANALYSIS";
        int tw = g.getFontMetrics().stringWidth(title);
        g.drawString(title, (TOTAL_W - tw) / 2, y + 45);

        g.setColor(COL_LABEL);
        g.setFont(boldFont(16));
        String sub = "Automated Detection • Explainable AI • Clinical Decision Support";
        int sw = g.getFontMetrics().stringWidth(sub);
        g.drawString(sub, (TOTAL_W - sw) / 2, y + 75);
        return y + HEADER_H;
    }

    private int drawTopPanels(Graphics2D g, Diagnosis d, byte[] ctBytes, byte[] gradCamBytes, byte[] segOverlayBytes, int y) {
        drawOriginalCt(g, 0, y, ctBytes);
        drawSegmentationImg(g, PANEL_W, y, d, segOverlayBytes);
        drawGradCamImg(g, PANEL_W * 2, y, d, gradCamBytes);
        return y + PANEL_H;
    }

    private void drawOriginalCt(Graphics2D g, int x, int y, byte[] ctBytes) {
        drawPanelBackground(g, x, y, PANEL_W, PANEL_H);
        drawPanelHeader(g, x, y, "ORIGINAL CT IMAGE");
        
        boolean loaded = drawImageBlock(g, x, y + 40, PANEL_W, PANEL_H - 100, ctBytes, "Source CT Unavailable", "ORIGINAL-CT");
        
        if (loaded) {
            drawCentred(g, x + PANEL_W/2, y + PANEL_H - 40, "Unmodified Source Scan", COL_VALUE, boldFont(16));
            drawCentred(g, x + PANEL_W/2, y + PANEL_H - 18, "Diagnostic Input", COL_DISCLAIMER, plainFont(13));
        }
    }

    private void drawSegmentationImg(Graphics2D g, int x, int y, Diagnosis d, byte[] segBytes) {
        drawPanelBackground(g, x, y, PANEL_W, PANEL_H);
        drawPanelHeader(g, x, y, "SEGMENTATION RESULT — WHERE IS THE STONE?");
        
        boolean loaded = drawImageBlock(g, x, y + 40, PANEL_W, PANEL_H - 100, segBytes, "Visualisation Artifact Unavailable", "SEGMENTATION");
        
        boolean detected = Boolean.TRUE.equals(d.getStoneDetected());
        String msg = detected ? "\u25CF Detected Stone Region (Segmentation Mask)" : "No Regions Detected Above Threshold";
        Color c = detected ? COL_WARN : COL_LABEL;
        
        if (!detected && !loaded) {
             msg = "No Stone Detected";
        }
        
        drawCentred(g, x + PANEL_W/2, y + PANEL_H - 40, msg, c, boldFont(16));
        drawCentred(g, x + PANEL_W/2, y + PANEL_H - 18, "Architecture localization evidence", COL_DISCLAIMER, plainFont(13));
    }

    private void drawGradCamImg(Graphics2D g, int x, int y, Diagnosis d, byte[] gcBytes) {
        drawPanelBackground(g, x, y, PANEL_W, PANEL_H);
        drawPanelHeader(g, x, y, "GRAD-CAM — WHY DID THE MODEL PREDICT?");
        
        boolean loaded = drawImageBlock(g, x, y + 40, PANEL_W, PANEL_H - 100, gcBytes, "Grad-CAM Artifact Unavailable", "GRAD-CAM");
        
        String legendStr = loaded ? "Low Influence \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500 High Influence" : "";
        drawCentred(g, x + PANEL_W/2, y + PANEL_H - 40, legendStr, COL_VALUE, boldFont(14));
        drawCentred(g, x + PANEL_W/2, y + PANEL_H - 18, "Classification model explainability", COL_DISCLAIMER, plainFont(13));
    }

    /** Returns true if image successfully decoded. */
    private boolean drawImageBlock(Graphics2D g, int bx, int by, int bw, int bh, byte[] bytes, String fallback, String logLabel) {
        if (bytes != null && bytes.length > 0) {
            try {
                BufferedImage img = ImageIO.read(new ByteArrayInputStream(bytes));
                if (img != null) {
                    log.info("[{}] decoded=true, dimensions={}x{}", logLabel, img.getWidth(), img.getHeight());
                    int padX = 40;
                    int padY = 20;
                    int[] dims = scaledDims(img.getWidth(), img.getHeight(), bw - padX * 2, bh - padY * 2);
                    int ix = bx + (bw - dims[0]) / 2;
                    int iy = by + (bh - dims[1]) / 2;
                    
                    // Draw black background behind image so it stands out natively 
                    g.setColor(Color.BLACK);
                    g.fillRect(ix - 2, iy - 2, dims[0] + 4, dims[1] + 4);
                    
                    g.drawImage(img, ix, iy, dims[0], dims[1], null);
                    return true;
                } else {
                    log.warn("[{}] decoded=false (ImageIO returned null)", logLabel);
                }
            } catch (IOException e) {
                log.error("[{}] Image decode payload failed: {}", logLabel, e.getMessage());
            }
        } else {
            log.warn("[{}] bytes array is null or empty", logLabel);
        }
        drawPlaceholderBox(g, bx + 50, by + 50, bw - 100, bh - 100, fallback);
        return false;
    }

    private int drawConsistencyPanel(Graphics2D g, Diagnosis d, int y) {
        g.setColor(COL_SEPARATOR);
        g.fillRect(0, y, TOTAL_W, 2);
        g.setColor(COL_BG_PANEL);
        g.fillRect(0, y + 2, TOTAL_W, CONSIST_H);
        
        String status = d.getConsistencyStatus();
        Color sideColor = consistencyColor(status);
        g.setColor(sideColor);
        g.fillRect(0, y + 2, 8, CONSIST_H);

        g.setFont(boldFont(16));
        g.setColor(COL_LABEL);
        g.drawString("CONSISTENCY / CROSS-VALIDATION", NUMERAL_PAD + 20, y + 45);

        String statusDisplay = status != null ? status.replace("_", " ") : "UNKNOWN";
        g.setFont(boldFont(18));
        int sw = g.getFontMetrics().stringWidth(statusDisplay);
        int sX = NUMERAL_PAD + 20;
        int sY = y + 65;
        int sPad = 15;
        
        g.setColor(new Color(sideColor.getRed(), sideColor.getGreen(), sideColor.getBlue(), 35));
        g.fillRoundRect(sX, sY, sw + sPad * 2, 40, 8, 8);
        g.setColor(sideColor);
        g.setStroke(new BasicStroke(2));
        g.drawRoundRect(sX, sY, sw + sPad * 2, 40, 8, 8);
        g.setColor(Color.WHITE);
        g.drawString(statusDisplay, sX + sPad, sY + 27);

        if (d.getConsistencyMessage() != null) {
            drawWrapped(g, sX + sw + 70, y + 55, TOTAL_W - 400, d.getConsistencyMessage(), COL_VALUE, plainFont(18));
        }
        return y + CONSIST_H;
    }

    private int drawStatsGrid(Graphics2D g, Diagnosis d, int y) {
        g.setColor(COL_SEPARATOR);
        g.fillRect(0, y, TOTAL_W, 2);
        g.setColor(COL_BG_DARK);
        g.fillRect(0, y+2, TOTAL_W, STATS_H);
        
        int statW = TOTAL_W / 4;
        
        // Col 1
        int cx = statW/2;
        String cls = d.getPredictedClass() != null ? d.getPredictedClass().toUpperCase() : "UNKNOWN";
        drawCentred(g, cx, y+50, "CLASSIFICATION PREDICTION", COL_LABEL, boldFont(16));
        drawCentred(g, cx, y+100, cls, classColor(d.getPredictedClass()), boldFont(32));
        
        String confStr = d.getConfidence() != null ? String.format("%.2f%%", d.getConfidence() * 100) : "N/A";
        drawCentred(g, cx, y+150, "Model Confidence", COL_DISCLAIMER, boldFont(14));
        drawCentred(g, cx, y+175, confStr, COL_VALUE, boldFont(22));

        // Col 2
        cx += statW;
        String pxStr = d.getStoneAreaPixels() != null ? d.getStoneAreaPixels() + " px" : "N/A";
        boolean detected = Boolean.TRUE.equals(d.getStoneDetected());
        String detLabel = detected ? "STONE REGION DETECTED" : "NO STONE DETECTED";
        
        drawCentred(g, cx, y+50, "SEGMENTATION ANALYSIS", COL_LABEL, boldFont(16));
        drawCentred(g, cx, y+100, detLabel, detected ? COL_WARN : COL_OK, boldFont(24));
        
        String covStr = d.getCoverageRatio() != null ? String.format("%.4f", d.getCoverageRatio()) : "N/A";
        drawCentred(g, cx - 60, y+150, "Stone Area", COL_DISCLAIMER, boldFont(14));
        drawCentred(g, cx - 60, y+175, pxStr, COL_VALUE, boldFont(20));
        drawCentred(g, cx + 60, y+150, "Coverage Ratio", COL_DISCLAIMER, boldFont(14));
        drawCentred(g, cx + 60, y+175, covStr, COL_VALUE, boldFont(20));

        // Col 3
        cx += statW;
        drawCentred(g, cx, y+50, "MODELS USED", COL_LABEL, boldFont(16));
        
        String clfModel = d.getClassificationModel() != null ? d.getClassificationModel() : "Unknown classification config";
        drawCentred(g, cx, y+95, "Classification Model", COL_DISCLAIMER, boldFont(14));
        drawCentred(g, cx, y+120, truncateStr(clfModel, 30), COL_VALUE, boldFont(18));
        
        String segModel = d.getSegmentationModel() != null ? d.getSegmentationModel() : "Unknown segmentation config";
        drawCentred(g, cx, y+160, "Segmentation Model", COL_DISCLAIMER, boldFont(14));
        drawCentred(g, cx, y+185, truncateStr(segModel, 30), COL_VALUE, boldFont(18));

        // Col 4
        cx += statW;
        drawCentred(g, cx, y+50, "PROCESSING INFORMATION", COL_LABEL, boldFont(16));
        
        String msTime = d.getProcessingTimeMs() != null ? d.getProcessingTimeMs() + " ms" : "N/A";
        drawCentred(g, cx, y+95, "Processing Time", COL_DISCLAIMER, boldFont(14));
        drawCentred(g, cx, y+120, msTime, COL_VALUE, boldFont(18));
        
        String device = d.getDevice() != null ? d.getDevice() : "N/A";
        drawCentred(g, cx, y+160, "Device Engine", COL_DISCLAIMER, boldFont(14));
        drawCentred(g, cx, y+185, device.toUpperCase(), COL_VALUE, boldFont(18));
        
        return y + STATS_H;
    }

    private void drawFooter(Graphics2D g, int y) {
        g.setColor(COL_SEPARATOR);
        g.fillRect(0, y, TOTAL_W, 2);
        g.setColor(COL_BG_HEADER);
        g.fillRect(0, y+2, TOTAL_W, FOOTER_H);
        g.setFont(boldFont(14));
        g.setColor(COL_DISCLAIMER);
        String footer = "\u26A0 Clinical Decision Support Disclaimer \u2014 AI predictions require physician evaluation before clinical action.";
        int fw = g.getFontMetrics().stringWidth(footer);
        g.drawString(footer, (TOTAL_W - fw) / 2, y + 32);
    }

    private void drawPanelBackground(Graphics2D g, int x, int y, int w, int h) {
        g.setColor(COL_BG_PANEL);
        g.fillRect(x, y, w, h);
        g.setColor(COL_BORDER);
        g.drawRect(x, y, w - 1, h - 1);
    }

    private void drawPanelHeader(Graphics2D g, int x, int y, String label) {
        g.setColor(COL_BG_DARK);
        g.fillRect(x, y, PANEL_W, 40);
        g.setColor(COL_BORDER);
        g.drawLine(x, y + 40, x + PANEL_W, y + 40);
        
        g.setFont(boldFont(15));
        g.setColor(COL_VALUE);
        g.drawString(label, x + NUMERAL_PAD, y + 26);
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
        int lineH = fm.getHeight() + 4;
        for (String line : text.split("\n")) {
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
        g.setColor(COL_BG_DARK);
        g.fillRect(x, y, w, h);
        g.setColor(COL_BORDER);
        g.setStroke(new BasicStroke(1, BasicStroke.CAP_BUTT, BasicStroke.JOIN_BEVEL, 0, new float[]{9}, 0));
        g.drawRect(x, y, w, h);
        g.setStroke(new BasicStroke(1)); // reset
        
        g.setFont(boldFont(16));
        g.setColor(COL_LABEL);
        int tw = g.getFontMetrics().stringWidth(message);
        g.drawString(message, x + (w - tw) / 2, y + h / 2);
    }

    private String truncateStr(String str, int maxLen) {
        if (str == null || str.length() <= maxLen) return str;
        return str.substring(0, maxLen - 3) + "...";
    }

    private static Color classColor(String cls) {
        if (cls == null) return COL_LABEL;
        return switch (cls.toLowerCase()) {
            case "stone"  -> new Color(255, 140,  40);
            case "tumor"  -> COL_ERROR;
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
            case "DISAGREEMENT"          -> COL_ERROR;
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
