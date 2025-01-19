# wildfire-smtp-proxy

![Build, Test, and Push Docker Image](https://github.com/t11z/wildfire-smtp-proxy/actions/workflows/docker-test-and-push.yml/badge.svg)

A lightweight SMTP proxy that scans mails for threats against the Palo Alto Networks WildFire API.

## Features

- **SMTP Proxy**: Acts as an intermediary SMTP server to process incoming emails.
- **Threat Detection**: Leverages the Palo Alto Networks WildFire API to scan email attachments for potential threats.
- **Attachment Cleaning**: Optionally removes malicious attachments and forwards the cleaned email to the intended recipient.
- **Dockerized Deployment**: Easily deployable using Docker.
- **Continuous Integration**: Fully integrated CI/CD pipeline with automated testing and Docker image publishing.

---

## Requirements

1. Python 3.9 or higher
2. Docker
3. Palo Alto Networks WildFire API Key

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/t11z/wildfire-smtp-proxy.git
   cd wildfire-smtp-proxy
   ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Set up your .env file:
    ```bash
    cp .env.example .env
    ```

4. Update the .env file with your configuration:
    ```bash
    SMTP_SERVER=localhost
    SMTP_PORT=1025
    REDIS_HOST=localhost
    WILDFIRE_API_KEY=your_api_key
    FORWARD_WASHED_MAIL=True
    ```

## Running the Project

1. Run Locally
    ```bash
    python3 wildfire_proxy.py
    ```

2. Run with Docker

    ##### Build the Docker Image
    ```bash
    docker build -t wildfire-smtp-proxy .
    ```

    ##### Run the Container
    ```bash
    docker run -p 1025:1025 wildfire-smtp-proxy
    ```

## Testing
A test script (*test_wrapper.py*) is included to verify the functionality of the proxy.

Run the test script:
```bash
python3 test_wrapper.py
```
The script downloads a malicious test sample from Palo Alto Networks WildFire API, sends it through the SMTP proxy, and verifies the results.

# Contributing
Contributions are welcome! Please fork the repository, make changes, and submit a pull request.

# License
This project is licensed under the MIT License. See the LICENSE file for details.