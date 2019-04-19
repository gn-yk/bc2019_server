FROM python:3.6.3
ADD . /code
WORKDIR /code
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]