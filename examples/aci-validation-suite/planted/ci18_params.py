"""CI18_PARAMETER_CLUSTER: function with 6+ required positional parameters."""


def create_user(name, email, age, role, department, location):
    return {
        "name": name,
        "email": email,
        "age": age,
        "role": role,
        "department": department,
        "location": location,
    }
