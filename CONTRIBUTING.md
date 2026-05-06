# Como Contribuir — Isagogici

Este projeto é uma tradução de IA do *Isagogicorum chronologiae canonum libri tres* de Joseph Scaliger (1606), publicada como **texto-semente para revisão acadêmica**. Erros são esperados, correções são bem-vindas.

## Áreas onde pesquisadores específicos podem ajudar muito

**Latinistas humanistas**: pelas 390 páginas, a tradução tem qualidade variável. O Isagogici é mais técnico-sistemático que o De Emendatione, com terminologia matemática-cronológica densa.

**Historiadores da cronologia**: o Isagogici é manual técnico. As definições, demonstrações e exemplos numéricos precisam de revisão por especialista que conheça calendário juliano, juliano-proléptico, ciclos lunares etc.

**Astrônomos históricos**: as demonstrações de Scaliger sobre Saros, Exeligmos, Hecatontaeteris e outros ciclos são tecnicamente densas. Astrônomos que trabalham com dados antigos (Steele, Stephenson tradition) podem refinar muito.

**Especialistas em Crusius**: Scaliger cita Paulus Crusius repetidamente. Pesquisadores que conheçam a obra de Crusius (sobretudo *Liber de epochis*, 1578) podem identificar os pontos exatos de divergência e concordância.

**Especialistas em Eusébio**: o Isagogici foi publicado como apêndice ao Thesaurus Temporum, que continha a edição de Scaliger da Crônica de Eusébio. Cross-referências entre as obras têm muita densidade.

## Os três níveis de contribuição

### Nível 1: Reportar erro (qualquer pessoa)

1. Acessa a página com erro no site
2. Clica em "Reportar erro nesta página" no rodapé
3. Vai abrir uma issue no GitHub com template pré-preenchido
4. Preenche e envia

### Nível 2: Anotação inline (pesquisadores)

1. Cria conta em https://hypothes.is
2. Instala extensão para Chrome/Firefox
3. Marca trechos no site, escreve comentários
4. Anotações ficam públicas para outros pesquisadores

### Nível 3: Pull Request (Git)

```bash
git clone https://github.com/SEU_USUARIO/Isagogici.git
cd Isagogici
# Edita translated/page-XXX.json
git commit -am "Correção p.XXX: <descrição>"
git push origin main
```

E abra um PR no GitHub.

## Áreas críticas onde queremos atenção redobrada

1. **Definições**: cada termo técnico que Scaliger introduz com "Sit", "Vocamus", "Definimus" foi capturado num campo `definitions` do JSON. Verificar se a definição capturada reflete fielmente o que ele diz.

2. **Cross-references**: campo `cross_references` distingue entre referências internas (ao próprio Isagogici) e externas (ao De Emendatione, Almagesto, Eusébio etc). Verificar acurácia.

3. **Eventos astronômicos**: campo `astronomical_events` lista eclipses, equinócios, solstícios, conjunções. Comparado contra catálogos NASA na auditoria automática. Erros aqui afetam a auditoria.

4. **Discordâncias com Crusius**: campo `uncertainty_flags` marca quando Scaliger explicitamente discorda de Paulus Crusius. Estas são passagens-chave para entender o desenvolvimento do método.

## Reconhecimento

Toda contribuição fica registrada no histórico do Git. Quando o projeto atingir massa crítica de revisão, vamos compilar uma página de **agradecimentos** com nomes e instituições.

## Código de conduta

- Crítica do conteúdo: bem-vinda
- Crítica pessoal: não tolerada
- Discussões teológicas/filosóficas tangenciais: levadas para Discussions
