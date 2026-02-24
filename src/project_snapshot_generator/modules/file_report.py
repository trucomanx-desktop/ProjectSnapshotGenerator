#!/usr/bin/python3


#!/usr/bin/python3

import ast
import os
import sys
from typing import Set, List


# -------------------------------------------------
# 1️⃣ Extrai módulos importados de um arquivo
# -------------------------------------------------
def extrair_imports(arquivo_py: str) -> Set[str]:
    with open(arquivo_py, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=arquivo_py)

    modulos = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modulos.add(alias.name)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modulos.add(node.module)

    return modulos


# -------------------------------------------------
# 2️⃣ Resolve nome do módulo → caminho real no base
# -------------------------------------------------
def resolver_modulo_para_caminho(modulo: str, diretorio_base: str) -> str | None:
    partes = modulo.split(".")
    caminho = os.path.join(diretorio_base, *partes)

    # modulo.py
    if os.path.isfile(caminho + ".py"):
        return os.path.abspath(caminho + ".py")

    # pacote/__init__.py
    if os.path.isfile(os.path.join(caminho, "__init__.py")):
        return os.path.abspath(os.path.join(caminho, "__init__.py"))

    return None


# -------------------------------------------------
# 3️⃣ Dependências diretas locais
# -------------------------------------------------
def encontrar_dependencias_diretas(arquivo_py: str, diretorio_base: str) -> List[str]:
    imports = extrair_imports(arquivo_py)
    dependencias = []

    for modulo in imports:
        caminho = resolver_modulo_para_caminho(modulo, diretorio_base)
        if caminho:
            dependencias.append(caminho)

    return dependencias


# -------------------------------------------------
# 4️⃣ Resolução recursiva (DFS)
# -------------------------------------------------
def resolver_dependencias_recursivas(
    arquivo_py: str,
    diretorio_base: str,
    visitados: Set[str] | None = None
) -> List[str]:

    if visitados is None:
        visitados = set()

    arquivo_py = os.path.abspath(arquivo_py)

    if arquivo_py in visitados:
        return []

    visitados.add(arquivo_py)

    resultado = [arquivo_py]

    dependencias = encontrar_dependencias_diretas(arquivo_py, diretorio_base)

    for dep in dependencias:
        resultado.extend(
            resolver_dependencias_recursivas(dep, diretorio_base, visitados)
        )

    return resultado


# -------------------------------------------------
# 5️⃣ Formatação da saída
# -------------------------------------------------
def formatar_saida(lista_arquivos: List[str], diretorio_base: str) -> str:
    blocos = []

    for arquivo in lista_arquivos:
        caminho_relativo = os.path.relpath(arquivo, diretorio_base)

        with open(arquivo, "r", encoding="utf-8") as f:
            conteudo = f.read()

        bloco = f"```{caminho_relativo}\n{conteudo}\n```"
        blocos.append(bloco)

    return "\n\n".join(blocos)


# -------------------------------------------------
# 6️⃣ Função principal pública
# -------------------------------------------------
def gerar_bundle_codigo(arquivo_principal: str, diretorio_base: str) -> str:
    arquivos = resolver_dependencias_recursivas(
        arquivo_principal,
        diretorio_base
    )

    return formatar_saida(arquivos, diretorio_base)


# -------------------------------------------------
# 7️⃣ MAIN
# -------------------------------------------------
def main():


    arquivo_principal = "/mnt/boveda/ARTIGOS/ArtigoPatientDoctor/tools/DetectionDatasetAnalysis/src/detection_dataset_analysis/program_yaml.py"
    diretorio_base = "/mnt/boveda/ARTIGOS/ArtigoPatientDoctor/tools/DetectionDatasetAnalysis/src/"


    bundle = gerar_bundle_codigo(arquivo_principal, diretorio_base)

    output_file = "snapshot.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(bundle)

    print(f"✅ Snapshot salvo em: {output_file}")
    print(f"📦 Total de arquivos incluídos: {bundle.count('```') // 2}")


if __name__ == "__main__":
    main()
