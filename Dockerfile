FROM python:3.10.5

ENV PYTHONUNBUFFERED=1

RUN mkdir /code
WORKDIR /code

COPY requirements.txt /code/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . /code/

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]

EXPOSE 80
