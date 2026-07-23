# FitFindr 

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```
# Tool inventory

## Tool 1: search_listings

**What it does:**
Query listings.json and return relevant clothing/accessory listings based on natural language or structured criteria.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): Description of the clothing 
- `size` (str): Size of the clothing 
- `max_price` (float): Max price of the clothing 

**What it returns:**
A list of matching listing dicts, sorted by relevance (best match first).

**What happens if it fails or returns nothing:**
- If search_listings returns nothing, FitFindr tells the user what to try differently and stops — it does not call suggest_outfit with empty input.
---

## Tool 2: suggest_outfit

**What it does:**
Given a specific item and the user's current wardrobe, suggests one or more complete outfit combinations.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): specific clothing item
- `wardrobe` (dict): User's owned pieces

**What it returns:**
- A non-empty string with outfit suggestions.

**What happens if it fails or returns nothing:**
- If the wardrobe is empty, offer general styling advice for the item

---

## Tool 3: create_fit_card

**What it does:**
Generates a short, shareable description of a complete outfit — the kind of thing someone would caption an Instagram post with. Must produce something different each time for different inputs.

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (str):  the full outfit dictionary (wardrobe pieces + sourced listings)
- `new_item` (dict): the anchor secondhand piece the whole look is built around

**What it returns:**
A description of the outfit

**What happens if it fails or returns nothing:**
If outfit is empty or missing, return a descriptive error message

# How the planning loop works (describe the conditional logic, not just "it decides what to do")

The planning tool  determines the next step:

- Always starts with search_listings
- Always calls suggest_outfit next — only if search_listings returned results
- Always calls create_fit_card last — suggest_outfit always returns something so this step is never skipped

# Error handling strategy for each tool

## Tool 1: search_listings 
Returns an empty list when no listings match — never raises. run_agent checks for this immediately after the call and sets session["error"] with a message telling the user what to try differently, then returns early. suggest_outfit is never called with empty input.

Concrete example: querying "vintage graphic tee under $5" with a low price ceiling filtered out every listing after the price check, scoring never ran, and an empty list came back. session["error"] was set to "No listings found for 'vintage graphic tee'. Try different keywords, a higher price, or remove the size filter." and the loop stopped there.

## Tool 2: suggest_outfit
Handles an empty or missing wardrobe["items"] gracefully — falls back to general styling advice instead of raising a KeyError or returning an empty string. Uses wardrobe.get("items", []) so a missing key doesn't crash.

Concrete example: passing get_empty_wardrobe() produced a general styling response rather than an exception — the LLM was prompted for vibe and pairing ideas instead of specific wardrobe combinations.

## Tool 3: create_fit_card
Guards against an empty or whitespace-only outfit string before hitting the API. Returns a descriptive error string rather than raising — run_agent stores it in session["fit_card"] and returns normally, leaving it to the UI to display.

Concrete example: if suggest_outfit somehow returned "   ", create_fit_card returns "Error: outfit description is missing — cannot generate a fit card." and the session completes without crashing.

