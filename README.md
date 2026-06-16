# 📡 Change-Over Monitor (CoM)

## 📖 Sobre o Projeto

O Monitor de Change-Over é uma aplicação desktop autônoma desenvolvida para a automação e monitoramento de eventos críticos de exibição e recepção na central técnica. O sistema realiza a leitura contínua de logs da operação (arquivos CSV mapeados em rede), avalia transições de estado de equipamentos de transmissão do sinal da Globo Recife e dispara notificações proativas em tempo real para a equipe através de um canal no Microsoft Teams.

O objetivo principal da ferramenta é eliminar a necessidade de checagens manuais e exaustivas por parte dos técnicos, reduzindo o tempo de resposta a incidentes críticos e padronizando a comunicação da equipe de engenharia de Telecom e operações.

## ✨ Funcionalidades

- **Monitoramento Contínuo (Loop)**: O sistema realiza varreduras automatizadas no arquivo de log a cada 120 segundos. Para não travar a interface visual, a leitura roda em segundo plano através de Threading.

- **Integração com MS Teams**: Disparo de alertas formatados em blocos visuais (Adaptive Cards) via Webhook, informando o horário exato, o canal afetado e a transição do estado.

- **Filtro Anti-Redundância (Memória)**: Utilização de um arquivo de controle local (`historico.json`) que mapeia o ID único de cada evento. Isso garante que o app não crie poluição visual no Teams com envios duplicados, mesmo se o equipamento disparar logs repetidos.

- **Interface Gráfica**: Painel limpo construído em Dark Mode que exibe o Status Global da operação e uma caixa de logs visível dentro da própria tela.

- **Trava de Segurança Operacional**: Ações de parada de monitoramento são interceptadas por um pop-up de confirmação (Sim/Não), evitando que cliques acidentais deixem a operação desprotegida.

## 🛠️ Tecnologias Utilizadas

- **Python**: Linguagem base.
- **CustomTkinter**: Biblioteca para a Interface Gráfica (GUI), garantindo botões modernos e um visual nativo noturno de fácil implementação.
- **Pandas**: Motor de processamento de dados utilizado para extração e leitura do CSV.
- **Requests**: Para o gerenciamento das requisições HTTP POST direcionadas à API/Webhook do Teams.
- **Threading**: Para a concorrência assíncrona, separando o loop infinito do monitoramento do loop principal da interface.
- **PyInstaller**: Utilizado para compilar o código em um binário executável (`.exe` no Windows) 100% autônomo, permitindo rodar na máquina corporativa sem depender do VS Code.

## 🚀 Como Executar o Projeto

1. Clone este repositório:

```
git clone https://github.com/seu-usuario/monitor-cho.git
```

2. Crie e ative o seu ambiente virtual (recomendado):

```
python -m venv venv
```

**No Windows**:
```
.\venv\Scripts\activate
```

3. Instale as dependências essenciais:

```
python -m pip install customtkinter pandas requests pyinstaller
```

4. Para rodar o código fonte diretamente em modo de testes:

```
python app_visual.py
```

5. Para compilar o arquivo executável final (.exe) :

```
python -m pyinstaller --onefile --noconsole app_visual.py
```

O executável pronto ficará disponível dentro da pasta `dist`.

Abraços! :)
