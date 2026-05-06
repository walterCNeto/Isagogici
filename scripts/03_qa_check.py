#!/usr/bin/env python3
"""
03_qa_check.py — QA estrutural das traducoes JSON.

Verifica:
- Todos os JSONs têm campos obrigatórios
- Razão pt/latim está em range razoável (1.0 a 2.0)
- Razão en/latim está em range razoável
- Páginas faltando
- JSONs com erro de parsing
- Flags de incerteza agregadas

Saída:
    qa_report.md — relatório markdown
    qa_suspects.txt — lista de páginas suspeitas pra revisão manual
"""
import argparse
import json
from pathlib import Path
from collections import Counter, defaultdict


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--src", default="translated",
                        help="Pasta com JSONs traduzidos")
    parser.add_argument("--report", default="qa_report.md")
    parser.add_argument("--suspects", default="qa_suspects.txt")
    args = parser.parse_args()

    src = Path(args.src)
    if not src.exists():
        print(f"ERRO: pasta {src} não existe")
        return

    files = sorted(src.glob("page-*.json"))
    print(f"Analisando {len(files)} JSONs...")

    invalid = []
    missing_fields = defaultdict(list)
    page_nums_found = set()
    ratios_pt = []
    ratios_en = []
    suspects = []
    all_flags = Counter()
    all_definitions = []
    cross_refs_internal = []
    cross_refs_external = []
    type_counts = Counter()

    for f in files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            invalid.append((f.name, str(e)))
            continue

        page_num = data.get("page", -1)
        page_nums_found.add(page_num)

        # campos obrigatórios
        for field in ["page", "page_type", "latin", "pt", "en"]:
            if field not in data or data[field] is None:
                missing_fields[field].append(page_num)

        # razões de tamanho
        latin = data.get("latin", "") or ""
        pt = data.get("pt", "") or ""
        en = data.get("en", "") or ""
        if len(latin) > 100:  # só calcula se tem texto suficiente
            r_pt = len(pt) / len(latin) if len(latin) else 0
            r_en = len(en) / len(latin) if len(latin) else 0
            ratios_pt.append((page_num, r_pt))
            ratios_en.append((page_num, r_en))

            # marca como suspeito se ratio muito fora do esperado
            if r_pt < 0.7 or r_pt > 2.5:
                suspects.append((page_num, f"pt/latim ratio = {r_pt:.2f}"))
            if r_en < 0.7 or r_en > 2.5:
                suspects.append((page_num, f"en/latim ratio = {r_en:.2f}"))

        # tipos
        ptype = data.get("page_type", "?")
        type_counts[ptype] += 1

        # flags
        for flag in (data.get("uncertainty_flags") or []):
            all_flags[flag[:80]] += 1
            suspects.append((page_num, f"flag: {flag[:60]}"))

        # definições
        for d in (data.get("definitions") or []):
            all_definitions.append({
                "page": page_num,
                "term": d.get("term", "?"),
            })

        # cross-references
        for cr in (data.get("cross_references") or []):
            if cr.get("type") == "internal":
                cross_refs_internal.append({"page": page_num, "target": cr.get("target", "?")})
            else:
                cross_refs_external.append({"page": page_num, "target": cr.get("target", "?")})

    # páginas faltando
    if page_nums_found:
        all_pages = set(range(min(page_nums_found), max(page_nums_found) + 1))
        missing = sorted(all_pages - page_nums_found)
    else:
        missing = []

    # Salva report
    lines = [
        "# QA Report — Isagogici Translation\n\n",
        f"## Resumo\n\n",
        f"- JSONs analisados: **{len(files)}**\n",
        f"- JSONs válidos: **{len(files) - len(invalid)}**\n",
        f"- JSONs inválidos: **{len(invalid)}**\n",
        f"- Páginas faltando no range: **{len(missing)}**\n",
        f"- Páginas com flags de incerteza: **{len(set(p for p, _ in suspects))}**\n",
        f"- Definições capturadas: **{len(all_definitions)}**\n",
        f"- Cross-refs internas: **{len(cross_refs_internal)}**\n",
        f"- Cross-refs externas (De Emendatione, fontes antigas, etc): **{len(cross_refs_external)}**\n\n",
    ]

    if invalid:
        lines.append("## JSONs inválidos\n\n")
        for fname, err in invalid[:20]:
            lines.append(f"- `{fname}`: {err[:120]}\n")
        if len(invalid) > 20:
            lines.append(f"- ...e mais {len(invalid) - 20}\n")
        lines.append("\n")

    if missing:
        lines.append(f"## Páginas faltando ({len(missing)})\n\n")
        chunks = [missing[i:i+20] for i in range(0, len(missing), 20)]
        for chunk in chunks:
            lines.append(f"- {chunk}\n")
        lines.append("\n")

    lines.append("## Tipos de página\n\n")
    for ptype, n in type_counts.most_common():
        lines.append(f"- `{ptype}`: {n}\n")
    lines.append("\n")

    if ratios_pt:
        avg_pt = sum(r for _, r in ratios_pt) / len(ratios_pt)
        avg_en = sum(r for _, r in ratios_en) / len(ratios_en)
        lines.append("## Estatísticas de tradução\n\n")
        lines.append(f"- Razão média pt/latim: **{avg_pt:.2f}**\n")
        lines.append(f"- Razão média en/latim: **{avg_en:.2f}**\n")
        lines.append("- (esperado: 1.0–1.5; valores fora indicam tradução truncada ou inflada)\n\n")

    if all_flags:
        lines.append(f"## Top flags de incerteza\n\n")
        for flag, n in all_flags.most_common(20):
            lines.append(f"- ({n}x) {flag}\n")
        lines.append("\n")

    if all_definitions:
        lines.append(f"## Definições capturadas (top 30)\n\n")
        # agrupa por termo
        by_term = defaultdict(list)
        for d in all_definitions:
            by_term[d["term"]].append(d["page"])
        for term, pages in sorted(by_term.items(), key=lambda x: -len(x[1]))[:30]:
            lines.append(f"- **{term}**: páginas {pages[:5]}{' (...)' if len(pages) > 5 else ''}\n")
        lines.append("\n")

    Path(args.report).write_text("".join(lines), encoding="utf-8")

    # Suspects file
    suspect_pages = sorted(set(p for p, _ in suspects))
    with open(args.suspects, "w", encoding="utf-8") as f:
        f.write(f"# Páginas suspeitas para revisão manual ({len(suspect_pages)})\n\n")
        for p in suspect_pages:
            reasons = [r for pp, r in suspects if pp == p]
            f.write(f"p.{p}: {'; '.join(reasons[:3])}\n")

    print(f"OK {args.report}")
    print(f"OK {args.suspects}")
    print()
    print(f"Resumo: {len(files)} JSONs, {len(invalid)} inválidos, {len(missing)} páginas faltando")
    print(f"        {len(suspect_pages)} páginas merecem revisão manual")


if __name__ == "__main__":
    main()
