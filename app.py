"""
app.py

Gradio interface for FitFindr. The layout and wiring are already set up —
your job is to fill in handle_query() so it calls run_agent() and maps
the session results to the three output panels.

Run with:
    python app.py

Then open the localhost URL shown in your terminal (usually http://localhost:7860,
but check your terminal — the port may differ).
"""

import gradio as gr

from agent import run_agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe


# ── query handler ─────────────────────────────────────────────────────────────

def handle_query(user_query: str, wardrobe_choice: str) -> tuple[str, str, str]:
    """
    Called by Gradio when the user submits a query.

    Args:
        user_query:     The text the user typed into the search box.
        wardrobe_choice: Either "Example wardrobe" or "Empty wardrobe (new user)".

    Returns:
        A tuple of three strings:
            (listing_text, outfit_suggestion, fit_card)
        Each string maps to one of the three output panels in the UI.
    """
    # Guard against empty query
    if not user_query or not user_query.strip():
        return "Please enter a search query (e.g., 'vintage graphic tee under $30').", "", ""

    # Select wardrobe based on choice
    if wardrobe_choice == "Empty wardrobe (new user)":
        wardrobe = get_empty_wardrobe()
    else:
        wardrobe = get_example_wardrobe()

    # Call the agent
    session = run_agent(query=user_query, wardrobe=wardrobe)

    # Check for errors
    if session["error"]:
        return session["error"], "", ""

    # Format the listing
    listing_text = _format_listing(session["selected_item"])

    # Return the three outputs
    return listing_text, session["outfit_suggestion"], session["fit_card"]


def _format_listing(item: dict) -> str:
    """
    Format a listing dict into a readable string for display.

    Args:
        item: A listing dict from search_listings()

    Returns:
        A formatted markdown string with the listing details.
    """
    parts = []

    parts.append(f"## {item.get('title', 'Untitled')}")

    if item.get("price"):
        parts.append(f"**Price:** ${item['price']}")

    if item.get("platform"):
        parts.append(f"**Platform:** {item['platform']}")

    if item.get("size"):
        parts.append(f"**Size:** {item['size']}")

    if item.get("category"):
        parts.append(f"**Category:** {item['category']}")

    if item.get("condition"):
        parts.append(f"**Condition:** {item['condition']}")

    if item.get("colors"):
        colors_str = ", ".join(item["colors"]) if isinstance(item["colors"], list) else item["colors"]
        parts.append(f"**Colors:** {colors_str}")

    if item.get("brand"):
        parts.append(f"**Brand:** {item['brand']}")

    if item.get("style_tags"):
        tags_str = ", ".join(item["style_tags"]) if isinstance(item["style_tags"], list) else item["style_tags"]
        parts.append(f"**Styles:** {tags_str}")

    if item.get("description"):
        parts.append(f"\n{item['description']}")

    return "\n".join(parts)


# ── interface ─────────────────────────────────────────────────────────────────

EXAMPLE_QUERIES = [
    "vintage graphic tee under $30",
    "90s track jacket in size M",
    "flowy midi skirt under $40",
    "black combat boots size 8",
    "designer ballgown size XXS under $5",   # deliberate no-results test
]

def build_interface():
    with gr.Blocks(title="FitFindr") as demo:
        gr.Markdown("""
# FitFindr 🛍️
Find secondhand pieces and get outfit ideas based on your wardrobe.
Describe what you're looking for — include size and price if you want to filter.
        """)

        with gr.Row():
            query_input = gr.Textbox(
                label="What are you looking for?",
                placeholder="e.g. vintage graphic tee under $30, size M",
                lines=2,
                scale=3,
            )
            wardrobe_choice = gr.Radio(
                choices=["Example wardrobe", "Empty wardrobe (new user)"],
                value="Example wardrobe",
                label="Wardrobe",
                scale=1,
            )

        submit_btn = gr.Button("Find it", variant="primary")

        with gr.Row():
            listing_output = gr.Textbox(
                label="🛍️ Top listing found",
                lines=8,
                interactive=False,
            )
            outfit_output = gr.Textbox(
                label="👗 Outfit idea",
                lines=8,
                interactive=False,
            )
            fitcard_output = gr.Textbox(
                label="✨ Your fit card",
                lines=8,
                interactive=False,
            )

        gr.Examples(
            examples=[[q, "Example wardrobe"] for q in EXAMPLE_QUERIES],
            inputs=[query_input, wardrobe_choice],
            label="Try these queries",
        )

        submit_btn.click(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[listing_output, outfit_output, fitcard_output],
        )
        query_input.submit(
            fn=handle_query,
            inputs=[query_input, wardrobe_choice],
            outputs=[listing_output, outfit_output, fitcard_output],
        )

    return demo


if __name__ == "__main__":
    demo = build_interface()
    demo.launch()
