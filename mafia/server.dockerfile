FROM python:3.11
RUN pip install grpcio-tools
COPY server.py .
COPY utilities.py .
CMD ["python3", "server.py"]