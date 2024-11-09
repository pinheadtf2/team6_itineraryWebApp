FROM Python
COPY ./templates to_docker/templates
COPY ./static to_docker/static
COPY requirements.txt to_docker/requirements.txt
COPY main.py to_docker/main.py
RUN pip install -r ./requirements.txt
EXPOSE 8080
CMD main.py