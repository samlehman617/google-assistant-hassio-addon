ARG BUILD_FROM
FROM $BUILD_FROM

# Install packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    jq tzdata swig3.0 sox sudo \
    python3 python3-dev python3-pip python-pyaudio python3-pyaudio \
    libssl-dev libatlas-base-dev \
    portaudio19-dev libportaudio2 libffi-dev libmpg123-dev \
    # bluealsa alsa-utils \
    alsa-utils \
    && pip3 install --no-cache-dir --upgrade setuptools \
    && pip3 install --no-cache-dir \
    google-assistant-library==1.0.0 \
    google-assistant-sdk==0.5.0 \
    google-assistant-grpc==0.2.0 \
    google-auth requests_oauthlib cherrypy pyaudio \
    && apt-get remove -y --purge python3-pip python3-dev \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

# Copy data
COPY *.sh /
COPY *.py /
COPY .asoundrc /

# Enable sudo commands inside container
RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo

LABEL io.hass.version="VERSION" io.hass.type="addon" io.hass.arch="armhf|aarch64|i386|amd64"

# Run container
RUN chmod a+x /run.sh
ENTRYPOINT [ "/run.sh" ]
