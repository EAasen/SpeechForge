# Dockerfile
FROM python:3.11

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Install ffmpeg for pydub audio conversion support
RUN apt-get update && apt-get install -y ffmpeg

# Ensure the outputs directory exists
RUN mkdir -p /outputs

# Copy the application code
COPY src/ ./src

# Expose the application port
EXPOSE 8000

# Command to run the application
CMD ["python", "src/app.py"]
