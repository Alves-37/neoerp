import argparse
from pathlib import Path


def list_pics(pics_dir: str) -> None:
    """
    Lista todos os ficheiros de imagem na pasta 'pics' (ou subpastas).
    Mostra nome, tamanho e data de modificação.
    """
    root = Path(pics_dir).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        print(f"Diretório não encontrado: {root}")
        return

    exts = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"}
    files = sorted([f for f in root.rglob("*") if f.is_file() and f.suffix.lower() in exts])

    if not files:
        print(f"Nenhuma imagem encontrada em: {root}")
        return

    print(f"Imagens encontradas em: {root}")
    print("-" * 80)
    for f in files:
        rel_path = f.relative_to(root)
        size_kb = f.stat().st_size / 1024
        mtime = f.stat().st_mtime
        print(f"{rel_path} ({size_kb:.1f} KB, mtime={mtime})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Listar imagens na pasta 'pics' (ou subpastas).")
    parser.add_argument(
        "pics_dir",
        nargs="?",
        default="pics",
        help="Caminho para a pasta de imagens. Padrão: 'pics' na pasta atual.",
    )
    args = parser.parse_args()

    list_pics(args.pics_dir)


if __name__ == "__main__":
    main()
