import json
from typing import List
from pydantic import BaseModel, Field, ConfigDict

# Nested Address model (unchanged)
class Address(BaseModel):
    street: str = Field(..., description="Street name")
    number: str = Field(..., description="House/building number")
    city: str = Field(..., description="City name")

# Person model: 1-3 addresses required
class Person(BaseModel):
    name: str = Field(..., description="Full name of the person")
    age: int = Field(..., gt=0, description="Age in years")
    addresses: List[Address] = Field(
        ..., 
        min_items=1, 
        max_items=3, 
        description="List of residential addresses (1-3 required)"
    )
    
    model_config = ConfigDict(extra='forbid')

# Generate and pretty print JSON Schema
schema = Person.model_json_schema()
pretty_schema = json.dumps(schema, indent=2)
print(pretty_schema)

# Usage examples
valid_person = Person(
    name="John Doe",
    age=30,
    addresses=[
        {"street": "Main Street", "number": "123", "city": "New York"},
        {"street": "Second Street", "number": "456", "city": "Boston"}
    ]
)
print(valid_person)

# These would fail validation:
# - Empty list: min_items=1 violated
# - 4+ addresses: max_items=3 violated
