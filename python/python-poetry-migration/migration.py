import os
import toml
import argparse
from pathlib import Path


TAG_PYTHON_VERSION = "<<PYTHON_VERSION>>"
TAG_MODULE_NAME = "<<MODULE_NAME>>"


def _find_requirements_files(project_root):
    prod_requirements_file = os.path.join(project_root, "requirements.prod.txt")
    dev_requirements_file = os.path.join(project_root, "requirements.txt")
    return prod_requirements_file, dev_requirements_file


def _find_package_name(root_dir):
    for dirname in os.listdir(root_dir):
        dirpath = os.path.join(root_dir, dirname)
        if Path(os.path.join(dirpath, "__init__.py")).is_file() and os.path.basename(dirpath) not in [
            "tests",
            "setup",
        ]:
            return os.path.basename(dirpath)
    return None


def _version_resolver(package_name, version):
    version = version.split("#")[0].strip()

    # handle extras
    if package_name.startswith("python-server-infra") and "[api-analytics]" in package_name:
        package_name = "python-server-infra"
        version = {"extras": ["api-analytics"], "version": version}
    if package_name.startswith("retrain-python-logger") and "[starlette]" in package_name:
        package_name = "retrain-python-logger"
        version = {"extras": ["starlette"], "version": version}

    return package_name, version


def migrate_requirements_to_pyproject(
    project_root,
    pyproject_file,
    project_version,
    python_version,
    description,
    pytorch_version: str = None,
    new_dockerfile_path="./Dockerfile",
    new_tests_action_path="./run-tests.yml",
    dry_run=False,
):
    print("1/3 Detecting package and requirements files...")
    prod_requirements_file, dev_requirements_file = _find_requirements_files(project_root)
    package_name = _find_package_name(project_root)

    if not package_name:
        print("1/3 Failed to find package directory with __init__.py file.")
        return
    print(f"1/3 Detected package name ${package_name}")

    # Read the contents of requirements.prod.txt
    with open(prod_requirements_file, "r") as f:
        prod_requirements = f.read().splitlines()

    # Read the contents of requirements.txt
    with open(dev_requirements_file, "r") as f:
        dev_requirements = f.read().splitlines()

    # Create the pyproject.toml data structure
    pyproject = {
        "tool": {
            "poetry": {
                "name": package_name,
                "version": project_version,
                "description": description,
                "authors": ["retrain.ai"],
                "dependencies": {},
                "dev-dependencies": {},
            }
        }
    }

    uses_pytorch = False

    # Parse requirements.prod.txt and add production dependencies to pyproject.toml
    pyproject["tool"]["poetry"]["dependencies"]["python"] = "^" + python_version
    for requirement in prod_requirements:
        if requirement and requirement[0] != "#":
            package, version = requirement.split("==")
            package, version = _version_resolver(package, version)
            pyproject["tool"]["poetry"]["dependencies"][package] = version

            if (
                package.startswith("torch")
                or package.startswith("sentence-transformers")
                or package.startswith("sentence_transformers")
            ):
                uses_pytorch = True

                if not pytorch_version:
                    raise ValueError("Pytorch version is required for pytorch projects")

                pyproject["tool"]["poetry"]["dependencies"]["torch"] = {
                    "version": "^" + pytorch_version,
                    "source": "pytorch-cpu",
                }

    # Parse requirements.txt and add extra development dependencies to pyproject.toml
    for requirement in dev_requirements:
        if requirement and requirement[0] != "#" and not requirement.startswith("keyring"):
            package, version = requirement.split("==")
            package, version = _version_resolver(package, version)
            if package not in pyproject["tool"]["poetry"]["dependencies"]:
                pyproject["tool"]["poetry"]["dev-dependencies"][package] = version

    # Add the fixed section to pyproject.toml
    pyproject["tool"]["poetry"]["source"] = [
        {
            "name": "retrain",
            "url": "https://europe-west4-python.pkg.dev/retrain-utils/retrain-pypi/simple/",
            "default": False,
            "secondary": True,
        }
    ]

    if uses_pytorch:
        pyproject["tool"]["poetry"]["source"].append(
            {
                "name": "pytorch-cpu",
                "url": "https://download.pytorch.org/whl/cpu",
                "default": False,
                "secondary": True,
            }
        )

    # Write the pyproject.toml file
    if dry_run:
        print("------------- pyproject.toml file -------------")
        print(toml.dumps(pyproject))
        print("-------------")
    else:
        with open(os.path.join(project_root, pyproject_file), "w") as f:
            f.write(toml.dumps(pyproject))

    # delete requirements files
    if not dry_run:
        print("1/3 Deleting old requirements files...")
        os.remove(prod_requirements_file)
        os.remove(dev_requirements_file)

    print(f"1/3 Migration successful. pyproject.toml file created: {pyproject_file}")

    # Replace the Dockerfile
    print("2/3 Replacing Dockerfile...")
    docker_file = ""
    with open(new_dockerfile_path) as f:
        docker_file = f.read()
        docker_file = docker_file.replace(TAG_MODULE_NAME, package_name)
        docker_file = docker_file.replace(TAG_PYTHON_VERSION, python_version)
    if dry_run:
        print("------------- Dockerfile -------------")
        print(docker_file)
        print("-------------")
    else:
        with open(os.path.join(project_root, "Dockerfile"), "w") as f:
            f.write(docker_file)
    print("2/3 Dockerfile replaced with the updated version.")

    # Replace the github tests action
    print("3/3 Replacing Github tests action...")
    tests_action_proj_path = os.path.join(project_root, ".github/workflows/run-tests.yml")
    tests_action = ""
    if os.path.exists(tests_action_proj_path):
        with open(new_tests_action_path) as f:
            tests_action = f.read()
            tests_action = tests_action.replace(TAG_PYTHON_VERSION, python_version)
        if dry_run:
            print("------------- Github tests action -------------")
            print(tests_action)
            print("-------------")
        else:
            with open(tests_action_proj_path, "w") as f:
                f.write(tests_action)
        print("3/3 Github tests action replaced with the updated version.")
    else:
        print("3/3 Github tests action not found! Skipping...")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate requirements.txt to pyproject.toml for Poetry")
    parser.add_argument("project_root", help="Root directory of the project")
    parser.add_argument("--pyproject", default="pyproject.toml", help="Path to pyproject.toml")
    parser.add_argument("--project_version", default="1.0.0", help="Version of the project")
    parser.add_argument("--python_version", default="3.9", help="Version of supported python")
    parser.add_argument("--torch_cpu_version", default="2.0.0+cpu", help="Version of supported pytorch package")
    parser.add_argument("--description", default="", help="Description of the project")
    parser.add_argument("--dry", action="store_true", help="Dry run only prints actions")

    args = parser.parse_args()

    migrate_requirements_to_pyproject(
        args.project_root,
        args.pyproject,
        args.project_version,
        args.python_version,
        args.description,
        args.torch_cpu_version,
        dry_run=args.dry,
    )
