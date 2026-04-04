"""
_________________________________________________________

SISTEMA DE ESTIMULAÇÃO BCI – INTERFACE GRÁFICA

Autor: Igor Sforzin
Data: 03.04.26

_________________________________________________________

Descrição:
Este programa implementa a interface gráfica responsável pela
configuração dos estímulos utilizados no sistema de estimulação.

A interface permite ao usuário definir os parâmetros dos estímulos
e gerar automaticamente a tabela de consulta (Look-Up Table – LUT)
utilizada no firmware embarcado.

_________________________________________________________

Funcionalidades:
- Ativação e desativação de estímulos individuais
- Configuração de frequência (Hz) e fase (rad)
- Definição dos parâmetros globais:
    • Período de amostragem (Ts)
    • Tempo de estimulação
    • Tempo de repouso
- Pré-visualização dos sinais gerados
- Estimativa de uso de memória
- Geração automática do arquivo "sinal_base.h"

_________________________________________________________

Integração:
- preview  → Visualização dos sinais
- signal_gen → Geração da LUT para o firmware
_________________________________________________________
"""

# _________________________________________________________
#
# IMPORTAÇÃO DE BIBLIOTECAS
# _________________________________________________________

from tkinter import *
from tkinter import PhotoImage, messagebox, ttk
import tkinter as tk

import math
import preview
import signal_gen
import os

# Diretório do sistema
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "assets", "icon.ico")
LOGO_PATH = os.path.join(BASE_DIR, "assets", "dspcom.png")

# _________________________________________________________
#
# CONFIGURAÇÃO DA JANELA PRINCIPAL
# _________________________________________________________

window = Tk()
window.title("Inteface gráfica Sistema de Estimulação")
window.geometry("720x576+250+50")
window.resizable(False, False)
window.iconbitmap(ICON_PATH)

messagebox.showinfo(
    "Seja Bem-vindo",
    "Recomendações para utilização:\n\n"
    "• Selecione apenas os estímulos desejados.\n"
    "• A frequência esta em Hz e a fase em Rad. \n"
    "• Adicione o período de amostragem.\n"
    "• Adicione o intervalo de estimulação e descanso.\n"
    "• Observe o limite de memória no rodapé (250kB)\n\n"
    "Use o botão Pré-visualizar e confira os sinais antes de gerá-los."
)

# _________________________________________________________
#
# FUNÇÕES AUXILIARES
# _________________________________________________________

def get_header_values():
    """
    Coleta Ts, intervalo e repouso
    """
    try:
        ts = float(ts_entry.get())
        interval = float(interval_entry.get())
        rest = float(rest_entry.get())
        return ts, interval, rest
    except ValueError:
        print("Erro: Verifique os valores do header.")
        return None


def get_stimulus_data():
    """
    Retorna vetores de frequência e fase
    """
    freqs = []
    phases = []

    for stim in stim_controls:
        if stim["active"]:
            try:
                f = float(stim["freq"].get())
            except ValueError:
                f = 0

            try:
                p = float(stim["phase"].get())
            except ValueError:
                p = 0
        else:
            f = 0
            p = 0

        freqs.append(f)
        phases.append(p)

    return freqs, phases


def sair_aplicacao():
    window.destroy()


def update_memory():
    header = get_header_values()

    if header is None:
        memory_label.config(text="Memória estimada: erro")
        return

    ts, interval, _ = header

    if ts <= 0 or interval <= 0:
        memory_label.config(text="Memória estimada: erro")
        return

    samples = interval / (ts * 1e-6)
    estimated_bytes = math.ceil(samples * 5)

    memory_label.config(text=f"Memória estimada: {estimated_bytes} bytes")

    if estimated_bytes > 250000:
        memory_label.config(fg="red")
    else:
        memory_label.config(fg="black")


def on_preview():
    header = get_header_values()
    if header is None:
        return

    ts, interval, _ = header
    freqs, phases = get_stimulus_data()

    preview.preview_signals(ts, interval, freqs, phases)


def gerar_sinal():
    header_values = get_header_values()
    if header_values is None:
        return

    ts, interval, rest = header_values
    freqs, phases = get_stimulus_data()

    progress_window = tk.Toplevel(window)
    progress_window.title("Gerando Sinal")
    progress_window.geometry("320x110+450+300")
    progress_window.resizable(False, False)
    progress_window.grab_set()

    tk.Label(progress_window, text="Gerando arquivo sinal_base.h...").pack(pady=10)

    progress = ttk.Progressbar(progress_window, orient="horizontal", length=260, mode="determinate")
    progress.pack(pady=5)

    try:
        for i in range(0, 70, 10):
            progress["value"] = i
            progress_window.update()
            window.after(40)

        signal_gen.generate_signal(freqs, phases, ts, interval, rest)

        progress["value"] = 100
        progress_window.update()

        progress_window.destroy()

        messagebox.showinfo("Sucesso", "Sinal gerado com sucesso!")

    except Exception as e:
        progress_window.destroy()
        messagebox.showerror("Erro", str(e))

# _________________________________________________________
#
# HEADER UI
# _________________________________________________________

header_frame = Frame(window, width=700, height=220, bg="white")
header_frame.pack_propagate(False)
header_frame.pack()

logo_frame = Frame(header_frame, width=185, height=220, bg="white")
logo_frame.pack(side=LEFT)

logo_img = PhotoImage(file=LOGO_PATH)
Label(logo_frame, image=logo_img, bg="white").pack()

right_header = Frame(header_frame, width=515, height=220, bg="white")
right_header.pack(side=LEFT)

menu_frame = Frame(right_header, bg="white")
menu_frame.pack()

Label(menu_frame, text="Ts [µs]:").place(x=40, y=20)
ts_entry = Entry(menu_frame, width=8)
ts_entry.place(x=40, y=45)
ts_entry.insert(0, "128")

Label(menu_frame, text="Estimulação [s]:").place(x=200, y=20)
interval_entry = Entry(menu_frame, width=8)
interval_entry.place(x=200, y=45)
interval_entry.insert(0, "1.5")

Label(menu_frame, text="Repouso [s]:").place(x=360, y=20)
rest_entry = Entry(menu_frame, width=8)
rest_entry.place(x=360, y=45)
rest_entry.insert(0, "1.5")

# _________________________________________________________
#
# GRID DE ESTÍMULOS
# _________________________________________________________

main_frame = Frame(window, bg="white")
main_frame.pack()

stim_controls = []

for row in range(5):
    for col in range(8):
        index = row * 8 + col

        cell = Frame(main_frame, bd=1, relief="solid")
        cell.grid(row=row, column=col)

        btn = Button(cell, text=str(index+1), bg="lightgray")
        btn.pack()

        freq = Entry(cell, width=4)
        freq.pack(side=LEFT)

        phase = Entry(cell, width=4)
        phase.pack(side=LEFT)

        stim_controls.append({
            "button": btn,
            "freq": freq,
            "phase": phase,
            "active": False
        })

        def make_toggle(i):
            def toggle():
                stim_controls[i]["active"] = not stim_controls[i]["active"]
                color = "green" if stim_controls[i]["active"] else "lightgray"
                stim_controls[i]["button"].config(bg=color)
                update_memory()
            return toggle

        btn.config(command=make_toggle(index))

# _________________________________________________________
#
# FOOTER
# _________________________________________________________

footer = Frame(window)
footer.pack(side=BOTTOM)

memory_label = Label(footer, text="Memória estimada: 0 bytes")
memory_label.pack(side=LEFT)

Button(footer, text="Pré-visualizar", command=on_preview).pack(side=RIGHT)
Button(footer, text="Gerar sinal", command=gerar_sinal).pack(side=RIGHT)
Button(footer, text="Sair", command=sair_aplicacao).pack(side=RIGHT)

# _________________________________________________________
#
# EXECUÇÃO
# _________________________________________________________

update_memory()
window.mainloop()