// Stable version, v1, testing...

#include <stdlib.h>
#include <stdio.h>
#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/pgmspace.h>
#include "sinal_base.h"

#define F_CPU 16000000UL

// Variaveis herdadas da versão MEGA2560

volatile unsigned long lut_add = 0x00;
unsigned int part_index;
volatile unsigned char part_offset;
volatile unsigned char value;

volatile unsigned char data_b;
volatile unsigned char data_c;

volatile unsigned char system_control; 
volatile unsigned char system_mode = 0x00;
unsigned char buffer_index = 0;
char buffer_data_vec[4];
char data_UART;


//Variaveis para leitura do joystick
enum posicaoJoystick {Esquerda, Frente, Tras, Direita, Parado};
enum posicaoJoystick posicaoAtual = Parado;

volatile int direcao[] = {511, 511}; // x, y
volatile char novaDirecao = 0;
volatile char joy_state = 1;



void configUSART(){
	/****************************************************************************************************************************
	Usart configurada no modo assincrono, com receptor e transmissor habilitados, baudrate de 9600 bps e interrupção de recepção
	completa ativa
	****************************************************************************************************************************/
	
	
	
	/****************************************************************************************************************************
	UBRRnL and UBRRnH – USART Baud Rate Registers

	Registradores que contém o valor do Baud Rate da USART
	****************************************************************************************************************************/
	UBRR0H = 0x00; // 9600 bps
	UBRR0L = 0xCF;

	/****************************************************************************************************************************
	UCSRnA – USART Control and Status Register n A
		

	+======+======+=======+=====+======+======+======+=======+
	| RXCn | TXCn | UDREn | FEn | DORn | UPEn | U2Xn | MPCMn |
	+======+======+=======+=====+======+======+======+=======+
	|   R  |   0  |   R   |  R  |   R  |   R  |   1  |   0   |
	+======+======+=======+=====+======+======+======+=======+

	Bits de Flag da USART
		RXCn: USART Receive Complete
		TXCn: USART Transmit Complete
		UDREn: USART Data Register Empty
	Bits de Erro da USART
		FEn: Frame Error
		DORn: Data OverRun
		UPEn: USART Parity Error
	U2Xn: Double the USART Transmission Speed
	MPCMn: Multi-processor Communication Mode
	****************************************************************************************************************************/
	UCSR0A = 0x02;

	/****************************************************************************************************************************
	UCSRnB – USART Control and Status Register n B

	+========+========+========+=======+=======+========+=======+=======+
	| RXCIEn | TXCIEn | UDRIEn | RXENn | TXENn | UCSZn2 | RXB8n | TXB8n |
	+========+========+========+=======+=======+========+=======+=======+
	|    1   |    0   |    0   |   1   |   1   |    0   |   R   |   0   |
	+========+========+========+=======+=======+========+=======+=======+



	Bits para habilitar as interrupções da USART
		RXCIEn: RX Complete Interrupt Enable n
		TXCIEn: TX Complete Interrupt Enable n
		UDRIEn: USART Data Register Empty Interrupt Enable n
	Bits para habilitar as funções da USART
		RXENn: Receiver Enable n
		TXENn: Transmitter Enable n
	Bit que define o número de bits do caractere, junto com UCSZn1:0 no UCSRnC
		UCSZn2: Character Size n
	Bits que contém o nono bit a ser enviado/recebido, caso necessário
		RXB8n: Receive Data Bit 8 n
		TXB8n: Transmit Data Bit 8 n
	****************************************************************************************************************************/
	UCSR0B = 0x98;


	/****************************************************************************************************************************
	UCSRnC – USART Control and Status Register n C

	+=========+=========+=======+=======+=======+========+========+========+
	| UMSELn1 | UMSELn0 | UPMn1 | UPMn0 | USBSn | UCSZn1 | UCSZn0 | UCPOLn |
	+=========+=========+=======+=======+=======+========+========+========+
	|     0   |     0   |   0   |   0   |   0   |    1   |    1   |    0   |
	+=========+=========+=======+=======+=======+========+========+========+

		UMSELn1:0 USART Mode Select
		UPMn1:0: Parity Mode
		USBSn: Stop Bit Select
		UCSZn1:0: Character Size
		UCPOLn: Clock Polarity
	****************************************************************************************************************************/
	UCSR0C = 0x06;
}

void configGPIO(){
	/****************************************************************************************************************************
	As conexões feitas nesse programa foram:
	
                        +===============+
                        |               |
                        |           (13)> 
                        |           (12)> 
                        |           (11)> Bit 8 do sinal
                        |           (10)> Bit 7 do sinal
                        |       A   (09)> Bit 6 do sinal
                        <(5V)   R   (08)> Bit 5 do sinal
                        <(Gnd)  D       |
                        <(Vin)  U   (07)> 
                        |       I   (06)>
    Bit 1 do sinal      <(A0)   N   (05)> 
    Bit 2 do sinal      <(A1)   O   (04)> 
    Bit 3 do sinal      <(A2)       (03)> 
    Bit 4 do sinal      <(A3)       (02)> Marcador das janelas
    Eixo X do Joystick  <(A4)       (01)> TX
    Eixo Y do Joystick  <(A5)       (00)> RX
                        |               |
                        +===============+
	
	Sendo que cada bit do sinal tem a capacidade de controlar um estímulo diferente e o marcador das janelas está conectado a um
	optoacoplador, tendo então seu sinal isolado da touca de sensores e invertido
	****************************************************************************************************************************/
	
	DDRB |= 0x0F;
	DDRC |= 0x0F;
	DDRC &= 0xCF;
	DDRD |= 0X04; // PD2 marca o sinal de estimulação
	PORTD |= (1<<2);
	MCUCR |= (1 << PUD); // Desliga os resistores de pull-UP das portas
}

void configTimer1(){
	//TODO: Timer 1 - sincronia da amostragem - rever configurações máximas e mínimas novamente (30kb memória)
	// No mega temos 1 interrupção, nestas configurações, a cada 1us com resol min 64US 
	// 30kb e 1 byte de sinal 30720 amostras 
	
	
	/**************************************************************************************************************************** 
	Configuracao do temporizador 1 (16 bits) para gerar interrupcoes periodicas no modo Clear Timer on Compare Match (CTC)

	Relogio = 16e6
	Prescaler = 8
	Faixa = 256(Contagem de 0 a OCR1A = 255)
	Intervalo entre interrupcoes: (Prescaler/Relogio)*Faixa = (256/16e6)*(249+1) = 128 us
	
	Nota que a faixa depende do arquivo de cabeçalho do sinal, podendo variar
	****************************************************************************************************************************/
	
	/****************************************************************************************************************************
	TCCR1A – Timer/Counter 1 Control Register A

	+========+========+========+========+=======+=======+=======+=======+
	| COM1A1 | COM1A0 | COM1B1 | COM1B0 |   –   |   –   | WGM11 | WGM10 |
	+========+========+========+========+=======+=======+=======+=======+
	|   0    |   0    |   0    |   0    |   -   |   -   |   0   |   0   |
	+========+========+========+========+=======+=======+=======+=======+
	
	
	COM1A1:0: Compare Match Output A Mode
	COM1B1:0: Compare Match Output B Mode
	WGM11:0: Waveform Generation Mode
	****************************************************************************************************************************/
	TCCR1A = 0x00;
	
	
	/****************************************************************************************************************************
	TCCR1B – Timer/Counter Control Register B

	+=======+=======+=======+=======+=======+======+======+======+
	| ICNC1 | ICES1 |   –   | WGM13 | WGM12 | CS12 | CS11 | CS10 |
	+=======+=======+=======+=======+=======+======+======+======+
	|   0   |   0   |   -   |   0   |   1   |  0   |  0   |  0   |
	+=======+=======+=======+=======+=======+======+======+======+
	
	
	ICNC1: Input Capture Noise Canceler
	ICES1: Input Capture Edge Select
	WGM13:2: Waveform Generation Mode
	CS12:0: Clock Select
	****************************************************************************************************************************/
	TCCR1B = 0x08; //(TCCR1B = 0x08 timer pausado)
	
	
	//OCR1A – Output Compare Register A
	//Define a faixa de contagem
	OCR1A = Ts;	// Valor do período de amostagem do sinal para o contador
	
	/****************************************************************************************************************************
	TIMSK0 – Timer/Counter Interrupt Mask Register

	+===+===+=======+===+===+========+========+=======+
	| - | - | ICIE1 | - | - | OCIE1B | OCIE1A | TOIE1 |
	+===+===+=======+===+===+========+========+=======+
	| - | - |   -   | - | - |   0    |   1    |   0   |
	+===+===+=======+===+===+========+========+=======+

	ICIE1: Timer/Counter1 Input Capture Interrupt Enable
	OCIE1B: Timer/Counter Output Compare Match B Interrupt Enable
	OCIE1A: Timer/Counter1 Output Compare Match A Interrupt Enable
	TOIE1: Timer/Counter1 Overflow Interrupt Enable
	****************************************************************************************************************************/
	TIMSK1 = 0x02;
}

void configADC(){
	/****************************************************************************************************************************
	ADMUX – ADC Multiplexer Selection Register
	+=======+=======+=======+===+======+======+======+======+
	| REFS1 | REFS0 | ADLAR | - | MUX3 | MUX2 | MUX1 | MUX0 |
	+=======+=======+=======+===+======+======+======+======+
	|   0   |   1   |   0   | - |   0  |   1  |   0  |   0  |
	+=======+=======+=======+===+======+======+======+======+

	REFS1:0 - Reference Selection Bits
		Refencia será o Vcc
	ADLAR - ADC Left Adjust Result
		Resultado alinhado a direita
	MUX3:0 - Analog Channel Selection Bits
		Iniciado com leitura no ADC4 (PC4)
		Será revezado com a leitura no ADC5 (PC5)
	****************************************************************************************************************************/
	ADMUX = 0x44;
	
	/****************************************************************************************************************************
	ADCSRA – ADC Control and Status Register A
	+======+======+=======+======+======+=======+=======+=======+
	| ADEN | ADSC | ADATE | ADIF | ADIE | ADPS2 | ADPS1 | ADPS0 |
	+======+======+=======+======+======+=======+=======+=======+
	|   1  |   0  |   0   |   0  |   1  |   1   |   1   |   1   |
	+======+======+=======+======+======+=======+=======+=======+

	ADEN - ADC Enable
	ADSC - ADC Start Conversion
	ADATE - ADC Auto Trigger Enable
	ADIF - ADC Interrupt Flag
	ADIE - ADC Interrupt Enable
	ADPS2:0 - ADC Prescaler Select Bits
	****************************************************************************************************************************/
	ADCSRA = 0x8F;
	
	/****************************************************************************************************************************
	ADCSRB – ADC Control and Status Register B
	+===+======+===+===+===+=======+=======+=======+
	| - | ACME | - | - | - | ADTS2 | ADTS1 | ADTS0 |
	+===+======+===+===+===+=======+=======+=======+
	| - |   0  | - | - | - |   0   |   0   |   0   |
	+===+======+===+===+===+=======+=======+=======+

	ACME - Analog Comparator Multiplexer Enable
	ADTS2:0 - ADC Auto Trigger Source
	****************************************************************************************************************************/	
	ADCSRB = 0x00;	
}

void configInicial(){
	// PRIMEIRA AMOSTRA
	part_index  = lut_add >> 8;
	part_offset = lut_add & 0xFF;
	value = pgm_read_byte((uint16_t)(&signal_parts[part_index][part_offset]));
	data_b = (value & 0xf0) >> 4;
	data_c = (value & 0x0f);
	lut_add++;
}

void config(){
	cli();
	
	// Portas
	configGPIO();
	
	//UART
	configUSART();
	
	//Timer 1
	configTimer1();	
	
	//ADC - Joystick
	configADC();
	
	sei();
	
	configInicial();
	
}

ISR(TIMER1_COMPA_vect) {
	// Apresentação do sinal
	PORTB = data_b;
	PORTC = data_c;
	
	if (lut_add >= signal_len) {
		lut_add = 0;      // Reinicia índice da LUT
		TCCR1B = 0x08;    // Para o Timer1 (sem clock)
		PORTD = (1<<2);   // Marca fim da janela
    PORTB = 0X00;
    PORTC = 0x00;
	}
	// New update method (EVOLUÇÃO DEPOIS DE EA701 :) de um while maluco para um for optimize ? maybe rsrs)
	part_index  = lut_add >> 8;
	part_offset = lut_add & 0xFF;
	value = pgm_read_byte((uint16_t)(&signal_parts[part_index][part_offset]));
	// Separação dos bytes
	// Vai vir do HEADER um byte onde 0xMSB.LSB -- MSB porta b LSB porta c
	data_b = (value & 0xf0) >> 4; // Fazer um cast para garantir
	data_c = value & 0x0f;
	lut_add++;
}

ISR(USART_RX_vect){
	// Comandos diferentes
		// Liga / Desliga
		// Estimulação
		// Reset 
	// Padrão
		// cd0* - Desliga
		// cd1* - Liga
		// cd2* - Janela de estimulação
		// cdr* - Reset sistema
	data_UART = UDR0;
	buffer_data_vec[buffer_index++] = data_UART;

	if (data_UART == '*'){
    //Iniciadas aquisições do ADC
    joy_state = 0x01;
	  ADCSRA |= 0x40;
    sei(); // Vai gerar uma interrupção aninhada
    while(joy_state){
      // Espera ADC coletar a intenção, não trava o restante do programa, pois é antes de uma janela de estimulação iniciar.
    }
    cli(); // Fim da interrupção aninhada
		UDR0 = posicaoAtual+48;  //Ao receber um comando, envia a posição do joystick
		buffer_index = 0;
		system_control = buffer_data_vec[2];
		system_mode = 0x01;
	}
}

ISR(ADC_vect){
	/****************************************************************************************************************************
	Essa interrupção acontece sempre que uma leitura é finalizada
	O ADC irá revezar em ler a porta A4 e A5, responsáveis pelos eixos X e Y, sendo que sempre que terminar o último eixo será
	setada uma flag para que seja verificada qual a direção do joystick na rotina principal, não consumindo muito tempo de
	execução.
	****************************************************************************************************************************/
	if (ADMUX == 0x44){
		ADMUX = 0x45;
		direcao[1] = ADC;
    ADCSRA |= 0x40; // Dispara a segunda conversão, agora para o ADC5
	}
	else if (ADMUX == 0x45){
		ADMUX = 0x44;
		direcao[0] = ADC;
    /*
		Os valores das direções de trás e esquerda beiram os 0V, enquanto as outras direçoes se aproximam de 4,6V
		O centro está próximo de 2,2V
		*/
    if ((direcao[0] >= 800)){
      posicaoAtual = Frente;
    }
    else if ((direcao[0] <= 200)){
      posicaoAtual = Tras;
    }
    else if ((direcao[1] >= 800)){
      posicaoAtual = Direita;
    }
    else if ((direcao[1] <= 200)){
      posicaoAtual = Esquerda;
    }
    else{
      posicaoAtual = Parado;
    }

    joy_state = 0x00;

	}
}

int main(void){
	
	config();
	sei();
	
	while(1){
		if(system_mode){
			// MEF do sistema em função do controle da BCI experimental
			switch(system_control){
				case('0'):
					// Comando de desliga estímulos
					DDRB = 0x01;		// 0000 0001 (somente PORTB0 como saída, delisgar pull up para não ficar em alto)
					DDRC = 0x00;
					TCCR1B = 0x0A;
					break;
				// WARNING: AQUI ESTOU SUPONDO QUE QUEM SABE QUAL O ESTADO DA ESCOLHA E DO PAINEL É A INTERFACE PYTHON (intenção do usuário)
				case('1'):
					// Comando de liga
					DDRB = 0x0F;
					DDRC = 0x0F;
					TCCR1B = 0x0A;
					break;
				case('2'):
					TCCR1B = 0x0A;
					break;
				case('r'): // rotina de comando de reset, implementar funcionalidades de controle e reset do sistema (ESTADO NATIVO) Necessita uma nova chamada para estimulação
					TCCR1B = 0x08; // Stop do sistema total
					DDRB = 0x0F; // Ligação forçada de todos os estímulos
					DDRC = 0x0F;
					lut_add = 0x00;
					break;
				default: break;
			}
			system_mode = 0x00;
			PORTD &= ~(1<<2); // Marca o início da janela
		}
	}
}