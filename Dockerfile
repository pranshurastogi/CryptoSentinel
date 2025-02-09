# Use an official lightweight Python image.
FROM python:3.9-slim

# Prevent Python from writing .pyc files and enable unbuffered logging.
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory in the container.
WORKDIR /app

# Copy the requirements file into the container.
COPY requirements.txt .

# Upgrade pip and install dependencies.
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the rest of your application’s code.
COPY . .

# Expose the port the app runs on.
EXPOSE 8000

# Set the default command to run your server.
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
