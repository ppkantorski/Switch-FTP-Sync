import sys
import ftplib
import os
import time
import configparser
from datetime import datetime
from PyQt5 import QtWidgets, QtGui, QtCore
import threading
import webbrowser
import shutil
import tempfile
import uuid
import requests

# Import win10toast for Windows notifications
if sys.platform == 'win32':
    from winotify import Notification, audio
elif sys.platform == 'darwin':  # macOS specific imports
    from Foundation import NSObject, NSUserNotification, NSUserNotificationCenter, NSUserNotificationDefaultSoundName

    class NotificationDelegate(NSObject):
        def userNotificationCenter_didActivateNotification_(self, center, notification):
            userInfo = notification.userInfo()
            log_message(f"Notification clicked. User info: {userInfo}")
            if userInfo:
                file_path = userInfo.get('file_path')
                log_message(f"Attempting to open file path: {file_path}")
                if file_path:
                    os.system(f'open "{file_path}"')
else:
    from plyer import notification


TITLE = "Switch FTP Sync"
VERSION = "0.1.7"
AUTHOR = "ppkantorski"


# Determine the directory where the script is located
if getattr(sys, 'frozen', False):
    script_dir = sys._MEIPASS
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))

# Use the standard temporary directory for the platform
temp_download_dir = os.path.join(tempfile.gettempdir(), "switch_ftp_sync")
if os.path.exists(temp_download_dir):
    shutil.rmtree(temp_download_dir)


# Path to the config.ini file
config_path = os.path.join(script_dir, 'config.ini')

# Ensure the config.ini file exists, create a default one if not
if not os.path.exists(config_path):
    default_config = """[FTP]
server = X.X.X.X
port = 5000
user = root
pass = 

[Screenshots]
dt_format = %Y-%m-%d_%H-%M-%S
output_path = 
sync_screenshots = True

[File Sync]
server_path_1 = 
output_path_1 =
sync_files_1 = False

server_path_2 = 
output_path_2 =
sync_files_2 = False

server_path_3 =
output_path_3 =
sync_files_3 = False

server_path_4 =
output_path_4 =
sync_files_4 = False

server_path_5 =
output_path_5 =
sync_files_5 = False

[Settings]
check_rate = 15
auto_start = False
"""
    with open(config_path, 'w') as config_file:
        config_file.write(default_config)

# Read configuration from config.ini
config = configparser.ConfigParser(interpolation=None)  # Disable interpolation
config.read(config_path)

# FTP server details
SERVER = config.get('FTP', 'server').strip('"')
PORT = config.getint('FTP', 'port')
USER = config.get('FTP', 'user').strip('"')
PASS = config.get('FTP', 'pass').strip('"')

# Screenshots settings
SCREENSHOTS_PATH = config.get('Screenshots', 'output_path').strip('"')
DT_FORMAT = config.get('Screenshots', 'dt_format')
SYNC_SCREENSHOTS = config.getboolean('Screenshots', 'sync_screenshots')

# File Sync paths
file_sync_paths = []
for i in range(1, 6):
    server_path = config.get('File Sync', f'server_path_{i}', fallback='').strip('"')
    output_path = config.get('File Sync', f'output_path_{i}', fallback='').strip('"')
    sync_files = config.getboolean('File Sync', f'sync_files_{i}', fallback=False)
    if server_path and output_path and sync_files:
        file_sync_paths.append((server_path, output_path))

# Settings
CHECK_RATE = int(config.get('Settings', 'check_rate'))
AUTO_START = config.getboolean('Settings', 'auto_start')

running = False
stop_event = threading.Event()

def log_message(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

# Explicitly keep a reference to the delegate to prevent garbage collection
notification_delegate = None

def notify_file(file_name, local_file_path="", type="new"):
    global notification_delegate
    is_screenshot = local_file_path.startswith(SCREENSHOTS_PATH)
    file_extension = os.path.splitext(file_name)[1].lower()

    message = ""

    if type == "new":
        if is_screenshot:
            if file_extension == ".mp4":
                message = f"New video {file_name} has been added."
            elif file_extension == ".jpg" or file_extension == ".bmp" or file_extension == ".png":
                message = f"New image {file_name} has been added."
            else:
                message = f"New file {file_name} has been added."
        else:
            message = f"New file {file_name} has been added."
    else:
        if is_screenshot:
            if file_extension == ".mp4":
                message = f"Video {file_name} has been updated."
            elif file_extension == ".jpg" or file_extension == ".bmp" or file_extension == ".png":
                message = f"Image {file_name} has been updated."
            else:
                message = f"File {file_name} has been updated."
        else:
            message = f"File {file_name} has been updated."

    if sys.platform == 'darwin':  # macOS
        notification = NSUserNotification.alloc().init()
        notification.setTitle_(TITLE)
        notification.setInformativeText_(message)
        notification.setSoundName_(NSUserNotificationDefaultSoundName)
        if is_screenshot:
            notification.setUserInfo_({'file_path': local_file_path})
        else:
            notification.setUserInfo_({'file_path': os.path.dirname(local_file_path)})

        center = NSUserNotificationCenter.defaultUserNotificationCenter()
        notification_delegate = NotificationDelegate.alloc().init()
        center.setDelegate_(notification_delegate)
        log_message("Delegate set for notification center")
        center.deliverNotification_(notification)
        log_message(f"Notification sent for new file: {file_name} with path: {local_file_path}")
    elif sys.platform == 'win32':  # Windows
        try:
            icon_path = os.path.join(script_dir, "icon.ico")
            launch_path = local_file_path if is_screenshot else os.path.dirname(local_file_path)
            toast = Notification(app_id=TITLE,
                                 title=TITLE,
                                 msg=message,
                                 icon=icon_path)
            toast.set_audio(audio.Default, loop=False)
            toast.add_actions(label="Open File", launch=launch_path)
            toast.show()
            log_message(f"Notification sent for new file: {file_name}")
        except Exception as e:
            log_message(f"Failed to send notification: {e}")
    else:
        try:
            notification.notify(
                title=TITLE,
                message=message,
                app_name=TITLE,
                app_icon=os.path.join(script_dir, "icon.png"),  # path to your app icon
                timeout=10  # Notification will disappear after 10 seconds
            )
            log_message(f"Notification sent for new file: {file_name}")
        except Exception as e:
            log_message(f"Failed to send notification: {e}")

def connect_ftp():
    try:
        ftp = ftplib.FTP()
        ftp.connect(SERVER, PORT, timeout=10)  # Set timeout for connection
        ftp.login(USER, PASS)
        # Switch to passive mode
        ftp.set_pasv(True)
        log_message(f"FTP Connection to {SERVER} successful.")
        return ftp
    except Exception as e:
        log_message(f"Error connecting to FTP server: {e}")
        return None

def list_files(ftp, path):
    file_list = []
    try:
        ftp.cwd(path)
        files = ftp.nlst()
        for file in files:
            full_path = os.path.join(path, file)
            try:
                ftp.cwd(full_path)
                file_list.extend(list_files(ftp, full_path))
                ftp.cwd('..')
            except ftplib.error_perm:
                file_list.append(full_path)
    except ftplib.all_errors as e:
        log_message(f"Error listing files in {path}: {e}")
    return file_list



def download_file(ftp, remote_file, local_file):
    
    # Ensure the switch_ftp_sync subdirectory exists
    os.makedirs(temp_download_dir, exist_ok=True)

    try:
        # Generate a unique temporary file path within the switch_ftp_sync subdirectory
        unique_filename = f"{uuid.uuid4()}.tmp"
        temp_file_path = os.path.join(temp_download_dir, unique_filename)
        
        # Ensure the local directory exists
        local_dir = os.path.dirname(local_file)
        os.makedirs(local_dir, exist_ok=True)

        # Download the file to the temporary path
        with open(temp_file_path, 'wb') as f:
            ftp.retrbinary(f'RETR {remote_file}', f.write)

        # Move the file from the temporary path to the final local path
        shutil.move(temp_file_path, local_file)
        # log_message(f"Downloaded {remote_file} to {local_file} via temporary path {temp_file_path}")
    except ftplib.all_errors as e:
        log_message(f"Error downloading file {remote_file} to {local_file}: {e}")
    finally:
        # No need to explicitly remove the temporary directory since we are using a shared temp directory
        pass


def get_file_timestamp(ftp, file_path):
    try:
        response = ftp.sendcmd(f"MDTM {file_path}")[4:].strip()
        if response.isdigit():
            return datetime.strptime(response, "%Y%m%d%H%M%S")
        else:
            log_message(f"Unexpected MDTM response for file {file_path}: {response}")
            return None
    except Exception as e:
        return None
    #except ftplib.all_errors as e:
    #    log_message(f"Error getting timestamp for file {file_path}: {e}")
    #    return None


def format_filename(file_name, dt_format):
    base_name, extension = os.path.splitext(file_name)
    
    # Check if the file extension is .bmp and set the format accordingly
    default_format = '%Y%m%d%H%M%S%f'
    if extension.lower() == '.bmp':
        default_format = "%Y-%m-%d_%H-%M-%S"
        
    try:
        timestamp_str = base_name.split('-')[0]
        timestamp_dt = datetime.strptime(timestamp_str, default_format)
        formatted_str = timestamp_dt.strftime(dt_format)
        return formatted_str
    except ValueError:
        return base_name

def sync_screenshots(ftp):
    time_in = time.time()
    screenshot_paths = ["/emuMMC/RAW1/Nintendo/Album/", "/Nintendo/Album/"]
    for path in screenshot_paths:
        log_message(f"Syncing {path} to {SCREENSHOTS_PATH}")
        current_files = list_files(ftp, path)
        for file in current_files:
            file_name = os.path.basename(file)
            formatted_name = format_filename(file_name, DT_FORMAT) + os.path.splitext(file_name)[1]
            local_file_path = os.path.join(SCREENSHOTS_PATH, formatted_name)
            remote_timestamp = get_file_timestamp(ftp, file)
            if remote_timestamp:
                local_timestamp = remote_timestamp
                if (os.path.exists(local_file_path)):
                    local_timestamp = datetime.fromtimestamp(os.path.getmtime(local_file_path))
                if not os.path.exists(local_file_path) or remote_timestamp > local_timestamp:
                    download_file(ftp, file, local_file_path)
                    os.utime(local_file_path, (remote_timestamp.timestamp(), remote_timestamp.timestamp()))
                    log_message(f"Downloaded: {file}")
                    if remote_timestamp > local_timestamp:
                        notify_file(formatted_name, local_file_path, "update")
                    else:
                        notify_file(formatted_name, local_file_path, "new")
    time_out = time.time()-time_in
    log_message(f"Screenshots sync loop time: {time_out}")

def sync_files(ftp, server_path, output_path):
    time_in = time.time()
    log_message(f"Syncing {server_path} to {output_path}")

    def process_files(ftp, server_path, output_path):
        try:
            ftp.cwd(server_path)
            files = ftp.nlst()

            for file in files:
                full_path = os.path.join(server_path, file)
                relative_path = os.path.relpath(full_path, server_path)
                local_file_path = os.path.join(output_path, relative_path)

                try:
                    ftp.cwd(full_path)
                    process_files(ftp, full_path, local_file_path)
                    ftp.cwd('..')
                except ftplib.error_perm:
                    remote_timestamp = get_file_timestamp(ftp, full_path)
                    if remote_timestamp:
                        local_dir = os.path.dirname(local_file_path)
                        if not os.path.exists(local_dir):
                            os.makedirs(local_dir, exist_ok=True)

                        local_timestamp = remote_timestamp
                        if (os.path.exists(local_file_path)):
                            local_timestamp = datetime.fromtimestamp(os.path.getmtime(local_file_path))
                        if not os.path.exists(local_file_path) or remote_timestamp > local_timestamp:
                            log_message(f"Downloading {full_path} to {local_file_path}")
                            download_file(ftp, full_path, local_file_path)
                            os.utime(local_file_path, (remote_timestamp.timestamp(), remote_timestamp.timestamp()))
                            log_message(f"Downloaded: {full_path}")
                            if remote_timestamp > local_timestamp:
                                notify_file(os.path.basename(full_path), local_file_path, "update")
                            else:
                                notify_file(os.path.basename(full_path), local_file_path, "new")
                    else:
                        log_message(f"Failed to get timestamp for {full_path}")
        except ftplib.all_errors as e:
            log_message(f"Error listing files in {server_path}: {e}")

    process_files(ftp, server_path, output_path)

    time_out = time.time()-time_in
    log_message(f"{server_path} sync loop time: {time_out}")

def reload_config():
    global SERVER, PORT, USER, PASS, SCREENSHOTS_PATH, DT_FORMAT, SYNC_SCREENSHOTS, file_sync_paths, CHECK_RATE, AUTO_START
    config.read(config_path)
    SERVER = config.get('FTP', 'server').strip('"')
    PORT = config.getint('FTP', 'port')
    USER = config.get('FTP', 'user').strip('"')
    PASS = config.get('FTP', 'pass').strip('"')
    
    # Screenshots settings
    SCREENSHOTS_PATH = config.get('Screenshots', 'output_path').strip('"')
    DT_FORMAT = config.get('Screenshots', 'dt_format')
    SYNC_SCREENSHOTS = config.get('Screenshots', 'sync_screenshots')
    
    # Update sync paths
    file_sync_paths = []
    for i in range(1, 6):
        server_path = config.get('File Sync', f'server_path_{i}', fallback='').strip('"')
        output_path = config.get('File Sync', f'output_path_{i}', fallback='').strip('"')
        sync_files = config.get('File Sync', f'sync_files_{i}', fallback=False)
        if server_path and output_path and sync_files:
            file_sync_paths.append((server_path, output_path))

    CHECK_RATE = int(config.get('Settings', 'check_rate'))
    AUTO_START = config.getboolean('Settings', 'auto_start')

class ConfigDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Switch FTP Sync")
        self.layout = QtWidgets.QFormLayout(self)
        self.setFixedWidth(480)

        self.config_items = {}
        self.browse_buttons = {}  # To keep track of browse buttons and their corresponding line edits
        for section in config.sections():
            if section != 'DEFAULT':
                if section != 'FTP':
                    self.layout.addRow(QtWidgets.QLabel(""))
                label = QtWidgets.QLabel(f"{section}")
                font = label.font()
                font.setBold(True)
                label.setFont(font)
                self.layout.addRow(label)
                self.layout.addRow(QtWidgets.QFrame())
            for key, value in config.items(section):
                item_label = key
                if key.startswith('sync_files') or key == 'sync_screenshots' or key == "auto_start":
                    continue  # Skip these keys for now
                line_edit = QtWidgets.QLineEdit(value.strip('"'))
                line_edit.setAlignment(QtCore.Qt.AlignRight)  # Align text to the right
                self.config_items[f"{section}.{key}"] = line_edit

                if key.startswith('output_path') or key == 'output_path':
                    browse_button = QtWidgets.QPushButton('\uD83D\uDCC2')  # Folder icon
                    self.browse_buttons[browse_button] = line_edit  # Associate browse button with line edit
                    browse_button.clicked.connect(self.handle_browse_button_clicked)
                    hbox = QtWidgets.QHBoxLayout()
                    line_edit.setFixedWidth(240)  # Adjust the width of the input box
                    hbox.addWidget(line_edit)
                    hbox.addWidget(browse_button)
                    checkbox = QtWidgets.QCheckBox()
                    if key == 'output_path':
                        checkbox.setChecked(config.getboolean(section, 'sync_screenshots'))
                        self.config_items[f"{section}.sync_screenshots"] = checkbox
                    else:
                        sync_key = key.replace('output_path', 'sync_files')
                        checkbox.setChecked(config.getboolean(section, sync_key))
                        self.config_items[f"{section}.{sync_key}"] = checkbox
                    hbox.addWidget(checkbox)
                    self.layout.addRow(QtWidgets.QLabel(f"  {item_label} "), hbox)
                else:
                    line_edit.setFixedWidth(300)  # Adjust the width of the input box
                    self.layout.addRow(QtWidgets.QLabel(f"  {item_label} "), line_edit)  # Added indent for key name

        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.update_config)
        self.button_box.rejected.connect(self.reject)
        self.layout.addRow(self.button_box)

    def handle_browse_button_clicked(self):
        sender = self.sender()
        if sender in self.browse_buttons:
            line_edit = self.browse_buttons[sender]
            self.select_output_directory(line_edit)

    def select_output_directory(self, line_edit):
        dir_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            if not dir_path.endswith('/'):
                dir_path += '/'
            line_edit.setText(dir_path)

    def update_config(self):
        try:
            for item_label, widget in self.config_items.items():
                section, key = item_label.split('.')
                if isinstance(widget, QtWidgets.QLineEdit):
                    config.set(section, key, widget.text())
                elif isinstance(widget, QtWidgets.QCheckBox):
                    config.set(section, key, str(widget.isChecked()))
            with open(config_path, 'w') as configfile:
                config.write(configfile)
            QtWidgets.QMessageBox.information(self, "Success", "Configuration updated successfully.")
            reload_config()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to update configuration: {e}")
        self.accept()  # Close the dialog




class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Switch FTP Sync")
        self.layout = QtWidgets.QVBoxLayout(self)
        self.setFixedSize(360, 250)

        icon_path = os.path.join(script_dir, "icon.png")
        if os.path.exists(icon_path):
            icon_label = QtWidgets.QLabel()
            pixmap = QtGui.QPixmap(icon_path).scaled(80, 80, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(QtCore.Qt.AlignCenter)
            self.layout.addWidget(icon_label)

        title_label = QtWidgets.QLabel(f"{TITLE} v{VERSION}")
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        font = title_label.font()
        font.setPointSize(14)
        font.setBold(True)
        title_label.setFont(font)
        self.layout.addWidget(title_label)

        description_label = QtWidgets.QLabel("Nintendo Switch FTP data-syncing utility.")
        description_label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(description_label)

        author_label = QtWidgets.QLabel(f"Created by {AUTHOR}")
        author_label.setAlignment(QtCore.Qt.AlignCenter)
        self.layout.addWidget(author_label)

        github_button = QtWidgets.QPushButton("View on GitHub")
        github_button.setFixedWidth(120)  # Set fixed width for the button
        github_button.clicked.connect(lambda: webbrowser.open("https://github.com/ppkantorski/Switch-FTP-Sync"))

        check_updates_button = QtWidgets.QPushButton("Check for Updates")
        check_updates_button.setFixedWidth(140)  # Set fixed width for the button
        check_updates_button.clicked.connect(self.check_for_updates)

        ok_button = QtWidgets.QPushButton("OK")
        ok_button.setFixedWidth(60)  # Set fixed width for the button
        ok_button.clicked.connect(self.accept)

        # Create a horizontal layout for the buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(github_button)
        button_layout.addWidget(check_updates_button)
        button_layout.addWidget(ok_button)

        # Add the horizontal layout to the main layout
        self.layout.addLayout(button_layout)

        self.layout.setAlignment(github_button, QtCore.Qt.AlignCenter)
        self.layout.setAlignment(check_updates_button, QtCore.Qt.AlignCenter)
        self.layout.setAlignment(ok_button, QtCore.Qt.AlignCenter)

    def check_for_updates(self):
        try:
            response = requests.get("https://api.github.com/repos/ppkantorski/Switch-FTP-Sync/releases/latest")
            response.raise_for_status()  # Raise an exception for HTTP errors
            latest_release = response.json()
            latest_version = latest_release["tag_name"].replace("v", "")
    
            # Split versions into parts and compare each part
            latest_version_parts = [int(part) for part in latest_version.split('.')]
            current_version_parts = [int(part) for part in VERSION.split('.')]
    
            if latest_version_parts > current_version_parts:
                QtWidgets.QMessageBox.information(self, "Update Available", 
                                                  f"\nA new version v{latest_version} is available.\nYou are currently using v{VERSION}.")
            else:
                QtWidgets.QMessageBox.information(self, "Up to Date", 
                                                  "\nYou are using the latest version.")
        except requests.RequestException as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"\nFailed to check for updates: {e}")
        except ValueError as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"\nFailed to parse version information: {e}")
    



class SystemTrayApp(QtWidgets.QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super(SystemTrayApp, self).__init__(icon, parent)
        self.setToolTip(f"{TITLE} v{VERSION}")
        self.parent = parent
        self.menu = QtWidgets.QMenu(parent)

        self.start_action = self.menu.addAction("\u25B6 Start Data Sync")
        self.auto_start_action = self.menu.addAction("    Auto-Start")
        self.menu.addSeparator()
        self.config_action = self.menu.addAction("    Configure...")
        self.menu.addSeparator()
        self.about_action = self.menu.addAction("    About Switch FTP Sync    ")
        self.menu.addSeparator()
        self.restart_action = self.menu.addAction("    Restart")  # Add Restart action
        self.exit_action = self.menu.addAction("    Quit")

        self.start_action.triggered.connect(self.toggle_capture)
        self.auto_start_action.triggered.connect(self.toggle_auto_start)
        self.config_action.triggered.connect(self.configure_config)
        self.about_action.triggered.connect(self.show_about_dialog)
        self.restart_action.triggered.connect(self.restart_app)  # Connect Restart action to method
        self.exit_action.triggered.connect(self.exit_app)

        self.setContextMenu(self.menu)
        self.update_auto_start_action()

        if AUTO_START:
            self.start_capture()

    def toggle_capture(self):
        global running
        if running:
            self.stop_capture()
        else:
            self.start_capture()

    def start_capture(self):
        global running
        if not running:
            running = True
            stop_event.clear()
            threading.Thread(target=self.sync_data, daemon=True).start()
            self.start_action.setText("\u25A0 Stop Data Sync")
        else:
            log_message("Switch FTP Sync is already running.")

    def stop_capture(self):
        global running
        if running:
            running = False
            stop_event.set()
            self.start_action.setText("\u25B6 Start Data Sync")
        else:
            log_message("Switch FTP Sync is not running.")

    def sync_data(self):
        global running
    
        def sync_screenshots_thread():
            while running and not stop_event.is_set():
                start_time = time.time()
                ftp = None
                try:
                    ftp = connect_ftp()
                    if ftp:
                        sync_screenshots(ftp)
                except ftplib.all_errors as e:
                    log_message(f"Error during sync operation: {e}")
                finally:
                    if ftp:
                        try:
                            ftp.quit()
                        except ftplib.all_errors as e:
                            log_message(f"Error quitting FTP: {e}")
                elapsed_time = time.time() - start_time
                sleep_time = max(0, CHECK_RATE - elapsed_time)
                time.sleep(sleep_time)
    
        def sync_single_file_path(server_path, output_path):
            while running and not stop_event.is_set():
                start_time = time.time()
                ftp = None
                try:
                    ftp = connect_ftp()
                    if ftp:
                        sync_files(ftp, server_path, output_path)
                except ftplib.all_errors as e:
                    log_message(f"Error during sync operation: {e}")
                finally:
                    if ftp:
                        try:
                            ftp.quit()
                        except ftplib.all_errors as e:
                            log_message(f"Error quitting FTP: {e}")
                elapsed_time = time.time() - start_time
                sleep_time = max(0, CHECK_RATE - elapsed_time)
                time.sleep(sleep_time)
    
        # Create and start a thread for syncing screenshots
        if SYNC_SCREENSHOTS:
            threading.Thread(target=sync_screenshots_thread, daemon=True).start()
    
        # Create and start a thread for each file sync path
        for server_path, output_path in file_sync_paths:
            threading.Thread(target=sync_single_file_path, args=(server_path, output_path), daemon=True).start()
    
        # Keep the main thread alive while syncing is running
        while running and not stop_event.is_set():
            time.sleep(1)
        log_message(f"Switch FTP Sync data sync service has been stopped.")


    def toggle_auto_start(self):
        current_auto_start = config.getboolean('Settings', 'auto_start')
        new_auto_start = not current_auto_start
        config.set('Settings', 'auto_start', str(new_auto_start))
        with open(config_path, 'w') as configfile:
            config.write(configfile)
        self.update_auto_start_action()
        reload_config()

    def update_auto_start_action(self):
        auto_start = config.getboolean('Settings', 'auto_start')
        if auto_start:
            self.auto_start_action.setText("\u2713 Auto-Start")
        else:
            self.auto_start_action.setText("    Auto-Start")

    def configure_config(self):
        dialog = ConfigDialog()
        dialog.exec_()
        dialog.show()

    def show_about_dialog(self):
        dialog = AboutDialog()
        dialog.exec_()
        dialog.show()

    def restart_app(self):
        QtWidgets.QApplication.quit()
        QtCore.QProcess.startDetached(sys.executable, sys.argv)

    def exit_app(self):
        global running
        if running:
            running = False
            stop_event.set()

        if os.path.exists(temp_download_dir):
            shutil.rmtree(temp_download_dir)
        
        QtWidgets.qApp.quit()

def main():
    app = QtWidgets.QApplication(sys.argv)

    def is_dark_mode():
        if sys.platform == 'darwin':
            import subprocess
            result = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True,
                text=True,
            )
            return "Dark" in result.stdout
        elif sys.platform == 'win32':
            import winreg
            try:
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                return value == 0  # 0 means dark mode, 1 means light mode
            except Exception as e:
                log_message(f"Failed to read registry: {e}")
                return False
        return False

    # Select the appropriate icon based on the system appearance
    icon_name = "dark_taskbar.png" if is_dark_mode() else "light_taskbar.png"
    icon_path = os.path.join(script_dir, icon_name)
    if os.path.exists(icon_path):
        tray_icon = SystemTrayApp(QtGui.QIcon(icon_path))
    else:
        tray_icon = SystemTrayApp(app.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))

    tray_icon.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
