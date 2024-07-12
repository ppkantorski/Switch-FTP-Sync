import os
import sys
import platform
import subprocess
import shutil

# Determine the operating system
current_platform = platform.system()

# Function to install required modules
def install_requirements():
    try:
        if current_platform == "Darwin":  # macOS
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements-macos.txt"])
        else:  # Windows or Linux
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    except subprocess.CalledProcessError as e:
        print(f"Error installing requirements: {e}")
        sys.exit(1)

# Delete dist and build folders if they exist
def delete_directory(dir_name):
    if os.path.exists(dir_name):
        if current_platform == "Windows":
            shutil.rmtree(dir_name, ignore_errors=True)
        else:
            os.system(f'rm -rf {dir_name}')

delete_directory('dist')
delete_directory('build')

# Install required modules
install_requirements()

if current_platform == "Windows":
    os.environ["PATH"] += os.pathsep + os.path.join(os.path.expanduser("~"), "AppData", "Local", "Packages", "PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0", "LocalCache", "local-packages", "Python312", "Scripts")

# Run PyInstaller with the .spec file
os.system('pyinstaller ftp_screenshots.spec')
