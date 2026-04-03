/**
 * _________________________________________________________
 *
 * @file main.c
 * Execução dos sinais de estimulação SSVEP
 * _________________________________________________________
 *
 * DETALHES
 * Firmware responsável pela apresentação dos sinais de estimulação visual no paradigma SSVEP.
 *
 * O sistema realiza a leitura de uma LUT (Look-Up Table) armazenada na memória
 * Flash, contendo as amostras dos sinais de estimulação previamente gerados.
 *
 * A temporização é realizada por meio de interrupções de hardware (Timer1), na qual
 * a duração do tratamento da interrupção corresponde ao período de amostragem do
 * sinal salvo.
 *
 * Fluxo:
 * - Apresenta amostra atual (RAM)
 * - Carrega próxima amostra (FLASH ? RAM)
 *
 * Funcionalidades:
 * - Controle de janelas de estimulação
 * - Períodos de descanso entre estímulos
 * - Comunicação UART
 *
 * Plataforma: ATmega2560
 * Projeto: BCI-SSVEP DSPCOM
 * Autor: Igor Sforzin
 * _________________________________________________________
 */

/**
 * _________________________________________________________
 * ATENÇÃO
 * _________________________________________________________
 *
 * Este sistema depende de temporização precisa.
 *
 * Alterações críticas:
 * - ISRs
 * - Ordem de execução
 * - Timers
 *
 * Validar experimentalmente.
 * _________________________________________________________
 */

/**
 * _________________________________________________________
 * BIBLIOTECAS E MACROS
 * _________________________________________________________
 */

#include <stdlib.h>
#include <stdio.h>
#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/pgmspace.h>
#include "sinal_base.h"

#define F_CPU 16000000UL

/**
 * _________________________________________________________
 * VARIÁVEIS GLOBAIS
 * _________________________________________________________
 */

// Variáveis de controle de leitura da LUT
uint32_t lut_add = 0x00;
/* Armazena o endereço base da Look-Up Table (LUT) na memória.
* Utilizado como ponteiro para acesso sequencial aos dados
* de estimulação armazenados em Flash.
*/
uint8_t ctrl = 0x00;
/*
* Variável de controle geral do sistema.
* Utilizada como flag de estado no controle do fluxo
* de apresentação do sinal no algoritmo principal.
*/
uint8_t upd_end = 0x00;
/*
* Indica condição de término ou atualização de leitura da LUT.
* Utilizada para controle de fim de ciclo ou reinício da sequência.
*/
uint16_t part_index;
uint8_t part_offset;
uint8_t value;

// Variáveis data buffer das portas
uint8_t data_a;
uint8_t data_c;
uint8_t data_f;
uint8_t data_k;
uint8_t data_l;

// Variável para controle entre janelas (Período de descanso)
uint8_t wait = 0x00;

// Variáveis para recebimento dos dados da UART
volatile unsigned char windows_control;
unsigned char buffer_index = 0;
unsigned char buffer_data_vec[3];
char data_UART;

/**
 * _________________________________________________________
 * CONFIGURAÇÃO
 * _________________________________________________________
 */

void config() {

	/**
     * _________________________________________________________
     * UART 
     * _________________________________________________________
     */
	
	/* _________________________________________________________
	 *
	 * UCSR0A – Registrador de controle e status A da USART0
	 *
	 * Bit:   7     6     5     4     3     2     1     0
	 *       -----------------------------------------------------
	 *       RXC0  TXC0  UDRE0 FE0   DOR0  UPE0 U2X0  MPCM0
	 *        0     0     0     0     0     0     1     0
	 *
	 * U2X0 = 1:
	 * Habilita modo double speed, aumentando a precisão do baud rate.
	 *
	 * Os demais bits não são utilizados diretamente.
	 * _________________________________________________________
	 */
	UCSR0A = 0x02;
	
	/* _________________________________________________________
	 *
	 * UCSR0B – Registrador de controle e status B da USART0
	 *
	 * Bit:   7      6      5      4      3      2      1      0
	 *       -----------------------------------------------------
	 *      RXCIE0 TXCIE0 UDRIE0 RXEN0  TXEN0  UCSZ02 RXB80 TXB80
	 *        1      0      0      1      1      0      0      0
	 *
	 * RXCIE0 = 1:
	 * Habilita interrupção de recepção UART.
	 *
	 * RXEN0 = 1:
	 * Habilita o receptor UART.
	 *
	 * TXEN0 = 1:
	 * Habilita o transmissor UART.
	 *
	 * Os demais bits não são utilizados.
	 * _________________________________________________________
	 */
    UCSR0B = 0x98;
	
	/* _________________________________________________________
	 *
	 * UCSR0C – Registrador de controle e status C da USART0
	 *
	 * Bit:   7       6       5      4      3      2      1      0
	 *       -----------------------------------------------------
	 *      UMSEL01 UMSEL00 UPM01  UPM00  USBS0 UCSZ01 UCSZ00 UCPOL0
	 *        0       0       0      0      0      1      1      0
	 *
	 * UCSZ01:0 = 11:
	 * Define 8 bits de dados.
	 *
	 * USBS0 = 0:
	 * Define 1 bit de parada.
	 *
	 * UPM01:0 = 00:
	 * Sem paridade.
	 * _________________________________________________________
	 */
    UCSR0C = 0x06;
	
	/* _________________________________________________________
	 *
	 * UBRR0 – Registrador de baud rate da USART0
	 *
	 * Valor: 0x00CF
	 *
	 * Baud rate configurado: 9600 bps
	 *
	 * Fórmula:
	 * Baud = F_CPU / (8 * (UBRR + 1))
	 *
	 * Considerando:
	 * F_CPU = 16 MHz
	 * U2X0 = 1
	 *
	 * _________________________________________________________
	 */
    UBRR0H = 0x00;
    UBRR0L = 0xCF;
	
	/* _________________________________________________________
	 *
	 * DDRA – Registrador de direção de dados da porta A
	 *
	 * Bit:   7     6     5     4     3     2     1     0
	 *       -----------------------------------------------------
	 *        1     1     1     1     1     1     1     1
	 *
	 * Todos os pinos configurados como saída.
	 *
	 * Utilização:
	 * Envio de sinais digitais de estimulação SSVEP.
	 *
	 * _________________________________________________________
	 */
    DDRA |= 0xFF;
	
	/* _________________________________________________________
	 *
	 * DDRC – Registrador de direção de dados da porta C
	 *
	 * Bit:   7     6     5     4     3     2     1     0
	 *       -----------------------------------------------------
	 *        1     1     1     1     1     1     1     1
	 *
	 * Todos os pinos configurados como saída.
	 *
	 * Utilização:
	 * Envio de sinais digitais de estimulação SSVEP.
	 *
	 * _________________________________________________________
	 */
    DDRC |= 0xFF;
	
    /* _________________________________________________________
	 *
	 * DDRF – Registrador de direção de dados da porta F
	 *
	 * Bit:   7     6     5     4     3     2     1     0
	 *       -----------------------------------------------------
	 *        1     1     1     1     1     1     1     1
	 *
	 * Todos os pinos configurados como saída.
	 *
	 * Utilização:
	 * Envio de sinais digitais de estimulação SSVEP.
	 *
	 * _________________________________________________________
	 */
    DDRF |= 0xFF;
	
    /* _________________________________________________________
	 *
	 * DDRK – Registrador de direção de dados da porta K
	 *
	 * Bit:   7     6     5     4     3     2     1     0
	 *       -----------------------------------------------------
	 *        1     1     1     1     1     1     1     1
	 *
	 * Todos os pinos configurados como saída.
	 *
	 * Utilização:
	 * Envio de sinais digitais de estimulação SSVEP.
	 *
	 * _________________________________________________________
	 */
    DDRK |= 0xFF;
	
    /* _________________________________________________________
	 *
	 * DDRL – Registrador de direção de dados da porta L
	 *
	 * Bit:   7     6     5     4     3     2     1     0
	 *       -----------------------------------------------------
	 *        1     1     1     1     1     1     1     1
	 *
	 * Todos os pinos configurados como saída.
	 *
	 * Utilização:
	 * Envio de sinais digitais de estimulação SSVEP.
	 *
	 * _________________________________________________________
	 */
    DDRL |= 0xFF;

    /* _________________________________________________________
	 *
	 * DDRD – Registrador de direção de dados da porta D
	 *
	 * Bit:   7     6     5     4     3     2     1     0
	 *       -----------------------------------------------------
	 *        0     0     0     0     0     0     0     1
	 *
	 * Todos os pinos configurados como saída.
	 *
	 * Utilização:
	 * Envio de sinais digitais de estimulação SSVEP.
	 *
	 * _________________________________________________________
	 */
    DDRD = (1<<0);
    
	/**
     * _________________________________________________________
     * TIMER 1
     * _________________________________________________________
     */
	
	/* _________________________________________________________
	 *
	 * TCCR1A – Registrador de controle A do Timer1
	 *
	 * Bit:   7     6     5     4     3     2     1     0
	 *       -----------------------------------------------------
	 *      COM1A1 COM1A0 COM1B1 COM1B0  -     -   WGM11 WGM10
	 *        0      0      0      0      0     0     0     0
	 *
	 * Modo normal (sem PWM).
	 *
	 * _________________________________________________________
	 */
    TCCR1A = 0x00;
	
	/* _________________________________________________________
	 *
	 * TCCR1B – Registrador de controle B do Timer1
	 *
	 * Bit:   7     6     5     4     3     2     1     0
	 *       -----------------------------------------------------
	 *      ICNC1 ICES1   -   WGM13 WGM12 CS12 CS11 CS10
	 *        0     0     0     0     1     0     1     0
	 *
	 * WGM12 = 1:
	 * Modo CTC (Clear Timer on Compare Match).
	 *
	 * CS11 = 1:
	 * Prescaler = 8. **ATIVADA SOMENTE NO INICIO DA TEMPORIZAÇÃO
	 *
	 * Função:
	 * Define a frequência de atualização dos estímulos.
	 *
	 * _________________________________________________________
	 */
    TCCR1B = (1 << WGM12);
    
	OCR1A = Ts;	// Valor do período de amostagem do sinal para o contador 
    TCNT1 = 0;  // Zera o buffer do contador
	
	/* _________________________________________________________
	 *
	 * TIMSK1 – Registrador de máscara de interrupção do Timer1
	 *
	 * Bit:   7     6     5     4     3     2     1     0
	 *       -----------------------------------------------------
	 *        X     X     ICIE1 X     X     OCIE1B OCIE1A TOIE1
	 *        X     X      0    X     X       0       1      0
	 *
	 * OCIE1A = 1:
	 * Habilita interrupção por comparação A.
	 *
	 * _________________________________________________________
	 */
    TIMSK1 |= (1 << OCIE1A);
	
	/**
     * _________________________________________________________
     * TIMER 3
     * _________________________________________________________
     */
	
	/* _________________________________________________________
	 *
	 * TCCR3A – Registrador de controle A do Timer3
	 *
	 * Bit:   7      6      5      4     3     2     1     0
	 *       -----------------------------------------------------
	 *      COM3A1 COM3A0 COM3B1 COM3B0  -     -   WGM31 WGM30
	 *        0      0      0      0     0     0     0     0
	 *
	 * Modo normal.
	 *
	 * _________________________________________________________
	 */
    TCCR3A = 0x00;
	
	/* _________________________________________________________
	 *
	 * TCCR3B – Registrador de controle B do Timer3
	 *
	 * Bit:   7     6     5     4     3     2     1     0
	 *       -----------------------------------------------------
	 *      ICNC3 ICES3   -   WGM33 WGM32 CS32  CS31  CS30
	 *        0     0     0     0     1     1     0     1
	 *
	 * WGM32 = 1:
	 * Modo CTC.
	 *
	 * CS3[2:0] = 101:
	 * Prescaler = 1024. **ATIVADA SOMENTE NO INICIO DA TEMPORIZAÇÃO
	 *
	 * Função:
	 * Controle do tempo de descanso entre estímulos.
	 *
	 * _________________________________________________________
	 */
    TCCR3B = (1 << WGM32);
	
    OCR3A = rest_pause; // Valor do período de descanso para o contador
    TCNT3 = 0;			// Zera o buffer do contador
	
	/* _________________________________________________________
	 *
	 * TIMSK3 – Registrador de máscara de interrupção do Timer3
	 *
	 * Bit:   7     6     5     4     3      2      1     0
	 *       -----------------------------------------------------
	 *        X     X   ICIE3   X     X   OCIE3B OCIE3A TOIE3
	 *        X     X     X     X     X      0      1     0
	 *
	 * OCIE3A = 1:
	 * Habilita interrupção de comparação do Timer3.
	 *
	 * _________________________________________________________
	 */
    TIMSK3 |= (1 << OCIE3A);

    /**
     * _________________________________________________________
     * PRIMEIRA AMOSTRA (Descrição do algoritmo na ISR Timer 1)
     * _________________________________________________________
     */
	
	PORTD = (1<<0); // Marcação para cyton (FORA DA ESTIMULAÇÃO)
    while (!upd_end){
		
        part_index  = lut_add >> 8;
        part_offset = lut_add & 0xFF;

        value = pgm_read_byte_far((uint32_t)(&signal_parts[part_index][part_offset]));

        switch (ctrl) {
            case(0x00): data_a = value; break;
            case(0x01): data_c = value; break;
            case(0x02): data_f = value; break;
            case(0x03): data_k = value; break;
            case(0x04):
                data_l = value;
                upd_end = 0x01;
            break;
        }

        ctrl++;
        lut_add++;
    }
}

/**
 * _________________________________________________________
 * ISR TIMER 1
 * _________________________________________________________
 */

/**
 * Rotina de interrupção do Timer1 (Compare Match A)
 *
 * Responsável por:
 * - Atualizar as portas de saída com os dados atuais
 * - Percorrer a LUT armazenada na memória Flash
 * - Carregar novos dados para o próximo ciclo de saída
 * - Verificar o fim da execução do sinal
 *
 * Funcionamento:
 * A cada interrupção:
 * 1. Os valores atuais são enviados às portas
 * 2. São lidos 5 novos valores da LUT
 * 3. Cada valor é direcionado para uma porta específica
 * 4. Ao final da LUT, o sistema reinicia e pausa o timer
 * _________________________________________________________
 */
ISR(TIMER1_COMPA_vect) {

    // Atualiza as portas de saída com os dados carregados
    PORTK = data_k;
    PORTA = data_a;
    PORTC = data_c;
    PORTF = data_f;
    PORTL = data_l;

    // Verifica se o final da LUT foi atingido
    if (lut_add >= signal_len) {
        lut_add = 0;      // Reinicia índice da LUT
        wait = 0x01;      // Sinaliza estado de descanso
        TCCR1B = 0x08;    // Para o Timer1 (sem clock)
    }

    // Inicializa variáveis de controle da leitura
    ctrl = 0x00;
    upd_end = 0;

    // Loop para leitura de 5 bytes da LUT
    while (!upd_end){

        // Calcula índice da partição da LUT
        part_index  = lut_add >> 8;
        // Calcula offset dentro da partição
        part_offset = lut_add & 0xFF;

        // Lê dado da memória Flash
        value = pgm_read_byte_far((uint32_t)(&signal_parts[part_index][part_offset]));

        // Direciona o valor lido para a respectiva porta
        switch (ctrl) {
            case(0x00): data_a = value; break; // Porta A
            case(0x01): data_c = value; break; // Porta C
            case(0x02): data_f = value; break; // Porta F
            case(0x03): data_k = value; break; // Porta K
            case(0x04):
                data_l = value;    // Porta L
                upd_end = 0x01;    // Finaliza leitura do ciclo
            break;
        }

        // Avança controle e endereço da LUT
        ctrl++; // Reset do indexador de atualização dos buffers acima
        lut_add++;
    }
}

/**
 * _________________________________________________________
 * ISR TIMER 3
 * _________________________________________________________
 */

/**
 * Rotina de interrupção do Timer3 (Compare Match A)
 *
 * Responsável por:
 * - Controlar o tempo de descanso
 * - Sincronizar o reinício do Timer1
 * - Gerenciar a variável de controle de janelas (windows_control)
 *
 * Funcionamento:
 * A cada interrupção:
 * 1. O Timer3 é interrompido
 * 2. Os contadores dos Timers 1 e 3 são resetados
 * 3. O contador de janelas é decrementado
 * 4. Caso ainda existam janelas a serem executadas:
 *    - O Timer1 é reativado
 * ________________________________________________________
 */
ISR(TIMER3_COMPA_vect){

    // Para o Timer3
    TCCR3B = 0x08;

    // Reinicia os contadores dos timers
    TCNT3 = 0;
    TCNT1 = 0;

    // Decrementa o número de janelas restantes 
    windows_control--;

    // Verifica se ainda há janelas de estimulação
    if (windows_control > 0){

        // Reativa o Timer1 (Ou seja, uma nova janela de estimulação)
        TCCR1B = 0x0A;
		// Marca a estimulação na próxima (primeira) amostra, assim como é feito nas configs
        PORTD = 0x00; 
    }
}

/**
 * _________________________________________________________
 * ISR UART
 * _________________________________________________________
 */

/**
 * Rotina de interrupção da UART
 *
 * Responsável por:
 * - Receber dados da interface serial
 * - Armazenar os dados em buffer
 * - Interpretar comandos recebidos
 * - Inicializar a sequência de estimulação
 *
 * Funcionamento:
 * A cada byte recebido:
 * 1. O dado é lido do registrador UDR0
 * 2. O mesmo dado é retransmitido (eco)
 * 3. O byte é armazenado em um buffer
 * 4. Ao receber o caractere '*', o comando é processado:
 *    - Converte os dois primeiros bytes em número inteiro
 *    - Define o número de janelas de estimulação
 *    - Reinicia os timers
 *    - Inicia o Timer1 (estimulação)
 *
 * Formato esperado do comando:
 * [d1][d2]*
 * Exemplo: "25*" ? 25 janelas de estimulação
 *
 * _________________________________________________________
 */
ISR(USART0_RX_vect){

    // Lê dado recebido da UART
    data_UART = UDR0;
    //Ecoa o dado recebido
    UDR0 = data_UART;
    //Armazena no buffer e incrementa índice
    buffer_data_vec[buffer_index++] = data_UART;

    // Verifica fim do comando
    if (data_UART == '*'){

        // Reinicia índice do buffer
        buffer_index = 0;

        // Converte caracteres ASCII para inteiro
        windows_control =
        ((buffer_data_vec[0] - '0') * 10) +
        (buffer_data_vec[1] - '0');

        // Reinicia contadores dos timers
        TCNT3 = 0;
        TCNT1 = 0;

        // Inicia Timer1 (estimulação)
        TCCR1B = 0x0A;
		// Marca a estimulação na próxima (primeira) amostra, assim como é feito nas configs
        PORTD = 0x00;
    }
}

/**
 * _________________________________________________________
 * MAIN
 * _________________________________________________________
 */

/**
 * Função principal do sistema
 *
 * Responsável por:
 * - Inicializar o hardware e periféricos
 * - Habilitar interrupções globais
 * - Gerenciar o estado de espera entre ciclos de estimulação
 *
 * Funcionamento:
 * 1. Executa a configuração inicial do sistema
 * 2. Habilita interrupções (Timers e UART)
 * 3. Permanece em loop infinito
 *
 * Durante a execução:
 * - A maior parte do processamento ocorre nas ISRs
 * - O main atua apenas no controle do estado de espera
 * - Garante que os sinais estarão desligados nesse caso
 *
 * Estado de espera (wait = 1):
 * - Ativa o Timer3 para controle do descanso entre janelas
 * - Sinaliza período de descanso via PORTD
 * - Zera todas as portas de saída
 *
 * _________________________________________________________
 */
int main(void) {

    // Inicialização de registradores e periféricos
    config();

    // Habilita interrupções globais 
    sei();

    // Loop principal
    while (1) {

        // Verifica estado de descanso entre janelas
        if (wait){

            // Ativa Timer3 (inicia o descanso)
            TCCR3B = 0x0D;

            // Indica período de descanso
            PORTD = 0x01;

            // Zera todas as saídas -> estímulos desligados
            PORTA = 0x00;
            PORTC = 0x00;
            PORTF = 0x00;
            PORTK = 0x00;
            PORTL = 0x00;

            // Limpa flag do descanso
            wait = 0x00;
        }
    }
}