import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import search_listings, suggest_outfit, create_fit_card

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50, interactive=False)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5, interactive=False)
    assert results == []   # empty list, no exception

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10, interactive=False)
    assert all(item["price"] <= 10 for item in results)

def test_suggest_outfit_empty_wardrobe():
    new_item = {
        "title": "Vintage Graphic Tee",
        "description": "Cool vintage band tee from the 90s",
        "category": "tops",
        "colors": ["white", "black"],
        "style_tags": ["vintage", "graphic tee", "casual"],
        "price": 15,
        "condition": "excellent"
    }
    wardrobe = {"items": []}
    suggestions = suggest_outfit(new_item, wardrobe)
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0

def test_suggest_outfit_with_items():
    new_item = {
        "title": "Vintage Graphic Tee",
        "description": "Cool vintage band tee from the 90s",
        "category": "tops",
        "colors": ["white", "black"],
        "style_tags": ["vintage", "graphic tee", "casual"],
        "price": 15,
        "condition": "excellent"
    }
    wardrobe = {
        "items": [
            {
                "name": "Denim Jacket",
                "category": "outerwear",
                "colors": ["blue"],
                "style_tags": ["denim", "vintage"],
                "notes": "Classic denim jacket"
            },
            {
                "name": "Black Jeans",
                "category": "bottoms",
                "colors": ["black"],
                "style_tags": ["denim", "casual"],
                "notes": "Straight leg"
            },
            {
                "name": "White Sneakers",
                "category": "shoes",
                "colors": ["white"],
                "style_tags": ["sneakers", "casual"],
                "notes": "Chunky sole"
            }
        ]
    }
    suggestions = suggest_outfit(new_item, wardrobe)
    assert isinstance(suggestions, list)
    assert len(suggestions) > 0

def test_suggest_outfit_no_suggestions():
    new_item = {
        "title": "Formal Ballgown",
        "description": "Elegant formal ballgown for special events",
        "category": "dresses",
        "colors": ["white", "silver"],
        "style_tags": ["formal", "elegant", "ballgown"],
        "price": 200,
        "condition": "excellent"
    }
    wardrobe = {
        "items": [
            {
                "name": "Casual T-Shirt",
                "category": "tops",
                "colors": ["white"],
                "style_tags": ["casual", "basics"],
                "notes": "Cotton"
            },
            {
                "name": "Jeans",
                "category": "bottoms",
                "colors": ["blue"],
                "style_tags": ["denim", "casual"],
                "notes": "Dark wash"
            },
            {
                "name": "Sneakers",
                "category": "shoes",
                "colors": ["white"],
                "style_tags": ["sneakers", "casual"],
                "notes": "Canvas"
            }
        ]
    }
    suggestions = suggest_outfit(new_item, wardrobe)
    # Function should still return suggestions, not an empty list
    # It will suggest how to use formal pieces with casual items
    assert isinstance(suggestions, list)

def test_create_fit_card_incomplete_outfit():
    new_item = {
        "title": "Vintage Band Tee",
        "description": "Classic 90s band tee in great condition",
        "category": "tops",
        "colors": ["white", "black"],
        "style_tags": ["vintage", "graphic tee", "band tee"],
        "price": 18,
        "condition": "excellent",
        "platform": "depop"
    }
    
    # Incomplete outfit that mentions missing pieces
    incomplete_outfit = (
        "Pair this vintage band tee with black jeans for an effortless 90s vibe. "
        "The graphic really pops against the plain black bottoms. Would look amazing "
        "with a leather jacket and black boots to complete the grunge aesthetic, but "
        "I'm still hunting for the perfect boots."
    )
    
    caption = create_fit_card(incomplete_outfit, new_item)
    
    # Verify it returns a non-empty string
    assert isinstance(caption, str)
    assert len(caption) > 0
    
    # Should mention the item or outfit in some way
    assert any(word in caption.lower() for word in ["tee", "band", "vintage", "boot", "jacket", "jeans", "$18", "depop"])