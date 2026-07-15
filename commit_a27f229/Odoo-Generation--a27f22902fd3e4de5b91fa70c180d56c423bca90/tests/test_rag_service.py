from app.services.rag_service import RAGService


def test_chunk_text_splits_large_content():
    service = RAGService.__new__(RAGService)
    text = " ".join([f"sentence_{i}" for i in range(40)])

    chunks = service._chunk_text(text, chunk_size=20, overlap=5)

    assert len(chunks) > 1
    assert all(chunk for chunk in chunks)
    assert chunks[0] != chunks[1]


def test_format_search_results_returns_reference_context():
    service = RAGService.__new__(RAGService)
    results = [
        {"content": "class SaleOrder(models.Model): ...", "metadata": {"source": "sale_order.py"}},
        {"content": "<record id=\"sale_order_view\">...</record>", "metadata": {"source": "sale_order.xml"}},
    ]

    context = service._format_search_results(results)

    assert "Reference Context" in context
    assert "sale_order.py" in context
    assert "sale_order.xml" in context
