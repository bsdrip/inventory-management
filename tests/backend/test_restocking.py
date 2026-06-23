"""
Tests for restocking API endpoints.
"""
from datetime import datetime, timedelta

import pytest


class TestRestockingRecommendations:
    """Test suite for GET /api/restocking/recommendations."""

    def test_get_recommendations(self, client):
        """Test getting all recommendations."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_recommendation_structure(self, client):
        """Test that recommendations have all required fields."""
        response = client.get("/api/restocking/recommendations")
        data = response.json()

        required_fields = [
            "item_sku", "item_name", "forecasted_demand", "quantity_on_hand",
            "shortage", "trend", "unit_cost", "recommended_quantity",
            "estimated_cost", "priority_score", "warehouse", "category",
        ]
        for rec in data:
            for field in required_fields:
                assert field in rec, f"Missing field: {field}"

    def test_recommendations_only_positive_shortage(self, client):
        """Test that only items with positive shortage are returned."""
        response = client.get("/api/restocking/recommendations")
        data = response.json()

        for rec in data:
            assert rec["shortage"] > 0

    def test_recommendations_sorted_by_priority(self, client):
        """Test that recommendations are sorted by priority_score descending."""
        response = client.get("/api/restocking/recommendations")
        data = response.json()

        scores = [r["priority_score"] for r in data]
        assert scores == sorted(scores, reverse=True)

    def test_recommendation_estimated_cost_calculation(self, client):
        """Test that estimated_cost = shortage * unit_cost."""
        response = client.get("/api/restocking/recommendations")
        data = response.json()

        for rec in data:
            expected = round(rec["shortage"] * rec["unit_cost"], 2)
            assert abs(rec["estimated_cost"] - expected) < 0.01

    def test_recommendation_data_types(self, client):
        """Test that numeric fields have correct types."""
        response = client.get("/api/restocking/recommendations")
        data = response.json()

        for rec in data:
            assert isinstance(rec["forecasted_demand"], int)
            assert isinstance(rec["quantity_on_hand"], int)
            assert isinstance(rec["shortage"], int)
            assert isinstance(rec["unit_cost"], (int, float))
            assert isinstance(rec["priority_score"], (int, float))
            assert rec["unit_cost"] > 0

    def test_recommendation_trend_values(self, client):
        """Test that trend values are valid."""
        response = client.get("/api/restocking/recommendations")
        data = response.json()

        valid_trends = ["increasing", "stable", "decreasing"]
        for rec in data:
            assert rec["trend"] in valid_trends

    def test_recommendations_filter_by_warehouse(self, client):
        """Test filtering recommendations by warehouse."""
        response = client.get("/api/restocking/recommendations?warehouse=London")
        assert response.status_code == 200

        data = response.json()
        for rec in data:
            assert rec["warehouse"] == "London"

    def test_recommendations_filter_by_category(self, client):
        """Test filtering recommendations by category."""
        response = client.get("/api/restocking/recommendations?category=Sensors")
        assert response.status_code == 200

        data = response.json()
        for rec in data:
            assert rec["category"].lower() == "sensors"

    def test_increasing_trend_has_higher_priority(self, client):
        """Test that increasing trend items get a higher priority multiplier."""
        response = client.get("/api/restocking/recommendations")
        data = response.json()

        for rec in data:
            if rec["trend"] == "increasing":
                assert rec["priority_score"] == rec["shortage"] * 2.0
            elif rec["trend"] == "stable":
                assert rec["priority_score"] == rec["shortage"] * 1.0


class TestRestockingOrders:
    """Test suite for POST /api/restocking/orders."""

    def test_submit_restocking_order(self, client):
        """Test submitting a restocking order."""
        order_data = {
            "items": [
                {"sku": "WDG-001", "name": "Industrial Widget Type A", "quantity": 100, "unit_cost": 12.50}
            ],
            "budget": 5000.0
        }
        response = client.post("/api/restocking/orders", json=order_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "Submitted"
        assert data["customer"] == "Internal Restocking"
        assert "order_number" in data
        assert "id" in data

    def test_submitted_order_total_value(self, client):
        """Test that total_value is calculated correctly."""
        order_data = {
            "items": [
                {"sku": "WDG-001", "name": "Widget A", "quantity": 10, "unit_cost": 12.50},
                {"sku": "GSK-203", "name": "Gasket", "quantity": 20, "unit_cost": 8.75},
            ],
            "budget": 5000.0
        }
        response = client.post("/api/restocking/orders", json=order_data)
        data = response.json()

        expected_total = (10 * 12.50) + (20 * 8.75)
        assert abs(data["total_value"] - expected_total) < 0.01

    def test_submitted_order_delivery_is_7_days(self, client):
        """Test that expected delivery is 7 days after order date."""
        order_data = {
            "items": [
                {"sku": "WDG-001", "name": "Test Item", "quantity": 10, "unit_cost": 12.50}
            ],
            "budget": 1000.0
        }
        response = client.post("/api/restocking/orders", json=order_data)
        data = response.json()

        order_date = datetime.fromisoformat(data["order_date"])
        expected_delivery = datetime.fromisoformat(data["expected_delivery"])
        assert (expected_delivery - order_date).days == 7

    def test_submitted_order_appears_in_orders(self, client):
        """Test that a submitted order appears in GET /api/orders."""
        order_data = {
            "items": [
                {"sku": "FLT-405", "name": "Oil Filter", "quantity": 50, "unit_cost": 6.50}
            ],
            "budget": 2000.0
        }
        post_response = client.post("/api/restocking/orders", json=order_data)
        new_order_id = post_response.json()["id"]

        response = client.get("/api/orders")
        data = response.json()

        matching = [o for o in data if o["id"] == new_order_id]
        assert len(matching) == 1
        assert matching[0]["status"] == "Submitted"

    def test_submitted_order_has_items_structure(self, client):
        """Test that submitted order items have proper structure."""
        order_data = {
            "items": [
                {"sku": "WDG-001", "name": "Widget", "quantity": 5, "unit_cost": 12.50}
            ],
            "budget": 1000.0
        }
        response = client.post("/api/restocking/orders", json=order_data)
        data = response.json()

        assert isinstance(data["items"], list)
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["sku"] == "WDG-001"
        assert item["quantity"] == 5
        assert item["unit_price"] == 12.50

    def test_order_number_format(self, client):
        """Test that generated order number follows ORD-2025-XXXX format."""
        order_data = {
            "items": [
                {"sku": "WDG-001", "name": "Widget", "quantity": 1, "unit_cost": 12.50}
            ],
            "budget": 100.0
        }
        response = client.post("/api/restocking/orders", json=order_data)
        data = response.json()

        assert data["order_number"].startswith("ORD-2025-")
        number_part = data["order_number"].split("-")[-1]
        assert len(number_part) == 4
        assert number_part.isdigit()
