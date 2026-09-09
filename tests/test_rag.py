from app.services.rag import retrieve


def test_retrieve_returns_only_chunks_for_selected_approval():
    chunks = retrieve("fire_noc", "new manufacturing site fire systems", limit=3)

    assert chunks
    assert all(chunk.approval_id == "fire_noc" for chunk in chunks)
    assert chunks[0].source.startswith("Illustrative")


def test_retrieve_unknown_approval_returns_empty_list():
    assert retrieve("unknown_approval", "anything") == []