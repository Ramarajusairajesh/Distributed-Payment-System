import pytest
from pydantic import ValidationError

from app.common.schemas.pagination import (
    PaginationParams,
    SortOrder,
    PaginatedResponse
)

class TestPaginationSchemas:
    """Test cases for pagination Pydantic schemas."""

    def test_sort_order_enum(self):
        """Test SortOrder enum."""
        assert SortOrder.ASC == "asc"
        assert SortOrder.DESC == "desc"
        
        # Test conversion from string
        assert SortOrder("asc") == SortOrder.ASC
        assert SortOrder("desc") == SortOrder.DESC
        
        # Test invalid value
        with pytest.raises(ValueError):
            SortOrder("invalid")

    def test_pagination_params_defaults(self):
        """Test default values for PaginationParams."""
        params = PaginationParams()
        assert params.page == 1
        assert params.limit == 10
        assert params.sort_by is None
        assert params.sort_order == SortOrder.ASC

    def test_pagination_params_custom(self):
        """Test custom values for PaginationParams."""
        params = PaginationParams(
            page=2,
            limit=20,
            sort_by="created_at",
            sort_order=SortOrder.DESC
        )
        assert params.page == 2
        assert params.limit == 20
        assert params.sort_by == "created_at"
        assert params.sort_order == SortOrder.DESC

    def test_pagination_params_validation(self):
        """Test validation in PaginationParams."""
        # Page must be positive
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(page=0)
        assert "page" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(page=-1)
        assert "page" in str(exc_info.value)
        
        # Limit must be positive
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(limit=0)
        assert "limit" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(limit=-1)
        assert "limit" in str(exc_info.value)
        
        # Limit max value
        with pytest.raises(ValidationError) as exc_info:
            PaginationParams(limit=101)  # Assuming max limit is 100
        assert "limit" in str(exc_info.value)

    def test_pagination_params_offset(self):
        """Test offset calculation in PaginationParams."""
        # Page 1, limit 10 -> offset 0
        params = PaginationParams(page=1, limit=10)
        assert params.offset == 0
        
        # Page 2, limit 10 -> offset 10
        params = PaginationParams(page=2, limit=10)
        assert params.offset == 10
        
        # Page 3, limit 20 -> offset 40
        params = PaginationParams(page=3, limit=20)
        assert params.offset == 40

    def test_paginated_response(self):
        """Test PaginatedResponse creation."""
        # Simple numeric items
        response = PaginatedResponse[int](
            items=[1, 2, 3, 4, 5],
            total=5,
            page=1,
            limit=10
        )
        
        assert response.items == [1, 2, 3, 4, 5]
        assert response.total == 5
        assert response.page == 1
        assert response.limit == 10
        assert response.pages == 1  # 5 items / 10 per page = 1 page
        
        # Test with dictionary items
        data = [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
            {"id": 3, "name": "Item 3"}
        ]
        
        response = PaginatedResponse[dict](
            items=data,
            total=100,  # Total in database
            page=1,
            limit=3
        )
        
        assert response.items == data
        assert response.total == 100
        assert response.page == 1
        assert response.limit == 3
        assert response.pages == 34  # 100 items / 3 per page = 33.33 -> 34 pages

    def test_paginated_response_last_page(self):
        """Test PaginatedResponse for last page."""
        # Last page with fewer items
        response = PaginatedResponse[int](
            items=[91, 92, 93, 94, 95],
            total=95,
            page=10,
            limit=10
        )
        
        assert len(response.items) == 5
        assert response.total == 95
        assert response.page == 10
        assert response.limit == 10
        assert response.pages == 10  # 95 items / 10 per page = 9.5 -> 10 pages

    def test_paginated_response_empty(self):
        """Test PaginatedResponse with empty results."""
        response = PaginatedResponse[str](
            items=[],
            total=0,
            page=1,
            limit=10
        )
        
        assert response.items == []
        assert response.total == 0
        assert response.page == 1
        assert response.limit == 10
        assert response.pages == 0  # No pages when there are no items

    def test_paginated_response_has_more(self):
        """Test has_more property in PaginatedResponse."""
        # First page with more pages
        response = PaginatedResponse[int](
            items=[1, 2, 3, 4, 5],
            total=20,
            page=1,
            limit=5
        )
        assert response.has_more is True
        
        # Last page
        response = PaginatedResponse[int](
            items=[16, 17, 18, 19, 20],
            total=20,
            page=4,
            limit=5
        )
        assert response.has_more is False
        
        # Empty response
        response = PaginatedResponse[int](
            items=[],
            total=0,
            page=1,
            limit=10
        )
        assert response.has_more is False 