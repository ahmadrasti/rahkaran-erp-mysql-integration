from __future__ import annotations

from dataclasses import dataclass


class ValidationError(ValueError):
    pass


REQUIRED = {
    "customers": {"customer_id", "name", "updated_at"},
    "products": {"product_id", "name", "unit_price", "updated_at"},
    "orders": {"order_id", "customer_id", "product_id", "order_date", "quantity", "unit_price", "status", "updated_at"},
}


def validate(entity: str, record: dict) -> dict:
    expected = REQUIRED.get(entity)
    if expected is None:
        raise ValidationError("unknown synthetic entity")
    if not isinstance(record, dict) or not expected.issubset(record):
        raise ValidationError(f"{entity} record is missing required generic fields")
    if entity == "orders" and (not isinstance(record["quantity"], int) or record["quantity"] < 1):
        raise ValidationError("order quantity must be a positive integer")
    if entity in {"orders", "products"} and not isinstance(record["unit_price"], (int, float)):
        raise ValidationError("unit_price must be numeric")
    return record


def transform(entity: str, record: dict) -> dict:
    validated = validate(entity, record)
    return {key: value.strip() if isinstance(value, str) else value for key, value in validated.items()}
