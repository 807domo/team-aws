FROM public.ecr.aws/lambda/python:3.13

# Install dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy application code
COPY main.py ${LAMBDA_TASK_ROOT}/
COPY app/ ${LAMBDA_TASK_ROOT}/app/
COPY migrations/ ${LAMBDA_TASK_ROOT}/migrations/

# Set the Lambda handler
CMD ["main.handler"]
