# Use an official lightweight Python image.
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependency files to the working directory
COPY pyproject.toml uv.lock ./

# Install project dependencies
# We use uv for speed, but pip would also work.
RUN pip install uv
RUN uv pip install --system .

# Copy the rest of the application's source code from the host to the image's filesystem.
COPY src/ ./src/

# Command to run the application
CMD ["python", "src/mcp_server/server.py"]
