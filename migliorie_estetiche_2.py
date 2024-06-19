import subprocess
from tkinter import *
from tkinter import simpledialog, messagebox, ttk
from PIL import Image, ImageTk
import pandas as pd
from manage_process_con_disable import *
import sys
import os

PIDs = {}

def check_root_user(root):
    if os.geteuid() == 0:
        root.withdraw()
        messagebox.showwarning("Attenzione", "Non è possibile eseguire l'applicazione come utente root. Accedere con un altro utente per proseguire")
        root.destroy()
        sys.exit("Applicazione terminata perché eseguita come utente root")

# Funzione per caricare le immagini
def load_images(image_paths, size):
    images = []
    for path in image_paths:
        image = Image.open(path)
        image = image.resize(size, Image.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        images.append(photo)
    return images

# Funzione per richiedere la password sudo
def ask_sudo_password():
    password = simpledialog.askstring("Password sudo", "Inserisci la password sudo:", show='*')
    return password

# Funzione per eseguire un comando con sudo
def run_sudo_command(command):
    password = ask_sudo_password()
    if password:
        try:
            result = subprocess.run(f'echo {password} | sudo -S -k {command}', shell=True, check=True, text=True, capture_output=True)
            if result.returncode == 0:
                messagebox.showinfo("Success", "Application terminated successfully")
                return True
            else:
                return False
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to kill application\n{e.stderr}")
            return False
    else:
        messagebox.showerror("Error", "Password not provided")
        return False

# Funzione per rimuovere l'immagine
def remove_image(canvas, image_id, x_button_id, title_id, pid):
    if run_sudo_command(f"kill -9 {pid}"):
        canvas.delete(image_id)
        canvas.delete(x_button_id)
        canvas.delete(title_id)
        del PIDs[pid]
        update_canvas(canvas)
        
#Funzione per posizionare le immagini e le icone "X" sul canvas
def arrange_images(canvas, images, titles, pids, x_icon_photo, image_size, x_icon_size, padding):
    canvas.delete("all")
    canvas.update_idletasks()

    canvas_width = canvas.winfo_width()
    max_columns = canvas_width // (image_size[0] + padding)

    if max_columns == 0:
        max_columns = 1

    # Posiziona le immagini e le icone "X" sul canvas
    for i, img in enumerate(images):
        row = i // max_columns
        column = i % max_columns

        # Calcola il numero di immagini in questa riga
        num_images_in_row = min(max_columns, len(images) - row * max_columns)

        # Calcola la posizione x per centrare le icone nella riga
        total_row_width = num_images_in_row * (image_size[0] + padding) - padding
        start_x = (canvas_width - total_row_width) // 2

        x = start_x + column * (image_size[0] + padding) + padding // 2
        y = row * (image_size[1] + padding) + padding // 2

        image_id = canvas.create_image(x, y, anchor='nw', image=img)
        title_id = canvas.create_text(x + image_size[0] // 2, y + image_size[1] + 10, text=titles[i], font=("Helvetica", 15), fill="white")
        x_button_id = canvas.create_image(x + image_size[0] - x_icon_size[0], y, anchor='nw', image=x_icon_photo)
        canvas.tag_bind(x_button_id, "<Button-1>", lambda event, img_id=image_id, x_id=x_button_id, t_id=title_id, pid=pids[i]: remove_image(canvas, img_id, x_id, t_id, pid))

# Funzione per aggiornare il canvas
def update_canvas(canvas):
    titles = [PIDs[pid][0] for pid in PIDs]
    image_paths = [PIDs[pid][1] for pid in PIDs]
    images = load_images(image_paths, image_size)
    root.image_refs = images
    arrange_images(canvas, images, titles, list(PIDs.keys()), x_icon_photo, image_size, x_icon_size, padding)

def main():
    global output_text, root, image_size, x_icon_size, padding, x_icon_photo

    root = Tk()
    root.geometry("800x600")
    root.title("Htop Analisys")
    root.configure(bg='#2e2e2e')

    check_root_user(root)

    output = subprocess.check_output("wmctrl -l -p", shell=True)
    lines = output.decode().split('\n')[:-1]
    for line in lines:
        line = line.split()
        PIDs[line[2]] = []
    for pid in PIDs:
        output = subprocess.check_output("cat /proc/" + str(pid) + "/comm", shell=True)
        name = output.decode().lower()[:-1]
        PIDs[pid].append(name)
        command = ["find", "/usr/share/", "-name", f"*{name}*.png"]
        output = subprocess.run(command, capture_output=True, text=True)
        if len(output.stdout.split('\n')) < 2:
            command = ["find", "/", "-name", f"*{name}*.png"]
            output = subprocess.run(command, capture_output=True, text=True)
        img_path = output.stdout.split('\n')
        if(len(img_path) == 1):
            PIDs[pid].append("./htop_analysis/not-found.png")
        if ("16x16" in img_path[0]):
            PIDs[pid].append(img_path[3])
        else:
            PIDs[pid].append(img_path[0])
    print(PIDs)
    titles = []
    image_paths = []
    for key, value in PIDs.items():
        if len(value[1]) != 0:
            image_paths.append(value[1])
        titles.append(value[0])

    style = ttk.Style()
    style.configure('TFrame', background='#2e2e2e')
    style.configure('TLabel', background='#2e2e2e', foreground='#ffffff', font=('Helvetica', 12))
    style.configure('App.TFrame', background='#3e3e3e', relief='raised', borderwidth=2)
    style.configure('App.TLabel', background='#3e3e3e')
    style.configure('AppText.TLabel', background='#3e3e3e', foreground='#ffffff', font=('Helvetica', 10, 'bold'))

    tab_control = ttk.Notebook(root)
    main_tab = ttk.Frame(tab_control, style='TFrame')
    tab_control.add(main_tab, text="Basic Functions")
    advanced_tab = ttk.Frame(tab_control, style='TFrame')
    tab_control.add(advanced_tab, text="Advanced Functions")
    tab_control.pack(expand=1, fill="both")

    print(image_paths)

    image_size = (100, 100)
    x_icon_size = (30, 30)
    padding = 80

    x_icon_path = './htop_analysis/cancel.png'
    x_icon_image = Image.open(x_icon_path).convert("RGBA")
    x_icon_image = x_icon_image.resize(x_icon_size, Image.LANCZOS)
    x_icon_photo = ImageTk.PhotoImage(x_icon_image)

    description_label = ttk.Label(main_tab, text="Applicazioni utente in esecuzione", style='TLabel')
    description_label.pack(pady=10)

    canvas = Canvas(main_tab, bg='#2e2e2e', highlightthickness=0)
    canvas.pack(fill=BOTH, expand=True)
    images = load_images(image_paths, image_size)

    def on_resize(event):
        update_canvas(canvas)

    root.image_refs = images
    root.x_icon_ref = x_icon_photo
    root.bind('<Configure>', on_resize)

    update_canvas(canvas)

    ttk.Label(advanced_tab, text="Lista dei processi attivi:", style='TLabel').pack(pady=20)

    output = subprocess.check_output("top -b -n 1 | head -n 17", shell=True)
    lines = output.decode().split('\n')

    header_index = next(i for i, line in enumerate(lines) if 'PID' in line)
    header = tuple(lines[header_index].strip().split())
    data = [tuple(line.strip().split()) for line in lines[header_index + 1:] if line.strip()]

    table_frame = ttk.Frame(advanced_tab, style='TFrame')
    table_frame.pack(fill=BOTH, expand=True)
    app = ProcessManagerApp(table_frame)

    root.mainloop()

if __name__ == "__main__":
    main()
