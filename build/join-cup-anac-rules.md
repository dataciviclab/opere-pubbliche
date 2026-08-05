# Join CUP → ANAC: cardinalità e regole di pulizia

Documenta il fenomeno della cardinalità CUP→CIG nel bridge ANAC e le regole
da applicare nei join del unified. Scoperte 2026-08-05 studiando la catena
end-to-end del PNRR.

## Il problema

Il bridge ANAC `anac_cup` (CIG→CUP, 7,0M coppie) contiene **cardinalità spurie**
che distorcono i join per CUP. Due fenomeni distinti:

### 1. CUP placeholder (28,5% dei CIG)

| Placeholder | CIG associati |
|---|---|
| `ND` | 1.971.347 |
| `000000000000000` | 27.481 |

- **2,0M CIG su 7,0M (28,5%)** hanno CUP placeholder
- Impatto sugli **importi**: solo €3,7 mld su €1.398 mld (**0,3%**) → tanti ma piccoli
- Distorcono i **conteggi** (n CIG per CUP), non gli importi

### 2. CUP-programma / ombrello (distorsione principale)

Alcuni CUP sono **contenitori programmatici** (un CUP finanzia molte gare
nazionali o di settore). Il join CUP→gare somma tutte le gare collegate →
importi gonfiati oltre ogni limite.

**Misura**: i 7.488 CUP con ≥50 CIG coprono **€5.074 mld = 364% dell'importo
valido totale** (€1.398 mld). Matematicamente impossibile → i CUP-programma
inquinano gli aggregati.

Esempi reali:
- `F68B22001000006` (smart grid MASE, €412M stanziati) → 156 CIG in pnrr_gare,
  858 nel bridge ANAC, €25 mld aggregati (61x lo stanziamento)
- OpenFiber, Istituto Superiore Sanità, "MULTISERVICE Lombardia/Emilia..." (€3,4 mld)

## Regola di pulizia (da applicare nel build)

Per i join CUP→ANAC/PNRR-gare nel unified:

1. **Escludere i CUP placeholder**: `cup NOT IN ('ND', '000000000000000', '')`
2. **Trattare i CUP con molti CIG come ombrello**: per il profilo CUP usare
   **conteggi e mediane**, non somme degli importi delle gare collegate.
   Soglia: `flag_ombrello = (anac_n_cig >= 50) AND (importo_gare > costo_anagrafe * 3)`.
   Il doppio criterio distingue i contenitori (smart grid: gare >> costo) dalle
   opere vere con tante gare (Terzo Valico: costo 4,7 mld > gare 1,5 mld).
   Il solo n_cig alto NON basta (vedi caso Terzo Valico).
3. **Validazione di coerenza**: il CUP deve stare in OpenCup (anagrafe) e il
   costo anagrafe deve essere >= della somma delle gare "piccole" (sotto soglia).
   Se le gare superano il costo anagrafe → CUP ombrello o join spurio.

## Implementazione

- `build/build_unified.py`: aggiungere `flag_ombrello` (n_cig >= 50) e
  colonne `anac_n_gare_piccole` / `anac_importo_gare_piccole` (solo CIG sotto
  soglia) al posto della somma totale.
- Le view che aggregano importi ANAC (`v_cup_rilevanti`, `v_analisi_gap`)
  devono usare le colonne "piccole", non la somma totale.
- Il CUP ombrello resta nel unified con `flag_ombrello=true` (non si elimina),
  ma i suoi importi non si sommano agli aggregati territoriali.
