# syntax=docker/dockerfile:1.3
FROM ubuntu:22.04

ENV EDITOR=vim
ENV PYTHON_VERSION=3.10

ARG USER_NAME=vscode
ARG USER_UID
ARG USER_GID

RUN groupadd --gid $USER_GID $USER_NAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USER_NAME \
    && apt-get update \
    && apt-get install -y sudo \
    && echo $USER_NAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USER_NAME \
    && chmod 0440 /etc/sudoers.d/$USER_NAME \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/* \
    && rm -rf /var/lib/apt/lists/*

ENV SHELL=/usr/bin/zsh
RUN chsh $USER_NAME -s $SHELL

# Install dev dependences & tools
RUN apt update && apt install -y \
    zsh \
    htop \
    vim \
    git \
    wget \
    curl \
    ssh \
    rsync \
    unzip \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    kmod \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-dev \
    python${PYTHON_VERSION}-distutils \
    python3-setuptools \
    python3-pip \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /tmp/* /var/tmp/* \
    && rm -rf /var/lib/apt/lists/*

# set default python version
RUN update-alternatives --install /usr/bin/python python /usr/bin/python${PYTHON_VERSION} 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1


# [Optional] If your pip requirements rarely change, uncomment this section to add them to the image.
COPY .devcontainer/requirements.txt .devcontainer/entrypoint.sh /home/$USER_NAME/
RUN --mount=type=cache,target=/root/.cache,id=pip \
    pip install -r /home/$USER_NAME/requirements.txt \
    && rm -rf /home/$USER_NAME/requirements.txt

# copy devs scripts
COPY .devcontainer/parse-deps.py /bin/
RUN chmod +x /bin/parse-deps.py

# create links to the project but delete them to be mounted by the devcontainer
RUN --mount=type=bind,source=.,target=/root/src/ \
    --mount=type=cache,target=/root/.cache,id=pip \
    pip install Cython wheel \
    && python /root/src/setup.py egg_info \
    && parse-deps.py CENSAr.egg-info/requires.txt \
    && pip install $(parse-deps.py CENSAr.egg-info/requires.txt) \
    && rm -rf *.egg-info

# create links to the project but delete them to be mounted by the devcontainer
COPY . /workspace/
RUN pip install --no-deps -e /workspace/ \
    && rm -rf /workspace/src

USER $USER_NAME
WORKDIR /tmp
RUN sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
