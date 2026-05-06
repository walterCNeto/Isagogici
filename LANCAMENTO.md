# Guia de Lançamento — Passo a Passo

Este documento descreve exatamente o que fazer pra colocar a tradução no ar.

## Pré-requisitos (você já tem)

- ✅ Python 3.11.9
- ✅ venv ativo em `C:\Users\User\Documents\Walter\Isagogicorum\venv`
- ✅ pdf2image + pillow instalados
- ✅ poppler funcional (testado com `python -c "from pdf2image import convert_from_path; print('OK')"`)
- ✅ ANTHROPIC_API_KEY configurada (chave nova, depois de revogar a vazada)
- ✅ Repo criado em https://github.com/walterCNeto/Isagogici

## Passo 1 — Extrair o bootstrap

Baixa `isagogici-bootstrap.tar.gz` e extrai dentro da pasta do projeto:

```cmd
cd "C:\Users\User\Documents\Walter\Isagogicorum"
tar xzf isagogici-bootstrap.tar.gz --strip-components=1
```

Confirma que apareceram os arquivos:

```cmd
dir
```

Tem que aparecer: `scripts\`, `docs\`, `data\`, `.github\`, `README.md`, `CONTRIBUTING.md`, `LICENSE`, `LANCAMENTO.md`, `.gitignore`, `requirements.txt`.

## Passo 2 — Confirmar dependências

Ainda no venv:

```cmd
venv\Scripts\activate
pip install -r requirements.txt
```

Tem que dizer "Requirement already satisfied" ou instalar `anthropic` (que ainda não tinha).

## Passo 3 — Confirmar API key

```cmd
echo %ANTHROPIC_API_KEY%
```

Tem que mostrar a chave nova (formato `sk-ant-api03-...`). Se mostrar `%ANTHROPIC_API_KEY%` literal, você precisa **abrir um CMD novo** (a variável só fica disponível em sessões abertas depois do `setx`).

## Passo 4 — Garantir que o PDF está no lugar certo

Confere:

```cmd
dir Isagogicorum_chronologiae_canonum_libri.pdf
```

Tem que listar o arquivo (390 páginas, alguns MB).

## Passo 5 — Rasterizar o PDF

```cmd
python scripts\01_rasterize_pdf.py
```

Vai converter as 390 páginas em PNGs dentro de `pages\`. Demora uns 5-10 minutos. No final você terá 390 arquivos `page-001.png`, `page-002.png`, ..., `page-390.png`.

## Passo 6 — Tradução com Opus 4.7

⚠️ **ATENÇÃO**: Este passo gasta créditos da API. Custo estimado: **~US$ 90**.

Antes de rodar tudo, faz um **teste com 3 páginas** pra confirmar que está funcionando:

```cmd
python scripts\02_translate_pages.py --start 1 --end 3
```

Demora uns 30-60 segundos. Vai gerar 3 arquivos JSON em `translated\`. Confere abrindo um deles no Notepad:

```cmd
notepad translated\page-001.json
```

Tem que ter os campos `page`, `latin`, `pt`, `en`, `definitions`, etc. **Se estiver bom**, segue pra rodada completa:

```cmd
python scripts\02_translate_pages.py --resume
```

O `--resume` faz pular as 3 que já fizemos e só processar as 387 restantes. Vai demorar **3-6 horas** dependendo do rate limit. Pode rodar de noite. Não precisa ficar olhando.

Se **algo travar** (timeout, erro de rede), basta rodar de novo com `--resume` que continua de onde parou.

Se **alguma página falhar**, no fim aparece quantas. Pra retentar só essas:

```cmd
python scripts\02_translate_pages.py --retry-failed
```

## Passo 7 — QA estrutural

Quando a tradução terminar:

```cmd
python scripts\03_qa_check.py
```

Gera `qa_report.md` (relatório) e `qa_suspects.txt` (páginas que merecem revisão manual). Abre os dois e dá uma olhada — só pra ver se algo grave aconteceu. Não é bloqueante.

## Passo 8 — Construir o site

```cmd
python scripts\04_build_site.py
```

Vai gerar 390 HTMLs em `docs\pages\` + index, about, methodology na raiz de `docs\`. Demora uns 30-60 segundos.

Abre localmente pra conferir antes do push:

```cmd
start docs\index.html
```

Confere:
- Landing page renderiza com tipografia certa
- Banner amarelo de aviso aparece
- Banner azul mencionando o projeto De Emendatione aparece
- Grid de 390 páginas com busca funcionando
- Clica numa página, abre o layout trilíngue

Se algo estiver feio, **me chama antes do push**.

## Passo 9 — Adicionar scans originais

```cmd
mkdir docs\assets\scans
xcopy pages\*.png docs\assets\scans\ /Y
```

Isso copia os 390 PNGs (~450 MB) pra dentro de `docs/`.

## Passo 10 — Inicializar Git e fazer push

```cmd
cd "C:\Users\User\Documents\Walter\Isagogicorum"

git init
git branch -M main
git remote add origin https://github.com/walterCNeto/Isagogici.git

git add .
git commit -m "Lancamento inicial: traducao trilingue do Isagogici 1606"
git push -u origin main
```

⚠️ **Push grande**: vai subir ~500 MB. Demora 5-15 minutos dependendo da internet.

Se pedir senha, usa um **Personal Access Token** (`ghp_...`) — não usa senha do GitHub.

## Passo 11 — Ativar GitHub Pages

1. Vai em https://github.com/walterCNeto/Isagogici/settings/pages
2. Source: `Deploy from a branch`
3. Branch: `main`
4. Folder: `/docs`
5. Save
6. Espera 1-2 minutos
7. Acessa https://waltercneto.github.io/Isagogici/

## Passo 12 — Habilitar Discussions (opcional)

1. https://github.com/walterCNeto/Isagogici/settings
2. Role até **Features**
3. Marca **Discussions**

## Passo 13 — Criar labels

Igual fizemos no projeto Scaliger:

1. https://github.com/walterCNeto/Isagogici/labels
2. **New label** três vezes:
   - `correção` (vermelho `#d73a4a`) — Erro factual ou de tradução
   - `discussão` (azul `#0075ca`) — Discussão acadêmica
   - `flag-de-incerteza` (amarelo `#fbca04`) — Ponto onde IA marcou dúvida

## Passo 14 — Atualizar a página pessoal

Depois que o site Isagogici estiver no ar, adiciona um card no portfólio (em `index.html` da página pessoal). Sugestão de card:

```html
<article class="card">
  <header>
    <h3>Isagogicorum chronologiae canonum</h3>
    <div class="tags">
      <span class="tag">Latim Humanista</span>
      <span class="tag">Cronologia Técnica</span>
      <span class="tag">Manual didático</span>
      <span class="tag">IA + Filologia</span>
    </div>
  </header>
  <p>Tradução do tratado técnico-sistemático que Joseph Scaliger escreveu em 1606
    como continuação didática do <em>De Emendatione Temporum</em>. 390 páginas
    com definições, demonstrações e exemplos numéricos. Manual de cronologia
    científica para a primeira geração de cronologistas humanistas. Projeto irmão
    do De Emendatione.</p>
  <div class="cta">
    <a class="link-btn" href="https://waltercneto.github.io/Isagogici/" target="_blank" rel="noopener">Site <span aria-hidden>↗</span></a>
    <a class="link-btn" href="https://github.com/walterCNeto/Isagogici" target="_blank" rel="noopener">Repositório <span aria-hidden>↗</span></a>
  </div>
</article>
```

## Custos esperados

| Etapa | Custo |
|-------|-------|
| API Anthropic (Opus 4.7) | ~US$ 90 |
| GitHub Pages | R$ 0 |
| Hypothes.is | R$ 0 |
| **Total** | **~US$ 90** |

## Em caso de problemas

Se algo travar em qualquer passo, **manda print do erro**. Os pontos onde costuma travar:

- **Rate limit da API Anthropic**: aumentar `--cooldown` para 1.0 ou 2.0
- **Falha de rede em meio à tradução**: rodar `--resume` continua
- **JSON inválido em alguma página**: rodar `--retry-failed` reprocessa
- **Push grande falha**: dividir em commits menores ou verificar tamanho do `.git/`
