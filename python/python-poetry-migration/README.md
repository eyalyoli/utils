# python-poetry-migration
This script will

1. Convert requirements files to pyproject.toml
2. Convert the Dockerfile to use Poetry
3. Replace Github tests action to use Poetry


## Usage
1. Clone the repo
2. do `poetry install` from the project root
3. run `poetry run python migration.py [PROJ_ROOT_PATH]`


You can use these optional vars:
```
--pyproject - to change the name of "pyproject.toml file"
--project_version - defaults module/package version would be "1.0.0"
--description - add extra description to the project
--python_version - defaults to 3.9
--dry - do a dry run (prints outputs) without changing the files
```

## Notes
+ Install a fresh venv after applying and sanity check the project
+ Verify that the PR builds and deploys ok on app-dev before continuing 
+ Tested on API projects only! 
