ARG OCI_IMAGE_VERSION
FROM $OCI_IMAGE_VERSION as base

ARG POETRY_VERSION=1.3.2
ARG DEBIAN_FRONTEND=noninteractive
ARG TZ=Etc/UTC

RUN apt-get update && \
    apt-get install gnupg2 gawk yamllint vim telnet expect sshpass inetutils-ping netcat wget -y && \
    wget https://github.com/infrahq/infra/releases/download/v0.21.0/infra_0.21.0_amd64.deb && \
    apt install ./infra_*.deb && \
    apt-get clean && apt clean

ENV PATH=/app/bin:/root/.local/bin:$PATH

ENV PYTHONPATH="/app/src:${PYTHONPATH}"

RUN python3 -m pip install --user pipx && \
    python3 -m pipx ensurepath && \
    pipx install poetry==$POETRY_VERSION && \
    pipx install build && \
    poetry config virtualenvs.in-project true && \
    pip install virtualenv

WORKDIR /app

FROM base
COPY . /app

COPY ./src/ska_mid_itf_engineering_tools/tango_control/tangoctl.py /app/bin/tangoctl
COPY ./src/ska_mid_itf_engineering_tools/tango_control/tangoctl.json /app/bin/
COPY ./src/ska_mid_itf_engineering_tools/tango_kontrol/tangoktl.py /app/bin/tangoktl
COPY ./src/ska_mid_itf_engineering_tools/tango_kontrol/tangoktl.json /app/bin/

RUN poetry install

USER root

ENV PATH=/app/.venv/bin/:$PATH

CMD ["bash"]
