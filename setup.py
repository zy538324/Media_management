import os
import subprocess
import platform

def install_dependencies():
    # Install Python dependencies
    subprocess.run(["pip", "install", "-r", "requirements.txt"])

def install_jellyfin():
    if platform.system() == "Windows":
        url = "https://repo.jellyfin.org/files/server/windows/latest-stable/amd64/jellyfin_10.10.6_windows-x64.exe"
        installer = os.path.join(os.getenv("TEMP"), "jellyfin_installer.exe")
    elif platform.system() == "Darwin":  # macOS
        url = "https://repo.jellyfin.org/files/server/macos/latest-stable/jellyfin-macos.zip"
        installer = "/tmp/jellyfin-macos.zip"
    else:  # Linux
        url = "https://repo.jellyfin.org/files/server/ubuntu/latest/jellyfin_10.10.6-1_amd64.deb"
        installer = "/tmp/jellyfin_installer.deb"

    subprocess.run(["curl", "-L", "-o", installer, url])
    if platform.system() == "Windows":
        subprocess.run([installer, "/S"])
    elif platform.system() == "Darwin":
        subprocess.run(["unzip", installer, "-d", "/Applications"])
    else:
        subprocess.run(["sudo", "dpkg", "-i", installer])

def install_jackett():
    if platform.system() == "Windows":
        url = "https://github.com/Jackett/Jackett/releases/download/v0.20.2048/Jackett.Binaries.Windows.zip"
        installer = os.path.join(os.getenv("TEMP"), "jackett_installer.zip")
    elif platform.system() == "Darwin":  # macOS
        url = "https://github.com/Jackett/Jackett/releases/download/v0.20.2048/Jackett.Binaries.MacOS.zip"
        installer = "/tmp/jackett_installer.zip"
    else:  # Linux
        url = "https://github.com/Jackett/Jackett/releases/download/v0.20.2048/Jackett.Binaries.LinuxAMDx64.tar.gz"
        installer = "/tmp/jackett_installer.tar.gz"

    subprocess.run(["curl", "-L", "-o", installer, url])
    if platform.system() == "Windows":
        subprocess.run(["powershell", "-Command", f"Expand-Archive -Path {installer} -DestinationPath C:\\Jackett"])
    elif platform.system() == "Darwin":
        subprocess.run(["unzip", installer, "-d", "/Applications/Jackett"])
    else:
        subprocess.run(["tar", "-xzf", installer, "-C", "/opt/Jackett"])

def install_qbittorrent():
    if platform.system() == "Windows":
        url = "https://www.fosshub.com/qBittorrent.html?dwl=qbittorrent_4.3.9_x64_setup.exe"
        installer = os.path.join(os.getenv("TEMP"), "qbittorrent_installer.exe")
    elif platform.system() == "Darwin":  # macOS
        url = "https://www.fosshub.com/qBittorrent.html?dwl=qBittorrent-4.3.9.dmg"
        installer = "/tmp/qbittorrent_installer.dmg"
    else:  # Linux
        url = "https://www.fosshub.com/qBittorrent.html?dwl=qBittorrent-4.3.9.tar.gz"
        installer = "/tmp/qbittorrent_installer.tar.gz"

    subprocess.run(["curl", "-L", "-o", installer, url])
    if platform.system() == "Windows":
        subprocess.run([installer, "/S"])
    elif platform.system() == "Darwin":
        subprocess.run(["hdiutil", "attach", installer])
        subprocess.run(["cp", "-r", "/Volumes/qBittorrent/qBittorrent.app", "/Applications"])
        subprocess.run(["hdiutil", "detach", "/Volumes/qBittorrent"])
    else:
        subprocess.run(["tar", "-xzf", installer, "-C", "/opt/qBittorrent"])

def install_mysql():
    if platform.system() == "Windows":
        url = "https://dev.mysql.com/get/Downloads/MySQLInstaller/mysql-installer-community-8.0.26.0.msi"
        installer = os.path.join(os.getenv("TEMP"), "mysql_installer.msi")
        subprocess.run(["curl", "-L", "-o", installer, url])
        subprocess.run(["msiexec", "/i", installer, "/quiet"])
    elif platform.system() == "Darwin":  # macOS
        url = "https://dev.mysql.com/get/Downloads/MySQL-8.0/mysql-8.0.26-macos10.15-x86_64.dmg"
        installer = "/tmp/mysql_installer.dmg"
        subprocess.run(["curl", "-L", "-o", installer, url])
        subprocess.run(["hdiutil", "attach", installer])
        subprocess.run(["sudo", "installer", "-pkg", "/Volumes/mysql-8.0.26-macos10.15-x86_64/mysql-8.0.26-macos10.15-x86_64.pkg", "-target", "/"])
        subprocess.run(["hdiutil", "detach", "/Volumes/mysql-8.0.26-macos10.15-x86_64"])
    else:  # Linux
        subprocess.run(["sudo", "apt-get", "update"])
        subprocess.run(["sudo", "apt-get", "install", "-y", "mysql-server"])

def main():
    install_dependencies()
    install_jellyfin()
    install_jackett()
    install_qbittorrent()
    install_mysql()

if __name__ == "__main__":
    main()