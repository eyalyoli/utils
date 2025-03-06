FROM python:<<PYTHON_VERSION>>-slim

ARG MODULE_NAME=<<MODULE_NAME>>

# Configure Poetry
ENV POETRY_VERSION=1.3.2
ENV PYTHONPATH="${PYTHONPATH}:/${MODULE_NAME}"

# Install poetry separated from system interpreter
RUN python3 -m pip install --user pipx \
    && python3 -m pipx ensurepath \
    && python3 -m pipx install poetry==${POETRY_VERSION}

ENV PATH="${PATH}:/root/.local/bin"

RUN poetry self add keyrings.google-artifactregistry-auth

WORKDIR /${MODULE_NAME}
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-dev --no-root --no-ansi

COPY ./${MODULE_NAME} ./${MODULE_NAME}
# optional copy project setup directory
COPY ./setu[p] ./setup 

CMD ["poetry", "run", "hypercorn", "--config", "python:python_server_infra.config", "<<MODULE_NAME>>.main:app"]