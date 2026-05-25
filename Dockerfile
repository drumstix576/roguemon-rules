# Build/serve toolchain for the RogueMon rules site (Jekyll + Just the Docs).
# Kept in a container so the host needs nothing but Docker. Gems install into a
# named volume at runtime (see docker-compose.yml); this image only provides
# Ruby plus the build tools that native gems (sass-embedded, ffi) need.
FROM ruby:3.3-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /site
EXPOSE 4000
