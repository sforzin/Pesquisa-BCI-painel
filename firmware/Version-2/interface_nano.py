from tkinter import *
from tkinter import messagebox, filedialog, scrolledtext
import os
import threading
import subprocess
import serial.tools.list_ports
import signal_gen_nano

# ================== CAMINHOS (auto-detecção) ==================
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
ICON_PATH   = os.path.join(BASE_DIR, "assets", "icon.ico")
LOGO_PATH   = os.path.join(BASE_DIR, "assets", "logo.png")
CONFIG_FILE = os.path.join(BASE_DIR, "pipeline_config.txt")

def _find_xc8():
    for base in [r"C:\Program Files\Microchip\xc8",
                 r"C:\Program Files (x86)\Microchip\xc8"]:
        if not os.path.exists(base):
            continue
        versions = sorted([d for d in os.listdir(base) if d.startswith("v")], reverse=True)
        for v in versions:
            exe = os.path.join(base, v, "bin", "xc8-cc.exe")
            if os.path.exists(exe):
                return os.path.join(base, v, "bin")
    return None

def _find_dfp():
    roots = [
        r"C:\Program Files (x86)\Atmel\Studio\7.0\Packs\atmel\ATmega_DFP",
        r"C:\Program Files\Atmel\Studio\7.0\Packs\atmel\ATmega_DFP",
        r"C:\Program Files (x86)\Microchip\Studio\7.0\Packs\atmel\ATmega_DFP",
        r"C:\Program Files\Microchip\Studio\7.0\Packs\atmel\ATmega_DFP",
    ]
    for root in roots:
        if not os.path.exists(root):
            continue
        versions = sorted(os.listdir(root), reverse=True)
        for v in versions:
            dfp = os.path.join(root, v, "xc8")
            if os.path.exists(dfp):
                return dfp
    return None

def _find_avrdude():
    # 1. Pasta bundled junto com o sistema (embutida pelo instalador)
    bundled = os.path.join(BASE_DIR, "avrdude")
    if os.path.exists(bundled):
        versions = sorted(os.listdir(bundled), reverse=True)
        for v in versions:
            exe  = os.path.join(bundled, v, "bin", "avrdude.exe")
            conf = os.path.join(bundled, v, "etc", "avrdude.conf")
            if os.path.exists(exe) and os.path.exists(conf):
                return exe, conf
    # 2. Fallback: Arduino15 instalado na maquina
    local_app = os.environ.get("LOCALAPPDATA", "")
    base = os.path.join(local_app, "Arduino15", "packages", "arduino", "tools", "avrdude")
    if not os.path.exists(base):
        return None, None
    versions = sorted(os.listdir(base), reverse=True)
    for v in versions:
        exe  = os.path.join(base, v, "bin", "avrdude.exe")
        conf = os.path.join(base, v, "etc", "avrdude.conf")
        if os.path.exists(exe) and os.path.exists(conf):
            return exe, conf
    return None, None

_xc8_bin     = _find_xc8()
XC8_EXE      = os.path.join(_xc8_bin, "xc8-cc.exe")     if _xc8_bin else ""
OBJCOPY_EXE  = os.path.join(_xc8_bin, "avr-objcopy.exe") if _xc8_bin else ""
DFP_PATH     = _find_dfp() or ""
AVRDUDE_EXE, AVRDUDE_CONF = _find_avrdude()
AVRDUDE_EXE  = AVRDUDE_EXE  or ""
AVRDUDE_CONF = AVRDUDE_CONF or ""

# ================== JANELA ==================
window = Tk()
window.title("Interface gráfica Sistema de Estimulação")
window.resizable(True, True)
window.update_idletasks()
screen_w = window.winfo_screenwidth()
screen_h = window.winfo_screenheight()
window.geometry(f"{screen_w}x{screen_h}+0+0")
window.state("zoomed")  # maximiza no Windows

try:
    window.iconbitmap(ICON_PATH)
except:
    pass

# ================== VARIÁVEIS ==================
ts_entry       = None
interval_entry = None
freq_entries   = []
phase_entries  = []

var_src    = StringVar()   # pasta do projeto (onde está main.c e sinal_base.h)
var_mcu    = StringVar(value="atmega328p")
var_baud   = StringVar(value="57600")
var_com    = StringVar(value="—")
com_combo  = None
btn_flash  = None

# ================== PERSISTÊNCIA ==================
def save_config():
    with open(CONFIG_FILE, "w") as f:
        for key, var in [("src", var_src), ("mcu", var_mcu), ("baud", var_baud)]:
            f.write(f"{key}={var.get()}\n")

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return
    with open(CONFIG_FILE) as f:
        for line in f:
            if "=" in line:
                key, _, val = line.strip().partition("=")
                for k, v in [("src", var_src), ("mcu", var_mcu), ("baud", var_baud)]:
                    if key == k:
                        v.set(val)

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

    Label(right, text="CONFIGURAÇÃO DOS ESTÍMULOS",
          font=("Arial", 12, "bold"), bg="white").pack(pady=10)

    inputs = Frame(right, bg="white")
    inputs.pack()

    Label(inputs, text="Ts [µs]:", bg="white").grid(row=0, column=0)
    ts_entry = Entry(inputs, width=8)
    ts_entry.grid(row=1, column=0, padx=20)
    ts_entry.insert(0, "128")

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

# ================== PAINEL PIPELINE ==================
def create_pipeline_config(parent):
    global com_combo

    outer = LabelFrame(parent, text=" Configuração do Pipeline ",
                       font=("Arial", 9, "bold"), padx=10, pady=8)
    outer.pack(fill=X, padx=16, pady=(0, 6))

    # Pasta do projeto
    row1 = Frame(outer)
    row1.pack(fill=X, pady=2)
    Label(row1, text="Pasta do projeto:", width=22, anchor="w").pack(side=LEFT)
    Entry(row1, textvariable=var_src, width=38).pack(side=LEFT, padx=4)
    Button(row1, text="…", width=2,
           command=lambda: var_src.set(filedialog.askdirectory() or var_src.get())
           ).pack(side=LEFT)

    Label(outer, text="(pasta onde estão main.c e sinal_base.h)",
          font=("Arial", 8), fg="gray").pack(anchor="w")

    # MCU + Baud + COM
    bottom = Frame(outer)
    bottom.pack(fill=X, pady=(10, 0))

    Label(bottom, text="MCU:").pack(side=LEFT)
    Entry(bottom, textvariable=var_mcu, width=14).pack(side=LEFT, padx=4)

    Label(bottom, text="Baud:").pack(side=LEFT, padx=(10, 0))
    Entry(bottom, textvariable=var_baud, width=8).pack(side=LEFT, padx=4)

    Label(bottom, text="Porta COM:").pack(side=LEFT, padx=(10, 0))
    com_combo = OptionMenu(bottom, var_com, "—")
    com_combo.config(width=8)
    com_combo.pack(side=LEFT, padx=4)
    Button(bottom, text="↻", command=scan_ports).pack(side=LEFT)

    Button(outer, text="Salvar configuração", command=save_config).pack(
        anchor="e", pady=(8, 0))

    scan_ports()

def scan_ports():
    ports = [p.device for p in serial.tools.list_ports.comports()]
    menu = com_combo["menu"]
    menu.delete(0, "end")
    if ports:
        for p in ports:
            menu.add_command(label=p, command=lambda v=p: var_com.set(v))
        if var_com.get() not in ports:
            var_com.set(ports[0])
    else:
        menu.add_command(label="—", command=lambda: var_com.set("—"))
        var_com.set("—")
        log("[WARN] Nenhuma porta COM detectada.", "warn")

# ================== LOG ==================
log_box = None

def create_log(parent):
    global log_box
    frame = LabelFrame(parent, text=" Log do Pipeline ",
                       font=("Arial", 9, "bold"), padx=6, pady=4)
    frame.pack(fill=X, padx=16, pady=(0, 6))
    log_box = scrolledtext.ScrolledText(
        frame, height=8, font=("Consolas", 9),
        state="disabled", bg="#0d0f14", fg="#e8eaf0")
    log_box.pack(fill=X)
    log_box.tag_config("ok",   foreground="#00e676")
    log_box.tag_config("err",  foreground="#ff1744")
    log_box.tag_config("warn", foreground="#ffab00")
    log_box.tag_config("dim",  foreground="#5a6070")

def log(msg, tag=""):
    log_box.configure(state="normal")
    log_box.insert("end", msg + "\n", tag)
    log_box.see("end")
    log_box.configure(state="disabled")

def log_clear():
    log_box.configure(state="normal")
    log_box.delete("1.0", "end")
    log_box.configure(state="disabled")

# ================== FUNÇÕES ==================
def get_header_values():
    try:
        return float(ts_entry.get()), float(interval_entry.get())
    except:
        messagebox.showerror("Erro", "Valores inválidos.")
        return None

def get_stimulus_data():
    freqs, phases = [], []
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

# ================== GERAR SINAL ==================
def gerar_sinal():
    vals = get_header_values()
    if vals is None:
        return
    ts, interval = vals
    freqs, phases = get_stimulus_data()
    try:
        signal_gen_nano.generate_signal(freqs, phases, ts, interval)
        messagebox.showinfo("Sucesso", "Sinal gerado com sucesso!\n\nArquivo atualizado.")
    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro:\n\n{e}")

# ================== COMPILAR E GRAVAR ==================
def compilar_e_gravar():
    src  = var_src.get()
    mcu  = var_mcu.get()
    baud = var_baud.get()
    port = var_com.get()

    erros = []
    if not src:     erros.append("Pasta do projeto não configurada.")
    if port == "—": erros.append("Nenhuma porta COM selecionada.")
    if erros:
        messagebox.showerror("Configuração incompleta", "\n".join(erros))
        return

    btn_flash.config(state="disabled", text="⏳ Aguarde...")
    log_clear()
    threading.Thread(
        target=_pipeline_thread,
        args=(src, mcu, baud, port),
        daemon=True
    ).start()

def _pipeline_thread(src, mcu, baud, port):
    build_dir = os.path.join(src, "build")
    os.makedirs(build_dir, exist_ok=True)

    main_c   = os.path.join(src, "main.c")
    main_o   = os.path.join(build_dir, "main.o")
    elf_file = os.path.join(build_dir, "nano_version.elf")
    hex_file = os.path.join(build_dir, "nano_version.hex")
    eep_file = os.path.join(build_dir, "nano_version.eep")

    mcu_xc8 = f"AT{mcu}" if not mcu.upper().startswith("AT") else mcu

    # ── Passo 1: Compilar main.c → main.o ────────────────────────────────
    log("━━━  [1/4] Compilando main.c  ━━━", "dim")
    cmd_compile = [
        XC8_EXE,
        f"-mcpu={mcu_xc8}",
        f'-mdfp={DFP_PATH}',
        "-c", "-x", "c",
        "-funsigned-char", "-funsigned-bitfields",
        "-mext=cci",
        f"-D__{mcu_xc8}__", "-DDEBUG",
        "-O0",
        "-ffunction-sections", "-fdata-sections",
        "-fpack-struct", "-fshort-enums",
        "-g2", "-Wall",
        "-MD", "-MP",
        f'-MF{os.path.join(build_dir, "main.d")}',
        f'-MT{os.path.join(build_dir, "main.d")}',
        f'-MT{main_o}',
        f"-I{src}",          # inclui sinal_base.h da pasta do projeto
        "-o", main_o,
        main_c
    ]
    ok = _run_cmd(cmd_compile, "Compilação")
    if not ok:
        _done(False)
        return

    # ── Passo 2: Linkar main.o → nano_version.elf ────────────────────────
    log("━━━  [2/4] Linkando  ━━━", "dim")
    cmd_link = [
        XC8_EXE,
        "-o", elf_file,
        main_o,
        f"-mcpu={mcu_xc8}",
        f'-mdfp={DFP_PATH}',
        f'-Wl,-Map={os.path.join(build_dir, "nano_version.map")}',
        "-funsigned-char", "-funsigned-bitfields",
        "-Wl,--start-group", "-Wl,-lm", "-Wl,--end-group",
        "-Wl,--gc-sections",
        "-O0",
        "-ffunction-sections", "-fdata-sections",
        "-fpack-struct", "-fshort-enums",
        f"--memorysummary,{os.path.join(build_dir, 'memoryfile.xml')}"
    ]
    ok = _run_cmd(cmd_link, "Link")
    if not ok:
        _done(False)
        return

    # ── Passo 3: .elf → .hex ─────────────────────────────────────────────
    log("━━━  [3/4] Gerando .hex  ━━━", "dim")
    cmd_hex = [
        OBJCOPY_EXE,
        "-O", "ihex",
        "-R", ".eeprom", "-R", ".fuse", "-R", ".lock",
        "-R", ".signature", "-R", ".user_signatures",
        elf_file, hex_file
    ]
    ok = _run_cmd(cmd_hex, "objcopy hex")
    if not ok:
        _done(False)
        return

    # ── Passo 4: .elf → .eep ─────────────────────────────────────────────
    log("━━━  [4/4] Gerando .eep  ━━━", "dim")
    cmd_eep = [
        OBJCOPY_EXE,
        "-j", ".eeprom",
        "--set-section-flags=.eeprom=alloc,load",
        "--change-section-lma", ".eeprom=0",
        "--no-change-warnings",
        "-O", "ihex",
        elf_file, eep_file
    ]
    _run_cmd(cmd_eep, "objcopy eep")  # não aborta se falhar

    # ── Passo 5: avrdude ─────────────────────────────────────────────────
    log("━━━  [5/5] Gravando com avrdude  ━━━", "dim")
    cmd_avr = [
        AVRDUDE_EXE,
        f"-C{AVRDUDE_CONF}",
        "-v", "-V",
        f"-p{mcu}",
        "-carduino",
        f"-P{port}",
        f"-b{baud}",
        "-D",
        f"-Uflash:w:{hex_file}:i"
    ]
    ok = _run_cmd(cmd_avr, "avrdude")
    _done(ok)

def _run_cmd(cmd, label):
    log(f"$ {' '.join(cmd)}", "dim")
    try:
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            cwd=os.path.join(var_src.get(), "build")
        )
        for line in proc.stdout:
            line = line.rstrip()
            if not line:
                continue
            low = line.lower()
            tag = "err" if "error" in low else ("warn" if "warning" in low else "")
            log(line, tag)
        proc.wait()
        if proc.returncode == 0:
            log(f"[OK] {label} concluído.\n", "ok")
            return True
        else:
            log(f"[ERRO] {label} falhou (código {proc.returncode}).\n", "err")
            return False
    except FileNotFoundError:
        log(f"[ERRO] Executável não encontrado: {cmd[0]}", "err")
        return False

def _done(success):
    if success:
        log("✔  Pipeline concluído com sucesso!", "ok")
        window.after(0, lambda: messagebox.showinfo(
            "Sucesso", "Build e gravação concluídos!"))
    else:
        log("✘  Pipeline encerrado com erros.", "err")
        window.after(0, lambda: messagebox.showerror(
            "Erro", "Falha no pipeline.\nVeja o log."))
    window.after(0, lambda: btn_flash.config(
        state="normal", text="▶ Compilar e Gravar"))

# ================== BOTÕES ==================
def create_buttons(parent):
    global btn_flash
    frame = Frame(parent)
    frame.pack(pady=8)

    Button(frame, text="Gerar Sinal", width=20,
           command=gerar_sinal).pack(side=LEFT, padx=8)

    btn_flash = Button(
        frame, text="▶ Compilar e Gravar", width=22,
        bg="#1565C0", fg="white",
        activebackground="#0d47a1", activeforeground="white",
        relief="flat", command=compilar_e_gravar
    )
    btn_flash.pack(side=LEFT, padx=8)

# ================== SCROLL CONTAINER ==================
def create_scroll_container(root):
    outer = Frame(root)
    outer.pack(fill=BOTH, expand=True)

    canvas = Canvas(outer, borderwidth=0, highlightthickness=0)
    scrollbar = Scrollbar(outer, orient=VERTICAL, command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side=RIGHT, fill=Y)
    canvas.pack(side=LEFT, fill=BOTH, expand=True)

    inner = Frame(canvas)
    canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

    def on_frame_configure(event):
        canvas.configure(scrollregion=canvas.bbox("all"))

    def on_canvas_configure(event):
        canvas.itemconfig(canvas_window, width=event.width)

    def on_mousewheel(event):
        canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    inner.bind("<Configure>", on_frame_configure)
    canvas.bind("<Configure>", on_canvas_configure)
    canvas.bind_all("<MouseWheel>", on_mousewheel)

    return inner

# ================== INIT ==================
load_config()
content = create_scroll_container(window)
create_header(content)
create_grid(content)
create_pipeline_config(content)
create_log(content)
create_buttons(content)

messagebox.showinfo("Bem-vindo", "Configure os estímulos e gere o sinal.")

window.mainloop()
