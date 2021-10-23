FROM python:3.8
RUN apt-get update \
    && apt-get install -y ffmpeg \
    && apt-get clean
RUN pip install unittest-xml-reporting . \
    && pip install amrchan --index-url https://${ACCESS_TOKEN_NAME}:${ACCESS_TOKEN}/projects/6162/packages/pypi/simple
COPY . ./mcvqoe-base
RUN pip install ./mcvqoe-base
CMD ["/bin/sh"]

