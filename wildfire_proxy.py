import os
from dotenv import load_dotenv
from celery import Celery
import redis
import logging
from email import policy
from email.parser import BytesParser
import smtplib
from pan.wfapi import PanWFapi
import time
from aiosmtpd.controller import Controller
from aiosmtpd.handlers import Message
import asyncio

# Load environment variables
load_dotenv()

# Configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'localhost')
SMTP_PORT = int(os.getenv('SMTP_PORT', 25))
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
WILDFIRE_API_KEY = os.getenv('WILDFIRE_API_KEY')
FORWARD_WASHED_MAIL = os.getenv('FORWARD_WASHED_MAIL', 'False').lower() in ['true', '1', 'yes']

if not WILDFIRE_API_KEY:
  raise EnvironmentError("WildFire API Key is required but not set.")

# Initialize services
celery_app = Celery('wildfire_proxy', broker=f'redis://{REDIS_HOST}:6379/0')
redis_client = redis.StrictRedis(host=REDIS_HOST, port=6379, db=0)
wfapi = PanWFapi(api_key=WILDFIRE_API_KEY)

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Forward email
def forward_email(raw_email):
  """Forward an email to its intended recipient."""
  try:
    msg = BytesParser(policy=policy.default).parsebytes(raw_email)
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
      server.send_message(msg)
    logger.info("Email successfully forwarded.")
  except Exception as e:
    logger.error(f"Error forwarding email: {e}")

# Forward cleaned email
def forward_cleaned_email(original_msg, clean_parts):
    """Forward the cleaned email with only non-malicious attachments."""
    cleaned_msg = original_msg.clone()

    # Remove all parts and add back only the clean ones
    del cleaned_msg._payload
    cleaned_msg.set_payload(clean_parts)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.send_message(cleaned_msg)
        logger.info("Cleaned email successfully forwarded.")
    except Exception as e:
        logger.error(f"Error forwarding cleaned email: {e}")

# Analyze email attachments
@celery_app.task
def analyze_email(mail_id, raw_email):
  """Analyze email attachments using WildFire."""
  msg = BytesParser(policy=policy.default).parsebytes(raw_email)
  attachments = [part.get_payload(decode=True) for part in msg.iter_attachments()]

  for attachment in attachments:
    try:
      # Upload file to WildFire
      wfapi.upload(file=attachment)
      if wfapi.status != 'success':
        logger.error(f"Error uploading file: {wfapi.response}")
        return

      file_hash = wfapi.file_hash
      redis_client.set(mail_id, raw_email)

      # Poll WildFire for results
      for _ in range(10):  # 10 retries with a 30-second interval
        time.sleep(30)
        wfapi.report(file_hash=file_hash)
        if wfapi.status == 'success':
          report = wfapi.report
          if report.get("status") == "completed":
            handle_analysis_result(mail_id, report.get("verdict", "unknown"))
            return
      logger.warning(f"Timeout waiting for analysis result for file {file_hash}")
    except Exception as e:
      logger.error(f"Error during WildFire analysis: {e}")

# Process analysis result
def handle_analysis_result(mail_id, report):
    """Handle the result of the WildFire analysis."""
    raw_email = redis_client.get(mail_id)
    if not raw_email:
        logger.warning(f"No email found for Mail ID: {mail_id}")
        return

    msg = BytesParser(policy=policy.default).parsebytes(raw_email)

    # Check and remove malicious attachments
    malicious_attachments = []
    clean_parts = []

    for part in msg.iter_parts():
        if part.get_content_disposition() == 'attachment':
            file_hash = hash(part.get_payload(decode=True))
            if report.get(file_hash) == "malicious":
                malicious_attachments.append(part.get_filename())
            else:
                clean_parts.append(part)
        else:
            clean_parts.append(part)

    if malicious_attachments:
        logger.warning(f"Malicious attachments detected: {malicious_attachments}.")
        if FORWARD_WASHED_MAIL:
            logger.info("Forwarding cleaned email without malicious attachments.")
            forward_cleaned_email(msg, clean_parts)
    else:
        logger.info("All attachments are clean. Forwarding the email.")
        forward_email(raw_email)

    redis_client.delete(mail_id)

# Custom SMTP Handler
class CustomSMTPHandler(Message):
  async def handle_message(self, message):
    """Handle incoming email messages."""
    raw_email = message.as_bytes()
    mail_id = str(hash(raw_email))
    analyze_email.delay(mail_id, raw_email)
    logger.info(f"Email received and queued for analysis, Mail ID: {mail_id}")

# Main Entry Point
async def main():
  handler = CustomSMTPHandler()
  controller = Controller(handler, hostname=SMTP_SERVER, port=SMTP_PORT)
  controller.start()
  logger.info(f"SMTP server running on {SMTP_SERVER}:{SMTP_PORT}")
  try:
    while True:
      await asyncio.sleep(1)
  except KeyboardInterrupt:
    logger.info("SMTP server stopped.")
  finally:
    controller.stop()

if __name__ == '__main__':
  try:
    asyncio.run(main())
  except RuntimeError as e:
    logger.error(f"Runtime error: {e}")
