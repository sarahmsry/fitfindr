"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Complete and test each tool before moving to agent.py.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""

import os

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client():
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not set. Add it to a .env file in the project root."
        )
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def _score_listings(
    listings: list[dict], description: str
) -> list[tuple[float, dict]]:
    """
    Helper function to score listings by keyword overlap with description.
    
    Args:
        listings: List of listing dicts to score.
        description: Keywords describing what the user is looking for.
    
    Returns:
        List of (score, listing) tuples, with only scored items (score > 0).
    """
    description_keywords = set(description.lower().split())
    scored_listings = []
    
    for listing in listings:
        score = 0
        
        # Search in title (weighted 2x)
        title_lower = listing["title"].lower()
        for keyword in description_keywords:
            if keyword in title_lower:
                score += 2
        
        # Search in description (weighted 1x)
        desc_lower = listing["description"].lower()
        for keyword in description_keywords:
            if keyword in desc_lower:
                score += 1
        
        # Search in style_tags (weighted 1.5x)
        for tag in listing["style_tags"]:
            tag_lower = tag.lower()
            for keyword in description_keywords:
                if keyword in tag_lower:
                    score += 1.5
        
        # Search in colors (weighted 1x)
        for color in listing["colors"]:
            color_lower = color.lower()
            for keyword in description_keywords:
                if keyword in color_lower:
                    score += 1
        
        # Only include listings with a score > 0
        if score > 0:
            scored_listings.append((score, listing))
    
    return scored_listings


def _filter_listings(
    all_listings: list[dict], size: str | None = None, max_price: float | None = None
) -> list[dict]:
    """
    Helper function to filter listings by size and price.
    
    Args:
        all_listings: List of all listing dicts.
        size: Size string to filter by (case-insensitive), or None.
        max_price: Maximum price (inclusive), or None.
    
    Returns:
        Filtered list of listing dicts.
    """
    filtered = []
    for listing in all_listings:
        # Check price filter
        if max_price is not None and listing["price"] > max_price:
            continue
        
        # Check size filter (case-insensitive substring match)
        if size is not None:
            listing_size = listing["size"].upper()
            search_size = size.upper()
            if search_size not in listing_size:
                continue
        
        filtered.append(listing)
    
    return filtered


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
    interactive: bool = True,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.

    Args:
        description: Keywords describing what the user is looking for
                     (e.g., "vintage graphic tee").
        size:        Size string to filter by, or None to skip size filtering.
                     Matching is case-insensitive (e.g., "M" matches "S/M").
        max_price:   Maximum price (inclusive), or None to skip price filtering.
        interactive: If True (default), prompts user to loosen criteria when
                     no results found. If False, returns empty list immediately.

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        If no matches are found and interactive=True, prompts the user to loosen 
        criteria and re-searches with relaxed filters. Does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    Implementation:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return top 3.
        6. If no results found and interactive=True, prompt user to refine 
           criteria and retry.
    """
    all_listings = load_listings()
    
    # First attempt: search with provided criteria
    filtered = _filter_listings(all_listings, size=size, max_price=max_price)
    scored = _score_listings(filtered, description)
    
    # If results found, return top 3
    if scored:
        scored.sort(key=lambda x: x[0], reverse=True)
        return [listing for score, listing in scored[:3]]
    
    # No results found
    if not interactive:
        # Non-interactive mode (e.g., for testing) — just return empty list
        return []
    
    # Interactive mode — prompt user to loosen criteria
    print("\nNo listings found matching your criteria.")
    print(f"  Description: {description}")
    if size:
        print(f"  Size: {size}")
    if max_price:
        print(f"  Max Price: ${max_price}")
    
    print("\nWould you like to search again with looser criteria?")
    print("Options: (1) Remove size filter, (2) Increase price limit, (3) Change description, (4) Cancel")
    
    choice = input("Enter your choice (1-4): ").strip()
    
    if choice == "1":
        # Retry without size constraint
        print("\nSearching again without size restriction...")
        filtered = _filter_listings(all_listings, size=None, max_price=max_price)
        scored = _score_listings(filtered, description)
    elif choice == "2":
        # Retry with higher price limit
        new_price = input("Enter new maximum price: ").strip()
        try:
            new_max_price = float(new_price)
            print(f"\nSearching again with max price ${new_max_price}...")
            filtered = _filter_listings(all_listings, size=size, max_price=new_max_price)
            scored = _score_listings(filtered, description)
        except ValueError:
            print("Invalid price. Searching again without price restriction...")
            filtered = _filter_listings(all_listings, size=size, max_price=None)
            scored = _score_listings(filtered, description)
    elif choice == "3":
        # Retry with new description
        new_desc = input("Enter new search description: ").strip()
        print(f"\nSearching again for '{new_desc}'...")
        filtered = _filter_listings(all_listings, size=size, max_price=max_price)
        scored = _score_listings(filtered, new_desc)
    else:
        # Cancel
        print("Search cancelled.")
        return []
    
    # Return results from retry attempt
    if scored:
        scored.sort(key=lambda x: x[0], reverse=True)
        return [listing for score, listing in scored[:3]]
    else:
        print("Still no results found. Try broadening your criteria further.")
        return []


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def _format_wardrobe_for_prompt(wardrobe_items: list[dict]) -> str:
    """
    Format wardrobe items into a readable list for the LLM prompt.
    
    Args:
        wardrobe_items: List of wardrobe item dicts.
    
    Returns:
        A formatted string describing the wardrobe items.
    """
    if not wardrobe_items:
        return "No items in wardrobe."
    
    formatted = "Current Wardrobe Items:\n"
    for item in wardrobe_items:
        name = item.get("name", "Unknown item")
        category = item.get("category", "unknown")
        colors = ", ".join(item.get("colors", []))
        styles = ", ".join(item.get("style_tags", []))
        formatted += f"- {name} ({category}) — Colors: {colors}, Style: {styles}\n"
    
    return formatted


def _format_new_item_for_prompt(new_item: dict) -> str:
    """
    Format a new item (from search_listings) into a readable description for the LLM.
    
    Args:
        new_item: A listing dict.
    
    Returns:
        A formatted string describing the new item.
    """
    title = new_item.get("title", "Unknown item")
    description = new_item.get("description", "")
    category = new_item.get("category", "unknown")
    colors = ", ".join(new_item.get("colors", []))
    styles = ", ".join(new_item.get("style_tags", []))
    price = new_item.get("price", 0)
    condition = new_item.get("condition", "unknown")
    
    return (
        f"New Item: {title}\n"
        f"Category: {category}\n"
        f"Colors: {colors}\n"
        f"Style Tags: {styles}\n"
        f"Condition: {condition}\n"
        f"Price: ${price}\n"
        f"Description: {description}"
    )


def suggest_outfit(new_item: dict, wardrobe: dict) -> list[str]:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty list of strings with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item.
        If the wardrobe is minimal, create partial outfits with suggestions 
        for missing pieces.

    Implementation:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas.
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations.
        4. Parse and return the LLM's response as a list of outfit strings.
    """
    client = _get_groq_client()
    
    # Format the new item for the prompt
    new_item_str = _format_new_item_for_prompt(new_item)
    
    # Check if wardrobe is empty
    wardrobe_items = wardrobe.get("items", [])
    
    if not wardrobe_items:
        # Empty wardrobe — ask LLM for general styling ideas
        prompt = (
            f"A user is considering buying this clothing item but has an empty wardrobe. "
            f"Provide 1-2 creative outfit suggestions that pair this item with other pieces "
            f"they could look for. Include styling tips and vibe suggestions. "
            f"Format your response as a numbered list (1. [outfit suggestion], 2. [outfit suggestion]).\n\n"
            f"{new_item_str}"
        )
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500,
        )
        
        suggestions_text = response.choices[0].message.content.strip()
        
        # Parse numbered list into outfit suggestions
        suggestions = []
        for line in suggestions_text.split("\n"):
            line = line.strip()
            if line and line[0].isdigit():
                # Remove leading number and period
                outfit = line.split(".", 1)[-1].strip()
                if outfit:
                    suggestions.append(outfit)
        
        if not suggestions:
            # Fallback if parsing didn't work
            suggestions = [suggestions_text]
        
        return suggestions
    
    else:
        # Non-empty wardrobe — suggest specific outfit combinations
        wardrobe_str = _format_wardrobe_for_prompt(wardrobe_items)
        
        prompt = (
            f"A user is considering buying this new item and wants outfit suggestions using pieces from their existing wardrobe.\n\n"
            f"Create 1-2 complete outfit suggestions that:\n"
            f"1. Include the new item\n"
            f"2. Use pieces from their existing wardrobe (mention them by name)\n"
            f"3. Include styling tips and how to wear it\n"
            f"4. Suggest what type of items would complete the look if needed\n\n"
            f"Format your response as a numbered list:\n"
            f"1. [Complete outfit suggestion with styling tips]\n"
            f"2. [Another outfit suggestion with styling tips]\n\n"
            f"{new_item_str}\n\n"
            f"{wardrobe_str}"
        )
        
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=800,
        )
        
        suggestions_text = response.choices[0].message.content.strip()
        
        # Parse numbered list into outfit suggestions
        suggestions = []
        for line in suggestions_text.split("\n"):
            line = line.strip()
            if line and line[0].isdigit():
                # Remove leading number and period
                outfit = line.split(".", 1)[-1].strip()
                if outfit:
                    suggestions.append(outfit)
        
        if not suggestions:
            # Fallback if parsing didn't work
            suggestions = [suggestions_text]
        
        return suggestions

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find.

    Args:
        outfit:   The outfit suggestion string from suggest_outfit().
        new_item: The listing dict for the thrifted item.

    Returns:
        A 2–4 sentence string usable as an Instagram/TikTok caption.
        If outfit is empty or missing, return a descriptive error message
        string — do NOT raise an exception.

    The caption should:
    - Feel casual and authentic (like a real OOTD post, not a product description)
    - Mention the item name, price, and platform naturally (once each)
    - Capture the outfit vibe in specific terms
    - Sound different each time for different inputs (use higher LLM temperature)

    Implementation:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.
    """
    # Guard against empty outfit string
    if not outfit or not outfit.strip():
        return "Check out this awesome thrifted find! 🛍️ Add it to your collection today."
    
    # Extract item details for the prompt
    title = new_item.get("title", "thrifted piece")
    price = new_item.get("price", "unknown")
    platform = new_item.get("platform", "thrift store")
    description = new_item.get("description", "")
    style_tags = ", ".join(new_item.get("style_tags", []))
    colors = ", ".join(new_item.get("colors", []))
    
    # Build the prompt
    prompt = (
        f"You are a fashion blogger creating an Instagram/TikTok caption for an OOTD (outfit of the day) post. "
        f"The post features a thrifted item and how it's styled in a complete outfit.\n\n"
        f"Item Details:\n"
        f"- Name: {title}\n"
        f"- Price: ${price}\n"
        f"- Platform: {platform}\n"
        f"- Colors: {colors}\n"
        f"- Style: {style_tags}\n"
        f"- Description: {description}\n\n"
        f"Complete Outfit Suggestion:\n{outfit}\n\n"
        f"Create a casual, authentic 2-3 sentence caption that:\n"
        f"1. Mentions the thrifted item naturally (e.g., 'thrifted this...')\n"
        f"2. Includes the price and platform once each\n"
        f"3. Describes how it fits into the outfit and the overall vibe\n"
        f"4. Expresses genuine excitement/satisfaction about the find\n"
        f"5. Sounds like a real OOTD post, not a product ad\n\n"
        f"If the outfit description is incomplete or mentions missing pieces, acknowledge what would complete the look naturally in the caption."
    )
    
    client = _get_groq_client()
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,  # Higher temperature for more creative/varied captions
            max_tokens=300,
        )
        
        caption = response.choices[0].message.content.strip()
        return caption
    
    except Exception as e:
        # Fallback if LLM fails
        return (
            f"Just thrifted this {title} from {platform} for ${price}! "
            f"It's perfect for the {style_tags} vibe. {outfit}"
        )
