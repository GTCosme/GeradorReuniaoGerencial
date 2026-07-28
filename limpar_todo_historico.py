from pathlib import Path
import shutil
import os
import stat
import time


PASTA_BASE = Path(
    r"C:\Users\gabriel.torres\OneDrive - CNPEM - Centro Nacional de Pesquisa em Energia e Materiais\Documentos\DAI - PMO DAI\1.REUNIÃO GERENCIAL DE ACOMPANHAMENTO DAI\REUNIÃO GERENCIAL - 2026"
)

PASTA_PROJETOS = PASTA_BASE / "PROJETOS"

DRY_RUN = False

def liberar_permissao_e_tentar_novamente(funcao, caminho, erro):
    """
    Tenta remover atributo somente leitura e executar novamente a exclusão.
    Usado pelo shutil.rmtree quando encontra PermissionError.
    """

    try:
        os.chmod(caminho, stat.S_IWRITE)
        funcao(caminho)
    except Exception as novo_erro:
        print(f"[ERRO] Nao foi possivel apagar: {caminho}")
        print(f"       Motivo: {novo_erro}")


def apagar_pasta_com_tentativas(pasta: Path):
    """
    Tenta apagar uma pasta algumas vezes.
    Ajuda quando o OneDrive ou Windows ainda esta segurando o arquivo.
    """

    tentativas = 3

    for tentativa in range(1, tentativas + 1):
        try:
            shutil.rmtree(
                pasta,
                onexc=liberar_permissao_e_tentar_novamente
            )
            print(f"[APAGADO] Pasta: {pasta}")
            return True

        except PermissionError as erro:
            print(f"[TENTATIVA {tentativa}] Acesso negado: {pasta}")
            print(f"Motivo: {erro}")

            if tentativa < tentativas:
                time.sleep(2)

        except Exception as erro:
            print(f"[ERRO] Falha ao apagar: {pasta}")
            print(f"Motivo: {erro}")
            return False

    print(f"[FALHOU] Nao foi possivel apagar apos {tentativas} tentativas: {pasta}")
    return False


def apagar_pastas_de_projetos():
    if not PASTA_PROJETOS.exists():
        print("A pasta PROJETOS nao foi encontrada.")
        print(PASTA_PROJETOS)
        return

    pastas_para_apagar = []

    for item in PASTA_PROJETOS.iterdir():
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

    total_apagadas = 0
    total_falhas = 0

    for pasta in pastas_para_apagar:
        if DRY_RUN:
            print(f"[SIMULACAO] Apagaria a pasta: {pasta}")
        else:
            sucesso = apagar_pasta_com_tentativas(pasta)

            if sucesso:
                total_apagadas += 1
            else:
                total_falhas += 1

    print("=" * 80)
    print("Processo finalizado.")
    print(f"Pastas apagadas: {total_apagadas}")
    print(f"Falhas: {total_falhas}")
    print("=" * 80)

    if DRY_RUN:
        print("Nada foi apagado porque DRY_RUN esta como True.")
        print("Para apagar de verdade, altere para:")
        print("DRY_RUN = False")


if __name__ == "__main__":
    apagar_pastas_de_projetos()