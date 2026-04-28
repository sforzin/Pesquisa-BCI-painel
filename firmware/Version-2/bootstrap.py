"""
bootstrap.py — Ponto de entrada do Sistema de Estimulação BCI
Verifica dependências e abre a interface principal.
"""

import sys
import os
import subprocess

REQUIRED = ["numpy", "serial"]   # serial = pyserial

def check_and_install():
    missing = []
    for pkg in REQUIRED:
        try:
            __import__(pkg)
        except ImportError:
            missing.append("pyserial" if pkg == "serial" else pkg)

    if missing:
        print(f"Instalando dependências faltantes: {missing}")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet"] + missing
        )

def main():
    check_and_install()

    # Garante que o diretório do script é o cwd
    base = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base)
    sys.path.insert(0, base)

    # Abre a interface
    import interface_nano  # noqa

if __name__ == "__main__":
    main()
