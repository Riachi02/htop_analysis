import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import psutil
import os
import subprocess
import platform

class ProcessManagerApp:
    def __init__(self, root):
        self.root = root
        #self.root.title("Process Manager")
        
        self.create_widgets()
        self.refresh_process_list()

    def create_widgets(self):
        self.tree = ttk.Treeview(self.root, columns=("PID", "User", "Name", "CPU%", "MEM%", "Status", "Nice"), show="headings")
        self.tree.heading("PID", text="PID")
        self.tree.heading("User", text="User")
        self.tree.heading("Name", text="Name")
        self.tree.heading("CPU%", text="CPU%")
        self.tree.heading("MEM%", text="MEM%")
        self.tree.heading("Status", text="Status")
        self.tree.heading("Nice", text="Nice")
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        self.kill_button = tk.Button(self.root, text="Kill Process", command=self.kill_process, state=tk.DISABLED)
        self.kill_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.nice_button = tk.Button(self.root, text="Change Nice Value", command=self.change_nice_value, state=tk.DISABLED)
        self.nice_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.refresh_button = tk.Button(self.root, text="Refresh", command=self.refresh_process_list)
        self.refresh_button.pack(side=tk.LEFT, padx=10, pady=10)

        self.filter_button = tk.Button(self.root, text="Filter", command=self.filter_process_list)
        self.filter_button.pack(side=tk.LEFT, padx=10, pady=10)

    def refresh_process_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        self.processes = list(psutil.process_iter(['pid', 'username', 'name', 'cpu_percent', 'memory_percent', 'status', 'nice']))

        # Ordina i processi in base alla percentuale di CPU utilizzata
        self.processes.sort(key=lambda proc: proc.cpu_percent(), reverse=True) # FORSE FUNZIONA
        for proc in self.processes:
            try:
                self.tree.insert("", "end", values=(proc.info['pid'], proc.info['username'], proc.info['name'], proc.info['cpu_percent'], proc.info['memory_percent'], proc.info['status'], proc.info['nice']))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    def on_tree_select(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            pid = int(self.tree.item(selected_item)['values'][0])
            user = self.tree.item(selected_item)['values'][1]
            #if self.is_protected_process(user):
            if user != os.getlogin():
                self.kill_button.config(state=tk.DISABLED)
                self.nice_button.config(state=tk.DISABLED)
                messagebox.showwarning("Warning", f"Process {pid} is protected and cannot be selected.")
                self.tree.selection_remove(selected_item)
            else:
                self.kill_button.config(state=tk.NORMAL)
                self.nice_button.config(state=tk.NORMAL)

    '''def is_protected_process(self, user):
        protected_pids = [0, 1, 10474]  # Add other critical PIDs as needed
        return pid in protected_pids'''

    def kill_process(self):
        selected_item = self.tree.selection()
        if selected_item:
            pid = int(self.tree.item(selected_item)['values'][0])
            try:
                self.ask_for_admin_password(pid, action='terminate')
                self.refresh_process_list()
            except psutil.NoSuchProcess:
                messagebox.showerror("Error", "No such process")
        else:
            messagebox.showwarning("Warning", "No process selected")

    def change_nice_value(self):
        selected_item = self.tree.selection()
        if selected_item:
            pid = int(self.tree.item(selected_item)['values'][0])
            nice_value = simpledialog.askinteger("Nice Value", "Enter new nice value (-20 to 19):", minvalue=-20, maxvalue=19)
            if nice_value is not None:
                try:
                    self.ask_for_admin_password(pid, action='nice', nice_value=nice_value)
                    self.refresh_process_list()
                except psutil.NoSuchProcess:
                    messagebox.showerror("Error", "No such process")
                except ValueError as e:
                    messagebox.showerror("Error", f"Invalid nice value: {e}")
                except Exception as e:
                    messagebox.showerror("Error", str(e))
        else:
            messagebox.showwarning("Warning", "No process selected")

    def ask_for_admin_password(self, pid, action, nice_value=None):
        password = simpledialog.askstring("Admin Password", "Enter admin password:", show='*')
        if password:
            self.run_as_admin_unix(pid, password, action, nice_value)

    def run_as_admin_unix(self, pid, password, action, nice_value):
        try:
            if action == 'terminate':
                command = f'kill -9 {pid}'
            elif action == 'nice':
                command = f'renice {nice_value} -p {pid}'

            # Usa il comando sudo con la password fornita
            result = subprocess.run(f'echo {password} | sudo -S -k {command}', shell=True, check=True, text=True, capture_output=True)

            if result.returncode == 0:
                messagebox.showinfo("Success", f"Process {pid} {action}ed successfully")
            else:
                messagebox.showerror("Error", f"Failed to {action} process {pid}\n{result.stderr}")
            self.refresh_process_list()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def filter_process_list(self):
        criteria = simpledialog.askstring("Filter Criteria", "Enter filter criteria (e.g., name:<process_name>, cpu:<cpu_percent>, memory:<memory_percent>):")
        if criteria:
            key, value = criteria.split(':')
            filtered_processes = []
            for proc in self.processes:
                try:
                    print(key, value.lower())
                    if (key == 'name' or key == 'username' or key == 'status') and value.lower() in proc.info[key].lower():
                        filtered_processes.append(proc)
                    elif (key == 'cpu' or key == 'memory') and proc.info[key + "_percent"] >= float(value):
                        filtered_processes.append(proc)
                    elif key == 'pid' and proc.info[key] < int(value):
                        filtered_processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            for i in self.tree.get_children():
                self.tree.delete(i)

            for proc in filtered_processes:
                self.tree.insert("", "end", values=(proc.info['pid'], proc.info['username'], proc.info['name'], proc.info['cpu_percent'], proc.info['memory_percent'], proc.info['status'], proc.info['nice']))

