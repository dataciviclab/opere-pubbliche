# Opere Pubbliche Intelligence

**Anagrafe universale dei progetti di investimento pubblico italiani (OpenCUP) + incrocio con i dataset del Lab.**

Il repo produce la base dati di intelligence sulle opere pubbliche: l'anagrafe completa dei CUP
(dal portale OpenCUP) come fondamento, arricchita con i sottoinsiemi del Lab (appalti ANAC, PNRR,
coesione) via join su CUP.

## Scopo in una frase

> Da un CUP a un profilo completo: anagrafe universale (OpenCUP) + contratti (ANAC) + stanziamento
> (PNRR/coesione) + erogazione — per rispondere a "dove vanno i soldi delle opere pubbliche in Italia".

## Perché un repo separato (non DI)

- **Fonte propria da 15GB** (OpenCUP: Progetti 2,2GB + Localizzazione 205MB + Soggetti 2,9MB),
  aggiornata mensilmente — non è un candidate standard, è una banca dati verticale.
- **Consuma i clean del Lab via GCS** (contratto stabile) come arricchimento, non li modifica.
- Pattern già usato dal Lab: `terzo-settore-intelligence`, `open-siope`.

## Come funziona

```
opencup/       # fonte propria: download + estrazione + conversione parquet
  scripts/     #   download_opencup.py, convert_to_parquet.py
  data/        #   raw/ (zip) + parquet/ (locali, fuori git)
lab/           # consumo layer clean del Lab via GCS (anac, pnrr, opencoesione)
build/         # incrocio CUP → unified_operas.parquet
data/          # deliverable: profilo per opera/CUP, per comune
```

## Fonti

| Fonte | File | Dim | URL |
|---|---|---|---|
| OpenCUP Progetti | `OpendataProgetti.zip` | 2,2 GB | opencup.gov.it (7 shard, 62 col, ~7,4M CUP) |
| OpenCUP Localizzazione | `OpendataLocalizzazione.zip` | 205 MB | localizzazioni dei CUP |
| OpenCUP Soggetti | `OpendataSoggetti.zip` | 2,9 MB | anagrafiche soggetti titolari/richiedenti |
| OpenCUP Fonti copertura | `OpendataFontiCopertura.zip` | — | fonti di copertura |
| Lab (consumo) | clean GCS | — | anac_appalti_master, pnrr_progetti, pnrr_gare, opencoesione |

## Stato

Bootstrap — script di import da costruire.
