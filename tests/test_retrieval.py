from app.retrieval import Retriever, load_passages


def test_current_returns_policy_beats_legacy():
    r = Retriever(load_passages("knowledge-base"))
    results = r.search("standard return window unused backpack")
    filenames = [x.passage.filename for x in results]
    assert "01-returns-policy-current.md" in filenames[:3]
    top = next(x for x in results if x.passage.filename == "01-returns-policy-current.md")
    assert top.score > next(x.score for x in results if x.passage.filename == "02-returns-policy-legacy.md")


def test_internal_migration_is_penalized():
    r = Retriever(load_passages("knowledge-base"))
    results = r.search("return policy 60 days migration")
    assert results[0].passage.filename != "14-internal-content-migration-notes.md"
