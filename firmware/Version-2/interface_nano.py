from tkinter import *
from tkinter import messagebox
import os
import signal_gen_nano

# ================== CONFIG ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "assets", "icon.ico")
LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.png")

window = Tk()
window.title("Interface gráfica Sistema de Estimulação")
window.geometry("720x576+250+50")
window.resizable(False, False)

try:
    window.iconbitmap(ICON_PATH)
except:
    pass

# ================== VARIÁVEIS ==================
ts_entry = None
interval_entry = None

freq_entries = []
phase_entries = []

# ================== HEADER ==================
def create_header(parent):
    global ts_entry, interval_entry

    frame = Frame(parent, bg="white", height=160)
    frame.pack(fill=X)

    left = Frame(frame, bg="white", width=180)
    left.pack(side=LEFT, fill=Y)

    try:
        logo = PhotoImage(file=LOGO_PATH)
        lbl = Label(left, image=logo, bg="white")
        lbl.image = logo
        lbl.pack(expand=True)
    except:
        Label(left, text="LOGO", bg="white").pack(expand=True)

    right = Frame(frame, bg="white")
    right.pack(side=LEFT, fill=BOTH, expand=True)

    Label(
        right,
        text="CONFIGURAÇÃO DOS ESTÍMULOS",
        font=("Arial", 12, "bold"),
        bg="white"
    ).pack(pady=10)

    inputs = Frame(right, bg="white")
    inputs.pack()

    # Ts
    Label(inputs, text="Ts [µs]:", bg="white").grid(row=0, column=0)
    ts_entry = Entry(inputs, width=8)
    ts_entry.grid(row=1, column=0, padx=20)
    ts_entry.insert(0, "128")

    # Intervalo
    Label(inputs, text="Estimulação [s]:", bg="white").grid(row=0, column=1)
    interval_entry = Entry(inputs, width=8)
    interval_entry.grid(row=1, column=1, padx=20)
    interval_entry.insert(0, "1.5")


# ================== GRID ==================
def create_grid(parent):
    frame = Frame(parent)
    frame.pack(pady=20)

    for row in range(2):
        freq_row = []
        phase_row = []

        for col in range(4):
            idx = row * 4 + col + 1

            cell = Frame(frame, bd=1, relief="solid", padx=5, pady=5)
            cell.grid(row=row, column=col, padx=5, pady=5)

            Label(cell, text=f"E{idx}").pack()

            f_entry = Entry(cell, width=6)
            f_entry.pack()
            f_entry.insert(0, "0")

            Label(cell, text="φ").pack()

            p_entry = Entry(cell, width=6)
            p_entry.pack()
            p_entry.insert(0, "0")

            freq_row.append(f_entry)
            phase_row.append(p_entry)

        freq_entries.append(freq_row)
        phase_entries.append(phase_row)


# ================== FUNÇÕES ==================
def get_header_values():
    try:
        ts = float(ts_entry.get())
        interval = float(interval_entry.get())
        return ts, interval
    except:
        messagebox.showerror("Erro", "Valores inválidos.")
        return None


def get_stimulus_data():
    freqs = []
    phases = []

    for i in range(2):
        for j in range(4):
            try:
                f = float(freq_entries[i][j].get())
                p = float(phase_entries[i][j].get())
            except:
                f, p = 0, 0

            freqs.append(f)
            phases.append(p)

    return freqs, phases


# ================== AÇÃO ==================
def gerar_sinal():
    header_values = get_header_values()
    if header_values is None:
        return

    ts, interval = header_values
    freqs, phases = get_stimulus_data()

    try:
        signal_gen_nano.generate_signal(freqs, phases, ts, interval)

        messagebox.showinfo(
            "Sucesso",
            "Sinal gerado com sucesso!\n\nArquivo atualizado."
        )

    except Exception as e:
        messagebox.showerror(
            "Erro",
            f"Ocorreu um erro:\n\n{e}"
        )


# ================== BOTÕES ==================
def create_buttons(parent):
    frame = Frame(parent)
    frame.pack(pady=10)

    Button(
        frame,
        text="Gerar Sinal",
        width=20,
        command=gerar_sinal
    ).pack()


# ================== INIT ==================
def show_start_message():
    messagebox.showinfo(
        "Bem-vindo",
        "Configure os estímulos e gere o sinal."
    )


create_header(window)
create_grid(window)
create_buttons(window)

show_start_message()

window.mainloop()