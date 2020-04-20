FROM python:3.7-stretch

# Copying in source code
COPY app.py /opt/app-root/
COPY requirements.txt /opt/app-root/
COPY templates /opt/app-root/templates/
RUN chown -R 1001:0 /opt/app-root/
RUN pip install -r /opt/app-root/requirements.txt
USER 1001
WORKDIR /opt/app-root
CMD ["gunicorn", "--access-logfile", "-", "-b", "0.0.0.0:8000", "app:app"]
EXPOSE 8000