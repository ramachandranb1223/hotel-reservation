"""
SEMANTIC SEARCH LAYER - Chroma Vector Database
================================================================================
Mini-project extension: Vector Database category.

ARCHITECTURE NOTE (for the report / viva):

    Oracle remains the SYSTEM OF RECORD. Every customer, booking, payment,
    invoice and review is written to Oracle first, inside an ACID transaction,
    protected by constraints, triggers and stored procedures.

    This Chroma collection is a DERIVED INDEX built FROM that Oracle data.
    It stores no original data of its own: delete the vector_store/ folder and
    rebuild it at any time with `python build_vector_index.py`. Oracle is never
    read from or written to by Chroma directly.

    This is the standard "polyglot persistence" pattern - use the relational
    database for what it is genuinely good at (transactions, joins, referential
    integrity) and add a specialised database for the one thing SQL cannot do
    natively: compare text by MEANING rather than by characters.

WHY A VECTOR DATABASE (the comparative-analysis argument):

    SQL matches characters. `WHERE Comments LIKE '%noisy%'` finds the literal
    string "noisy" and nothing else - it misses "loud", "couldn't sleep",
    "thin walls", "could hear everything next door", all of which are the same
    complaint. Oracle has no notion that those phrases are related.

    A vector database stores each review as an EMBEDDING: a list of ~384
    numbers produced by a language model, positioned so that text with similar
    meaning sits close together in that 384-dimensional space. Searching then
    means "find the vectors nearest to the query vector" (approximate nearest
    neighbour search), which returns the semantically related reviews even when
    they share no words at all with the query.

    Trade-off, stated honestly: the vector search is approximate and has no
    notion of correctness or transactions - two identical queries could in
    principle return slightly different orderings, and nothing here is ACID.
    That is exactly why it indexes a copy and never owns the booking data.
================================================================================
"""

import os
import logging

from db.connection import db

logger = logging.getLogger("semantic_search")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# Where Chroma persists its index on disk (sits beside the Oracle scripts;
# it is regenerable, so it belongs in .gitignore).
VECTOR_STORE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vector_store"
)

REVIEWS_COLLECTION = "hotel_reviews"
ROOM_TYPES_COLLECTION = "hotel_room_types"

# Cosine distance makes the score easy to read: similarity = 1 - distance,
# so 1.0 is an exact meaning match and 0.0 is unrelated.
COLLECTION_METADATA = {"hnsw:space": "cosine"}

_client = None
_embedding_function = None  # None = let Chroma use its built-in default


# ---------------------------------------------------------------------------
# Oracle/SQLite column-name helper
# ---------------------------------------------------------------------------
def _val(row, *names):
    """
    Read a column from a result row regardless of backend casing.

    Oracle lowercases every column name in its results; the SQLite mirror
    preserves whatever case the SQL used. Rather than guess, try each spelling.
    """
    for name in names:
        if name in row:
            return row[name]
        if name.lower() in row:
            return row[name.lower()]
    return None


# ---------------------------------------------------------------------------
# Chroma client / embedding model
# ---------------------------------------------------------------------------
def get_client():
    """
    Returns a persistent Chroma client, creating the store on first use.

    Raises RuntimeError with a readable message if chromadb isn't installed,
    rather than letting an ImportError escape into a Flask 500 page.
    """
    global _client
    if _client is not None:
        return _client

    try:
        import chromadb
    except ImportError as exc:
        raise RuntimeError(
            "chromadb is not installed. Run:  pip install chromadb"
        ) from exc

    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    _client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
    logger.info("Chroma vector store opened at %s", VECTOR_STORE_DIR)
    return _client


def set_embedding_function(fn):
    """
    Override the embedding model used for every collection.

    Chroma's built-in default is all-MiniLM-L6-v2 (384 dimensions), which runs
    locally on the CPU via onnxruntime - no API key, and no internet needed
    after the model downloads once (~80MB) on first use.

    If onnxruntime has no wheel for your Python version (a real possibility on
    very new releases such as 3.14), either run the project in a virtualenv on
    Python 3.12/3.13, or call this with another Chroma-compatible embedding
    function before building the index. Passing None restores the default.
    """
    global _embedding_function
    _embedding_function = fn


def _get_collection(name, create=True):
    """
    Fetch a collection. The embedding model is wired in HERE and nowhere else,
    so swapping models is a single change in one place.
    """
    client = get_client()
    kwargs = {"name": name}
    if _embedding_function is not None:
        kwargs["embedding_function"] = _embedding_function

    if create:
        return client.get_or_create_collection(metadata=COLLECTION_METADATA, **kwargs)
    return client.get_collection(**kwargs)


# ---------------------------------------------------------------------------
# Indexing (Oracle -> Chroma)
# ---------------------------------------------------------------------------
def index_reviews():
    """
    Reads every guest review out of Oracle and embeds it into Chroma.

    Each vector carries metadata (rating, guest, room type) so results can be
    filtered or displayed without going back to Oracle for the common case.
    """
    sql = """
        SELECT
            f.Feedback_ID,
            f.Rating,
            f.Comments,
            c.Name        AS Customer_Name,
            rt.Type_Name  AS Room_Type
        FROM FEEDBACK f
        INNER JOIN CUSTOMER c   ON f.Customer_ID = c.Customer_ID
        LEFT JOIN BOOKING b     ON f.Booking_ID = b.Booking_ID
        LEFT JOIN ROOM r        ON b.Room_ID = r.Room_ID
        LEFT JOIN ROOM_TYPE rt  ON r.RoomType_ID = rt.RoomType_ID
    """
    rows = db.query(sql)

    ids, documents, metadatas = [], [], []
    for row in rows:
        comments = _val(row, "Comments")
        if not comments or not str(comments).strip():
            continue  # nothing to embed

        feedback_id = _val(row, "Feedback_ID")
        ids.append(f"review-{feedback_id}")
        documents.append(str(comments))
        metadatas.append({
            "feedback_id": int(feedback_id),
            "rating": int(_val(row, "Rating") or 0),
            "customer_name": str(_val(row, "Customer_Name") or "Guest"),
            "room_type": str(_val(row, "Room_Type") or "Unassigned"),
        })

    if not ids:
        logger.warning("No reviews with comments found in Oracle - nothing indexed.")
        return 0

    collection = _get_collection(REVIEWS_COLLECTION)
    # upsert: re-running the builder refreshes existing rows instead of duplicating
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    logger.info("Indexed %d reviews into '%s'", len(ids), REVIEWS_COLLECTION)
    return len(ids)


def index_room_types():
    """
    Embeds each room category's marketing text so a guest can search for what
    they WANT ("somewhere quiet to work") instead of picking a category name.

    The embedded document is name + description + amenities concatenated, so a
    query can match on any of the three.
    """
    sql = """
        SELECT RoomType_ID, Type_Name, Description, Base_Price,
               Max_Occupancy, Amenities, Image_URL
        FROM ROOM_TYPE
    """
    rows = db.query(sql)

    ids, documents, metadatas = [], [], []
    for row in rows:
        rt_id = _val(row, "RoomType_ID")
        name = str(_val(row, "Type_Name") or "")
        description = str(_val(row, "Description") or "")
        amenities = str(_val(row, "Amenities") or "")

        ids.append(f"roomtype-{rt_id}")
        documents.append(f"{name}. {description} Amenities: {amenities}")
        metadatas.append({
            "roomtype_id": int(rt_id),
            "type_name": name,
            "base_price": float(_val(row, "Base_Price") or 0),
            "max_occupancy": int(_val(row, "Max_Occupancy") or 0),
            "amenities": amenities,
            "image_url": str(_val(row, "Image_URL") or ""),
        })

    if not ids:
        logger.warning("No room types found in Oracle - nothing indexed.")
        return 0

    collection = _get_collection(ROOM_TYPES_COLLECTION)
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    logger.info("Indexed %d room types into '%s'", len(ids), ROOM_TYPES_COLLECTION)
    return len(ids)


def rebuild_all(drop_first=True):
    """Rebuilds both collections from Oracle. Returns a {collection: count} dict."""
    if drop_first:
        client = get_client()
        for name in (REVIEWS_COLLECTION, ROOM_TYPES_COLLECTION):
            try:
                client.delete_collection(name)
            except Exception:
                pass  # collection didn't exist yet - fine on a first run

    return {
        REVIEWS_COLLECTION: index_reviews(),
        ROOM_TYPES_COLLECTION: index_room_types(),
    }


# ---------------------------------------------------------------------------
# Querying
# ---------------------------------------------------------------------------
def _format_results(raw):
    """Flattens Chroma's parallel-array response into a list of dicts."""
    out = []
    if not raw or not raw.get("ids") or not raw["ids"][0]:
        return out

    for i, doc_id in enumerate(raw["ids"][0]):
        distance = raw["distances"][0][i] if raw.get("distances") else None
        out.append({
            "id": doc_id,
            "text": raw["documents"][0][i] if raw.get("documents") else "",
            "metadata": raw["metadatas"][0][i] if raw.get("metadatas") else {},
            # cosine distance -> similarity percentage, clamped for display
            "similarity": round(max(0.0, min(1.0, 1.0 - distance)) * 100, 1)
            if distance is not None else None,
        })
    return out


def search_reviews(query_text, n_results=5, min_rating=None):
    """
    Semantic search over guest reviews.

    `min_rating` demonstrates vector search combined with metadata filtering -
    the equivalent of putting a WHERE clause alongside the similarity search.
    """
    collection = _get_collection(REVIEWS_COLLECTION, create=False)
    kwargs = {"query_texts": [query_text], "n_results": n_results}
    if min_rating is not None:
        kwargs["where"] = {"rating": {"$gte": int(min_rating)}}

    return _format_results(collection.query(**kwargs))


def search_room_types(query_text, n_results=3, max_price=None):
    """Semantic search over room categories, optionally capped by nightly price."""
    collection = _get_collection(ROOM_TYPES_COLLECTION, create=False)
    kwargs = {"query_texts": [query_text], "n_results": n_results}
    if max_price is not None:
        kwargs["where"] = {"base_price": {"$lte": float(max_price)}}

    return _format_results(collection.query(**kwargs))


def keyword_search_reviews(query_text, n_results=5):
    """
    The SQL BASELINE, kept deliberately for the side-by-side demo.

    This is what the relational database alone can do: a literal substring
    match. Comparing its results against search_reviews() for the same query is
    the clearest single demonstration of why the vector database was added.
    """
    sql = """
        SELECT f.Feedback_ID, f.Rating, f.Comments, c.Name AS Customer_Name
        FROM FEEDBACK f
        INNER JOIN CUSTOMER c ON f.Customer_ID = c.Customer_ID
        WHERE LOWER(f.Comments) LIKE :pattern
    """
    rows = db.query(sql, {"pattern": f"%{(query_text or '').lower()}%"})

    return [{
        "id": f"review-{_val(r, 'Feedback_ID')}",
        "text": str(_val(r, "Comments") or ""),
        "metadata": {
            "feedback_id": _val(r, "Feedback_ID"),
            "rating": _val(r, "Rating"),
            "customer_name": _val(r, "Customer_Name"),
        },
        "similarity": None,  # SQL LIKE has no notion of relevance ranking
    } for r in rows[:n_results]]


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------
def index_status():
    """
    Reports whether the vector store has been built, for the UI and for a
    friendly error instead of a stack trace when it hasn't been.
    """
    try:
        client = get_client()
    except RuntimeError as exc:
        return {"available": False, "error": str(exc), "collections": {}}

    counts = {}
    for name in (REVIEWS_COLLECTION, ROOM_TYPES_COLLECTION):
        try:
            counts[name] = client.get_collection(name).count()
        except Exception:
            counts[name] = 0

    return {
        "available": True,
        "built": sum(counts.values()) > 0,
        "collections": counts,
        "store_path": VECTOR_STORE_DIR,
    }
