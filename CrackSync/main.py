import os
import configparser
import tkinter as tk
from gui import CrackSync, SyncHandler
from watchdog.observers import Observer

def load_config(crack_sync):
    config = configparser.ConfigParser()
    if os.path.exists(crack_sync.config_file):
        config.read(crack_sync.config_file)
        if 'Folders' in config:
            folders_str = config['Folders'].get('paths', '')
            crack_sync.source_folders = [path.strip('"') for path in folders_str.split(';') if path]
            # Populate source_folders_listbox with loaded paths
            crack_sync.source_folders_listbox.insert(tk.END, *crack_sync.source_folders)

def save_config(crack_sync):
    config = configparser.ConfigParser()
    config['Folders'] = {'paths': ';'.join([f'"{path}"' for path in crack_sync.source_folders])}
    with open(crack_sync.config_file, 'w') as config_file:
        config.write(config_file)

def start_monitoring(crack_sync, source_folder, usb_drive):
    handler = SyncHandler(source_folder, usb_drive, crack_sync.result_label)
    observer = Observer()
    observer.schedule(handler, source_folder, recursive=True)
    observer.start()
    crack_sync.observers.append(observer)

def main():
    root = tk.Tk()
    crack_sync = CrackSync(root)
    load_config(crack_sync)

    root.mainloop()

    # Save configuration when the application is closed
    save_config(crack_sync)

    if crack_sync.drive_var.get():
        for source_folder in crack_sync.source_folders:
            start_monitoring(crack_sync, source_folder, crack_sync.drive_var.get())

if __name__ == "__main__":
    main()
