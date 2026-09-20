import os

import pytest

from bootstrap.container import VerzaContainer

# Ensure the test fails fast if easyocr is not installed.
try:
    import easyocr  # type: ignore # noqa: F401
    HAS_VISION = True
except ImportError:
    HAS_VISION = False

pytestmark = pytest.mark.skipif(
    not HAS_VISION, 
    reason="ENVIRONMENT DEPENDENCY FAILURE: easyocr is missing."
)


@pytest.fixture
def ocr_fixture_path():
    path = os.path.join(os.path.dirname(__file__), "fixtures", "ocr_fixture.png")
    assert os.path.exists(path), f"Fixture missing: {path}. Run generate_ocr_fixture.py first."
    return path


@pytest.fixture
def easyocr_provider():
    # We resolve from the real DI container to ensure architecture compliance
    container = VerzaContainer()
    return container.easyocr_provider()


def test_real_easyocr_extraction(easyocr_provider, ocr_fixture_path):
    """
    Phase 2: Real M2 Vision/OCR Execution.
    Verifies that the EasyOCRProvider loads the real model, processes the image, 
    and perfectly maps outputs to the DocumentUnderstanding schema.
    """
    # Execute extraction
    results = easyocr_provider.extract_text(ocr_fixture_path)
    
    # Structural Assertions
    assert results is not None
    assert isinstance(results, list)
    assert len(results) > 0, "Expected at least one block of text to be detected."
    
    # We flatten the text from all detections to check semantic content globally
    full_text = " ".join([doc.detected_text for doc in results]).lower()
    
    assert "verza" in full_text, f"Expected 'verza' in OCR result, got: {full_text}"
    assert "ocr" in full_text, f"Expected 'ocr' in OCR result, got: {full_text}"
    assert "system" in full_text, f"Expected 'system' in OCR result, got: {full_text}"
    
    # Assert DocumentUnderstanding Schema Integrity on the first valid block
    for doc in results:
        assert isinstance(doc.detected_text, str)
        assert len(doc.location) == 4, "Expected bounding box to be flattened to [min_x, min_y, max_x, max_y]"
        assert doc.location[0] <= doc.location[2] # min_x <= max_x
        assert doc.location[1] <= doc.location[3] # min_y <= max_y
        
        assert doc.certainty is not None
        assert isinstance(doc.certainty.confidence, float)
        assert doc.certainty.confidence > 0.0
        assert "easyocr" in doc.certainty.source
