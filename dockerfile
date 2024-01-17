FROM python:3.7-alpine

ARG google_username
ADD * /
RUN pip3 install -r requirements.txt
RUN apk add --update curl whois
CMD ["python3", "/HTTPHelper.py"]
