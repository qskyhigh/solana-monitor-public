FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --root-user-action=ignore -r requirements.txt

CMD ["python", "-u",  "main.py"]