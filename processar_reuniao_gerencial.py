from pathlib import Path
import re
import shutil
import pandas as pd
import fitz  # PyMuPDF
from unidecode import unidecode
from datetime import datetime
import sys


# =====================================================
# CONFIGURE AQUI O CAMINHO DA SUA PASTA DE 2026
# =====================================================

PASTA_BASE = Path(
    r"C:\Users\gabriel.torres\OneDrive - CNPEM - Centro Nacional de Pesquisa em Energia e Materiais\Documentos\DAI - PMO DAI\1.REUNIÃO GERENCIAL DE ACOMPANHAMENTO DAI\REUNIÃO GERENCIAL - 2026"
)

PASTA_PROJETOS = PASTA_BASE / "PROJETOS"

CSV_PROJETOS = PASTA_PROJETOS / "projetos_detectados.csv"
CSV_INDICE = PASTA_PROJETOS / "indice_links_reports.csv"


# =====================================================
# FUNÇÕES DE TEXTO
# =====================================================

def normalizar(texto: str) -> str:
    texto = texto or ""
    texto = unidecode(texto)
    texto = texto.upper()
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def limpar_nome_pasta(texto: str) -> str:
    texto = unidecode(texto or "")
    texto = texto.upper()
    texto = re.sub(r"[^A-Z0-9]+", "_", texto)
    texto = re.sub(r"_+", "_", texto)
    texto = texto.strip("_")
    return texto[:100]


def extrair_mes_ano(nome_arquivo: str):
    """
    Exemplo:
    04 2026 GERENCIAL SPRINT REVIEW ABRIL.pdf
    """
    match = re.search(r"(\d{2})\s+(\d{4})", nome_arquivo)

    if match:
        mes = match.group(1)
        ano = match.group(2)
    else:
        mes = datetime.now().strftime("%m")
        ano = datetime.now().strftime("%Y")

    return ano, mes


# =====================================================
# DETECÇÃO DE PROJETOS
# =====================================================

PADROES_CODIGO = [
    r"\bENT\.?\d{3}\.?\d{3}\b",
    r"\bENT\.?\d{3}\.?\d{2}\.?\d{3}\b",
    r"\bDAI\.?\d{3}\.?\d{3}\b",
    r"\bDAI\.?\d{3}\.?\d{2}\.?\d{3}\b",
    r"\bDAI\d{3}\.?\d{3}\b",
    r"\bOS[:\s\-]*\d{4,6}\b",
]


PALAVRAS_IGNORAR = [
    "STATUS REPORT",
    "OUTRAS CONSIDERACOES",
    "FASE DO PROJETO",
    "RESUMO DO PROJETO",
    "ATIVIDADES DESENVOLVIDAS",
    "ATIVIDADES CONCLUIDAS",
    "ATIVIDADES EM ANDAMENTO",
    "ATIVIDADES FUTURAS",
    "PROXIMOS PASSOS",
    "PONTOS DE ATENCAO",
    "PREVISAO ORCAMENTARIA",
    "VALOR COMPROMETIDO",
    "REVISAO DE PROJETOS",
    "OPERACAO, MELHORIAS E MANUTENCAO",
    "GERENCIAL DAI",
    "OBRIGADA",
    "OBRIGADO",
]


def linha_eh_generica(linha_norm: str) -> bool:
    if len(linha_norm) < 5:
        return True

    for termo in PALAVRAS_IGNORAR:
        if termo in linha_norm:
            return True

    return False


def extrair_codigo(linha: str):
    linha_norm = normalizar(linha)

    for padrao in PADROES_CODIGO:
        match = re.search(padrao, linha_norm)

        if match:
            codigo = match.group(0)
            codigo = codigo.replace(".", "")
            codigo = codigo.replace(" ", "")
            codigo = codigo.replace(":", "")
            codigo = codigo.replace("-", "")
            return codigo

    return None


def detectar_projeto_pagina(texto_pagina: str):
    """
    Tenta detectar o projeto de uma página.
    Procura códigos ENT, DAI ou OS nas primeiras linhas.
    """

    linhas = [l.strip() for l in texto_pagina.splitlines() if l.strip()]
    candidatos = []

    for linha in linhas[:45]:
        linha_norm = normalizar(linha)

        if linha_eh_generica(linha_norm):
            continue

        codigo = extrair_codigo(linha)

        if codigo:
            candidatos.append({
                "codigo_projeto": codigo,
                "titulo_projeto": linha.strip()
            })

    if candidatos:
        return candidatos[0]

    return None


# =====================================================
# CSV
# =====================================================

def carregar_csv_existente(caminho: Path):
    if caminho.exists():
        return pd.read_csv(caminho, dtype=str).fillna("")
    return pd.DataFrame()


def salvar_csv(df: pd.DataFrame, caminho: Path):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho, index=False, encoding="utf-8-sig")


# =====================================================
# FUNÇÃO DE HISTÓRICO VERSIONADO
# =====================================================

def gerar_caminho_unico(caminho: Path) -> Path:
    """
    Se o arquivo já existir, cria uma nova versão:
    arquivo.pdf
    arquivo_v2.pdf
    arquivo_v3.pdf
    arquivo_v4.pdf
    etc.
    """
    if not caminho.exists():
        return caminho

    pasta = caminho.parent
    nome_base = caminho.stem
    extensao = caminho.suffix

    contador = 2

    while True:
        novo_caminho = pasta / f"{nome_base}_v{contador}{extensao}"

        if not novo_caminho.exists():
            return novo_caminho

        contador += 1


# =====================================================
# LOCALIZAÇÃO DO PDF
# =====================================================

def obter_pdfs_validos():
    """
    Procura PDFs na pasta base e subpastas,
    ignorando qualquer PDF dentro da pasta PROJETOS.
    """
    pdfs = []

    for pdf in PASTA_BASE.rglob("*.pdf"):
        caminho_norm = normalizar(str(pdf))

        if "PROJETOS" in caminho_norm:
            continue

        pdfs.append(pdf)

    return pdfs


def chave_mes_ano(pdf_path: Path):
    """
    Extrai (ano, mes) do nome do arquivo para ordenação cronológica.
    Ex.: '04 2026 GERENCIAL...' -> (2026, 4)
    """
    match = re.search(r"(\d{2})\s+(\d{4})", pdf_path.name)

    if match:
        mes = int(match.group(1))
        ano = int(match.group(2))
        return ano, mes

    return 0, 0


def obter_pdf_mais_recente():
    """
    Escolhe o PDF mais recente com base no mês/ano do nome,
    e não pela data de modificação.
    """
    pdfs = obter_pdfs_validos()

    if not pdfs:
        raise FileNotFoundError("Nenhum PDF encontrado na pasta base ou subpastas.")

    return max(pdfs, key=chave_mes_ano)


# =====================================================
# MANIPULAÇÃO DE PDF
# =====================================================

def criar_pdf_com_paginas(pdf_origem, paginas, destino: Path, sobrescrever=False):
    """
    Cria um PDF com as páginas informadas.

    Se sobrescrever=False:
        não sobrescreve; cria _v2, _v3 etc.

    Se sobrescrever=True:
        sobrescreve o arquivo destino.
    """
    novo_pdf = fitz.open()

    for pagina_idx in paginas:
        novo_pdf.insert_pdf(pdf_origem, from_page=pagina_idx, to_page=pagina_idx)

    destino.parent.mkdir(parents=True, exist_ok=True)

    if destino.exists():
        if sobrescrever:
            destino.unlink()
        else:
            destino = gerar_caminho_unico(destino)

    novo_pdf.save(destino)
    novo_pdf.close()

    return destino


# =====================================================
# PROCESSAMENTO PRINCIPAL (1 ARQUIVO)
# =====================================================

def processar_pdf(pdf_path: Path):
    print("=" * 80)
    print(f"Processando arquivo: {pdf_path}")
    print("=" * 80)

    ano, mes = extrair_mes_ano(pdf_path.name)
    mes_referencia = f"{ano}-{mes}"

    print(f"Mês de referência identificado: {mes_referencia}")

    PASTA_PROJETOS.mkdir(parents=True, exist_ok=True)

    pdf = fitz.open(pdf_path)

    projetos_encontrados = {}

    for idx, pagina in enumerate(pdf):
        texto = pagina.get_text("text")
        projeto = detectar_projeto_pagina(texto)

        if not projeto:
            continue

        codigo = projeto["codigo_projeto"]
        titulo = projeto["titulo_projeto"]

        if codigo not in projetos_encontrados:
            projetos_encontrados[codigo] = {
                "codigo_projeto": codigo,
                "titulo_projeto": titulo,
                "paginas": []
            }

        projetos_encontrados[codigo]["paginas"].append(idx)

    if not projetos_encontrados:
        print("Nenhum projeto detectado no PDF.")
        pdf.close()
        return

    df_projetos_antigo = carregar_csv_existente(CSV_PROJETOS)
    df_indice_antigo = carregar_csv_existente(CSV_INDICE)

    novos_cadastros = []
    novas_linhas_indice = []

    codigos_ja_cadastrados = set()

    if not df_projetos_antigo.empty and "codigo_projeto" in df_projetos_antigo.columns:
        codigos_ja_cadastrados = set(df_projetos_antigo["codigo_projeto"].astype(str))

    for codigo, dados in projetos_encontrados.items():
        titulo = dados["titulo_projeto"]
        paginas = dados["paginas"]

        # Usamos apenas o código do projeto (sem o título) para manter o
        # caminho curto e evitar o limite de 260 caracteres do Windows,
        # que pode fazer o PDF falhar silenciosamente ao salvar.
        pasta_nome = limpar_nome_pasta(codigo)
        pasta_projeto = PASTA_PROJETOS / pasta_nome
        pasta_historico = pasta_projeto / "Historico"

        pasta_projeto.mkdir(parents=True, exist_ok=True)
        pasta_historico.mkdir(parents=True, exist_ok=True)

        arquivo_historico_base = pasta_historico / f"{mes_referencia}_{pasta_nome}.pdf"
        arquivo_atual = pasta_projeto / "Atual.pdf"

        # Histórico: nunca sobrescreve.
        # Se já existir, cria _v2, _v3 etc.
        arquivo_historico = criar_pdf_com_paginas(
            pdf_origem=pdf,
            paginas=paginas,
            destino=arquivo_historico_base,
            sobrescrever=False
        )

        # Atual.pdf: sempre recebe o conteúdo mais recente,
        # mas mantém o mesmo caminho e o mesmo nome.
        shutil.copyfile(arquivo_historico, arquivo_atual)

        paginas_humanas = ", ".join(str(p + 1) for p in paginas)

        if codigo not in codigos_ja_cadastrados:
            novos_cadastros.append({
                "codigo_projeto": codigo,
                "titulo_projeto": titulo,
                "pasta_projeto": str(pasta_projeto),
                "primeiro_arquivo": pdf_path.name,
                "primeira_pagina": str(paginas[0] + 1),
                "data_criacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        novas_linhas_indice.append({
            "codigo_projeto": codigo,
            "titulo_projeto": titulo,
            "mes_referencia": mes_referencia,
            "arquivo_origem": str(pdf_path),
            "paginas_encontradas": paginas_humanas,
            "arquivo_atual": str(arquivo_atual),
            "arquivo_historico": str(arquivo_historico),
            "data_processamento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "Atualizado"
        })

        print(f"OK - {codigo} | páginas {paginas_humanas}")
        print(f"     Histórico criado: {arquivo_historico.name}")
        print("     Atual.pdf atualizado")

    pdf.close()

    # =====================================================
    # Atualiza projetos_detectados.csv
    # =====================================================

    df_novos_cadastros = pd.DataFrame(novos_cadastros)

    if df_projetos_antigo.empty:
        df_projetos_final = df_novos_cadastros
    else:
        df_projetos_final = pd.concat(
            [df_projetos_antigo, df_novos_cadastros],
            ignore_index=True
        )

    if not df_projetos_final.empty:
        df_projetos_final = df_projetos_final.drop_duplicates(
            subset=["codigo_projeto"],
            keep="first"
        )

    salvar_csv(df_projetos_final, CSV_PROJETOS)

    # =====================================================
    # Atualiza indice_links_reports.csv
    # Mantém somente a última versão por projeto.
    # =====================================================

    df_novo_indice = pd.DataFrame(novas_linhas_indice)

    if df_indice_antigo.empty:
        df_indice_final = df_novo_indice
    else:
        df_indice_final = pd.concat(
            [df_indice_antigo, df_novo_indice],
            ignore_index=True
        )

    if not df_indice_final.empty:
        df_indice_final = df_indice_final.drop_duplicates(
            subset=["codigo_projeto"],
            keep="last"
        )

    salvar_csv(df_indice_final, CSV_INDICE)

    print()
    print("=" * 80)
    print("Processamento finalizado.")
    print(f"Cadastro de projetos: {CSV_PROJETOS}")
    print(f"Índice atual: {CSV_INDICE}")
    print("=" * 80)


# =====================================================
# PROCESSAMENTO DE TODOS OS GERENCIAIS (EM LOTE)
# =====================================================

def processar_todos_os_gerenciais():
    """
    Lê todos os PDFs gerenciais válidos encontrados na pasta base
    (ignorando a pasta PROJETOS) e processa cada um, em ORDEM
    CRONOLÓGICA (do mês/ano mais antigo para o mais recente).

    Isso garante que o histórico de cada projeto seja construído
    na sequência correta (ex.: 2026-01, depois 2026-02, depois 2026-03...),
    já que criar_pdf_com_paginas() sempre acrescenta uma nova versão
    (_v2, _v3...) quando o arquivo de histórico daquele mês já existe,
    e Atual.pdf é sobrescrito a cada rodada com o conteúdo mais recente
    processado.
    """
    pdfs = obter_pdfs_validos()

    if not pdfs:
        print("Nenhum PDF encontrado na pasta base ou subpastas.")
        return

    pdfs_ordenados = sorted(pdfs, key=chave_mes_ano)

    
    print(f"Serão processados {len(pdfs_ordenados)} arquivo(s), em ordem cronológica:")
    for pdf_path in pdfs_ordenados:
        ano, mes = chave_mes_ano(pdf_path)
        print(f"  - [{ano:04d}-{mes:02d}] {pdf_path.name}")



    total = len(pdfs_ordenados)

    for i, pdf_path in enumerate(pdfs_ordenados, start=1):
        print(f"\n>>> ({i}/{total}) Iniciando processamento...")
        try:
            processar_pdf(pdf_path)
        except Exception as e:
            print(f"ERRO ao processar '{pdf_path.name}': {e}")
            print("Seguindo para o próximo arquivo...")


    print("Processamento em lote finalizado.")
    print(f"Total de arquivos processados: {total}")



# =====================================================
# EXECUÇÃO
# =====================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg.lower() in ("--todos", "-t", "todos"):
            # python ler_mpp_para_csv.py --todos
            processar_todos_os_gerenciais()
        else:
            # python ler_mpp_para_csv.py "caminho\do\arquivo.pdf"
            pdf_especifico = Path(arg)

            if not pdf_especifico.exists():
                raise FileNotFoundError(f"Arquivo informado não existe: {pdf_especifico}")

            processar_pdf(pdf_especifico)

    else:
        # Sem argumentos: processa apenas o PDF mais recente
        pdf_recente = obter_pdf_mais_recente()
        processar_pdf(pdf_recente)