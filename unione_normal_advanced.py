import subprocess, sys
from tkinter import *
from PIL import Image, ImageTk
from manage_process_con_disable import *

PIDs = {}

def check_root_user(root):
    if os.geteuid() == 0:  # Controlla se l'utente è root
        root.withdraw()  # Nasconde la finestra principale di Tkinter
        messagebox.showwarning("Attenzione", "Non è possibile eseguire l'applicazione come utente root. Accedere con un altro utente per proseguire")
        root.destroy()
        sys.exit("Applicazione terminata perché eseguita come utente root")


# Funzione per caricare le immagini
def load_images(image_paths, size):
    images = []
    for path in image_paths:
        image = Image.open(path)
        image = image.resize(size, Image.LANCZOS)  # Ridimensiona l'immagine
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
        #stderr = 0
        try:
            # Usa il comando sudo con la password fornita
            result = subprocess.run(f'echo {password} | sudo -S -k {command}', shell=True, check=True, text=True, capture_output=True)
            #stderr = result.stderr
            if result.returncode == 0:
                messagebox.showinfo("Success", "Application termineted successfully")
                return True
            else:
                return False
            #return result.returncode == 0  # Ritorna True se il comando ha avuto successo
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to kill application\n{e.stderr}")
            return False
    else:
        #output_text.set("Password non fornita.")
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


# Funzione per posizionare le immagini e le icone "X" sul canvas
def arrange_images(canvas, images, titles, pids, x_icon_photo, image_size, x_icon_size, padding):
    canvas.delete("all")  # Rimuove tutti gli elementi dal canvas
    canvas.update_idletasks()  # Aggiorna il canvas

    canvas_width = canvas.winfo_width()
    max_columns = canvas_width // (image_size[0] + padding)
    
    if max_columns == 0:
        max_columns = 1
        
    # Posiziona le immagini e le icone "X" sul canvas
    for i, img in enumerate(images):
        row = i // max_columns
        column = i % max_columns
        
        x = column * (image_size[0] + padding) + padding // 2
        y = row * (image_size[1] + padding) + padding // 2
        
        # Aggiungi l'immagine al canvas
        image_id = canvas.create_image(x, y, anchor='nw', image=img)

        # Aggiungi il titolo sotto l'immagine
        title_id = canvas.create_text(x + image_size[0] // 2, y + image_size[1] + 10, text=titles[i], font=("Helvetica", 15), fill="white")
        
        # Aggiungi il bottone "X" sopra l'immagine
        x_button_id = canvas.create_image(x + image_size[0] - x_icon_size[0], y, anchor='nw', image=x_icon_photo)
        
        # Configura il click per rimuovere l'immagine e l'icona "X"
        canvas.tag_bind(x_button_id, "<Button-1>", lambda event, img_id=image_id, x_id=x_button_id, t_id=title_id, pid=pids[i]: remove_image(canvas, img_id, x_id, t_id, pid))

# Funzione per aggiornare il canvas
def update_canvas(canvas):
    titles = [PIDs[pid][0] for pid in PIDs]
    image_paths = [PIDs[pid][1] for pid in PIDs]
    images = load_images(image_paths, image_size)
    root.image_refs = images  # Mantiene un riferimento alle nuove immagini caricate
    arrange_images(canvas, images, titles, list(PIDs.keys()), x_icon_photo, image_size, x_icon_size, padding)

def get_running_applications():
    output = subprocess.check_output("wmctrl -l -p", shell=True)
    lines = output.decode().split('\n')[:-1]

    for line in lines:
        line = line.split()
        if line[2] == "0":
            continue
        elif line[2] not in PIDs:
            PIDs[line[2]] = []

    for pid in PIDs:
        if len(PIDs[pid]) == 0:
            print(pid, PIDs[pid])
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
    titles = []
    image_paths = []
    for key, value in PIDs.items():
        if len(value[1]) != 0:
            image_paths.append(value[1])
        titles.append(value[0])
    
    return titles, image_paths

def refetch_applications():
    titles, image_paths = get_running_applications()
    update_canvas(canvas)


def main():
    global root, image_size, x_icon_size, padding, x_icon_photo, canvas

    root = Tk()
    root.geometry("800x600")
    root.title("Htop Analisys")
    root.configure(bg='black')

    check_root_user(root)

    titles, image_paths = get_running_applications()

    style = ttk.Style()
    style.configure('TFrame', background='#2e2e2e')
    style.configure('TLabel', background='#2e2e2e', foreground='#ffffff', font=('Helvetica', 18))
    style.configure('App.TFrame', background='#3e3e3e', relief='raised', borderwidth=2)
    style.configure('App.TLabel', background='#3e3e3e')
    style.configure('AppText.TLabel', background='#3e3e3e', foreground='#ffffff', font=('Helvetica', 10, 'bold'))

    # Creazione del tab control
    tab_control = ttk.Notebook(root)
    main_tab = ttk.Frame(tab_control, style='TFrame')
    tab_control.add(main_tab, text="Basic Functions")
    advanced_tab = ttk.Frame(tab_control, style='TFrame')
    tab_control.add(advanced_tab, text="Advanced Functions")
    tab_control.pack(expand=1, fill="both")

    print(image_paths)

    # Dimensioni desiderate per le immagini (larghezza, altezza)
    image_size = (100, 100)
    x_icon_size = (30, 30)
    padding = 80  # Spazio tra le immagini

    # Carica e ridimensiona l'icona "X"
    x_icon_path = './htop_analysis/cancel.png'
    x_icon_image = Image.open(x_icon_path).convert("RGBA")
    x_icon_image = x_icon_image.resize(x_icon_size, Image.LANCZOS)
    x_icon_photo = ImageTk.PhotoImage(x_icon_image)

    description_label = ttk.Label(main_tab, text="Applicazioni utente in esecuzione", style='TLabel')
    description_label.pack(pady=10)

    canvas = Canvas(main_tab, bg='#2e2e2e', highlightthickness=0)
    canvas.pack(fill=BOTH, expand=True)
    images = load_images(image_paths, image_size)

    refresh_button = tk.Button(main_tab, text="Refresh", command=refetch_applications)
    refresh_button.pack(side=tk.LEFT, padx=10, pady=10)

    # Calcola il numero di colonne
    max_columns = 3
    column_width = image_size[0] + padding
    row_height = image_size[1] + padding

    # Chiamare arrange_images ogni volta che la finestra viene ridimensionata
    def on_resize(event):
        update_canvas(canvas)

    # Mantiene un riferimento alle immagini e all'icona "X" per evitare la garbage collection
    root.image_refs = images
    root.x_icon_ref = x_icon_photo
    root.bind('<Configure>', on_resize)

    # Inizializza il canvas
    update_canvas(canvas)

    #********************** Advanced tab *************************#

    ttk.Label(advanced_tab, text="Lista dei processi attivi:", style='TLabel').pack(pady=20)

    table_frame = ttk.Frame(advanced_tab, style='TFrame')
    table_frame.pack(fill=BOTH, expand=True)
    app = ProcessManagerApp(table_frame)

    root.mainloop()

if __name__ == "__main__":
    main()
