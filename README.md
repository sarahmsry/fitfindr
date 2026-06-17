# FitFindr — Thrifting Agent

Groq-powered agent that searches for secondhand clothing items and suggests complete outfit combinations based on a user's existing wardrobe.

## Project Structure

```
fitfindr/
├── agent.py                   # Planning loop orchestrating the three tools
├── tools.py                   # Three standalone tool implementations
├── app.py                     # Gradio web interface
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Data loading utilities
├── tests/
│   ├── test_tools.py          # Unit tests for individual tools
│   ├── test_agent_interaction.py  # Integration tests
│   └── checkpoint_test.py      # State flow verification
├── checkpoint_test.py         # Root-level checkpoint test 
├── planning.md                # Planning and design notes
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env with Groq API key 
echo "GROQ_API_KEY=your_key_here" > .env
```

## Tool Inventory

The agent consists of three standalone tools defined in `tools.py`:

### 1. `search_listings()`

**Inputs:**
- `description: str` — Keywords describing what user is looking for (e.g., "vintage graphic tee")
- `size: str | None` — Size filter (e.g., "M", "S/M", case-insensitive substring match)
- `max_price: float | None` — Price ceiling in dollars
- `interactive: bool` — If True, prompts user to refine criteria when no results found; if False, returns empty list

**Outputs:**
- `list[dict]` — Up to 3 listings ranked by relevance. Each listing dict contains: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, `platform`

**Purpose:**
Keyword-based search of the mock listings dataset with optional size/price filtering. Scores listings by word overlap in title (weight 2x), description (1x), style_tags (1.5x), and colors (1x). Returns empty list if no matches found.

---

### 2. `suggest_outfit()`

**Inputs:**
- `new_item: dict` — A listing dict from `search_listings()`
- `wardrobe: dict` — User's wardrobe dict with optional `items` key containing list of wardrobe item dicts

**Outputs:**
- `list[str]` — 1–2 outfit suggestion strings, each a complete styling description

**Purpose:**
Uses Groq LLM (llama-3.3-70b-versatile) to generate outfit suggestions. If wardrobe is empty, provides general styling ideas. If wardrobe is populated, creates specific combinations using actual wardrobe item names. Always returns non-empty list.

---

### 3. `create_fit_card()`

**Inputs:**
- `outfit: str` — An outfit suggestion string from `suggest_outfit()`
- `new_item: dict` — The listing dict for the thrifted item

**Outputs:**
- `str` — A 2–4 sentence Instagram-style caption for the outfit

**Purpose:**
Uses Groq LLM with higher temperature (0.9) to generate casual, authentic outfit captions. Mentions item name, price, and platform naturally. Returns descriptive error message if outfit is empty.

---

## Planning Loop

The agent's main entry point is `run_agent(query, wardrobe)` in `agent.py`. It executes the following planning loop:

1. **Initialize session** — Create session dict with keys: `query`, `parsed`, `search_results`, `selected_item`, `wardrobe`, `outfit_suggestion`, `fit_card`, `error`

2. **Parse query** — Extract `description`, `size`, `max_price` from query using regex patterns for:
   - Prices: `$30`, `under $30`, `max $20`
   - Sizes: `S`, `M`, `L`, `XL`, `S/M`, `M/L`, etc. (optional "oversized")
   - Description: everything else after removing price/size 

3. **Call search_listings()** — Search with parsed parameters and `interactive=False`

4. **Branch on results:**
   - **If no results:** Set `session["error"]` to helpful message and **return early**
   - **If results found:** Continue to step 5

5. **Select top result** — Take `search_results[0]` as `selected_item`

6. **Call suggest_outfit()** — Pass `selected_item` and user's `wardrobe` to generate outfit suggestions. Take first suggestion as `outfit_suggestion`

7. **Call create_fit_card()** — Pass `outfit_suggestion` and `selected_item` to generate caption as `fit_card`. Return completed session.

**Key Design:** Agent short-circuits on empty search results and does not call downstream tools (`suggest_outfit`, `create_fit_card`) in that case.

---

## State Management

State flows through the planning loop using a **session dict** initialized at the beginning and passed through each step:

```python
session = {
    "query": user_input,
    "wardrobe": user_wardrobe,
    "parsed": {"description": "...", "size": None, "max_price": 30.0},
    "search_results": [...],        # list of matching listings
    "selected_item": {...},          # dict (top search result) or None
    "outfit_suggestion": "...",      # str or None
    "fit_card": "...",               # str or None
    "error": None or error_message   # None on success, str on error
}
```

**Flow:**
- `selected_item` (dict) → passed to `suggest_outfit()`
- `outfit_suggestion` (str) → passed to `create_fit_card()`
- No re-entry: each tool called exactly once, no retry loops
- No hardcoded values: all outputs derived from actual tool calls
- Error path: if `error` is set, downstream fields remain `None`

---

## Error Handling

### `search_listings()` — No-Results Case

**Error Type:** Empty search results

**Handling:** Returns empty list (no exception)

**Example from Testing:**
```
Query: "designer ballgown size XXXL under $5"
Result: []  (no matches found)
```

Agent detects empty list and sets error:
```
session["error"] = "No listings found matching your criteria. Try loosening your filters..."
```

---

### `suggest_outfit()` — Handled Gracefully

**Error Type:** LLM response parsing failure

**Handling:** Falls back to unparsed full response string instead of raising exception

**Example:** If LLM returns malformed numbered list, function returns full text as single suggestion in list. Always returns non-empty list.

---

### `create_fit_card()` — Empty Outfit String

**Error Type:** Missing outfit suggestion (upstream tool failure)

**Handling:** Returns descriptive error message string instead of raising exception

**Testing Example:**
```python
results = search_listings('vintage graphic tee', interactive=False)
caption = create_fit_card('', results[0])
# Returns: "Error: outfit suggestion is empty. Unable to generate fit card without outfit details."
```

**Rationale:** The agent's conditional branching ensures cascading failures never happen in normal flow (outfit is always populated before passing to `create_fit_card`)

---

## Spec Reflection

The spec helped me to take enough time to consider all possible error cases and what the most efficient way to handle them is. The spec also helped me to really think through how I wanted to handle state management and how the entire program flows with that. Initially in my spec, I wanted to have the state management handled directly in the app layer rather than send the updated states to the agent each time it is updated. 

## AI Usage

**First instance**
*What I gave*: I gave my AI the description of search_listings(), including input parameters and what it returns, and what will happen if it fails. I explained in detail what I wanted to occur at each step and how it will handle inputs. 

*What the AI returned*: The AI wrote search_listings() but did not include one of the features I prompted it to add, which was an error message prompting the user to loosen their item criteria if no matching listings were found, and to research the database based on the new criteria. I went back in and made sure that feature was implemented and working before proceeding to tool 2.

**Second instance**
*What I gave*: I gave my AI the agent diagram and planning loop and state management sections from my planning.md file to help me implement the planning loop

*What the AI returned*: The AI implemented my planning loop with all required specs and tests passed. I did not need to override anything here, but I tested to make sure that in case of errors, the next tools are not called unconditionally. 