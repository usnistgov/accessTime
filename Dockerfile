FROM python:3.8
ARG ACCESS_TOKEN_NAME
ARG ACCESS_TOKEN
ARG CI_API_V4_URL
RUN apt-get update \
    && apt-get install -y ffmpeg libavcodec-extra \
    && apt-get clean
COPY . ./mcvqoe-base
RUN pip install unittest-xml-reporting plotly ./mcvqoe-base \
    && pip install amrchan --index-url https://${ACCESS_TOKEN_NAME}:${ACCESS_TOKEN}@gitlab.nist.gov/gitlab/api/v4/projects/6162/packages/pypi/simple
CMD ["/bin/sh"]

