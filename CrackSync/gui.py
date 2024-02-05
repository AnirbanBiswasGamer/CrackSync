# gui.py
import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import psutil
import configparser

class SyncHandler(FileSystemEventHandler):
    def __init__(self, source_folder, usb_drive, result_label):
        super().__init__()
        self.source_folder = source_folder
        self.usb_drive = usb_drive
        self.result_label = result_label
        

    def on_modified(self, event):
        pass

    def on_created(self, event):
        pass

    def sync_to_usb(self):
        root.after(10, self.do_sync)

    def do_sync(self):
        try:
            source_folder = self.source_folder
            usb_drive = self.usb_drive

            if not os.path.exists(usb_drive):
                self.result_label.config(text=f"USB drive '{usb_drive}' is not accessible.", foreground='red')
                return

            destination_path = os.path.join(usb_drive, os.path.basename(source_folder))

            copy_number = 1
            while os.path.exists(destination_path):
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                destination_path = os.path.join(usb_drive, f"{os.path.basename(source_folder)}_{timestamp}_{copy_number}")
                copy_number += 1

            try:
                shutil.copytree(source_folder, destination_path)
                self.result_label.config(text=f"Folder '{source_folder}' synced to USB drive '{usb_drive}' successfully.", foreground='green')
            except Exception as e:
                self.result_label.config(text=f"Error: {e}", foreground='red')

        except Exception as e:
            self.result_label.config(text=f"Error: {e}", foreground='red')

    def check_and_delete_old_copies(self, usb_drive, folder_name, max_copies=5):
        try:
            folder_copies = [f for f in os.listdir(usb_drive) if f.startswith(folder_name)]
            folder_copies.sort()

            if len(folder_copies) > max_copies:
                num_copies_to_delete = len(folder_copies) - max_copies
                copies_to_delete = folder_copies[:num_copies_to_delete]

                for copy_to_delete in copies_to_delete:
                    copy_to_delete_path = os.path.join(usb_drive, copy_to_delete)
                    shutil.rmtree(copy_to_delete_path)
                    self.result_label.config(text=f"Deleted old copy: '{copy_to_delete}'", foreground='orange')

        except Exception as e:
            self.result_label.config(text=f"Error: {e}", foreground='red')

class CrackSync:
    def __init__(self, root):
        self.root = root
        self.root.title("Crack Sync")
        self.style = ttk.Style()
        self.style.configure("TLabel", padding=5, font=('Helvetica', 10))
        self.style.configure("TButton", padding=5, font=('Helvetica', 10))

        self.source_folders = []
        self.observers = []

        # Load configuration
        self.config_file = "config.ini"

        # Source Folders
        self.source_folders_label = ttk.Label(root, text="Select Source Folders:")
        self.source_folders_label.grid(row=0, column=0, sticky='w')

        self.source_folders_listbox = tk.Listbox(root, selectmode=tk.MULTIPLE)
        self.source_folders_listbox.grid(row=1, column=0, columnspan=2, sticky='ew', padx=5)

        self.browse_drives_label = ttk.Label(root, text="Select USB Drive:")
        self.browse_drives_label.grid(row=2, column=0, sticky='w')

        self.drive_var = tk.StringVar()
        self.drive_combobox = ttk.Combobox(root, textvariable=self.drive_var, state='readonly', values=self.get_drive_list())
        self.drive_combobox.grid(row=3, column=0, columnspan=2, sticky='ew', padx=5)

        self.browse_folders_button = ttk.Button(root, text="Add Folder", command=self.browse_source_folder)
        self.browse_folders_button.grid(row=1, column=2, padx=5)

        self.remove_folder_button = ttk.Button(root, text="Remove", command=self.remove_selected_folders)
        self.remove_folder_button.grid(row=1, column=3, padx=5)

        self.result_label = ttk.Label(root, text="", foreground='black')
        self.result_label.grid(row=4, column=0, columnspan=4, pady=10)

        self.sync_button = ttk.Button(root, text="Sync All", command=self.sync_all)
        self.sync_button.grid(row=5, column=0, columnspan=4, pady=10)

        self.startup_var = tk.BooleanVar(value=False)

        self.startup_checkbox = ttk.Checkbutton(root, text="Start on Windows Startup", variable=self.startup_var)
        self.startup_checkbox.grid(row=6, column=0, columnspan=4, pady=10)

        # Populate source_folders_listbox with loaded paths
        self.source_folders_listbox.insert(tk.END, *self.source_folders)


        # Populate source_folders_listbox with loaded paths
        self.source_folders_listbox.insert(tk.END, *self.source_folders)

    def load_config(self):
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file)
            if 'Folders' in config:
                folders_str = config['Folders'].get('paths', '')
                self.source_folders = [path.strip('"') for path in folders_str.split(';') if path]

    def save_config(self):
        config = configparser.ConfigParser()
        config['Folders'] = {'paths': ';'.join([f'"{path}"' for path in self.source_folders])}
        with open(self.config_file, 'w') as config_file:
            config.write(config_file)

    def get_drive_list(self):
        drive_list = []
        for partition in psutil.disk_partitions():
            drive_list.append(partition.device)
        return drive_list

    def browse_source_folder(self):
        source_folder = filedialog.askdirectory()
        if source_folder:
            self.source_folders.append(source_folder)
            self.source_folders_listbox.insert(tk.END, source_folder)
            self.save_config()

    def sync_all(self):
        usb_drive = self.drive_var.get()

        for source_folder in self.source_folders:
            sync_handler = SyncHandler(source_folder, usb_drive, self.result_label)
            sync_handler.do_sync()

            observer = self.start_monitoring(source_folder, usb_drive)
            self.observers.append(observer)

        self.save_config()

    def remove_selected_folders(self):
        selected_indices = self.source_folders_listbox.curselection()
        for index in reversed(selected_indices):
            removed_folder = self.source_folders.pop(index)
            self.source_folders_listbox.delete(index)
            self.save_config()
            self.result_label.config(text=f"Removed folder: '{removed_folder}'", foreground='blue')

    def start_monitoring(self, source_folder, usb_drive):
        handler = SyncHandler(source_folder, usb_drive, self.result_label)
        observer = Observer()
        observer.schedule(handler, source_folder, recursive=True)
        observer.start()
        return observer

    def stop_monitoring(self, observer):
        observer.stop()
        observer.join()

# GUI setup
if __name__ == "__main__":
    root = tk.Tk()
    app = CrackSync(root)
    root.mainloop()

    # Stop monitoring when the application is closed
    for observer in app.observers:
        app.stop_monitoring(observer)