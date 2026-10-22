"""
Vector Index Builder - Chroma Vector Database
================================================================================
Companion to setup_db.py.

    setup_db.py          builds the Oracle database (tables, PL/SQL, data)
    build_vector_index.py  builds the Chroma vector index FROM that Oracle data

Run setup_db.py first, then this. Re-run this any time the review data in
Oracle changes - it upserts, so re-running refreshes rather than duplicates.

Usage:
    python build_vector_index.py            # rebuild both collections
    python build_vector_index.py --status   # just report what's indexed
    python build_vector_index.py --demo     # rebuild, then run a sample query
================================================================================
"""

import sys

from db.connection import db
from services import semantic_service


def print_header(title):
    print("=" * 70)
    print(title)
    print("=" * 70)


def show_status():
    status = semantic_service.index_status()

    if not status["available"]:
        print(f" Vector store unavailable: {status['error']}")
        return False

    print(f"Store location: {status['store_path']}")
    print("Indexed documents:")
    for name, count in status["collections"].items():
        print(f"  - {name}: {count}")

    if not status["built"]:
        print("\n Index is empty. Run:  python build_vector_index.py")
    return status["built"]


def run_demo_query():
    """
    The side-by-side comparison that makes the case for the vector database.

    The query deliberately uses words that appear in NO review, so SQL LIKE
    returns nothing while semantic search still finds the relevant complaints.
    """
    query = "somewhere peaceful to get work done"

    print()
    print_header(f"DEMO QUERY: \"{query}\"")

    print("\n--- SQL baseline (Oracle: WHERE Comments LIKE '%...%') ---")
    keyword_hits = semantic_service.keyword_search_reviews(query)
    if keyword_hits:
        for hit in keyword_hits:
            print(f"  [{hit['metadata']['rating']}*] {hit['text'][:90]}...")
    else:
        print("  (no rows - no review contains that exact phrase)")

    print("\n--- Vector search (Chroma: nearest neighbours by meaning) ---")
    try:
        semantic_hits = semantic_service.search_reviews(query, n_results=3)
    except Exception as exc:
        print(f"  Could not query the vector store: {exc}")
        return

    for hit in semantic_hits:
        meta = hit["metadata"]
        print(f"  [{hit['similarity']}% similar] [{meta['rating']}*] "
              f"{meta['customer_name']} on {meta['room_type']}:")
        print(f"      {hit['text'][:110]}...")

    print("\nSame query, same data. SQL matches characters; the vector")
    print("database matches meaning.")


def main():
    args = sys.argv[1:]

    print_header("SMART HOTEL - VECTOR INDEX BUILDER (Chroma)")
    print(f"Source database: {'Oracle' if db.is_oracle_active() else 'SQLite mirror'}")

    if "--status" in args:
        show_status()
        return

    try:
        semantic_service.get_client()
    except RuntimeError as exc:
        print(f"\n {exc}")
        print(" Install it, then re-run this script.")
        sys.exit(1)

    print("\nReading source rows from the database and embedding them...")
    print("(first run downloads the ~80MB embedding model - this is one-time)")

    try:
        counts = semantic_service.rebuild_all()
    except Exception as exc:
        print(f"\n Index build failed: {exc}")
        sys.exit(1)

    print()
    for name, count in counts.items():
        print(f" {name}: {count} documents embedded")

    total = sum(counts.values())
    if total == 0:
        print("\n Nothing was indexed. Is the Oracle sample data loaded?")
        print("   Run setup_db.py first, then try again.")
        sys.exit(1)

    print(f"\n Vector index built: {total} documents total.")
    print(f"   Stored at: {semantic_service.VECTOR_STORE_DIR}")

    if "--demo" in args:
        run_demo_query()


if __name__ == "__main__":
    main()
