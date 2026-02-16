from pathlib import Path


def generate_tree(root_path, patterns=None, ignorar=None):
    """
    Gera uma árvore de diretórios mostrando apenas arquivos que correspondem aos padrões.
    
    Args:
        root_path: Caminho raiz do projeto
        patterns: String ou lista de padrões (ex: "*.py", ["*.py", "*.conf", "*.js"])
        ignorar: Lista de pastas/arquivos a ignorar (ex: ['__pycache__', '.git', 'venv'])
    
    Returns:
        String com a estrutura em árvore
    """
    if ignorar is None:
        ignorar = ['__pycache__', '.git', 'venv', 'node_modules', '.env', '.venv']
    
    # Converte pattern para lista se for string
    if patterns is None:
        patterns = ["*.py"]
    elif isinstance(patterns, str):
        patterns = [patterns]
    
    root = Path(root_path).resolve()
    
    def deve_ignorar(caminho):
        return any(parte in ignorar for parte in caminho.parts)
    
    # Coleta todos os arquivos para cada padrão
    arquivos = []
    for pattern in patterns:
        for arquivo in root.rglob(pattern):
            if arquivo.is_file() and not deve_ignorar(arquivo.relative_to(root)):
                if arquivo not in arquivos:  # Evita duplicatas
                    arquivos.append(arquivo)
    
    arquivos.sort()
    
    # Constrói a árvore
    patterns_str = ", ".join(patterns)
    resultado = [f"📁 {root.name}/ [{patterns_str}]"]
    
    # Agrupa por diretório
    estrutura = {}
    for arquivo in arquivos:
        rel_path = arquivo.relative_to(root)
        partes = rel_path.parts
        
        atual = estrutura
        for parte in partes[:-1]:
            if parte not in atual:
                atual[parte] = {}
            atual = atual[parte]
        
        # Adiciona o arquivo
        if '__arquivos__' not in atual:
            atual['__arquivos__'] = []
        atual['__arquivos__'].append(partes[-1])
    
    def imprimir_estrutura(dicionario, prefixo=""):
        items = [(k, v) for k, v in sorted(dicionario.items()) if k != '__arquivos__']
        
        for i, (nome, conteudo) in enumerate(items):
            e_ultimo_item = (i == len(items) - 1)
            conector = "└── " if e_ultimo_item else "├── "
            
            resultado.append(f"{prefixo}{conector}📁 {nome}/")
            
            novo_prefixo = prefixo + ("    " if e_ultimo_item else "│   ")
            
            # Imprime arquivos desta pasta
            if '__arquivos__' in conteudo:
                arquivos_pasta = sorted(conteudo['__arquivos__'])
                subpastas = [k for k in conteudo.keys() if k != '__arquivos__']
                
                for j, arq in enumerate(arquivos_pasta):
                    e_ultimo_arq = (j == len(arquivos_pasta) - 1 and len(subpastas) == 0)
                    conector_arq = "└── " if e_ultimo_arq else "├── "
                    resultado.append(f"{novo_prefixo}{conector_arq}📄 {arq}")
            
            # Recursão para subpastas
            imprimir_estrutura(conteudo, novo_prefixo)
    
    # Arquivos na raiz
    if '__arquivos__' in estrutura:
        for i, arq in enumerate(sorted(estrutura['__arquivos__'])):
            tem_pastas = len([k for k in estrutura.keys() if k != '__arquivos__']) > 0
            e_ultimo = (i == len(estrutura['__arquivos__']) - 1 and not tem_pastas)
            conector = "└── " if e_ultimo else "├── "
            resultado.append(f"{conector}📄 {arq}")
    
    imprimir_estrutura(estrutura)
    
    resultado.append("")
    resultado.append(f"Total files ({patterns_str}): {len(arquivos)}")
    
    return "\n".join(resultado)


def serialize_project(root_path, patterns=None, incluir_tree=True, ignorar=None):
    """
    Serializa arquivos de um projeto em uma string formatada.
    
    Args:
        root_path: Caminho raiz do projeto
        patterns: String ou lista de padrões (ex: "*.py", ["*.py", "*.js", "*.txt"])
        incluir_tree: Se True, inclui árvore de diretórios no início
        ignorar: Lista de pastas/arquivos a ignorar
    
    Returns:
        String com a estrutura e conteúdo dos arquivos
    """
    root = Path(root_path).resolve()
    
    if ignorar is None:
        ignorar = ['__pycache__', '.git', 'venv', 'node_modules', '.env', '.venv']
    
    # Converte pattern para lista se for string
    if patterns is None:
        patterns = ["*.py"]
    elif isinstance(patterns, str):
        patterns = [patterns]
    
    def deve_ignorar(caminho):
        return any(parte in ignorar for parte in caminho.parts)
    
    # Coleta todos os arquivos que correspondem aos padrões
    arquivos_encontrados = []
    for pattern in patterns:
        for arquivo in root.rglob(pattern):
            if arquivo.is_file() and not deve_ignorar(arquivo.relative_to(root)):
                if arquivo not in arquivos_encontrados:  # Evita duplicatas
                    arquivos_encontrados.append(arquivo)
    
    # Ordena os arquivos por caminho
    arquivos_encontrados.sort()
    
    resultado = []
    
    # Gera a árvore de diretórios usando a função generate_tree()
    if incluir_tree:
        resultado.append("=" * 80)
        resultado.append("DIRECTORY STRUCTURE")
        resultado.append("=" * 80)
        resultado.append("")
        resultado.append(generate_tree(root_path, patterns, ignorar))
        resultado.append("")
    
    # Adiciona conteúdo dos arquivos
    resultado.append("=" * 80)
    resultado.append("FILE CONTENT")
    resultado.append("=" * 80)
    resultado.append("")
    
    for arquivo in arquivos_encontrados:
        caminho_rel = arquivo.relative_to(root)
        
        resultado.append(f"```{caminho_rel}")
        
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                resultado.append(conteudo)
        except Exception as e:
            resultado.append(f"[ERROR WHEN READING FILE: {e}]")
        
        resultado.append("```")
        resultado.append("")
    
    return "\n".join(resultado)


# Exemplos de uso
if __name__ == "__main__":
    caminho = "/home/fernando/Downloads/VoiceOutTranslator/src"
    
    # Exemplo 1: Um único padrão (string)
    print("=" * 80)
    print("EXEMPLO 1: Apenas arquivos .py")
    print("=" * 80)
    tree = generate_tree(caminho, patterns="*.py")
    print(tree)
    print("\n\n")
    
    # Exemplo 2: Múltiplos padrões (lista)
    print("=" * 80)
    print("EXEMPLO 2: Arquivos .py e .md")
    print("=" * 80)
    tree = generate_tree(caminho, patterns=["*.py", "*.md"])
    print(tree)
    print("\n\n")
    
    
    # Exemplo 4: Serialização completa com múltiplos padrões
    print("Gerando serialização completa...")
    output = serialize_project(
        caminho, 
        patterns=["*.py", "*.md", "*.json"],
        incluir_tree=True
    )
    
    # Salva em um arquivo
    with open("projeto_serializado.txt", "w", encoding="utf-8") as f:
        f.write(output)
    
    print("Arquivo 'projeto_serializado.txt' criado com sucesso!")
