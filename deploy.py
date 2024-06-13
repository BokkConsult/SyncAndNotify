import json
import os
import re

def prompt_user(prompt, validator=None):
    while True:
        value = input(prompt)
        if validator:
            if validator(value):
                return value
            else:
                print("Invalid input. Please try again.")
        else:
            return value

def validate_boolean(value):
    return value.lower() in ['true', 'false']

def validate_integer(value):
    return value.isdigit()

def validate_email(value):
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, value) is not None

def create_backup_config():
    backup_config = {}
    backup_config['send_heartbeat'] = prompt_user("Send heartbeat (true/false): ", validate_boolean).lower() == 'true'
    backup_config['heartbeat_link'] = prompt_user("Enter heartbeat link: ")
    backup_config['num_threads'] = int(prompt_user("Enter number of threads: ", validate_integer))
    
    with open('backupconfig.json', 'w') as file:
        json.dump(backup_config, file, indent=4)
    print("Created backupconfig.json")

def create_mail_config():
    mail_config = {}
    mail_config['receiver_email'] = prompt_user("Enter receiver's email: ", validate_email)
    mail_config['sender_email'] = prompt_user("Enter sender's email: ", validate_email)
    mail_config['password'] = prompt_user("Enter sender's email password: ")
    mail_config['smtp_server'] = prompt_user("Enter SMTP server: ")
    mail_config['smtp_port'] = prompt_user("Enter SMTP port: ", validate_integer)
    
    with open('mailconfig.json', 'w') as file:
        json.dump(mail_config, file, indent=4)
    print("Created mailconfig.json")

def create_directories():
    os.makedirs('log', exist_ok=True)
    os.makedirs('tasks', exist_ok=True)
    print("Created directories 'log' and 'tasks'")

def main():
    create_backup_config()
    create_mail_config()
    create_directories()

if __name__ == "__main__":
    main()
