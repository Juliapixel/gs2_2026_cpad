FROM python:3.14-slim-trixie
COPY . .
RUN pip install -r requirements.txt
ENTRYPOINT [ "uvicorn", "api:app", "--host", "0.0.0.0" ]
