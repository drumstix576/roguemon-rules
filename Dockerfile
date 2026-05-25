# Build/serve toolchain for the RogueMon rules site (Jekyll + Just the Docs).
# Kept in a container so the host needs nothing but Docker. Gems are baked into
# the image (not a runtime volume) so the image is self-contained and portable:
# `docker compose run --rm jekyll bundle exec jekyll build` works on any host
# once the image is built. build-essential/git are needed for native gems.
FROM ruby:3.3-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /site
COPY Gemfile Gemfile.lock* ./
RUN bundle install

EXPOSE 4000
