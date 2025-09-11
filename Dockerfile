# Use Python 3.11 base image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy everything from local folder to container
COPY . .

# Install system dependencies and Python packages
RUN apt-get update && apt-get install -y libglib2.0-0 libsm6 libxext6 libxrender-dev && \
    pip install --no-cache-dir -r requirements.txt

# Expose Streamlit default port
EXPOSE 8501

# Run the Streamlit app
CMD ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]
