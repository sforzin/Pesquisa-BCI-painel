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

void config(){
	// Portas
	DDRB |= 0x0F;
	DDRC |= 0x0F;
	DDRD |= 0X04; // PD2 marca o sinal de estimulação
	PORTD = (1<<2);
	MCUCR |= (1 << PUD); // Desliga os resistores de pull-UP das portas
	//UART
	UCSR0A = 0x02;
	UCSR0B = 0x98;
	UCSR0C = 0x06;
	UBRR0H = 0x00; // 9600 bps
	UBRR0L = 0xCF;
	//Timer 1 - sincronia da amostragem - rever configurações máximas e mínimas novamente (30kb memória)
	// No mega temos 1 interrupção, nestas configurações, a cada 1us com resol min 64US 
	// 30kb e 1 byte de sinal 30720 amostras 
	TCCR1A = 0x00;
	TCCR1B = (1 << WGM12); //(TCCR1B = 0x08 timer pausado)
	OCR1A = Ts;	// Valor do período de amostagem do sinal para o contador
	TCNT1 = 0;
	TIMSK1 |= (1 << OCIE1A);
	
	// PRIMEIRA AMOSTRA
	part_index  = lut_add >> 8;
	part_offset = lut_add & 0xFF;
	value = pgm_read_byte((uint16_t)(&signal_parts[part_index][part_offset]));
	data_b = (value & 0xf0) >> 4;
	data_c = (value & 0x0f);
	lut_add++;
}

ISR(TIMER1_COMPA_vect) {
	// Apresentação do sinal
	PORTB = data_b;
	PORTC = data_c;
	
	if (lut_add >= signal_len) {
		lut_add = 0;      // Reinicia índice da LUT
		TCCR1B = 0x08;    // Para o Timer1 (sem clock)
		PORTD = (1<<2);   // Marca fim da janela
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

ISR(USART0_RX_vect){
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
	UDR0 = data_UART;
	buffer_data_vec[buffer_index++] = data_UART;

	if (data_UART == '*'){
		buffer_index = 0;
		system_control = buffer_data_vec[2];
		system_mode = 0x01;
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
			PORTD |= (0<<2); // Marca o início da janela
		}
	}
}