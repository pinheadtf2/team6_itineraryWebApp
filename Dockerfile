FROM Python
RUN pip install -r ./requirements.txt
COPY ./templates/index.html
COPY ./templates/index.css
COPY main.py
EXPOSE 8080