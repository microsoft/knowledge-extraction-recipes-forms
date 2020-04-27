FROM base_image
ENV FLASK_DEBUG_MODE=0
RUN mkdir /app
RUN mkdir /app/src
ADD app.py /app
COPY ./src/* /app/src/
WORKDIR /app
EXPOSE 5000
ENTRYPOINT ["python3"]
CMD ["app.py"]