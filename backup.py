import os
import json
import socket
import threading
import argparse
import subprocess
import urllib.request
import urllib.error
import time
import pexpect
from datetime import datetime
from queue import Queue

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "log")
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backupconfig.json")

def create_config():
    config = {
        "send_heartbeat": False,
        "heartbeat_link": "",
        "num_threads": 1,
    }
    
    send_heartbeat = input("Should a heartbeat signal be sent? (True/False): ")
    config["send_heartbeat"] = send_heartbeat.lower() in ("true", "1", "t", "y", "yes")
    config["heartbeat_link"] = input("Enter heartbeat link: ")
    num_threads_input = input("Enter number of threads (press Enter for default value 1): ")
    config["num_threads"] = int(num_threads_input) if num_threads_input else 1

    with open(CONFIG_FILE, 'w') as config_file:
        json.dump(config, config_file, indent=4)
    
    print(f"Configuration file created: {CONFIG_FILE}")
    return config

def load_config():
    with open(CONFIG_FILE, 'r') as config_file:
        return json.load(config_file)

def log_error(error_message, json_filename):
    log_file_path = os.path.join(LOG_DIR, "fail.log")

    with open(log_file_path, 'a') as log_file:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file.write(f"[{timestamp}] {error_message}\n")

def log_sync_result(username, json_filename, success, rsync_output, start_time):
    end_time = datetime.now()
    duration = end_time - start_time
    log_file_name = f"logfile_{json_filename}_{start_time.strftime('%Y%m%d_%H%M%S')}.log"
    log_file_path = os.path.join(LOG_DIR, log_file_name)

    with open(log_file_path, 'a') as log_file:
        log_file.write(rsync_output)
        log_file.write(f"\nStart time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        log_file.write(f"\nEnd time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        log_file.write(f"\nDuration: {duration}\n")

    return log_file_path

def send_heartbeat(config, success):
    if config["send_heartbeat"]:
        try:
            url = config["heartbeat_link"]
            response = urllib.request.urlopen(url, timeout=10)
            if response.getcode() == 200:
                print(f"Heartbeat signal sent successfully to {url}.")
            else:
                print(f"Error sending heartbeat signal to {url}: {response.getcode()}")
        except urllib.error.URLError as e:
            print(f"Error sending heartbeat signal to {url}: {e.reason}")
        except socket.timeout:
            print(f"Timeout sending heartbeat signal to {url}.")
        except Exception as e:
            print(f"Error sending heartbeat signal to {url}: {str(e)}")

def send_error_mail(error_message, json_filename, fail_log_path, start_time, end_time, username, server_address, port, remote_folder_path, local_folder_path):
    subject = f"Error during synchronization: {json_filename}"
    duration = end_time - start_time

    text = (f"An error occurred during synchronization.\n\n"
            f"Error message: {error_message}\n\n"
            f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Duration: {duration}\n\n"
            f"Username: {username}\n"
            f"Server address: {server_address}\n"
            f"Port: {port}\n"
            f"Remote folder: {remote_folder_path}\n"
            f"Local folder: {local_folder_path}\n\n"
            f"Log file: {fail_log_path}\n")

    mail_command = ["python", "mail_sender.py", "-s", subject, "-t", text]
    result = subprocess.run(mail_command, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Email sent successfully!")
    else:
        print(f"Failed to send email: {result.stderr}")

def synchronize_folders(server_address, port, username, private_key_path, remote_folder_path,
                        local_folder_path, json_filename, delete_remote_files, config):
    attempts = 0
    max_attempts = 5
    wait_time = 30
    success = False
    rsync_output = ""
    error_message = None
    start_time = datetime.now()
    log_file_name = f"logfile_{json_filename}_{start_time.strftime('%Y%m%d_%H%M%S')}.log"
    log_file_path = os.path.join(LOG_DIR, log_file_name)

    while attempts < max_attempts and not success:
        try:
            if not remote_folder_path or not local_folder_path:
                raise ValueError("Remote or local folder path is empty.")
            
            remote = f"{username}@{server_address}:{remote_folder_path}"
            ssh_command = f"ssh -i {private_key_path} -p {port}"
            rsync_command = f"rsync -avz --checksum --partial -e '{ssh_command}' {remote} {local_folder_path}"

            if delete_remote_files:
                rsync_command = rsync_command.replace("--partial", "--partial --delete")
            
            print("Running rsync command:", rsync_command)  # Debugging output

            child = pexpect.spawn(rsync_command)
            i = child.expect([pexpect.EOF, "password:", pexpect.TIMEOUT], timeout=None)  # Ingen timeout her
            
            if i == 1:  # Password prompt
                error_message = "Password prompt detected. Likely due to incorrect username or SSH key."
                print(error_message)
                log_error(error_message, json_filename)
                break  # Exit the loop and do not retry
            elif i == 0:  # EOF
                child.close()
                if child.exitstatus == 0:
                    success = True
                    rsync_output = child.before.decode()  # Capture rsync output
                    print(f"Files were synchronized between '{remote_folder_path}' and '{local_folder_path}'")
                else:
                    error_message = f"Error during synchronization with rsync: {child.before.decode()}"
                    print(error_message)
                    log_error(error_message, json_filename)
                    attempts += 1
                    if attempts < max_attempts:
                        print(f"Retrying in {wait_time} seconds... (Attempt {attempts} of {max_attempts})")
                        time.sleep(wait_time)
            elif i == 2:  # Timeout
                error_message = "Error: rsync command timed out."
                print(error_message)
                log_error(error_message, json_filename)
                attempts += 1
                if attempts < max_attempts:
                    print(f"Retrying in {wait_time} seconds... (Attempt {attempts} of {max_attempts})")
                    time.sleep(wait_time)
        except Exception as e:
            error_message = f"Error during synchronization between {server_address}:{port}: {str(e)}"
            print(error_message)
            log_error(error_message, json_filename)
            attempts += 1
            if attempts < max_attempts:
                print(f"Retrying in {wait_time} seconds... (Attempt {attempts} of {max_attempts})")
                time.sleep(wait_time)
    
    end_time = datetime.now()
    log_file_path = log_sync_result(username, json_filename, success, rsync_output, start_time)
    
    if not success:
        send_error_mail(error_message, json_filename, log_file_path, start_time, end_time, username, server_address, port, remote_folder_path, local_folder_path)
    
    return success

def worker(queue, config):
    while not queue.empty():
        task = queue.get()
        filename = task["filename"]
        server_address = task["server_address"]
        port = task["port"]
        username = task["username"]
        private_key_path = task["private_key_path"]
        remote_folder_path = task["remote_folder_path"]
        local_folder_path = task["local_folder_path"]
        delete_remote_files = task["delete_remote_files"]
        try:
            print(f"Starting synchronization for JSON file '{filename}'...")
            synchronize_folders(server_address, port, username, private_key_path, remote_folder_path, local_folder_path, filename, delete_remote_files, config)
            print(f"Synchronization finished for JSON file '{filename}'.\n")
        finally:
            queue.task_done()

def main():
    parser = argparse.ArgumentParser(description="Backup and synchronization script.")
    parser.add_argument('-cc', '--createconfig', action='store_true', help="Create a new configuration file")
    args = parser.parse_args()

    if args.createconfig:
        create_config()
        return

    if not os.path.exists(CONFIG_FILE):
        print(f"Configuration file '{CONFIG_FILE}' not found. Run the script with the -cc or --createconfig argument to create the configuration file.")
        return

    config = load_config()
    num_threads = config.get("num_threads")

    if num_threads is None:
        print("Number of threads is not defined in the configuration file. Add 'num_threads' and try again.")
        return

    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # Send heartbeat signal
    send_heartbeat(config, True)

    script_directory = os.path.dirname(os.path.abspath(__file__))
    tasks_directory = os.path.join(script_directory, "tasks")

    task_queue = Queue()

    for filename in os.listdir(tasks_directory):
        if filename.endswith(".json"):
            config_file_path = os.path.join(tasks_directory, filename)
            with open(config_file_path, 'r') as config_file:
                config_data = json.load(config_file)

                private_key_path = os.path.expanduser(f"~/.ssh/{config_data.get('private_key_name')}")

                task = {
                    "filename": filename,
                    "server_address": config_data.get("server_address"),
                    "port": config_data.get("port"),
                    "username": config_data.get("username"),
                    "private_key_path": private_key_path,
                    "remote_folder_path": config_data.get("remote_folder_path"),
                    "local_folder_path": config_data.get("local_folder_path"),
                    "delete_remote_files": config_data.get("delete_remote_files")
                }

                task_queue.put(task)

    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(target=worker, args=(task_queue, config))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
