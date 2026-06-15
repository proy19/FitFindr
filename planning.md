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

### Tool 2: suggest_outfit

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

### Tool 3: create_fit_card

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

---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
The agent tool's output determines the next step:

- Always starts with search_listings
- Always calls suggest_outfit next — only if search_listings returned results
- Always calls create_fit_card last — suggest_outfit always returns something so this step is never skipped

---

## State Management

**How does information from one tool get passed to the next?**

What is stored: 
The session dict is the single source of truth for one full interaction. It holds the raw query, the parsed parameters extracted from it, the full ranked list of listings, the top listing selected as the anchor item, the user's wardrobe, the outfit suggestion string, the fit card caption, and any error that caused early termination.

When it is written: 
Each field is written exactly once, at the step that produces it. parsed is written after the LLM extracts description, size, and max price from the query. search_results is written after search_listings runs. selected_item is written immediately after by taking search_results[0]. outfit_suggestion is written after suggest_outfit returns. fit_card is written after create_fit_card returns. error is written only if the loop exits early — currently only when search_results is empty.

How it is passed between tools:
No tool reads from the session dict directly. Each tool receives only the values it needs as explicit arguments. run_agent pulls the right fields out of session and passes them. 

The session accumulates state; the tools stay stateless. Neither suggest_outfit nor create_fit_card knows the session exists — they just take inputs and return strings.

Each tool reads from session and writes back to it.

A diagram of the state management:

    user describes a piece
        │
        ▼ session["query"] = "vintage levi's under $80"
    search_listings(session["query"])
        │
        ▼ session["item"] = results[0]  # most relevant
    suggest_outfit(session["item"], session["wardrobe"])
        │
        ▼ session["outfit"] = combinations or styling advice
    create_fit_card(session["outfit"], session["item"])
        │
        ▼ session["fit_card"] = caption string

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | Tells the user to try a different listing size, price, or platform and the agents stop  
| suggest_outfit | Wardrobe is empty | Offer general styling advice for the item
| create_fit_card | Outfit input is missing or incomplete | Returns a descriptive error message|

---

## Architecture
          user describes a piece
                    │
                    ▼
          ┌───────────────────────────────────────────────┐
          │ search_listings (description, size, max_price)│
          └────────┬──────────────────────────────────────┘
                   │
         ┌─────────┴──────────┐
         │                    │
         ▼                    ▼
    no results          results returned
         │                    │
         ▼                    ▼
    Asks user to try a 
    different           Tool picks the most relevant outfit
    size, price, or        
    platform                  │
                              ▼
             ┌─────────────────────────┐
             │      suggest_outfit     │◄── wardrobe dict
             │   (item, wardrobe)      │
             └────────────┬────────────┘
                          │
             ┌────────────┴────────────┐
             │                         │
             ▼                         ▼
    no wardrobe match            outfit combinations
             │                         │
             ▼                         └──────────┐
    general styling advice                        │
    for the anchor item                           │
             │                                    │
             └───────────────────────────┬────────┘
                               ┌─────────────────────┐
                               │   create_fit_card   │
                               │  (outfit, new_item) │
                               └────┬────────────────┘
                                    │
                     ┌──────────────┼──────────────┐
                     │                             │
                     ▼                             ▼
          Outfit missing name,                 caption returned
                   price, or                            │
                   platform                             ▼
                          │                     shareable caption
                          ▼
                 validation error
                   agent stops

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
I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement search_listings() using load_listings() from the data loader — then test it against 3 queries before trusting it. 

**Milestone 4 — Planning loop and state management:**
I'll give Claude the three tools with what they return and ask it to implement the loop and state management. To test it, I will run 3 test queries to ensure that the session stays consistent and user interference isn't needed to pass data along the three tools. 

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
The agent calls search_listings with description="vintage graphic tee" and max_price=30.00. It loads all listings, filters out anything over $30, scores the rest by keyword overlap against title and description, drops anything with a score of zero, and returns the full ranked list. The top result — a Vintage Nirvana Tee for $18 on Depop — becomes the anchor item and is stored in session.

**Step 2:**
The agent then calls suggest_outfit with the anchor item and the user's wardrobe. The LLM scores combinations of wardrobe pieces against the anchor item and returns the highest scoring combo — the baggy jeans and chunky New Balances. The full outfit is stored in session.

**Step 3:**
Finally the agent calls create_fit_card with the outfit and the anchor item. It validates that name, price, and platform are all present, then calls the Anthropic API to generate a caption. It returns something like "$18 nirvana tee off depop doing the heavy lifting. baggy jeans, chunky new balances. the whole fit for under twenty bucks." The caption is stored in session and returned to the user. 

**Final output to user:**
The new item, outfit suggestion, and the caption is stored in session and returned to the user.
