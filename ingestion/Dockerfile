FROM public.ecr.aws/lambda/python:3.12

COPY ingestion/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ingestion/*.py ./
COPY backend/app ./app

CMD ["lambda_handler.lambda_handler"]
