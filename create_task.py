import os
import json
import subprocess

def prompt_for_data():
    server_address = input("Enter the server address: ")
    port = input("Enter the port number (press Enter for default port 22): ")
    username = input("Enter the username: ")
    private_key_name = input("Enter the name of the private key (without the file extension): ")
    remote_folder_path = input("Enter the remote (source) path to the folder: ")
    local_folder_path = input("Enter the local (destination) path to the folder: ")
    delete_remote_files = input("Do you want to delete remote files? (True/False): ").lower() in ("true", "1", "t", "y", "yes")

    if not port:
        port = 22
    
    return {
        "server_address": server_address,
        "port": int(port),
        "username": username,
        "private_key_name": private_key_name,
        "local_folder_path": local_folder_path,
        "remote_folder_path": remote_folder_path,
        "delete_remote_files": delete_remote_files
    }

def generate_ssh_key(private_key_name):
    key_path = os.path.expanduser(f"~/.ssh/{private_key_name}")
    subprocess.run(["ssh-keygen", "-t", "rsa", "-b", "4096", "-C", "", "-f", key_path])

def upload_ssh_key(server_address, port, username, private_key_name):
    key_path = os.path.expanduser(f"~/.ssh/{private_key_name}")
    subprocess.run(["ssh-copy-id", "-i", key_path, "-p", str(port), f"{username}@{server_address}"])

def main():
    config_data = prompt_for_data()
    generate_ssh_key(config_data["private_key_name"])
    upload_ssh_key(config_data["server_address"], config_data["port"], config_data["username"], config_data["private_key_name"])

    file_name = input("Enter the filename for the configuration file (press Enter to use the default name): ")
    if not file_name:
        file_name = f"{config_data['server_address']}_{config_data['username']}.json"
    else:
        file_name += ".json"
    
    tasks_dir = os.path.join(os.path.dirname(__file__), "tasks")
    if not os.path.exists(config_data["local_folder_path"]):
        os.makedirs(config_data["local_folder_path"])

    config_file_path = os.path.join(tasks_dir, file_name)

    with open(config_file_path, "w") as file:
        json.dump(config_data, file, indent=4)
    
    print(f"The configuration file has been created as '{file_name}', and the SSH key has been generated and uploaded.")

if __name__ == "__main__":
    main()
