#!/usr/bin/env python3
"""
02_translate_pages.py — Tradução com Opus 4.7 (versão 2 — corrigida).

CORREÇÕES desta versão:
- max_tokens 8000 -> 16000 (resolve truncamento de páginas densas)
- Redimensionamento automático de imagens > 4 MB (resolve erro 400 da p.1)
- Salva resposta raw em raw_responses/ quando JSON falha (pra recuperação manual)
- Tenta reparar JSON truncado automaticamente

Uso:
    python scripts/02_translate_pages.py --resume
    python scripts/02_translate_pages.py --retry-failed
"""
import argparse
import base64
import io
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import anthropic
    from PIL import Image
except ImportError:
    print("ERRO: pacote 'anthropic' ou 'pillow' não instalado.")
    print("Rode: pip install anthropic pillow")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent))
from prompt_isagogici import PROMPT_ISAGOGICI


# === CONFIGURAÇÃO ===
MODEL_NAME = "claude-opus-4-7"
MAX_OUTPUT_TOKENS = 16000          # dobrado, evita truncamento
MAX_IMAGE_BYTES = 4_500_000        # margem de segurança contra limite de 5MB
COOLDOWN_SECONDS = 0.5

PAGES_DIR = Path("pages")
OUTPUT_DIR = Path("translated")
RAW_DIR = Path("raw_responses")    # respostas que falharam parsing
LOG_FILE = Path("translation_log.jsonl")


def shrink_image_if_needed(image_path: Path) -> bytes:
    """Lê imagem e reduz se ultrapassar limite da API."""
    img_bytes = image_path.read_bytes()
    if len(img_bytes) <= MAX_IMAGE_BYTES:
        return img_bytes

    # Imagem muito grande, redimensiona preservando legibilidade
    img = Image.open(io.BytesIO(img_bytes))

    # Tenta redimensionar progressivamente até caber
    scale = 0.85
    while scale > 0.3:
        new_width = int(img.width * scale)
        new_height = int(img.height * scale)
        resized = img.resize((new_width, new_height), Image.LANCZOS)
        buf = io.BytesIO()
        resized.save(buf, format="PNG", optimize=True)
        new_bytes = buf.getvalue()
        if len(new_bytes) <= MAX_IMAGE_BYTES:
            print(f" [imagem reduzida {scale*100:.0f}%]", end="", flush=True)
            return new_bytes
        scale -= 0.1

    # Último recurso: salva como JPEG com qualidade alta
    img = img.convert("RGB")
    for quality in [85, 75, 65]:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        new_bytes = buf.getvalue()
        if len(new_bytes) <= MAX_IMAGE_BYTES:
            print(f" [convertida JPEG q={quality}]", end="", flush=True)
            return new_bytes

    raise ValueError(f"Imagem muito grande mesmo após reduções: {image_path.name}")


def get_media_type(image_bytes: bytes) -> str:
    """Detecta tipo da imagem pelos primeiros bytes."""
    if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
        return "image/png"
    elif image_bytes[:3] == b'\xff\xd8\xff':
        return "image/jpeg"
    return "image/png"  # default


def try_repair_json(raw: str) -> dict:
    """Tenta reparar JSON truncado/malformado."""
    # Remove markdown fence
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])

    raw = raw.strip()

    # Tentativa 1: parsing direto
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Tentativa 2: remover último campo incompleto e fechar
    # Procura último campo completo seguido de vírgula/quebra
    # Estratégia: trunca no último } ou ] válido aninhado
    open_braces = 0
    open_brackets = 0
    in_string = False
    escape = False
    last_safe_pos = -1

    for i, c in enumerate(raw):
        if escape:
            escape = False
            continue
        if c == "\\":
            escape = True
            continue
        if c == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if c == "{":
            open_braces += 1
        elif c == "}":
            open_braces -= 1
        elif c == "[":
            open_brackets += 1
        elif c == "]":
            open_brackets -= 1

        # Posição "segura" = depois de uma vírgula no nível superior
        if (c == "," and open_braces == 1 and open_brackets == 0
                and not in_string):
            last_safe_pos = i

    if last_safe_pos > 0:
        # Trunca no último ponto seguro e fecha o JSON
        truncated = raw[:last_safe_pos]
        # Adiciona fechos suficientes
        attempt = truncated + "}"
        try:
            return json.loads(attempt)
        except json.JSONDecodeError:
            pass

    # Tentativa 3: regex que extrai bloco JSON balanceado do começo
    match = re.search(r'\{', raw)
    if match:
        start = match.start()
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(raw)):
            c = raw[i]
            if esc:
                esc = False
                continue
            if c == "\\":
                esc = True
                continue
            if c == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    chunk = raw[start:i+1]
                    try:
                        return json.loads(chunk)
                    except json.JSONDecodeError:
                        break

    raise ValueError("Não consegui reparar o JSON")


def encode_image_base64(image_bytes: bytes) -> str:
    return base64.standard_b64encode(image_bytes).decode("utf-8")


def translate_page(client, page_num: int, image_path: Path) -> dict:
    image_bytes = shrink_image_if_needed(image_path)
    image_data = encode_image_base64(image_bytes)
    media_type = get_media_type(image_bytes)

    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=MAX_OUTPUT_TOKENS,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data,
                    },
                },
                {
                    "type": "text",
                    "text": PROMPT_ISAGOGICI + f"\n\n## Página número: {page_num}\n",
                },
            ],
        }],
    )

    raw = response.content[0].text.strip()

    # Salva raw em todo caso (pra debug)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / f"page-{page_num:03d}.txt"
    raw_path.write_text(raw, encoding="utf-8")

    try:
        data = try_repair_json(raw)
    except ValueError as e:
        # Mantém raw response mas marca página como falhada
        raise ValueError(f"JSON irreparável: {e}. Raw em {raw_path}")

    if "page" not in data or data["page"] != page_num:
        data["page"] = page_num

    data["_meta"] = {
        "model": MODEL_NAME,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "stop_reason": response.stop_reason,
    }

    # Se reparado, marca pra revisão
    if response.stop_reason == "max_tokens":
        flags = data.get("uncertainty_flags") or []
        flags.append("ATENÇÃO: tradução pode estar truncada (max_tokens atingido). Verificar completude.")
        data["uncertainty_flags"] = flags

    return data


def log_result(page_num: int, status: str, tokens_in: int, tokens_out: int, error: str = None):
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "page": page_num,
        "status": status,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
    }
    if error:
        entry["error"] = str(error)[:300]
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def get_failed_pages() -> set:
    if not LOG_FILE.exists():
        return set()
    failed = set()
    success = set()
    with open(LOG_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line)
                if entry["status"] == "ok":
                    success.add(entry["page"])
                elif entry["status"] == "error":
                    failed.add(entry["page"])
            except json.JSONDecodeError:
                continue
    return failed - success


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--cooldown", type=float, default=COOLDOWN_SECONDS)
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERRO: ANTHROPIC_API_KEY não definida.")
        sys.exit(1)

    if not PAGES_DIR.exists():
        print(f"ERRO: pasta {PAGES_DIR} não existe.")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_pngs = sorted(PAGES_DIR.glob("page-*.png"))
    if not all_pngs:
        print(f"ERRO: nenhum PNG em {PAGES_DIR}/")
        sys.exit(1)

    page_nums = []
    for png in all_pngs:
        try:
            n = int(png.stem.replace("page-", ""))
            page_nums.append(n)
        except ValueError:
            continue
    page_nums.sort()

    if args.retry_failed:
        target_pages = sorted(get_failed_pages())
        print(f"Re-tentando {len(target_pages)} páginas que falharam.")
    else:
        end = args.end or page_nums[-1]
        target_pages = [n for n in page_nums if args.start <= n <= end]

    if args.resume and not args.retry_failed:
        already_done = set()
        for jsonf in OUTPUT_DIR.glob("page-*.json"):
            try:
                n = int(jsonf.stem.replace("page-", ""))
                already_done.add(n)
            except ValueError:
                continue
        target_pages = [n for n in target_pages if n not in already_done]
        print(f"Resume: {len(already_done)} já feitas, {len(target_pages)} restantes.")

    if not target_pages:
        print("Nada a fazer.")
        return

    print(f"Modelo: {MODEL_NAME}")
    print(f"Max output tokens: {MAX_OUTPUT_TOKENS}")
    print(f"Páginas a processar: {len(target_pages)}")
    print(f"Cooldown: {args.cooldown}s")
    cost_est = len(target_pages) * 0.30  # estimativa com max_tokens maior
    print(f"Custo estimado: ~US$ {cost_est:.2f}")
    print()

    client = anthropic.Anthropic(api_key=api_key)

    total_in = 0
    total_out = 0
    n_ok = 0
    n_err = 0
    n_truncated = 0

    for i, page_num in enumerate(target_pages, 1):
        png_path = PAGES_DIR / f"page-{page_num:03d}.png"
        if not png_path.exists():
            print(f"  [{i}/{len(target_pages)}] p.{page_num}: PNG ausente")
            log_result(page_num, "missing_png", 0, 0, "PNG ausente")
            n_err += 1
            continue

        try:
            print(f"  [{i}/{len(target_pages)}] p.{page_num}: traduzindo...", end="", flush=True)
            t0 = time.time()
            data = translate_page(client, page_num, png_path)
            dt = time.time() - t0

            output_path = OUTPUT_DIR / f"page-{page_num:03d}.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            tin = data["_meta"]["input_tokens"]
            tout = data["_meta"]["output_tokens"]
            stop = data["_meta"]["stop_reason"]
            total_in += tin
            total_out += tout
            n_ok += 1
            if stop == "max_tokens":
                n_truncated += 1

            log_result(page_num, "ok", tin, tout)
            tag = " [TRUNCADA]" if stop == "max_tokens" else ""
            print(f" OK ({dt:.1f}s, {tin}+{tout} tok){tag}")

        except Exception as e:
            print(f" ERRO: {str(e)[:100]}")
            log_result(page_num, "error", 0, 0, str(e))
            n_err += 1

        if i < len(target_pages):
            time.sleep(args.cooldown)

    print()
    print("=" * 60)
    print(f"Total: {n_ok} ok, {n_err} erro(s)")
    if n_truncated:
        print(f"Páginas com max_tokens atingido: {n_truncated} (revisar manualmente)")
    print(f"Tokens: {total_in:,} input + {total_out:,} output")
    cost = (total_in / 1_000_000 * 15) + (total_out / 1_000_000 * 75)
    print(f"Custo desta rodada: ~US$ {cost:.2f}")
    print(f"Log: {LOG_FILE}")
    if n_err:
        print(f"\nPara retentar: python scripts/02_translate_pages.py --retry-failed")


if __name__ == "__main__":
    main()