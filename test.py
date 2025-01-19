import os
import logging
import asyncio
from aiosmtpd.controller import Controller
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
import requests

# Configuration
TEST_SMTP_SERVER = "localhost"  # Test SMTP Server (own implementation)
TEST_SMTP_PORT = 2525           # Port for the test server
WILDFIRE_SMTP_PROXY_HOST = "localhost"  # The SMTP server to be tested
WILDFIRE_SMTP_PROXY_PORT = 1025          # Port of the server to be tested
WILDFIRE_TEST_FILE_URL = "http://wildfire.paloaltonetworks.com/publicapi/test/pe"
TEST_FILENAME = "wildfire-test-pe-file.exe"
SENDER_EMAIL = "test.sender@example.com"
RECIPIENT_EMAIL = "test.recipient@example.com"

# Logger setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class TestSMTPHandler:
    """Handler for the Test SMTP Server to capture emails."""
    def __init__(self):
        self.received_emails = []

    async def handle_DATA(self, server, session, envelope):
        """Handle incoming emails and store them for verification."""
        logger.info(f"Received email from {session.peer}")
        self.received_emails.append(envelope)
        return '250 OK'

def download_test_file():
    """Download the WildFire test file."""
    logger.info("Downloading WildFire test file...")
    response = requests.get(WILDFIRE_TEST_FILE_URL, stream=True)
    response.raise_for_status()
    with open(TEST_FILENAME, "wb") as f:
        f.write(response.content)
    logger.info(f"Test file downloaded: {TEST_FILENAME}")

def construct_test_email():
    """Construct a test email with the WildFire test file as an attachment."""
    logger.info("Constructing test email...")
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECIPIENT_EMAIL
    msg["Subject"] = "Test Email with Malicious Attachment"

    # Body of the email
    body = "This is a test email containing a malicious attachment."
    msg.attach(MIMEText(body, "plain"))

    # Attach the test file
    with open(TEST_FILENAME, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header(
        "Content-Disposition",
        f"attachment; filename={TEST_FILENAME}",
    )
    msg.attach(part)

    logger.info("Test email constructed successfully.")
    return msg

def send_email_to_target_server(msg):
    """Send the test email to the target SMTP server."""
    logger.info("Sending test email to target SMTP server...")
    with smtplib.SMTP(WILDFIRE_SMTP_PROXY_HOST, WILDFIRE_SMTP_PROXY_PORT) as server:
        server.sendmail(SENDER_EMAIL, RECIPIENT_EMAIL, msg.as_string())
    logger.info("Test email sent to target SMTP server.")

async def run_test():
    """Run the complete test process."""
    # Step 1: Download the test file
    download_test_file()

    # Step 2: Start the test SMTP server to capture the processed email
    handler = TestSMTPHandler()
    controller = Controller(handler, hostname=TEST_SMTP_SERVER, port=TEST_SMTP_PORT)
    controller.start()
    logger.info(f"Test SMTP server running on {TEST_SMTP_SERVER}:{TEST_SMTP_PORT}")

    try:
        # Step 3: Construct the test email
        msg = construct_test_email()

        # Step 4: Send the test email to the target SMTP server
        send_email_to_target_server(msg)

        # Step 5: Wait for the processed email
        logger.info("Waiting for the processed email...")
        await asyncio.sleep(10)  # Allow time for the target server to process the email

        # Step 6: Verify the result
        if handler.received_emails:
            logger.info("Processed email received.")
            for envelope in handler.received_emails:
                processed_msg = envelope.content.decode("utf-8")
                if "wildfire-test-pe-file.exe" in processed_msg:
                    logger.error("Test failed: Malicious attachment was not removed.")
                else:
                    logger.info("Test passed: Malicious attachment was removed.")
        else:
            logger.error("Test failed: No processed email received.")
    except Exception as e:
        logger.error(f"Error during test execution: {e}")
    finally:
        # Step 7: Cleanup
        controller.stop()
        if os.path.exists(TEST_FILENAME):
            os.remove(TEST_FILENAME)
            logger.info("Test file removed.")

if __name__ == "__main__":
    asyncio.run(run_test())
