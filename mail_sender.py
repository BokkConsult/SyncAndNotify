import json
import smtplib
from email.message import EmailMessage
import os
import sys
import re
import argparse

def read_config():
    config_file = 'mailconfig.json'
    if not os.path.exists(config_file):
        print("Mail configuration file not found. Please run the script with the -cc or --createconfig argument to create the configuration file.")
        sys.exit(0)
    with open(config_file, 'r') as file:
        config = json.load(file)
    return config

def create_config(filename):
    config = {}
    config['receiver_email'] = input("Enter receiver's email: ")
    while not validate_email(config['receiver_email']):
        print("Invalid email address. Try again.")
        config['receiver_email'] = input("Enter receiver's email: ")

    config['sender_email'] = input("Enter sender's email: ")
    while not validate_email(config['sender_email']):
        print("Invalid email address. Try again.")
        config['sender_email'] = input("Enter sender's email: ")

    config['password'] = input("Enter sender's email password: ")
    config['smtp_server'] = input("Enter SMTP server: ")
    config['smtp_port'] = input("Enter SMTP port (usually 465 for SSL): ")
    with open(filename, 'w') as file:
        json.dump(config, file, indent=4)

def validate_email(email):
    # Simple email validation using regular expressions
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email)

def send_email(subject, body, attachment, config, receiver_email=None):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = config['sender_email']
    msg['To'] = receiver_email if receiver_email else config['receiver_email']

    if body:
        msg.set_content(body)
    else:
        msg.set_content("There is no text in this email.")

    if attachment:
        if os.path.exists(attachment):
            with open(attachment, 'rb') as file:
                file_data = file.read()
                file_name = os.path.basename(attachment)
            msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)
        else:
            print("The specified file was not found.")

    try:
        with smtplib.SMTP_SSL(config['smtp_server'], config['smtp_port']) as server:
            server.login(config['sender_email'], config['password'])
            server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='Send an email with subject, text, and optional attachment.')
    parser.add_argument('-cc', '--createconfig', action='store_true', help="Create a new configuration file")
    parser.add_argument('-s', '--subject', required=not sys.stdin.isatty(), help='Subject of the email')
    parser.add_argument('-t', '--text', required=not sys.stdin.isatty(), help='Text of the email')
    parser.add_argument('-f', '--file', help='Attachment file (optional)')
    parser.add_argument('-r', '--receiver', help='Alternative receiver email (optional)')

    args = parser.parse_args()

    if args.createconfig:
        create_config('mailconfig.json')
        return

    if not os.path.exists('mailconfig.json'):
        print("Mail configuration file not found. Please run the script with the -cc or --createconfig argument to create the configuration file.")
        sys.exit(0)

    if not args.subject or not args.text:
        parser.print_help()
        sys.exit(1)

    config = read_config()
    send_email(args.subject, args.text, args.file, config, args.receiver)

if __name__ == "__main__":
    main()
