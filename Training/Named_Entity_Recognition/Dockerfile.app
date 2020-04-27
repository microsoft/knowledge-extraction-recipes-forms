FROM ner_flask_app
ENV FLASK_PORT=5000
ENV FLASK_DEBUG_MODE=0
RUN mkdir /app
RUN mkdir /app/src
ADD app.py /app
COPY ./src/* /app/src/
EXPOSE $FLASK_PORT
CMD python /app/app.py