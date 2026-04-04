"""
_________________________________________________________

SISTEMA DE ESTIMULAÇÃO BCI – MÓDULO DE PRÉ-VISUALIZAÇÃO

Autor: Igor Sforzin
Data: 03.04.26

_________________________________________________________

Descrição:
Este módulo é responsável pela visualização gráfica dos sinais
SSVEP configurados pelo usuário na interface principal.

Os sinais são gerados dinamicamente a partir dos parâmetros de
frequência e fase, permitindo uma verificação visual antes da
geração da LUT utilizada no firmware.

_________________________________________________________

Funcionalidades:
- Geração de sinais senoidais binarizados
- Plotagem dos 40 estímulos
- Interface com rolagem vertical

_________________________________________________________

Integração:
- interface → fornece parâmetros (freq, fase, tempo)
- matplotlib → renderização dos gráficos
- numpy → geração dos sinais

_________________________________________________________
"""

# _________________________________________________________
#
# IMPORTAÇÃO DE BIBLIOTECAS
# _________________________________________________________

import numpy as np
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import os

# _________________________________________________________
#
# CONFIGURAÇÃO DE CAMINHOS (PORTABILIDADE)
# _________________________________________________________

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_PATH = os.path.join(BASE_DIR, "assets", "icon.ico")

# _________________________________________________________
#
# FUNÇÃO PRINCIPAL
# _________________________________________________________

def preview_signals(ts, interval, freqs, phases):
    """
    _________________________________________________________
    
    PRÉ-VISUALIZAÇÃO DOS SINAIS SSVEP
    
    Responsável por:
    - Gerar sinais com base em frequência e fase
    - Exibir os sinais em gráfico multi-canal
    - Permitir análise visual antes da geração da LUT
    
    Entradas:
    - ts        → período de amostragem
    - interval  → tempo de estimulação
    - freqs     → vetor de frequências
    - phases    → vetor de fases
    
    _________________________________________________________
    """

    # _________________________________________________________
    #
    # CONFIGURAÇÃO DO SINAL
    # _________________________________________________________

    interval_preview = min(interval, 0.5)  # limita preview
    num_points = 500

    t = np.linspace(0, interval_preview, num_points)

    # _________________________________________________________
    #
    # CRIAÇÃO DA JANELA
    # _________________________________________________________

    preview_window = tk.Toplevel()
    preview_window.title("Sistema de Estimulação - Preview")
    preview_window.geometry("720x576+250+50")
    preview_window.resizable(False, False)
    preview_window.configure(bg="white")

    try:
        preview_window.iconbitmap(ICON_PATH)
    except:
        print("Erro ao carregar ícone.")

    # _________________________________________________________
    #
    # CANVAS COM SCROLL
    # _________________________________________________________

    canvas = tk.Canvas(preview_window, bg="white", highlightthickness=0)
    canvas.pack(side="left", fill="both", expand=True)

    scrollbar = tk.Scrollbar(preview_window, orient="vertical", command=canvas.yview)
    scrollbar.pack(side="right", fill="y")

    canvas.configure(yscrollcommand=scrollbar.set)

    scroll_frame = tk.Frame(canvas, bg="white")
    canvas.create_window((0, 0), window=scroll_frame, anchor="n")

    scroll_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )

    # _________________________________________________________
    #
    # CONFIGURAÇÃO DA FIGURA
    # _________________________________________________________

    usable_width_pixels = 680
    dpi = 100

    fig_width_inches = usable_width_pixels / dpi
    fig_height_inches = 28  # altura grande para scroll

    fig, axes = plt.subplots(
        40, 1,
        figsize=(fig_width_inches, fig_height_inches),
        sharex=True,
        dpi=dpi
    )

    fig.patch.set_facecolor("white")

    # _________________________________________________________
    #
    # GERAÇÃO DOS SINAIS
    # _________________________________________________________

    for i in range(40):

        if freqs[i] != 0:
            sine = np.sin(2 * np.pi * freqs[i] * t + phases[i])
            signal = (sine >= 0).astype(int)
        else:
            signal = np.zeros_like(t)

        axes[i].plot(t, signal)
        axes[i].set_ylabel(f"S{i+1}", fontsize=7)
        axes[i].set_ylim(-0.2, 1.2)
        axes[i].tick_params(labelsize=6)
        axes[i].grid(True)

    axes[-1].set_xlabel("Tempo (s)", fontsize=8)

    plt.tight_layout()

    # _________________________________________________________
    #
    # EMBUTIR NO TKINTER
    # _________________________________________________________

    canvas_plot = FigureCanvasTkAgg(fig, master=scroll_frame)
    canvas_plot.draw()
    canvas_plot.get_tk_widget().pack(pady=10)