FROM python:3.11-slim

WORKDIR /workspace

# Install basic tools
RUN apt-get update && apt-get install -y \
    bash \
    && rm -rf /var/lib/apt/lists/*
