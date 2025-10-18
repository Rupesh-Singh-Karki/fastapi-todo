import os
import sys


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python generate_module.py <directory_name>")
        sys.exit(1)

    dir_name = sys.argv[1]

    # Change to src directory
    src_path = os.path.join(os.getcwd(), "src")
    if not os.path.exists(src_path):
        print("src directory does not exist.")
        sys.exit(1)

    os.chdir(src_path)

    # Create the new directory
    new_dir_path = os.path.join(src_path, dir_name)
    os.makedirs(new_dir_path, exist_ok=True)

    # Create __init__.py in the new directory
    with open(os.path.join(new_dir_path, "__init__.py"), "w") as f:
        f.write("")

    # Create schema.py
    with open(os.path.join(new_dir_path, "schema.py"), "w") as f:
        f.write("")

    # Create model.py
    with open(os.path.join(new_dir_path, "model.py"), "w") as f:
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

    print(f"Created directory {dir_name} in src with required files.")


if __name__ == "__main__":
    main()
