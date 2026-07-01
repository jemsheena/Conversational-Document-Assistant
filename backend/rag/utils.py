"""
Pipeline utility functions: deduplication, diversification, citation validation.
"""

import re
from collections import defaultdict
from typing import Dict, List


def diversify_passages(
    passages: List[Dict], max_per_doc: int = 3, max_per_page: int = 2
) -> List[Dict]:
    """
    Pipeline Stage 5: Dedupe/diversify passages across pages/docs.

    Ensures diversity in retrieved results by limiting passages per document/page.
    Prioritizes higher-scored passages.

    Args:
        passages: List of passage dicts with 'doc', 'page', 'score'
        max_per_doc: Maximum passages per document
        max_per_page: Maximum passages per page

    Returns:
        Diversified list of passages
    """
    if not passages:
        return []

    # Group by doc
    by_doc = defaultdict(list)
    for p in passages:
        by_doc[p.get("doc", "unknown")].append(p)

    # Within each doc, limit per page
    diversified = []
    for doc, doc_passages in by_doc.items():
        # Sort by score (descending)
        doc_passages.sort(key=lambda x: x.get("score", 0), reverse=True)

        # Group by page within doc
        by_page = defaultdict(list)
        for p in doc_passages:
            page_key = f"{p.get('doc', '')}_{p.get('page', 0)}"
            by_page[page_key].append(p)

        # Take max_per_page from each page
        page_selected = []
        for page_passages in by_page.values():
            page_selected.extend(page_passages[:max_per_page])

        # Sort again and take top max_per_doc
        page_selected.sort(key=lambda x: x.get("score", 0), reverse=True)
        diversified.extend(page_selected[:max_per_doc])

    # Final sort by score
    diversified.sort(key=lambda x: x.get("score", 0), reverse=True)
    return diversified


def validate_citations(answer_text: str, num_sources: int) -> tuple[bool, List[int]]:
    """
    Pipeline Stage 8: Post-processing & citation binding.

    Validates that citations [1]..[N] exist and refer to valid sources.

    Args:
        answer_text: Generated answer text
        num_sources: Number of sources provided

    Returns:
        (is_valid, list of cited source numbers)
    """
    # Find all citation patterns [1], [2], etc.
    citation_pattern = r"\[(\d+)\]"
    citations = re.findall(citation_pattern, answer_text)
    cited_nums = [int(c) for c in citations]

    # Check validity: citations must be 1-indexed and <= num_sources
    valid_citations = [n for n in cited_nums if 1 <= n <= num_sources]
    invalid_citations = [n for n in cited_nums if n < 1 or n > num_sources]

    is_valid = len(invalid_citations) == 0

    return is_valid, valid_citations


def hash_query(query: str, collection: str) -> str:
    """
    Generate hash for query caching (Pipeline Stage 9).

    Args:
        query: User query text
        collection: Collection ID

    Returns:
        SHA256 hash string
    """
    import hashlib

    combined = f"{collection}:{query.lower().strip()}"
    return hashlib.sha256(combined.encode()).hexdigest()
