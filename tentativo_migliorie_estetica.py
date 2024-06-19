import subprocess
from tkinter import *
from tkinter import simpledialog
from tkinter import ttk
from PIL import Image, ImageTk, ImageEnhance
import pandas as pd
from manage_process_con_disable import *
import sys

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

def make_image_opaque(image_path, opacity):
    image = Image.open(image_path).convert("RGBA")
    alpha = image.split()[3]
    alpha = alpha.point(lambda p: p * opacity)
    image.putalpha(alpha)
    return image



# Funzione per rimuovere l'immagine
def remove_image(canvas, image_id, x_button_id, title_id, pid, img_ref):
    if run_sudo_command(f"kill -9 {pid}"):

        # Rimuovi dal canvas dopo un breve ritardo
        canvas.after(1000, lambda: canvas.delete(image_id))
        canvas.after(1000, lambda: canvas.delete(x_button_id))
        canvas.after(1000, lambda: canvas.delete(title_id))
        del PIDs[pid]
        canvas.after(1000, lambda: update_canvas(canvas))


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
        
        # Disegna il rettangolo di sfondo
        rect_id = canvas.create_rectangle(x - 10, y - 10, x + image_size[0] + 10, y + image_size[1] + 30, outline="white", width=2)

        # Aggiungi l'immagine al canvas
        image_id = canvas.create_image(x, y, anchor='nw', image=img)

        # Aggiungi il titolo sotto l'immagine
        title_id = canvas.create_text(x + image_size[0] // 2, y + image_size[1] + 10, text=titles[i], font=("Helvetica", 15), fill="white")
        
        # Aggiungi il bottone "X" sopra l'immagine
        x_button_id = canvas.create_image(x + image_size[0] - x_icon_size[0], y, anchor='nw', image=x_icon_photo)
        
        # Configura il click per rimuovere l'immagine e l'icona "X"
        canvas.tag_bind(x_button_id, "<Button-1>", lambda event, img_id=image_id, x_id=x_button_id, t_id=title_id, pid=pids[i]: remove_image(canvas, img_id, x_id, t_id, pid, img_ref))

# Funzione per aggiornare il canvas
def update_canvas(canvas):
    titles = [PIDs[pid][0] for pid in PIDs]
    image_paths = [PIDs[pid][1] for pid in PIDs]
    images = load_images(image_paths, image_size)
    root.image_refs = images  # Mantiene un riferimento alle nuove immagini caricate
    arrange_images(canvas, images, titles, list(PIDs.keys()), x_icon_photo, image_size, x_icon_size, padding)

def create_table(frame, lst):
    # Trova il numero totale di righe e colonne nella lista
    total_rows = len(lst)
    total_columns = len(lst[0])

    # Crea la tabella
    for i in range(total_rows):
        for j in range(total_columns):
            e = Entry(frame, width=20, fg='blue', font=('Arial', 16, 'bold'))
            e.grid(row=i, column=j)
            e.insert(END, lst[i][j])

def main():
    global output_text, root, image_size, x_icon_size, padding, x_icon_photo, img_ref

    root = Tk()
    root.geometry("800x600")
    root.title("Htop Analisys")
    root.configure(bg='black')

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

    # Creazione del tab control
    tab_control = ttk.Notebook(root)
    main_tab = Frame(tab_control, bg='black')
    tab_control.add(main_tab, text="Basic Functions")
    advanced_tab = Frame(tab_control, bg='black')
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

    # Descrizione sopra il canvas
    description_label = Label(main_tab, text="Processi attivi", font=("Helvetica", 18), bg='black', fg='white')
    description_label.pack(pady=10)

    # Aggiungi un frame per contenere il canvas
    canvas_frame = Frame(main_tab, bg='black', highlightbackground="white", highlightcolor="white", highlightthickness=1)
    canvas_frame.pack(padx=20, pady=20, fill=BOTH, expand=True)
    canvas = Canvas(canvas_frame, bg='black')
    canvas.pack(fill=BOTH, expand=True)


    '''# Crea un canvas per posizionare le immagini e le icone "X"
    canvas = Canvas(main_tab, bg='black')
    canvas.pack(fill=BOTH, expand=True)'''
    images = load_images(image_paths, image_size)

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
    img_ref = {pid: None for pid in PIDs}  # Mantiene riferimenti alle immagini opacizzate
    root.bind('<Configure>', on_resize)

    # Inizializza il canvas
    update_canvas(canvas)

    #********************** Advanced tab *************************#

    Label(advanced_tab, text="Lista dei processi attivi:", bg='black', fg='white').pack(pady=20)

    output = subprocess.check_output("top -b -n 1 | head -n 17", shell=True)
    lines = output.decode().split('\n')
    
    # Trova l'indice della riga che inizia con 'PID'
    header_index = next(i for i, line in enumerate(lines) if 'PID' in line)
    header = tuple(lines[header_index].strip().split())
    data = [tuple(line.strip().split()) for line in lines[header_index + 1:] if line.strip()]

    table_frame = Frame(advanced_tab, bg='black')
    table_frame.pack(fill=BOTH, expand=True)
    app = ProcessManagerApp(table_frame)

    root.mainloop()

if __name__ == "__main__":
    main()
