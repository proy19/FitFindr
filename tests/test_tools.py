import pytest
from search_listings import search_listings
 
def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0
 
 
def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []   # empty list, no exception
 
 
def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert all(item["price"] <= 10 for item in results)

def test_search_no_size_filter():
    # omitting size should return more results than filtering by a rare size
    all_results = search_listings("tee", size=None, max_price=None)
    filtered_results = search_listings("tee", size="XXS", max_price=None)
    assert len(all_results) >= len(filtered_results)

def test_search_returns_list_of_dicts():
    results = search_listings("jacket", size=None, max_price=None)
    for item in results:
        assert isinstance(item, dict)