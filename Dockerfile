FROM python:3
WORKDIR /app
COPY requirements.txt requirements.txt
ENV PRODUCTS_SPREADSHEET_KEY="HERE GOES SOURCE SPREADSHEET KEY"
ENV ARCHIVE_SPREADSHEET_KEY="HERE GOES ARCHIVE KEY"
RUN pip install -r requirements.txt
COPY . .
CMD [ "python", "main.py" ]