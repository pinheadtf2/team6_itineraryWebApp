FROM python
COPY ./templates /team6_itinerarywebapp/templates
COPY ./static /team6_itinerarywebapp/static
COPY requirements.txt /
COPY app.py /team6_itinerarywebapp/app.py
RUN pip install -r requirements.txt
EXPOSE 5000
CMD ["python", "/team6_itinerarywebapp/app.py"]