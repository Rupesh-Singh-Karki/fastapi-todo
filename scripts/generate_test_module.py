import os
import sys


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python generate_module.py <directory_name>")
        sys.exit(1)

    dir_name = sys.argv[1]

    # Change to tests directory
    tests_path = os.path.join(os.getcwd(), "tests")
    if not os.path.exists(tests_path):
        print("tests directory does not exist.")
        sys.exit(1)

    os.chdir(tests_path)

    # Create the new directory
    new_dir_path = os.path.join(tests_path, dir_name)
    os.makedirs(new_dir_path, exist_ok=True)

    # Create __init__.py in the new directory
    with open(os.path.join(new_dir_path, "__init__.py"), "w") as f:
        f.write("")

    # Create test_schema.py
    with open(os.path.join(new_dir_path, "test_schema.py"), "w") as f:
        f.write("")

    # Create test_model.py
    with open(os.path.join(new_dir_path, "test_model.py"), "w") as f:
        f.write("")

    # Create routes directory and __init__.py
    routes_dir = os.path.join(new_dir_path, "routes")
    os.makedirs(routes_dir, exist_ok=True)
    with open(os.path.join(routes_dir, "__init__.py"), "w") as f:
        f.write("")

    # Create services directory and __init__.py
    services_dir = os.path.join(new_dir_path, "services")
    os.makedirs(services_dir, exist_ok=True)
    with open(os.path.join(services_dir, "__init__.py"), "w") as f:
        f.write("")

    print(f"Created directory {dir_name} in tests with required files.")


if __name__ == "__main__":
    main()
