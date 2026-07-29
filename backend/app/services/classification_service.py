def classify_document(text: str) -> str:
    normalized_text = text.lower()

    if "invoice" in normalized_text:
        return "invoice"

    if "receipt" in normalized_text:
        return "receipt"

    receipt_score = calculate_score(
        normalized_text,
        [
            "ticket de vente",
            "ticket client",
            "ticket de caisse",
            "a payer",
            "à payer",
            "carte bancaire",
            "sans contact",
            "nombre de lignes",
            "merci de votre visite",
            "merci pour votre achat",
            "total promotion",
            "lidl plus",
            "article quantité prix",
            "article quantite prix",
            "methode de paiement",
            "méthode de paiement",
            "cb",
            "hors taxe",
        ],
    )

    invoice_score = calculate_score(
        normalized_text,
        [
            "facture",
            "numéro de facture",
            "numero de facture",
            "date de facture",
            "billing address",
            "adresse de facturation",
            "tva intracommunautaire",
            "conditions de paiement",
            "montant ht",
            "montant ttc",
        ],
    )

    if receipt_score >= 1 and receipt_score >= invoice_score:
        return "receipt"

    if invoice_score >= 1 and invoice_score > receipt_score:
        return "invoice"

    return "unknown"


def calculate_score(text: str, keywords: list[str]) -> int:
    return sum(1 for keyword in keywords if keyword in text)