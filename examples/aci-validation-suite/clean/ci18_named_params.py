"""Clean counterpart: parameters grouped into a dataclass — under the 6-arg threshold."""
from dataclasses import dataclass


@dataclass
class UserSpec:
    name: str
    email: str
    age: int
    role: str
    department: str
    location: str


def create_user(spec: UserSpec) -> dict:
    return {
        "name": spec.name,
        "email": spec.email,
        "age": spec.age,
        "role": spec.role,
        "department": spec.department,
        "location": spec.location,
    }
