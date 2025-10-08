# Use lightweight Python 3 image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app.py .

# Create storage directory in container
RUN mkdir -p /storage

# Expose Flask port
EXPOSE 5001

# Run app
CMD ["python", "app.py"]
