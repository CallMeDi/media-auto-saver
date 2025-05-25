# Use an official Python runtime as a parent image
FROM python:3.13.3-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app_code

# Copy requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire backend application code (from the build context, which is `backend/`)
# into the WORKDIR (`/app_code`) in the container.
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# This assumes your FastAPI app instance is named `app` in `backend/app/main.py`
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
