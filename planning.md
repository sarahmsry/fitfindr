# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
this tool will search through a database of listings in json format and search for a clothing item that matches the user's specifications which are taken as input. It will return a dict of the top three matches sorted by relevance to the user's specifications. The top result is what is given to the user. 

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): the description of the desired item (i.e. fit, color, style, pattern)
- `size` (str): the clothing size of the user 
- `max_price` (float): maximum price the user is willing to pay

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
it will return a dict of the top three item matches, with each item having id, color(s), name, category, style, and additional notes keys. 

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
If the agent doesn't find any matching listings, it will ask the user to loosen their criteria and re-search the the database for matches based on the new, less strict criteria.
---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
This tool takes the top match from the search_listings tool as input along with the user's current wardrobe information and creates one or more outfit suggestions using the new piece and pieces from the user's current wardrobe. 

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): the result of search_listings(), which is the best match item for the user's search criteria
- `wardrobe` (dict): contains information for each clothing item in the user's current wardrobe that can be used to create an outfit

**What it returns:**
<!-- Describe the return value -->
returns a list of strings that describes the suggested outfits with the new piece and any pieces from the user's wardrobe used to make the outfits. It will also give suggestions on how to style the outfits, rather than simply list off pieces to use. set outfit = suggestions[user's pick]

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
if the wardrobe is empty or no outfit can be suggested, the agent will prompt the user to enter at least one clothing item in their wardrobe to create an outfit. if the wardrobe is minimal, the agent will create a partial outfit with the items available, and give descriptions for what type of pieces would fit in the missing slots. for example, if the user was missing a matching pair of shoes for a grunge style outfit in their wardrobe, the agent would build the rest of the outfit and explain to the user that "a platform pair of leather doc martins would go very well with this oufit."
---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
this tool creates a description of the final outfit including the new selected piece. 

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (list): the description of the suggested outfit that was selected by the user
- `new_item` (str): the thrifted piece that the agent found 

**What it returns:**
<!-- Describe the return value -->
will return a str containing the description for the complete outfit including price, style, which pieces it matches with, and an expression of satisfaction with the item. will sound similar to a social media post. 

**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
if the outfit data is incomplete, the agent will describe a piece that would complete the outfit. For example, if the outfit is missing a pair of jeans, the description will say "thrifted this vintage band tee that I love. Would go amazing with a pair of ripped baggy jeans that I still need to find."
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
Once search_listings finds one or more matching pieces, selected_piece = results[0] and suggest_outfit will be called. If matching pieces are not found, send message to user to re-enter looser criteria for their desired item and try again. 
Once suggest_outfit is called, if there are enough pieces with matching styles to create one or more outfit suggestions, the user will select their favorite from the list. set outfit = suggestions[users pick]. If there are not enough pieces with matching styles or a minimal wardrobe, the agent will create as much of an outfit as possible (ie shirt, pants, and no shoes, or pants, shoes, and no shirt, etc) and for every missing piece will give a description of what would match. For example: grunge top, ripped baggy pants, no shoes found. agent will suggest "a pair of platform doc martins would match this outfit." Once the user selects their favorite outfit suggestion, create_fit_card will be called. 
Once create_fit_card is called, it will use the user's selected suggested outfit to create a shareable description including the new piece. If the selected outfit was an incomplete one, the description will include the suggestions for what would match with the rest of the outfit. 
---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
The agent stores and accesses session state using a dict integrated in the app layer which will be ingested into each planning loop. Each time the planning loop runs, the session state will update and this will be repeated. Another way to do this without the agent accessing state at all is having the app layer store all states independently and calling each tool based on the previous state.
---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query |agent will ask the user to loosen their criteria and will re-search the database for matches based on the new, less strict criteria. |
| suggest_outfit | Wardrobe is empty |the agent will prompt the user to enter at least one clothing item in their wardrobe to create an outfit. if the wardrobe is minimal, the agent will create a partial outfit with the items available, and give descriptions for what type of pieces would fit in the missing slots. for example, if the user was missing a matching pair of shoes for a grunge style outfit in their wardrobe, the agent would build the rest of the outfit and explain to the user that "a platform pair of leather doc martins would go very well with this oufit." |
| create_fit_card | Outfit input is missing or incomplete |if the outfit data is incomplete, the agent will describe a piece that would complete the outfit. For example, if the outfit is missing a pair of jeans, the description will say "thrifted this vintage band tee that I love. Would go amazing with a pair of ripped baggy jeans that I still need to find." |

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

  [USER]
  ├─ description
  ├─ size
  └─ max_price
           │
           │  {description, size, max_price}
           ▼
  ╔═════════════════╗       ┌──────────────────────────────┐
  ║  PLANNING LOOP  ║──────►│ SESSION STATE                │
  ║                 ║◄──────│  • selected_piece            │
  ╚═════════════════╝       │  • outfit_suggestions[ ]     │
           │                │  • outfit (user's pick)      │
           │                └──────────────────────────────┘
           │
           │ {description, size, max_price}
           ▼
  ┌─────────────────────┐
  │  [1] search_listings│
  └─────────────────────┘
           │
      ┌────┴──────────────────────────────────────────────┐
      │                                                   │
      │ no matches found                                  │ top 3 matches dict
      ▼                                                   │ {id, name, color,
  ┌──────────────────────────────┐                        │  category, style,
  │ ► ask user to loosen         │                        │  notes}
  │   criteria                   │                        ▼
  │                              │               selected_piece = results[0]
  │   retry? ──yes──► [USER]     │                        │
  │      │                       │                        │ {selected_piece}
  │      no                      │                        ▼
  │      │                       │               ┌─────────────────────┐
  │      ▼                       │               │  [2] suggest_outfit │
  │  ✗ TERMINATE                 │               └─────────────────────┘
  │    (no results found)        │                        │
  └──────────────────────────────┘                   ┌────┴──────────────┐
                                                     │                   │
                                              wardrobe empty /    outfit suggestions
                                              no style match      returned
                                                     │                   │
                                                     ▼                   ▼
                                             partial outfit +    suggestions[ ]
                                             missing piece        sent to [USER]
                                             descriptions                │
                                                     │                   │
                                                     └────────┬──────────┘
                                                              │
                                                              │ outfit = suggestions
                                                              │ [user's pick]
                                                              ▼
                                                     ┌─────────────────────┐
                                                     │  [3] create_fit_card│
                                                     └─────────────────────┘
                                                              │
                                                         ┌────┴────────────┐
                                                         │                 │
                                                  incomplete data    complete data
                                                         │                 │
                                                         ▼                 ▼
                                                  card includes      full fit card
                                                  missing piece      generated
                                                  suggestion              │
                                                         │                │
                                                         └────────┬───────┘
                                                                  │
                                                                  ▼
                                                            [USER] receives fit card (price · style pairings · post)
---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
I will be using copilot for all tool implementation.
For search_listings, I will give copilot the tool 1 planning section description and tell it to use the load_listings() fucntion from data_loader.py. 
For suggest_outfit, I will give copilot the tool 2 planning section description and have it use the load_wardrobe_schema() function from data_loader.py. 
For create_outfit_card, I will give copilot the tool 3 planning section description.
For all tool implementations, I will ensure that error handling is done correctly before running. I will test each tool with three different queries to make sure there are no missing edge cases. 

**Milestone 4 — Planning loop and state management:**
I will use copilot for this milestone. 
I will give copilot my planning loop diagram, and my planning loop, state management, and error handling descriptions. I will ensure that all state is handled correctly at each step and that the logic follows my planning loop diagram before I proceed. 
---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
The agent will call search_listings() with the desired clothing specifications that the user mentioned (in this case, vintage graphic tee under 30 dollars). 

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
search_listings() will either return 3 items that match the criteria sorted my relevance in terms of the given criteria and the top item is chosen. The item will be fed to suggest_outfit() along with the users wardrobe, or it will prompt the user to reinput more details about what they are looking for if no matching listing is found. It will then call suggest_outfit once a piece is found. 

**Step 3:**
<!-- Continue until the full interaction is complete -->
suggest_outfit() will then return one or more outfit suggestions with the new item based on the user's existing wardrobe. It will describe which pieces to pair together and how to style them. If a user is missing pieces to make a complete outfit or there is an empty wardrobe, the agent will a. ask the user to enter at least one item (if wardrobe is empty) and b. use any existing wardrobe items to create a partial outfit, and then for each missing piece, describe a clothing iteme that would match the rest of the outfit. Then, create_fit_card() will take in the user's favorite selected outfit suggestion as well as the new item and creates a short, shareable description of the entire outfit (similar to an instagram caption)

**Final output to user:**
<!-- What does the user actually see at the end? -->
The user sees the new selected item, the outfit suggestion based on their existing wardrobe, and their outfit card at the very end. 
