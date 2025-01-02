#python image to run project
FROM python:3.11.0

RUN pip install -r ./requirements.txt
RUN scrapyd
