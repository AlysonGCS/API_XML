import requests
from datetime import datetime
import calendar
import os

Host = "http://192.168.200.240:8080"
Empresas = ["Wiring", "Electronic"]
Formas = ["entrada", "saida", "canceladas", "cte"]

diretorioBase = r"C:\XMLs"
diretorioLog = os.path.join(diretorioBase, "logs")
os.makedirs(diretorioLog, exist_ok=True)
ArquivoLog = os.path.join(diretorioLog, "executar_xmls.log")


def escrever_log(msg):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{agora}] {msg}"
    print(linha)
    with open(ArquivoLog, "a", encoding="utf-8") as f:
        f.write(linha + "\n")


def VerificarDia():
    hoje = datetime.today()
    ano, mes = hoje.year, hoje.month
    dia = hoje.day

    if dia == 1:
        mes_passado = mes - 1 if mes > 1 else 12
        ano_passado = ano if mes > 1 else ano - 1
        ultimo_dia_mes_passado = calendar.monthrange(ano_passado, mes_passado)[1]
        dt_ini = f"{ano_passado:04d}-{mes_passado:02d}-16"
        dt_fim = f"{ano_passado:04d}-{mes_passado:02d}-{ultimo_dia_mes_passado:02d}"
        periodo_desc = f"16-{ultimo_dia_mes_passado:02d}"
        return dt_ini, dt_fim, periodo_desc

    elif dia == 16:
        data_ini = f"{ano:04d}-{mes:02d}-01"
        data_fim = f"{ano:04d}-{mes:02d}-15"
        periodo_desc = "01-15"
        return data_ini, data_fim, periodo_desc

    return None, None, None


def executar_xmls():
    data_ini, data_fim, periodo_desc = VerificarDia()
    if not data_ini:
        escrever_log("Hoje não é dia 1 nem 16. Saindo...")
        return

    escrever_log(f"Início da exportação do periodo {periodo_desc}")

    for empresa in Empresas:
        for forma in Formas:
            url = f"{Host}/{forma}/"
            try:
                resp = requests.get(url, params={
                    "empresa": empresa,
                    "data_ini": data_ini,
                    "data_fim": data_fim
                })
                if resp.status_code == 200:
                    data = resp.json()
                    qtd = len(data.get("id_notas", []))
                    escrever_log(f"[OK] {forma.capitalize()} - {empresa}: {qtd} XMLs exportados")
                else:
                    escrever_log(f"[ERRO] {forma.capitalize()} - {empresa}: status {resp.status_code} - {resp.text}")
            except Exception as e:
                escrever_log(f"[ERRO] {forma.capitalize()} - {empresa}: {e}")

    escrever_log(f"Fim da exportação do periodo {periodo_desc} \n")


if __name__ == "__main__":
    executar_xmls()
