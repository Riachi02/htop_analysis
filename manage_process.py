import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import psutil
import os
import subprocess
import platform

class ProcessManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Process Manager")
        
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
        self.tree.pack(fill=tk.BOTH, expand=True)
        
        self.kill_button = tk.Button(self.root, text="Kill Process", command=self.kill_process)
        self.kill_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.nice_button = tk.Button(self.root, text="Change Nice Value", command=self.change_nice_value)
        self.nice_button.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.refresh_button = tk.Button(self.root, text="Refresh", command=self.refresh_process_list)
        self.refresh_button.pack(side=tk.LEFT, padx=10, pady=10)

    def refresh_process_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        for proc in psutil.process_iter(['pid', 'username', 'name', 'cpu_percent', 'memory_percent', 'status', 'nice']):
            try:
                self.tree.insert("", "end", values=(proc.info['pid'], proc.info['username'], proc.info['name'], proc.info['cpu_percent'], proc.info['memory_percent'], proc.info['status'], proc.info['nice']))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass

    def kill_process(self):
        selected_item = self.tree.selection()
        if selected_item:
            pid = int(self.tree.item(selected_item)['values'][0])
            try:
                p = psutil.Process(pid)
                p.terminate()
                p.wait()  
                self.refresh_process_list()
                messagebox.showinfo("Success", f"Process {pid} terminated successfully")
            except psutil.NoSuchProcess:
                messagebox.showerror("Error", "No such process")
            except psutil.AccessDenied:
                self.ask_for_admin_password(pid, action='terminate')
            except Exception as e:
                messagebox.showerror("Error", str(e))
        else:
            messagebox.showwarning("Warning", "No process selected")

    def change_nice_value(self):
        selected_item = self.tree.selection()
        if selected_item:
            pid = int(self.tree.item(selected_item)['values'][0])
            nice_value = simpledialog.askinteger("Nice Value", "Enter new nice value (-20 to 19):", minvalue=-20, maxvalue=19)
            if nice_value is not None:
                try:
                    p = psutil.Process(pid)
                    p.nice(nice_value)
                    self.refresh_process_list()
                    messagebox.showinfo("Success", f"Nice value of process {pid} changed to {nice_value}")
                except psutil.NoSuchProcess:
                    messagebox.showerror("Error", "No such process")
                except psutil.AccessDenied:
                    self.ask_for_admin_password(pid, action='nice', nice_value=nice_value)
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

            result = subprocess.run(
                ['sudo', '-S', command],
                input=password + '\n',
                text=True,
                capture_output=True
            )

            if result.returncode == 0:
                messagebox.showinfo("Success", f"Process {pid} {action}ed successfully")
            else:
                messagebox.showerror("Error", f"Failed to {action} process {pid}\n{result.stderr}")
            self.refresh_process_list()
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = ProcessManagerApp(root)
    root.mainloop()
