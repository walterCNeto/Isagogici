#!/usr/bin/env python3
"""
01_rasterize_pdf.py — Converte o PDF do Isagogici em PNGs (200 DPI).

Uso:
    python scripts/01_rasterize_pdf.py
    python scripts/01_rasterize_pdf.py --pdf custom_path.pdf --dpi 150

Saída:
    pages/page-001.png, page-002.png, ...
"""
import argparse
from pathlib import Path
import sys

try:
    from pdf2image import convert_from_path
except ImportError:
    print("ERRO: pacote 'pdf2image' não instalado.")
    print("Rode: pip install pdf2image pillow")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pdf",
        default="Isagogicorum_chronologiae_canonum_libri.pdf",
        help="Caminho do PDF de entrada",
    )
    parser.add_argument("--dpi", type=int, default=200,
                        help="Resolução em DPI (default: 200)")
    parser.add_argument("--output", default="pages",
                        help="Pasta de saída")
    parser.add_argument("--start", type=int, default=1,
                        help="Página inicial (1-indexed)")
    parser.add_argument("--end", type=int, default=None,
                        help="Página final (1-indexed)")
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"ERRO: PDF não encontrado em {pdf_path}")
        print("Coloque o PDF na raiz do projeto ou use --pdf <caminho>.")
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Rasterizando {pdf_path}...")
    print(f"  DPI: {args.dpi}")
    print(f"  Saída: {output_dir}/")
    print()

    # Converte PDF em batches de 50 páginas pra economizar memória
    BATCH_SIZE = 50
    total = 0

    # Primeiro, descobre número total de páginas
    from pdf2image.pdf2image import pdfinfo_from_path
    info = pdfinfo_from_path(str(pdf_path))
    total_pages = info["Pages"]
    print(f"Total de páginas no PDF: {total_pages}")

    end = args.end or total_pages
    print(f"Processando páginas {args.start} a {end}")
    print()

    current = args.start
    while current <= end:
        batch_end = min(current + BATCH_SIZE - 1, end)
        print(f"  Batch: páginas {current}-{batch_end}...", end="", flush=True)

        try:
            images = convert_from_path(
                str(pdf_path),
                dpi=args.dpi,
                first_page=current,
                last_page=batch_end,
            )
        except Exception as e:
            print(f"\nERRO no batch {current}-{batch_end}: {e}")
            print("Se for erro de poppler, instale-o: https://github.com/oschwartz10612/poppler-windows/releases/")
            sys.exit(1)

        for offset, img in enumerate(images):
            page_num = current + offset
            output_path = output_dir / f"page-{page_num:03d}.png"
            img.save(output_path, "PNG")
            total += 1

        print(f" OK ({len(images)} páginas)")
        current = batch_end + 1

    print()
    print(f"✓ {total} páginas geradas em {output_dir}/")
    print(f"  Tamanho médio: ", end="")
    sizes = [p.stat().st_size for p in output_dir.glob("page-*.png")]
    if sizes:
        avg_kb = sum(sizes) / len(sizes) / 1024
        total_mb = sum(sizes) / 1024 / 1024
        print(f"{avg_kb:.0f} KB/página, total {total_mb:.0f} MB")


if __name__ == "__main__":
    main()
