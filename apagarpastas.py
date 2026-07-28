from pathlib import Path
import shutil


PASTA_BASE = Path(
    r"C:\Users\gabriel.torres\OneDrive - CNPEM - Centro Nacional de Pesquisa em Energia e Materiais\Documentos\DAI - PMO DAI\1.REUNIÃO GERENCIAL DE ACOMPANHAMENTO DAI\REUNIÃO GERENCIAL - 2026"
)

PASTA_PROJETOS = PASTA_BASE / "PROJETOS"

DRY_RUN = False


def apagar_pastas_de_projetos():
    if not PASTA_PROJETOS.exists():
        print("A pasta PROJETOS nao foi encontrada.")
        print(PASTA_PROJETOS)
        return

    itens = list(PASTA_PROJETOS.iterdir())

    pastas_para_apagar = []

    for item in itens:
        if item.is_dir():
            pastas_para_apagar.append(item)

    if not pastas_para_apagar:
        print("Nenhuma pasta de projeto encontrada para apagar.")
        return

    print("=" * 80)
    print("PASTAS DE PROJETOS ENCONTRADAS")
    print("=" * 80)

    for pasta in pastas_para_apagar:
        print(pasta)

    print("=" * 80)
    print(f"Total de pastas encontradas: {len(pastas_para_apagar)}")
    print(f"DRY_RUN: {DRY_RUN}")
    print("=" * 80)

    for pasta in pastas_para_apagar:
        if DRY_RUN:
            print(f"[SIMULACAO] Apagaria a pasta: {pasta}")
        else:
            shutil.rmtree(pasta)
            print(f"[APAGADO] Pasta: {pasta}")

    print("=" * 80)
    print("Processo finalizado.")
    print("=" * 80)

    if DRY_RUN:
        print("Nada foi apagado porque DRY_RUN esta como True.")
        print("Para apagar de verdade, altere para:")
        print("DRY_RUN = False")


if __name__ == "__main__":
    apagar_pastas_de_projetos()