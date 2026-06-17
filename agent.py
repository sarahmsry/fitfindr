"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import re
from tools import search_listings, suggest_outfit, create_fit_card


# ── query parsing ─────────────────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """
    Extract description, size, and max_price from a natural language query.

    Uses regex to identify:
    - Price: looks for patterns like "under $30", "$30", "max $20", etc.
    - Size: looks for single-letter sizes (S, M, L, XL) or ranges (S/M, M/L)
    - Description: everything else

    Args:
        query: Natural language query string

    Returns:
        A dict with keys: description, size, max_price
        Values are None if not found in the query.
    """
    description = query
    size = None
    max_price = None

    # Extract price (look for patterns like "$30", "under $30", "max $20")
    price_match = re.search(r'\$(\d+(?:\.\d{2})?)', query)
    if price_match:
        max_price = float(price_match.group(1))
        # Remove price from description
        description = re.sub(r'\b(?:under|max|upto|up to)?\s*\$\d+(?:\.\d{2})?\b', '', description, flags=re.IGNORECASE)

    # Extract size (look for patterns like "size M", "M", "XL", "S/M")
    size_match = re.search(r'\b(?:size\s+)?([SML](?:/[SML])?(?:\s*\(oversized\))?|XL+)\b', query, re.IGNORECASE)
    if size_match:
        size = size_match.group(1).strip()
        # Remove size from description
        description = re.sub(r'\b(?:size\s+)?[SML](?:/[SML])?(?:\s*\(oversized\))?\b', '', description, flags=re.IGNORECASE)
        description = re.sub(r'\bXL+\b', '', description, flags=re.IGNORECASE)

    # Clean up description
    description = re.sub(r'\s+', ' ', description).strip()
    # Remove common punctuation at the end
    description = re.sub(r'[,;:\s]+$', '', description)

    return {
        "description": description if description else None,
        "size": size,
        "max_price": max_price,
    }




def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    Implementation follows the planning loop from planning.md:

        Step 1: Initialize the session with _new_session().
        Step 2: Parse the user's query to extract description, size, and max_price.
        Step 3: Call search_listings() with the parsed parameters.
                Branch: If no results, set error and return early.
        Step 4: Select the top result as the selected item.
        Step 5: Call suggest_outfit() with the selected item and wardrobe.
        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
        Step 7: Return the session.
    """
    # Step 1: Initialize session
    session = _new_session(query, wardrobe)

    # Step 2: Parse the query to extract description, size, max_price
    parsed = _parse_query(query)
    session["parsed"] = parsed

    # Validate that we have at least a description
    if not parsed["description"]:
        session["error"] = (
            "Could not understand your query. Please provide a description of "
            "what you're looking for (e.g., 'vintage graphic tee under $30, size M')."
        )
        return session

    # Step 3: Call search_listings() with parsed parameters
    search_results = search_listings(
        description=parsed["description"],
        size=parsed["size"],
        max_price=parsed["max_price"],
        interactive=False,  # For now, don't prompt for interaction in agent
    )
    session["search_results"] = search_results

    # BRANCH: If no results found, set error and return early
    if not search_results:
        session["error"] = (
            f"No listings found matching your criteria. Try loosening your filters "
            f"(e.g., increase max price, remove size restriction, or use different keywords)."
        )
        return session

    # Step 4: Select the top result (best match)
    selected_item = search_results[0]
    session["selected_item"] = selected_item

    # Step 5: Call suggest_outfit() with selected item and wardrobe
    outfit_suggestions = suggest_outfit(new_item=selected_item, wardrobe=wardrobe)
    
    # For now, select the first suggestion (in a full app, user would pick)
    if outfit_suggestions:
        session["outfit_suggestion"] = outfit_suggestions[0]
    else:
        session["error"] = "Could not generate outfit suggestions. Please try again."
        return session

    # Step 6: Call create_fit_card() with outfit suggestion and selected item
    fit_card = create_fit_card(
        outfit=session["outfit_suggestion"],
        new_item=selected_item
    )
    session["fit_card"] = fit_card

    # Step 7: Return the completed session
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
