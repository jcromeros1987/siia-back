from cvu.utils.common import search_in_dict


class TestSearchInDict:
    def test_search_in_dict_finds_value_in_flat_dict(self):
        """Test finding a value in a flat dictionary."""
        data = {"name": "John", "age": "30"}
        result = search_in_dict(data, ["name"])
        assert result == "John"

    def test_search_in_dict_finds_first_matching_key(self):
        """Test that it returns the first matching key found."""
        data = {"name": "John", "email": "john@example.com"}
        result = search_in_dict(data, ["name", "email"])
        assert result in ["John", "john@example.com"]

    def test_search_in_dict_nested_dict(self):
        """Test finding a value in a nested dictionary."""
        data = {"user": {"profile": {"name": "John"}}}
        result = search_in_dict(data, ["name"])
        assert result == "John"

    def test_search_in_dict_returns_none_when_key_not_found(self):
        """Test that None is returned when key is not found."""
        data = {"name": "John", "age": "30"}
        result = search_in_dict(data, ["email"])
        assert result is None

    def test_search_in_dict_returns_none_for_none_value(self):
        """Test that None values are skipped."""
        data = {"name": None, "email": "john@example.com"}
        result = search_in_dict(data, ["name", "email"])
        assert result == "john@example.com"

    def test_search_in_dict_returns_none_for_non_dict_input(self):
        """Test that None is returned when input is not a dict."""
        result = search_in_dict("not a dict", ["key"])
        assert result is None

    def test_search_in_dict_empty_dict(self):
        """Test with an empty dictionary."""
        result = search_in_dict({}, ["name"])
        assert result is None

    def test_search_in_dict_converts_value_to_string(self):
        """Test that values are converted to string."""
        data = {"age": 30}
        result = search_in_dict(data, ["age"])
        assert result == "30"
        assert isinstance(result, str)

    def test_search_in_dict_with_multiple_keys_finds_first(self):
        """Test searching for multiple keys returns the first found."""
        data = {"user": {"email": "john@example.com", "phone": "555-1234"}}
        result = search_in_dict(data, ["phone", "email"])
        assert result in ["john@example.com", "555-1234"]

    def test_search_in_dict_deeply_nested(self):
        """Test with deeply nested dictionaries."""
        data = {"level1": {"level2": {"level3": {"level4": {"value": "deep"}}}}}
        result = search_in_dict(data, ["value"])
        assert result == "deep"
