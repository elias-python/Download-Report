import pyautogui
import time
import os
import shutil
from datetime import datetime

# Configurações iniciais
pyautogui.PAUSE = 1.2  # Pausa entre comandos para o sistema processar os cliques
pyautogui.FAILSAFE = True 

# Configurações de Datas e Nomes
hoje = datetime.now()
mes_ano = hoje.strftime("%m.%Y")
unidade = "Paranagua 1" 

# Ajuste estes caminhos conforme seu computador
caminho_downloads = r'C:\Users\esantan3\Downloads' 
caminho_base = r'C:\Users\esantan3\OneDrive - The Mosaic Company\Área de Trabalho\Projetos\Automação\Base'

def realizar_automacao():
    print("Iniciando Automação Total...")

    # --- NOVOS PASSOS: ABERTURA E SELEÇÃO ---
    # Passo 1: Abrir o programa (Ícone na barra de tarefas ou desktop)
    pyautogui.click(925, 1059) 
    print("Abrindo o sistema... aguardando 10 segundos para carregamento.")
    time.sleep(10) # Tempo de carregamento do software

    # Passo 2: Selecionar Unidade/Centro
    pyautogui.click(378, 813)
    # Passo 3: Clicar no centro específico
    pyautogui.click(475, 338)
     # Passo Atlas cargo
    pyautogui.click(405,233)
    time.sleep(10)
    # --- PASSOS ANTERIORES: LOGIN E RELATÓRIO ---
    # Login
    pyautogui.click(665, 490)  # Campo Usuário
    pyautogui.write('ESANTAN3')
    pyautogui.click(1187, 692)  # Campo Senha
    pyautogui.write('Mosaic@2026')
    pyautogui.click(1289, 685) # Botão Entrar
    pyautogui.click(1480, 204) # Tela cheia
    time.sleep(5) 

    # Navegação nos Menus
    pyautogui.click(542, 75)   # Impressão
    pyautogui.click(553, 108)  # Relatórios
    pyautogui.click(671, 175)  # Relatório de Recepção
    pyautogui.click(281,244)
    pyautogui.click(432,362)
    pyautogui.click(110,356)

    # Configuração de Datas (Dia 1 e Hora Zero)
    pyautogui.click(69, 204)  # Dia 1
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('backspace')
    data_inicio = hoje.strftime("01/%m/%Y")
    pyautogui.write(data_inicio)
    pyautogui.press('tab')    

    pyautogui.click(161, 195)  # Hora 0
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('backspace')
    pyautogui.write('0')

    pyautogui.click(199, 205)  # Minuto 0
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('backspace')
    pyautogui.write('0')

    pyautogui.click(250, 202)  # Segundo 0
    pyautogui.hotkey('ctrl', 'a')
    pyautogui.press('backspace')
    pyautogui.write('0')
    
    # Data Final
    #pyautogui.click(1051, 244) # Seleciona data atual

    # Seleção de Filtros e Formato
    pyautogui.click(280, 244)  # Fluxo
    pyautogui.click(125, 358)  # Integração Carregamento
    pyautogui.click(1343, 357) # Tipo Saída
    pyautogui.click(1298, 401) # Excel

    # Executar Download
    pyautogui.click(67, 927)   # Baixar
    print("Gerando Excel... aguardando download concluir.")
    time.sleep(15) # Tempo de segurança para gerar o relatório pesado

    organizar_arquivo()

def organizar_arquivo():
    # Verifica se a pasta de destino existe, se não, cria
    if not os.path.exists(caminho_base):
        os.makedirs(caminho_base)

    arquivos = [f for f in os.listdir(caminho_downloads) if f.endswith('.xlsx')]
    if not arquivos:
        print("Erro: Nenhum arquivo Excel encontrado na pasta de Downloads.")
        return

    # Localiza o arquivo mais recente
    arquivo_recente = max([os.path.join(caminho_downloads, f) for f in arquivos], key=os.path.getmtime)
    
    # Define o novo nome: Paranagua 1 04.2026.xlsx
    novo_nome = f"{unidade} {mes_ano}.xlsx"
    destino_final = os.path.join(caminho_base, novo_nome)

    try:
        shutil.move(arquivo_recente, destino_final)
        print(f"✅ Sucesso! Relatório movido para: {destino_final}")
    except Exception as e:
        print(f"❌ Erro ao mover arquivo: {e}")

if __name__ == "__main__":
    realizar_automacao()