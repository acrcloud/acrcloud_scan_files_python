FROM python:2.7.16-slim-stretch

COPY . /acr_scan_tool
WORKDIR /acr_scan_tool
RUN chmod +x /acr_scan_tool/acrcloud_scan_files_python.py

ENV PATH=${PATH}:/acr_scan_tool

RUN apt-get update \
&& apt-get install -y --no-install-recommends git \
&& apt-get purge -y --auto-remove \
&& rm -rf /var/lib/apt/lists/*

RUN pip install git+https://github.com/acrcloud/acrcloud_sdk_python
RUN pip install fuzzywuzzy requests openpyxl python-dateutil backports.csv


ENTRYPOINT ["acrcloud_scan_files_python.py"]
