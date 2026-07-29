from app.services.extraction_service import extract_structured_data, extract_total_amount


CARREFOUR_NOISY_OCR_TEXT = """
Se

Carrefour < es
inpis6 49054

CRF CITY, RENNES VOLTAIRE
8 BYD VOLTAIRE
35000 RENNES
Tel : 02.23,44,81.10

wernt

QTE x P.U. OHTA. TIC

HEGIANO RE a 2.98€

HL 1,58 Eee ee 6:

*33CL COLA ZERG PER eB ov reso 3eH | 1.90€
Bs FAOYHOD *D2A x 0.95€ eH |

«441006 SKYR HAT 2.26€

x6 OEUFS POULES ELE 1.81€

x6X30G CHIPS LISSE 1,90€

5 ¥*750G CASSON R. at 2.06€

- *BANANES UTS 16 2 I9IQ59 1.37€

lonsa} nse:

18.50€

Hors Taxe
i s TXIM 9 gy aN
nollzgp env wod | 1fae & . 17.53
aldsenogze; 0.90 Lr Vv 17.53
"""


def test_carrefour_generic_parser_extracts_items_from_noisy_ocr():
    result = extract_structured_data(CARREFOUR_NOISY_OCR_TEXT, "receipt")

    assert result.merchant_name == "CARREFOUR"
    assert len(result.items) == 8
    assert result.total_amount == 18.5


def test_total_amount_ignores_phone_number_with_colon_format():
    """
    Regression test: 'Tel : 02.23.44.81.10' was previously mistaken for a
    price line, making extract_total_amount return 44.81 (from '44,81')
    instead of the real total of 18.50.
    """
    text = "Tel : 02.23,44,81.10\nSome item 2.98€\n18.50€\n"

    assert extract_total_amount(text) == 18.5
