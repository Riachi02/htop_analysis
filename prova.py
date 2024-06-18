import subprocess
from tkinter import * 
from tkinter import simpledialog
from PIL import Image, ImageTk
PIDs = {}
root = Tk()

# Funzione per caricare le immagini
def load_images(image_paths, size):
    images = []
    for path in image_paths:
        image = Image.open(path)
        image = image.resize(size, Image.LANCZOS)  # Ridimensiona l'immagine
        photo = ImageTk.PhotoImage(image)
        images.append(photo)
    return images

# Funzione per rimuovere l'immagine
def remove_image(canvas, image_id, x_button_id, title_id, pid):
    if run_sudo_command(f"kill -9 {pid}"):
        canvas.delete(image_id)
        canvas.delete(x_button_id)
        canvas.delete(title_id)
        del PIDs[pid]

# Funzione per posizionare le immagini e le icone "X" sul canvas
def arrange_images(canvas, x_icon_photo, image_size, x_icon_size, padding):
    canvas.delete("all")  # Rimuove tutti gli elementi dal canvas
    canvas.update_idletasks()  # Aggiorna il canvas
    pids = list(PIDs.keys())
    titles = []
    image_paths = []
    for key, value in PIDs.items():
        if len(value[1]) != 0:
            image_paths.append(value[1])
        titles.append(value[0])
    
    images = load_images(image_paths, image_size)

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

# Funzione per richiedere la password sudo
def ask_sudo_password():
    password = simpledialog.askstring("Password sudo", "Inserisci la password sudo:", show='*')
    return password

# Funzione per eseguire un comando con sudo
def run_sudo_command(command):
    password = ask_sudo_password()

    if password:
        try:
            # Usa il comando sudo con la password fornita
            result = subprocess.run(f'echo {password} | sudo -k -S {command}', shell=True, check=True, text=True, capture_output=True)
            output_text.set(result.stdout)
            return result.returncode == 0  # Ritorna True se il comando ha avuto successo
        except subprocess.CalledProcessError as e:
            output_text.set(f"Errore durante l'esecuzione del comando: {e.stderr}")
            return False

    else:
        output_text.set("Password non fornita.")
        return False


def main():
    global output_text
    PIDs = {}
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

    root = Tk()
    root.geometry("800x600")
    root.title("Htop Analisys")
    root.configure(bg='black')

    # Dimensioni desiderate per le immagini (larghezza, altezza)
    image_size = (100, 100)
    x_icon_size = (30, 30)
    padding = 80  # Spazio tra le immagini

    # Carica e ridimensiona l'icona "X"
    x_icon_path = './htop_analysis/cancel.png'
    x_icon_image = Image.open(x_icon_path).convert("RGBA")
    x_icon_image = x_icon_image.resize(x_icon_size, Image.LANCZOS)
    x_icon_photo = ImageTk.PhotoImage(x_icon_image)

    # Crea un canvas per posizionare le immagini e le icone "X"
    canvas = Canvas(root, bg='black')
    canvas.pack(fill=BOTH, expand=True)
    images = load_images(image_paths, image_size)

    # Calcola il numero di colonne
    max_columns = 3
    column_width = image_size[0] + padding
    row_height = image_size[1] + padding

    # Chiamare arrange_images ogni volta che la finestra viene ridimensionata
    def on_resize(event):
        arrange_images(canvas, x_icon_photo, image_size, x_icon_size, padding)

    # Mantiene un riferimento alle immagini e all'icona "X" per evitare la garbage collection
    root.image_refs = images
    root.x_icon_ref = x_icon_photo
    root.bind('<Configure>', on_resize)

    # Aggiungi una Label per mostrare l'output
    output_text = StringVar()
    output_label = Label(root, textvariable=output_text, wraplength=400, bg='black', fg='white')
    output_label.pack(pady=20)

    root.mainloop()

if __name__ == "__main__":
    main()
