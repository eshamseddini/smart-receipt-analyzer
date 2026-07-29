from app.services.classification_service import classify_document


def test_invoice():
    text = "This is an invoice document."
    result = classify_document(text)
    assert result == "invoice"

def test_receipt():
    text = "This is a receipt document."
    result = classify_document(text)
    assert result == "receipt"

def test_unknown():
    text = "This is an unknown document."
    result = classify_document(text)
    assert result == "unknown"  
 
def test_sans_mot():
    text = ""
    result = classify_document(text)
    assert result == "unknown"

def test_noisy_receipt_with_single_keyword_match():
    """
    Real-world noisy OCR (poor scan quality) where most receipt keywords
    are unreadable, but "Hors Taxe" survives clearly. A single strong
    keyword match should be enough to classify as a receipt.
    """
    text = """
    Carrefour < es
    CRF CITY, RENNES VOLTAIRE
    Tel : 02.23,44,81.10
    HEGIANO RE a 2.98€
    18.50€
    Hors Taxe
    """
    result = classify_document(text)
    assert result == "receipt"