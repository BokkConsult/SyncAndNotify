# SyncAndNotify

## Getting Started

This repository contains scripts for managing and executing backup tasks across remote servers.

### Prerequisites

- Python 3.x
- Internet connectivity for heartbeat and email notifications

### Installation

```bash
git clone https://github.com/bokkconsult/syncandnotify.git
```

cd your-repository
```bash
cd syncandnotify
```
Make sure you have Python 3.x installed. Then, install the required dependencies using pip:
```bash
pip install -r requirements.txt
```

This will install all the necessary Python modules listed in requirements.txt. If you encounter any issues with dependencies, ensure your Python environment is correctly configured.

### Configuration

- **Initial Setup:** Run `python deploy.py` to initialize configurations and directories.
- **Backup Configuration:** Use `python backup.py --createconfig` to re-configure backup settings if needed after initial config.
- **Task Creation:** Employ `python create_task.py` to define new backup tasks.
- **Email Setup:** re-Configure email settings using `python mail_sender.py --createconfig` if needed after initial config.

### deploy.py

Script to initialize necessary configurations and directories for the backup system.

#### Usage:

Run `python deploy.py` to create configuration files (`backupconfig.json` and `mailconfig.json`), and necessary directories (`log` and `tasks`).

---

### backup.py

Main script responsible for executing backup and synchronization tasks.

#### Features:

- **Configuration Management:** Generates and manages configuration files (`backupconfig.json`) for synchronization tasks.
- **Multi-threaded Execution:** Supports concurrent execution of backup tasks using configurable thread count.
- **Error Handling:** Logs synchronization errors and sends email notifications using `mail_sender.py` in case of failures.
- **Heartbeat Signal:** Optionally sends heartbeat signals to monitor script health.

#### Usage:

1. **Configuration Setup:** Run `python backup.py --createconfig` to create or update `backupconfig.json`.
2. **Execution:** Simply execute `python backup.py` to start synchronization based on configured tasks in the `tasks` directory.

---

### create_task.py

Utility script for creating new backup tasks in the tasks directory.

#### Features:
- Interactively create new backup task configuration files (*.json) for use with `backup.py`.
- Facilitates the generation and uploading of SSH keys to the server from which data will be backed up.

#### Usage:
Run `python create_task.py` to interactively create a new backup task configuration file (*.json) in the tasks directory.


---

### mail_sender.py

Script for sending email notifications on backup task failures.

#### Features:

- **Email Configuration:** Uses `mailconfig.json` for SMTP server details and sender information.
- **Attachment Support:** Allows attaching log files (`*.log`) for detailed error reporting.

#### Usage:

1. **Configuration Setup:** Run `python mail_sender.py --createconfig` to create or update `mailconfig.json`.
2. **Sending Email:** Execute `python mail_sender.py -s "Subject" -t "Email text"` to send an email with an optional attachment (`-f`).

### Notes

- **Security:** Ensure secure handling of sensitive information such as SSH keys and email credentials.
- **Maintenance:** Regularly review logs (`log/*.log`) for task status and errors.
