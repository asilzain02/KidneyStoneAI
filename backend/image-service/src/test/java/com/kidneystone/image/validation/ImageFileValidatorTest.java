package com.kidneystone.image.validation;

import com.kidneystone.shared.exception.ValidationException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.util.ReflectionTestUtils;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

@DisplayName("ImageFileValidator Unit Tests")
class ImageFileValidatorTest {

    private ImageFileValidator validator;

    @BeforeEach
    void setUp() {
        validator = new ImageFileValidator();
        ReflectionTestUtils.setField(validator, "maxFileSizeBytes", 52428800L);
    }

    @Test
    void validate_png_passes() {
        MockMultipartFile f = new MockMultipartFile("file", "scan.png", "image/png", new byte[100]);
        validator.validate(f); // no exception
    }

    @Test
    void validate_jpg_passes() {
        MockMultipartFile f = new MockMultipartFile("file", "scan.jpg", "image/jpeg", new byte[100]);
        validator.validate(f);
    }

    @Test
    void validate_jpeg_passes() {
        MockMultipartFile f = new MockMultipartFile("file", "scan.jpeg", "image/jpeg", new byte[100]);
        validator.validate(f);
    }

    @Test
    void validate_dicom_passes() {
        MockMultipartFile f = new MockMultipartFile("file", "scan.dcm", "application/dicom", new byte[100]);
        validator.validate(f);
    }

    @Test
    @DisplayName("reject PDF")
    void validate_pdf_throws() {
        MockMultipartFile f = new MockMultipartFile("file", "report.pdf", "application/pdf", new byte[100]);
        assertThatThrownBy(() -> validator.validate(f))
                .isInstanceOf(ValidationException.class)
                .hasMessageContaining("Unsupported file type");
    }

    @Test
    @DisplayName("reject ZIP")
    void validate_zip_throws() {
        MockMultipartFile f = new MockMultipartFile("file", "archive.zip", "application/zip", new byte[100]);
        assertThatThrownBy(() -> validator.validate(f))
                .isInstanceOf(ValidationException.class)
                .hasMessageContaining("Unsupported file type");
    }

    @Test
    @DisplayName("reject empty file")
    void validate_empty_throws() {
        MockMultipartFile f = new MockMultipartFile("file", "scan.png", "image/png", new byte[0]);
        assertThatThrownBy(() -> validator.validate(f))
                .isInstanceOf(ValidationException.class)
                .hasMessageContaining("empty");
    }

    @Test
    @DisplayName("reject oversized file")
    void validate_oversized_throws() {
        byte[] big = new byte[52428801]; // 50 MB + 1 byte
        MockMultipartFile f = new MockMultipartFile("file", "big.png", "image/png", big);
        assertThatThrownBy(() -> validator.validate(f))
                .isInstanceOf(ValidationException.class)
                .hasMessageContaining("exceeds maximum");
    }

    @Test
    void detectModality_dcm_returnsDICOM() {
        assertThat(validator.detectModality("scan.dcm")).isEqualTo("DICOM");
    }

    @Test
    void detectModality_png_returnsIMAGE() {
        assertThat(validator.detectModality("scan.png")).isEqualTo("IMAGE");
    }

    @Test
    void detectModality_unknown_returnsUNKNOWN() {
        assertThat(validator.detectModality("file.xyz")).isEqualTo("UNKNOWN");
    }
}
