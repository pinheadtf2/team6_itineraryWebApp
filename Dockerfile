FROM Python
RUN pip install -r ./requirements.txt
COPY ./templates /home/itineraryplanner/templates
COPY ./static /home/itineraryplanner/templates
COPY main.py /home/itineraryplanner/main.py
EXPOSE 8080
CMD main.py