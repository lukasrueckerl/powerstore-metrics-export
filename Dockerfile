FROM python:latest

ADD code /code
RUN pip3 install -r /code/pip-requirements.txt

WORKDIR /code
ENV PYTHONPATH '/code/'

CMD ["python" , "/code/collector.py"]