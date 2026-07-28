from pathlib import Path
import re


# =====================================================
# CONFIGURE AQUI O CAMINHO DA SUA PASTA DE 2026
# =====================================================

PASTA_BASE = Path(
    r"C:\Users\gabriel.torres\OneDrive - CNPEM - Centro Nacional de Pesquisa em Energia e Materiais\Documentos\DAI - PMO DAI\1.REUNIÃO GERENCIAL DE ACOMPANHAMENTO DAI\REUNIÃO GERENCIAL - 2026"
)

PASTA_PROJETOS = PASTA_BASE / "PROJETOS"


# =====================================================
# MODO SEGURO
# =====================================================
# True  = apenas mostra o que seria apagado
# False = apaga de verdade

DRY_RUN = False


# =====================================================
# CONFIGURAÇÕES DE LIMPEZA
# =====================================================

# Apaga arquivos do histórico com sufixo _v2, _v3, _v4...
APAGAR_VERSOES_TESTE = True

# Se quiser apagar também os CSVs gerados, mude para True
APAGAR_CSVS = False

# Se quiser apagar pastas de projeto que ficaram completamente vazias, mude para True
APAGAR_PASTAS_VAZIAS = False


def apagar_arquivo(caminho: Path):
    if DRY_RUN:
        print(f"[SIMULAÇÃO] Apagaria: {caminho}")
    else:
        caminho.unlink()
        print(f"[APAGADO] {caminho}")


def apagar_pasta_vazia(caminho: Path):
    if not caminho.exists():
        return

    try:
        caminho.rmdir()
        if DRY_RUN:
            print(f"[SIMULAÇÃO] Apagaria pasta vazia: {caminho}")
        else:
            print(f"[PASTA VAZIA APAGADA] {caminho}")
    except OSError:
        # Pasta não está vazia
        pass


def limpar_versoes_teste():
    """
    Remove arquivos PDF versionados no Histórico:
    *_v2.pdf
    *_v3.pdf
    *_v4.pdf
    etc.
    """

    if not PASTA_PROJETOS.exists():
        print(f"Pasta PROJETOS não encontrada: {PASTA_PROJETOS}")
        return

    padrao_versao = re.compile(r"_v\d+\.pdf$", re.IGNORECASE)

    arquivos_encontrados = []

    for arquivo in PASTA_PROJETOS.rglob("*.pdf"):
        if padrao_versao.search(arquivo.name):
            arquivos_encontrados.append(arquivo)

    if not arquivos_encontrados:
        print("Nenhum arquivo de teste versionado encontrado.")
        return

    print("\nArquivos de teste encontrados:")
    print("-" * 80)

    for arquivo in arquivos_encontrados:
        apagar_arquivo(arquivo)

    print("-" * 80)
    print(f"Total encontrado: {len(arquivos_encontrados)}")


def limpar_csvs():
    """
    Opcional: remove CSVs gerados pelo processamento.
    """
    csvs = [
        PASTA_PROJETOS / "projetos_detectados.csv",
        PASTA_PROJETOS / "indice_links_reports.csv",
    ]

    for csv in csvs:
        if csv.exists():
            apagar_arquivo(csv)


def limpar_pastas_vazias():
    """
    Opcional: tenta limpar pastas vazias dentro de PROJETOS.
    """
    if not PASTA_PROJETOS.exists():
        return

    # Percorre de baixo para cima
    pastas = sorted(
        [p for p in PASTA_PROJETOS.rglob("*") if p.is_dir()],
        key=lambda p: len(str(p)),
        reverse=True
    )

    for pasta in pastas:
        apagar_pasta_vazia(pasta)


def main():
    print("=" * 80)
    print("LIMPEZA DE TESTES DO HISTÓRICO")
    print("=" * 80)
    print(f"Pasta base: {PASTA_BASE}")
    print(f"Pasta projetos: {PASTA_PROJETOS}")
    print(f"DRY_RUN: {DRY_RUN}")
    print("=" * 80)

    if APAGAR_VERSOES_TESTE:
        limpar_versoes_teste()

    if APAGAR_CSVS:
        print("\nLimpando CSVs...")
        limpar_csvs()

    if APAGAR_PASTAS_VAZIAS:
        print("\nLimpando pastas vazias...")
        limpar_pastas_vazias()

    print("\nFinalizado.")

    if DRY_RUN:
        print("\nATENÇÃO: Nada foi apagado porque DRY_RUN está como True.")
        print("Se a lista estiver correta, altere para:")
        print("DRY_RUN = False")


if __name__ == "__main__":
    main()