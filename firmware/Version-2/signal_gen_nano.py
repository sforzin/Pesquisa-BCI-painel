"""
___________________________________________________________

SISTEMA DE ESTIMULAÇÃO BCI – MÓDULO GERADOR DE SINAIS

Autor: Igor Sforzin
Data: 03.04.26

___________________________________________________________

Este módulo é responsável por:

1. Gerar sinais senoidais a partir de frequências e fases
2. Converter os sinais para formato digital (binário)
3. Organizar os dados em pacotes de bytes
4. Gerar automaticamente um arquivo .h compatível com AVR

Observações:
- O vetor de tempo não inclui o ponto final (endpoint=False)
  visando melhor precisão na frequência gerada.
- O sistema foi projetado para uso com leitura em memória
  FLASH (PROGMEM) no microcontrolador.

___________________________________________________________
"""

# _________________________________________________________
#
# IMPORTAÇÃO DE BIBLIOTECAS
# _________________________________________________________

import numpy as np

# _________________________________________________________
#
# FUNÇÃO PRINCIPAL
# _________________________________________________________

def generate_signal(freqs, fases, Ts, interval):

    # _________________________________________________________
    #
    # AJUSTE DOS PARÂMETROS DE AMOSTRAGEM
    # _________________________________________________________

    ts = int(Ts)
    Ts = ts * 1e-6

    interval = float(interval)

    Fs = int(interval / Ts)                       # Número de amostras
    x = np.linspace(0, interval, Fs, endpoint=False)  # Vetor temporal

    # _________________________________________________________
    #
    # VERIFICAÇÃO DE LIMITE DE MEMÓRIA
    # _________________________________________________________

    if (len(x) * len(freqs)) / 8 > 30000:
        print("Overflow de memória do Arduino!")

    # _________________________________________________________
    #
    # GERAÇÃO DO SINAL SENOIDAL
    # _________________________________________________________

    def signal_sin(freqs, fases, x):

        Y = []

        for i in range(len(freqs)):
            y_sen = np.sin(2 * np.pi * freqs[i] * x + fases[i])
            Y.append(y_sen)

        return np.array(Y)

    signal_sin = signal_sin(freqs, fases, x)

    # _________________________________________________________
    #
    # CONVERSÃO PARA SINAL BINÁRIO
    # _________________________________________________________

    def signal_bin(signal_sin):

        Y = []

        for i in range(len(signal_sin)):
            ret_wave = [1 if val > 0 else 0 for val in signal_sin[i]]
            Y.append(ret_wave)

        return np.array(Y)

    signal_bin = signal_bin(signal_sin)

    # _________________________________________________________
    #
    # ALOCAÇÃO DOS DADOS EM PACOTES DE BYTES
    # _________________________________________________________

    def allocation_data(signal_bin, freqs):

        pack = int(np.ceil(len(freqs) / 8))   # Número de bytes por amostra
        print(pack)
        data_allocated = []
        num_ams = len(signal_bin[0])

        for ams_i in range(num_ams):

            pack_temp = []

            for k in range(pack):

                bits = []

                for j in range(8):

                    freq_i = k * 8 + j

                    if freq_i < len(freqs) and freqs[freq_i] != 0:
                        bit = signal_bin[freq_i][ams_i]
                        bits.append(str(bit))
                    else:
                        bits.append('0')

                byte_str = ''.join(bits)
                byte_hex = hex(int(byte_str, 2))

                pack_temp.append(byte_hex)

            data_allocated.append(pack_temp)

        # Flatten da matriz
        data = []

        for i in range(num_ams):
            for k in range(pack):
                data.append(data_allocated[i][k])

        return np.array(data)

    data = allocation_data(signal_bin, freqs)

    # _________________________________________________________
    #
    # GERAÇÃO DO ARQUIVO HEADER (.h)
    # _________________________________________________________

    def save_to_header(data, filename="sinal_base.h"):

        data_bytes = [int(byte, 16) for byte in data]

        # Número de blocos de até 256 bytes
        num_parts = (len(data_bytes) + 255) // 256

        with open(filename, "w") as f:

            # Header guard
            f.write("#ifndef SIGNAL_H\n#define SIGNAL_H\n\n")

            # Biblioteca PROGMEM
            f.write("#include <avr/pgmspace.h>\n\n")

            # Escrita dos blocos
            for part in range(num_parts):

                part_data = data_bytes[part*256:(part+1)*256]

                f.write(f"const uint8_t signal_part{part}[] PROGMEM = {{\n")

                for i in range(0, len(part_data), 16):
                    linha = part_data[i:i+16]
                    f.write("  " + ", ".join(f"0x{b:02X}" for b in linha) + ",\n")

                f.write("};\n\n")

            # Parâmetros globais
            f.write(f"const uint32_t signal_len = {len(data_bytes)};\n")
            f.write(f"const uint16_t Ts = 0x{((ts*2)-1):04X};\n")

            # Vetor de ponteiros
            f.write(f"const uint8_t* const signal_parts[{num_parts}] PROGMEM = {{")

            for part in range(num_parts):
                f.write(f"signal_part{part},")

            f.write("};\n\n#endif // SIGNAL_H\n")

    save_to_header(data)

    print("Arquivo sinal_base.h gerado com sucesso!")


# _________________________________________________________
#
# EXECUÇÃO DIRETA (DEBUG / TESTE)
# _________________________________________________________

if __name__ == "__main__":
    print("Este módulo deve ser chamado pela interface.")