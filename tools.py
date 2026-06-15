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
def _score_listing(listing: dict, keywords: set[str]) -> int:
    fields = " ".join([
        listing["title"],
        listing["description"],
    ]).lower().split()
    return len(keywords & set(fields))

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
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

    Returns:
        A list of matching listing dicts, sorted by relevance (best match first).
        Returns an empty list if nothing matches — does NOT raise an exception.

    Each listing dict has the following fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand, platform

    TODO:
        1. Load all listings with load_listings().
        2. Filter by max_price and size (if provided).
        3. Score each remaining listing by keyword overlap with `description`.
        4. Drop any listings with a score of 0 (no relevant matches).
        5. Sort by score, highest first, and return the listing dicts.

    Before writing code, fill in the Tool 1 section of planning.md.
    """

    listings = load_listings()

    # Step 2 — filter by max_price and size
    if max_price is not None:
        listings = [l for l in listings if l["price"] <= max_price]
 
    if size is not None:
        listings = [
            l for l in listings
            if size.lower() in l["size"].lower()
        ]

    # Step 3 — score each listing by keyword overlap with description
    keywords = set(description.lower().split())
    scored = [(_score_listing(l, keywords), l) for l in listings]
 
    # Step 4 — drop score == 0
    scored = [(s, l) for s, l in scored if s > 0]
 
    # Step 5 — sort by score descending, return listing dicts
    scored.sort(key=lambda x: x[0], reverse=True)

    return [l for _, l in scored]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────
def _call_llm(prompt: str) -> str:
    client = Groq()
    message = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1000,
        temperature=0.9,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.choices[0].message.content

def _format_wardrobe(wardrobe: dict) -> str:
    lines = []
    for item in wardrobe["items"]:
        lines.append(f"- {item['name']} ({item['category']}, {item['colors']})")
    return "\n".join(lines)

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest 1–2 complete outfits.

    Args:
        new_item: A listing dict (the item the user is considering buying).
        wardrobe: A wardrobe dict with an 'items' key containing a list of
                  wardrobe item dicts. May be empty — handle this gracefully.

    Returns:
        A non-empty string with outfit suggestions.
        If the wardrobe is empty, offer general styling advice for the item
        rather than raising an exception or returning an empty string.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If empty: call the LLM with a prompt for general styling ideas
           (what kinds of items pair well, what vibe it suits, etc.).
        3. If not empty: format the wardrobe items into a prompt and ask
           the LLM to suggest specific outfit combinations using the new item
           and named pieces from the wardrobe.
        4. Return the LLM's response as a string.

    Before writing code, fill in the Tool 2 section of planning.md.
    """
    items = wardrobe.get("items", [])

    if not items:
    # Step 2 — general styling advice
     prompt = f"""You are a secondhand fashion stylist.
        A user is considering buying this item:
        - Name: {new_item['title']}
        - Category: {new_item['category']}
        - Colors: {', '.join(new_item['colors'])}
        - Style tags: {', '.join(new_item['style_tags'])}
        They haven't told you what else they own. Suggest what kinds of pieces pair well \
        with this item, what vibe it suits, and how they might wear it. Keep it concise \
        and practical."""

    else:
        # Step 3 — specific outfit combinations from wardrobe
     prompt = f"""You are a secondhand fashion stylist.
        A user is considering buying this item:
        - Name: {new_item['title']}
        - Category: {new_item['category']}
        - Colors: {', '.join(new_item['colors'])}
        - Style tags: {', '.join(new_item['style_tags'])}
        Their wardrobe contains:
        {_format_wardrobe(wardrobe)}
        Suggest 1–2 complete outfit combinations using the new item and named pieces \
        from their wardrobe. Be specific — reference the actual piece names. Keep it \
        concise and practical."""

    # Step 4 — return LLM response
    return _call_llm(prompt)


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

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

    TODO:
        1. Guard against an empty or whitespace-only outfit string.
        2. Build a prompt that gives the LLM the item details and the outfit,
           and asks for a caption matching the style guidelines above.
        3. Call the LLM and return the response.

    Before writing code, fill in the Tool 3 section of planning.md.
    """
    if not outfit or not outfit.strip():
        return "Error: outfit description is missing — cannot generate a fit card."
        
    else:
     prompt = f"""You are writing captions for a secondhand fashion app.
        The thrifted item:
        - Name: {new_item['title']}
        - Price: ${new_item['price']}
        - Platform: {new_item['platform']}
        The outfit:
        {outfit}
        Write a 2–4 sentence Instagram caption for this outfit. Rules:
        - Casual and authentic, like a real person's OOTD post — not a product description
        - Mention the item name, price, and platform naturally, once each
        - Capture the specific vibe of the outfit
        - No hashtags unless they feel completely natural
        - All lowercase is fine"""
 
    return _call_llm(prompt)
