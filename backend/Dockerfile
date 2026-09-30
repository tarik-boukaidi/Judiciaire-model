FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Install Python and Git
RUN apt-get update && apt-get install -y python3-pip python3-dev git && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Copy requirements and install
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy backend application files
COPY . /code/backend

# Copy the dataset from the parent's data folder into the container
COPY ../data /code/data

# Set working directory to backend to run main.py
WORKDIR /code/backend

# Run the application (using main.py instead of app.py based on your screenshot)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]