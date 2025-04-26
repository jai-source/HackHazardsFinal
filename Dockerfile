FROM python:3.10-slim-bullseye

# Install ffmpeg and other system dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port your app runs on (optional for FastAPI/Flask apps)
EXPOSE 10000

# Command to run your Python app
CMD ["python", "webapp/hackhackards.py"]
