import json

from models.resources import Infrastructure


def load_infrastructure():
    with open("data/sample_infrastructure.json", "r") as file:
        data = json.load(file)

    infrastructure = Infrastructure(**data)

    return infrastructure


if __name__ == "__main__":
    infrastructure = load_infrastructure()

    print("AeroDrift Infrastructure")
    print("=" * 30)

    for resource in infrastructure.resources:
        print(
            f"{resource.resource_type}: "
            f"{resource.name} "
            f"({resource.id})"
        )