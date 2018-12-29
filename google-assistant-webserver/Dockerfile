ARG BUILD_FROM
FROM $BUILD_FROM

WORKDIR /

# Copy data
COPY run.sh /
COPY /setup/.asoundrc /
COPY /src /src
COPY /training /training

# Install system packages
COPY /setup/package.list /
RUN apt-get update -qq
RUN bash -c "xargs -a <(awk '! /^ *(#|$)/' 'package.list') -r -- apt-get -qq install -y --no-install-recommends"

# Install Python packages
COPY /setup/requirements.txt /
RUN pip3 install --no-cache-dir --upgrade setuptools \
  && pip3 -q install --no-cache-dir -r /requirements.txt \
  && rm requirements.txt

# Get snowboy reqs
RUN git clone https://github.com/Kitt-AI/snowboy 
RUN cd snowboy/swig/Python3 \
  && make
RUN cp /snowboy/swig/Python3/snowboydetect.py /src \
  && cp /snowboy/swig/Python3/_snowboydetect.so /src \
  && cp /snowboy/examples/Python3/snowboydecoder.py /src \
  && cp -r /snowboy/resources /

RUN pwd && ls

# Clean up
RUN apt-get remove -y --purge python3-pip python3-dev \
  && apt-get clean -y \
  && rm -rf /var/lib/apt/lists/* \
  && rm -rf /packages/* \
  && rm -rf /resources/alexa \
  && rm package.list


# Enable sudo commands inside container
RUN useradd -m docker && echo "docker:docker" | chpasswd && adduser docker sudo

LABEL \
  maintainer="samlehman617@gmail.com" \
  description="Google Assistant with custom hotword, bluetooth, and GPIO support."
  io.hass.version="VERSION" \
  io.hass.type="addon" \
  io.hass.arch="armhf|aarch64|i386|amd64"

# Run container
RUN chmod a+x /run.sh
ENTRYPOINT [ "/run.sh" ]
