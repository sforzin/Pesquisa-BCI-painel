# PAINEL DE ESTIMULAÇÃO VISUAL BCI-SSVEP DSPCOM

## Introdução

Uma Interface Cérebro-Computador (BCI, do inglês *Brain-Computer Interface*) é um sistema que permite a comunicação e o controle de dispositivos por meio do processamento da atividade cerebral do usuário. Essa tecnologia pode ser utilizada como interface assistiva, oferecendo a indivíduos com limitações motoras uma alternativa de interação com o ambiente externo.

De forma geral, uma BCI é composta por quatro subsistemas principais: (i) sistema de estimulação, (ii) sistema de aquisição de sinais cerebrais, (iii) sistema de processamento e (iv) sistema de controle. O sistema de estimulação tem como função apresentar estímulos capazes de evocar respostas neurais específicas, que posteriormente são detectadas e interpretadas.

Dentre os paradigmas utilizados, destaca-se o *SSVEP* (*Steady-State Visually Evoked Potential*), no qual estímulos visuais periódicos são apresentados ao usuário com frequências e fases bem definidas. Como resposta, surgem um potencial evocado no sinal de EEG nessas mesmas frequências e em suas harmônicas. A identificação dessas componentes permite inferir para qual estímulo o usuário direcionou sua atenção, possibilitando a associação de estímulos a comandos de controle.

---

## Objetivo do Sistema

O objetivo deste sistema é gerar estímulos visuais cintilantes com alta precisão temporal, adequados para aplicações em BCI baseadas no paradigma SSVEP, com foco em uso experimental no Laboratório DSPCOM da Universidade Estadual de Campinas.

O sistema foi projetado para garantir controle preciso de frequência, fase e temporização dos estímulos, fatores críticos para a evocação dos potenciais SSVEP e para o desempenho de uma interface cérebro-computador.

---

## Visão Geral do Sistema

O sistema de estimulação é composto por três módulos principais:

- **Interface de configuração dos estímulos**  
  Permite ao usuário definir parâmetros como frequência, fase, duração da estimulação, tempo de repouso e taxa de amostragem dos sinais.

- **Algoritmo de geração dos sinais**  
  Responsável pela construção dos sinais digitais de estimulação, utilizando uma abordagem baseada em quantização de sinais senoidais e armazenamento em memória (*Look-Up Tables* - LUTs).

- **Firmware de controle e apresentação**  
  Executado em um microcontrolador ATmega2560, realiza a leitura das LUTs armazenadas na memória flash e a apresentação dos sinais nas saídas digitais (GPIOs), garantindo sincronização temporal por meio de temporizadores e interrupções.

Fisicamente, o sistema é implementado como um painel modular baseado em matrizes de LEDs, controlado pelo microcontrolador. Cada estímulo visual é associado a uma saída digital do microcontrolador, permitindo a apresentação paralela e simultânea dos múltiplos estímulos.

O sistema suporta até **40 estímulos simultâneos**, distribuídos em cinco portas digitais de 8 bits, com controle individual de frequência e fase. A arquitetura permite flexibilidade de montagem e adaptação a diferentes aplicações, incluindo configurações experimentais e sistemas embarcados.

A primeira versão do sistema foi implementada com um painel contendo oito estímulos, utilizado para validação experimental. Resultados preliminares indicaram desempenho superior em relação a sistemas baseados em monitor, com maior acurácia na detecção dos estímulos em aplicações de BCI.

O sistema foi projetado visando a integração com plataformas de aquisição de EEG e algoritmos de classificação, compondo a plataforma experimental baseada no paradigma SSVEP desenvolida no laboratório.

---

## Diagrama de blocos

A Figura 1 apresenta a arquitetura geral do sistema de estimulação, evidenciando a divisão entre os módulos de configuração, geração e controle dos estímulos.

<p align="center">
![Diagrama de blocos do sistema](/images/sistema-diagrama.png)
</p>
<p align="center">
  <em>Figura 1 – Diagrama de blocos do sistema de estimulação BCI-SSVEP.</em>
</p>