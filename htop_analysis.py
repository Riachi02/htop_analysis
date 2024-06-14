import subprocess
import pandas as pd
import argparse
from tkinter import * 

class Table:
     
    def __init__(self, root, lst):

        # find total number of rows and
        # columns in list
        total_rows = len(lst)
        total_columns = len(lst[0])

        # code for creating table
        for i in range(total_rows):
            for j in range(total_columns):
                self.e = Entry(root, width=20, fg='blue',
                               font=('Arial',16,'bold'))
                 
                self.e.grid(row=i, column=j)
                self.e.insert(END, lst[i][j])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n","--name")
    args = parser.parse_args()
    name_process = args.name
    cmd = "ps aux | grep " + str(name_process) + " | tr -s ' ' | cut -d ' ' -f 2"
    process_pid = subprocess.check_output(cmd, shell=True)
    process_pid = process_pid.decode().split()[0]
    print(process_pid)

    #output = subprocess.run(['top', '-b', '-n 1', '| head -n 12'])
    output = subprocess.check_output("top -b -n 1 | head -n 17", shell=True)
    lines = output.decode().split('\n')
    
    # Trova l'indice della riga che inizia con 'PID'
    header_index = next(i for i, line in enumerate(lines) if 'PID' in line)
    header = tuple(lines[header_index].strip().split())
    data = [tuple(line.strip().split()) for line in lines[header_index + 1:] if line.strip()]
    print(data)

    # Crea un DataFrame
    df = pd.DataFrame(data, columns=header)

    # Mostra il DataFrame
    print(df)
    window = Tk()
    window.geometry("600x600")
    window.title("Htop Analisys")
    window.configure(bg='black')
    text = "Hello World!"
    
    # take the data
    lst = [(1,'Raj','Mumbai',19),
        (2,'Aaryan','Pune',18),
        (3,'Vaishnavi','Mumbai',20),
        (4,'Rachna','Mumbai',21),
        (5,'Shubham','Delhi',21)]
    
    # create root window
    t = Table(window, data)
    window.mainloop()


if __name__ == "__main__":
    main()