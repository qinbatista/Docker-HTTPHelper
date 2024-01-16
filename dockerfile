FROM python:3.7-alpine

ARG google_username

ADD * /
RUN pip3 install -r requirements.txt

CMD ["python3", "/HTTPHelper.py"]
