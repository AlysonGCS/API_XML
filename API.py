# Api para gerar XMLS para a contabilidade que foi terceirizada, Att 18/08/2025 - Alyson
from fastapi import FastAPI, Query
import pyodbc
import os
import json
from datetime import datetime

app = FastAPI()

with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

diretorioBase = CONFIG["paths"]["diretorioBase"]


def getConnect(database):
    return pyodbc.connect(
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER= [servidor];"
        f"DATABASE={database};" #deixei como parametro pois para o grupo possui 2 empresas e 1 base de dados diferente para cada uma delas
        f"UID=[usuarioBanco];"
        f"PWD=[SenhaBanco]];"
        f"TrustServerCertificate=yes;"
    )


def GerarCaminhoCasoNaoExista(tipo, empresa, dt_ini, dt_fim):
    try:
        d1 = datetime.strptime(dt_ini, "%Y-%m-%d")
        d2 = datetime.strptime(dt_fim, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Erro - formato errado de data.")

    periodo = f"{d1.strftime('%d-%m-%y')}_{d2.strftime('%d-%m-%y')}"

    pasta = os.path.join(diretorioBase, tipo, empresa, periodo)
    os.makedirs(pasta, exist_ok=True)
    return pasta


# ENTRADA
@app.get("/entrada/")
def exportar_entrada(
        empresa: str = Query(..., description="Kabel ou Quantum"),
        dt_ini: str = Query(..., description="AAAA-MM-DD"),
        dt_fim: str = Query(..., description="AAAA-MM-DD")
):
    if empresa not in CONFIG:
        return {"erro": f"Empresa '{empresa}' não encontrada no config.json"}

    db_name = CONFIG[empresa]["database"]
    pasta_destino = GerarCaminhoCasoNaoExista("Entrada", empresa, dt_ini, dt_fim)
    conn = getConnect(db_name)
    cursor = conn.cursor()

    sql = f"""
        SELECT X.ID_NOTA, CONVERT(VARCHAR(MAX), ARQUIVO) AS XML
        FROM NFE_XML_RECEBIMENTO X (NOLOCK)
        INNER JOIN HISTLISE_FOR F (NOLOCK)
            ON F.NFISCAL = X.NUMERO
            AND F.CODFOR = X.CODFOR
            AND X.SERIE = F.SERIE
        WHERE cast(F.DTENT as date) >= '{dt_ini}' AND cast(F.DTENT as date) <= '{dt_fim}'
          AND ISNUMERIC(ID_NOTA) = 1
    """
    cursor.execute(sql)
    rows = cursor.fetchall()

    if not rows:
        return {"mensagem": "Nenhum XML de entrada encontrado."}

    id_notas = []
    for id_nota, xml in rows:
        file_path = os.path.join(pasta_destino, f"{id_nota}.xml")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml)
        id_notas.append(id_nota)

    return {"mensagem": f"{len(id_notas)} XMLs de entrada exportados", "id_notas": id_notas}


# ------------------ ROTA SAÍDA ------------------
@app.get("/saida/")
def exportar_saida(
        empresa: str = Query(..., description="Kabel ou Quantum"),
        dt_ini: str = Query(..., description="AAAA-MM-DD"),
        dt_fim: str = Query(..., description="AAAA-MM-DD")
):
    if empresa not in CONFIG:
        return {"erro": f"Empresa '{empresa}' não encontrada no config.json"}

    db_name = CONFIG[empresa]["database"]
    pasta_destino = GerarCaminhoCasoNaoExista("Saida", empresa, dt_ini, dt_fim)
    conn = getConnect(db_name)
    cursor = conn.cursor()

    sql = f"""
        SELECT CONVERT(VARCHAR(MAX), A.ARQUIVO) AS XML, N.NUMERO AS ID_NOTA
        FROM NFE_ARQUIVO A (NOLOCK)
        INNER JOIN NOTAFISC N (NOLOCK) ON N.R_E_C_N_O_ = A.RECNO_NOTAFISC
        INNER JOIN EMPRESA E (NOLOCK) ON A.EMPRESA_RECNO = E.R_E_C_N_O_
        WHERE cast(A.DATAHORA as date) >= '{dt_ini}' AND cast(A.DATAHORA as date) <= '{dt_fim}'
          AND A.EMPRESA_RECNO = 1
          AND N.SITUACAO NOT IN ('ENVIADA','ABERTA','CANCELADA','INUTILIZADA')
    """
    cursor.execute(sql)
    rows = cursor.fetchall()

    if not rows:
        return {"mensagem": "Nenhum XML de saída encontrado."}

    id_notas = []
    for xml, id_nota in rows:
        file_path = os.path.join(pasta_destino, f"{id_nota}.xml")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml)
        id_notas.append(id_nota)

    return {"mensagem": f"{len(id_notas)} XMLs de saída exportados", "id_notas": id_notas}


# --------------------- ROTA CANCELADAS ---------------------------------------

@app.get("/canceladas/")
def exportar_saida(
        empresa: str = Query(..., description="Kabel ou Quantum"),
        dt_ini: str = Query(..., description="AAAA-MM-DD"),
        dt_fim: str = Query(..., description="AAAA-MM-DD")
):
    if empresa not in CONFIG:
        return {"erro": f"Empresa '{empresa}' não encontrada no config.json"}

    db_name = CONFIG[empresa]["database"]
    pasta_destino = GerarCaminhoCasoNaoExista("Cancelados", empresa, dt_ini, dt_fim)
    conn = getConnect(db_name)
    cursor = conn.cursor()

    sql = f"""
        SELECT CONVERT(VARCHAR(MAX), A.ARQUIVO) AS XML, N.NUMERO AS ID_NOTA
        FROM NFE_ARQUIVO A (NOLOCK)
        INNER JOIN NOTAFISC N (NOLOCK) ON N.R_E_C_N_O_ = A.RECNO_NOTAFISC
        INNER JOIN EMPRESA E (NOLOCK) ON A.EMPRESA_RECNO = E.R_E_C_N_O_
        WHERE cast(A.DATAHORA as date) >= '{dt_ini}' AND cast(A.DATAHORA as date) <= '{dt_fim}'
          AND A.EMPRESA_RECNO = 1
          AND N.SITUACAO IN ('CANCELADA')
    """
    cursor.execute(sql)
    rows = cursor.fetchall()

    if not rows:
        return {"mensagem": "Nenhum XML de saída cancelado encontrado."}

    id_notas = []
    for xml, id_nota in rows:
        file_path = os.path.join(pasta_destino, f"{id_nota}.xml")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml)
        id_notas.append(id_nota)

    return {"mensagem": f"{len(id_notas)} XMLs de saída cancelados exportados", "id_notas": id_notas}


# --------------------- ROTA CTE ---------------------------------------

@app.get("/cte/")
def exportar_saida(
        empresa: str = Query(..., description="Kabel ou Quantum"),
        dt_ini: str = Query(..., description="AAAA-MM-DD"),
        dt_fim: str = Query(..., description="AAAA-MM-DD")
):
    if empresa not in CONFIG:
        return {"erro": f"Empresa '{empresa}' não encontrada no config.json"}

    db_name = CONFIG[empresa]["database"]
    pasta_destino = GerarCaminhoCasoNaoExista("CTE entrada", empresa, dt_ini, dt_fim)
    conn = getConnect(db_name)
    cursor = conn.cursor()

    sql = f"""
            SELECT CAST(ARQUIVO_XML AS VARCHAR(MAX)) as XML, CHV_CTE AS ID_NOTA FROM FRETE_CONHECIMENTO X(NOLOCK)
            WHERE DT_ENTRADA >= '{dt_ini}' AND DT_ENTRADA <= '{dt_fim}'
    """

    cursor.execute(sql)
    rows = cursor.fetchall()

    if not rows:
        return {"mensagem": "Nenhum XML de cte encontrado."}

    id_notas = []
    for xml, id_nota in rows:
        file_path = os.path.join(pasta_destino, f"{id_nota}.xml")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(xml)
        id_notas.append(id_nota)

    return {"mensagem": f"{len(id_notas)} XMLs de CTE exportados", "id_notas": id_notas}
