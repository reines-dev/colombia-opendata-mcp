FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt mcp[cli]

# Copy application code
COPY mcp_server.py .

# Command to run the FastMCP server
ENTRYPOINT ["python", "mcp_server.py"]
