# RDE Report — Automação de Relatórios Atlas & SAP

Desenvolvimento de uma solução completa de **hiperautomação (RPA)** voltada para eliminação de atividades manuais repetitivas, aumento da eficiência operacional e padronização no processo de coleta e gestão de relatórios logísticos.

A solução automatiza o fluxo de ponta a ponta — desde a abertura do sistema corporativo de pesagem e movimentação de cargas até o download, renomeação e organização dos arquivos —, garantindo rastreabilidade, integridade das informações e suporte à tomada de decisão.

---

### 📌 Escopo da Solução

**🔸 Automação de Interface Gráfica (RPA)**

- Controle autônomo do sistema corporativo de pesagem e movimentação de cargas via reconhecimento de imagem em tela
- Login automático, seleção de unidade, navegação por menus e download de relatórios
- Suporte a múltiplas unidades operacionais em sequência: PGUA 1, PGUA 2, Uberaba, Candeias, Catalão, Sorriso, Rondonópolis, Rio Verde, Rio Grande, Palmeirante
- Tratamento de modais, pop-ups e estados inesperados da interface

**🔸 Gestão e Organização de Arquivos**

- Renomeação automática dos relatórios com unidade e competência (MM.AAAA)
- Movimentação para pastas de destino configuráveis por tipo de relatório
- Suporte a três fluxos independentes: Descarga, Carregamento e Recepção

**🔸 Integração com SAP**

- Automação de extração de dados via SAP GUI Scripting (win32com)
- Execução de transações parametrizadas e exportação de relatórios ALV
- Detecção e movimentação automática do arquivo gerado pelo SAP
- Keep-alive assíncrono para evitar expiração de sessão SAP

**🔸 Interface Gráfica Desktop**

- UI moderna construída com CustomTkinter
- Configuração de credenciais, caminhos de destino e seleção de unidades
- Log em tempo real do progresso da automação
- Relógio, aviso de resolução de tela e persistência de configurações

**🔸 Distribuição e Empacotamento**

- Empacotamento como executável Windows (`.exe`) via PyInstaller
- Distribuição sem necessidade de Python instalado na máquina do usuário
- Configurações salvas localmente em JSON

---

### 🛠️ Tecnologias e Ferramentas

**Core:**

Python 3.10 • PyAutoGUI • OpenCV (cv2) • Pillow • CustomTkinter • PyInstaller

**Integração:**

SAP GUI Scripting • win32com • win32gui • pywin32

**Ecossistema:**

Engenharia de Prompt (GitHub Copilot) • Git • PyInstaller onedir • JSON config

---

### 🏭 Unidades Atendidas

| Unidade | Descarga | Carregamento | Recepção |
|---|---|---|---|
| PGUA 1 (Paranaguá) | ✅ | ✅ | ✅ |
| PGUA 2 (Paranaguá) | ✅ | ✅ | ✅ |
| Uberaba | ✅ | ✅ | ✅ |
| Candeias | ✅ | ✅ | ✅ |
| Catalão | ✅ | ✅ | ✅ |
| Sorriso | ✅ | ✅ | ✅ |
| Rondonópolis | ✅ | ✅ | ✅ |
| Rio Verde | ✅ | ✅ | ✅ |
| Rio Grande | ✅ | ✅ | ✅ |
| Palmeirante | ✅ | ✅ | ✅ |

---

### ⚙️ Como Funciona

```
Usuário clica em "Iniciar"
        │
        ▼
RPA abre o sistema de pesagem e movimentação de cargas
        │
        ▼
Login automático + seleção de unidade
        │
        ▼
Navegação: Impressão → Relatórios → tipo correto
        │
        ▼
Download do relatório
        │
        ▼
Arquivo renomeado e movido para pasta de destino
        │
        ▼
Repete para todas as unidades selecionadas
        │
        ▼
Executa passos SAP (opcional)
        │
        ▼
LOG indica conclusão
```

---

### 🔒 Segurança e Boas Práticas

- Credenciais armazenadas localmente (nunca em código ou repositório)
- Configurações em arquivo JSON ignorado pelo `.gitignore`
- Distribuição como `.exe` sem expor código-fonte


