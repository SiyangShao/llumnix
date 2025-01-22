FROM nvidia/cuda:12.2.2-cudnn8-devel-ubuntu22.04

# Update and install dependencies

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

RUN apt-get update && apt-get install -yq git wget gcc g++ python3.10 zlib1g-dev zip libuv1.dev && apt-get install -yq pip

RUN wget "https://github.com/bazelbuild/bazel/releases/download/5.1.0/bazel_5.1.0-linux-x86_64.deb" -O bazel_5.1.0-linux-x86_64.deb

RUN dpkg -i bazel_5.1.0-linux-x86_64.deb

RUN apt-get install -yq python-is-python3

# Install Llumnix

RUN mkdir -p /app/llumnix

WORKDIR /app/llumnix

COPY . .

RUN make pygloo

RUN make cupy-cuda

RUN make install 

