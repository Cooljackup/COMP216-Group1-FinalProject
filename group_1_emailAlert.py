# COMP216-402 - Final Project - Group 1

# Import necessary packages.
import smtplib
from email.mime.text import MIMEText
#python-dotenv is not a standard lib but throwing login credentials into the open is horrible practice.
from dotenv import load_dotenv
import os

load_dotenv()

class EmailAlert:
    def __init__(self):
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.sender_email = os.getenv("APP_EMAIL")
        self.sender_password = os.getenv("APP_PASSWORD")
        
    def send_alert(self, recipient_email, subject, message):
        try:
            # Creating the email.
            msg = MIMEText(message)
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            
            # Connecting to the SMTP server to send the email.
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
                
            print("email sent successfully.")
        except Exception:
            print("email failed to send.")
        
        
if __name__ == "__main__":
    email_alert = EmailAlert()
    #email_alert.send_alert("", "Test Subject", "Test message.")