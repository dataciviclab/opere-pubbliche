"""Regression test: le metriche ANAC di `op-cup-lab` ricostruite dalle clean.

Protegge gli invarianti della migrazione da `anac_cross` (compose CIG-level,
rimosso in appalti-pubblici) alle clean primitive:

1. **un CIG senza aggiudicazione conta in `anac_n_cig`** e vale 0 nelle
   metriche — e' la base del vecchio clean ("tutti i CIG noti"), ed e' l'errore
   che la prima stesura della migrazione faceva (1,33M CIG invece di 5,13M);
2. **i CUP sentinella sono esclusi alla fonte**, non a valle: un CIG mappato sia
   su `'000000000000000'` sia su un CUP reale deve finire sotto il CUP reale
   (il vecchio clean usava `MIN(cup)`, che avrebbe scelto il sentinella);
3. **un CIG con due CUP reali** viene contato una volta sola, sotto `MIN(cup)`,
   perche' i consumer CUP-level joinano su una stringa.

Le fixture sono minuscole: il test non verifica i volumi (quelli li guarda
l'equivalenza una tantum), verifica la costruzione.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CLEAN_SQL = REPO_ROOT / "compose" / "op-cup-lab" / "sql" / "clean.sql"
MART_COSTI = REPO_ROOT / "compose" / "op-cup-lab" / "sql" / "mart_costi.sql"

SENTINEL = "000000000000000"


def _parquet(con: duckdb.DuckDBPyConnection, path: Path, sql: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY ({sql}) TO '{path.as_posix()}' (FORMAT PARQUET)")
    return path.as_posix()


def _vuoto(colonne: str, path: Path, con: duckdb.DuckDBPyConnection) -> str:
    return _parquet(con, path, f"SELECT {colonne} WHERE FALSE")


@pytest.mark.regression
def test_anac_n_cig_conta_anche_i_cig_senza_aggiudicazione(tmp_path: Path) -> None:
    con = duckdb.connect()

    # Anagrafe CUP (OpenCUP): solo CUP reali. Il sentinella vive nel mapping ANAC.
    con.execute(
        """
        CREATE TABLE raw_input AS SELECT * FROM (VALUES
            ('CUP_REAL',          2020, 'ATTIVO', 1.0, 0.001, 1.0, 'SA', 'LAVORI', 'd', FALSE, FALSE),
            ('CUP_SENTINEL_CIG',  2020, 'ATTIVO', 1.0, 0.001, 1.0, 'SA', 'LAVORI', 'd', FALSE, FALSE),
            ('CUP_MULTI_AA',      2020, 'ATTIVO', 1.0, 0.001, 1.0, 'SA', 'LAVORI', 'd', FALSE, FALSE),
            ('CUP_MULTI_ZZ',      2020, 'ATTIVO', 1.0, 0.001, 1.0, 'SA', 'LAVORI', 'd', FALSE, FALSE)
        ) AS t(cup, anno_decisione, stato_progetto, costo_progetto, costo_mld,
               finanziamento_progetto, soggetto_titolare, settore_intervento,
               descrizione_intervento, flag_chiuso, flag_sub_progetto)
        """
    )

    cup = _parquet(
        con,
        tmp_path / "anac_cup.parquet",
        f"""
        SELECT * FROM (VALUES
            ('CIG_A',     'CUP_REAL'),
            ('CIG_NOAGG', 'CUP_REAL'),
            ('CIG_SENT',  '{SENTINEL}'),
            ('CIG_SENT',  'CUP_SENTINEL_CIG'),
            ('CIG_MULTI', 'CUP_MULTI_ZZ'),
            ('CIG_MULTI', 'CUP_MULTI_AA')
        ) AS t(cig, cup)
        """,
    )
    agg = _parquet(
        con,
        tmp_path / "anac_aggiudicazioni.parquet",
        """
        SELECT * FROM (VALUES
            ('CIG_A',     1, 100.0, DATE '2024-01-01'),
            ('CIG_SENT',  2,  50.0, DATE '2024-02-01'),
            ('CIG_MULTI', 3, 200.0, DATE '2024-03-01')
        ) AS t(cig, id_aggiudicazione, importo_aggiudicazione, data_aggiudicazione_definitiva)
        """,
    )
    sal = _parquet(
        con,
        tmp_path / "anac_stati_avanzamento.parquet",
        """
        SELECT * FROM (VALUES
            ('CIG_A',   'IN RITARDO', 40.0, DATE '2024-05-01'),
            ('CIG_A',   'IN LINEA',   10.0, DATE '2024-06-01'),
            ('CIG_MULTI', 'IN LINEA',  5.0, DATE '2024-07-01')
        ) AS t(cig, flag_ritardo, importo_quota, data_emissione_sal)
        """,
    )

    qe = _parquet(
        con,
        tmp_path / "anac_quadro_economico.parquet",
        """
        SELECT * FROM (VALUES
            ('CIG_A', 1, NULL, 'BASE_ASTA',  100.0, 0.0, 0.0),
            ('CIG_A', 1, DATE '2024-02-01', 'VARIANTE', 110.0, 0.0, 0.0),
            ('CIG_A', 1, NULL, 'CONSUNTIVO', 120.0, 0.0, 0.0),
            ('CIG_NOAGG', 9, NULL, 'BASE_ASTA', 50.0, 0.0, 0.0),
            ('CIG_SENT',  2, NULL, 'BASE_ASTA', 10.0, 0.0, 0.0)
        ) AS t(cig, id_aggiudicazione, data, descrizione_evento,
               importo_lavori, importo_servizi, importo_forniture)
        """,
    )

    path = {
        "anac_cup": cup,
        "anac_aggiudicazioni": agg,
        "anac_stati_avanzamento": sal,
        "anac_quadro_economico": qe,
        "localizzazione": _vuoto(
            "CAST(NULL AS VARCHAR) AS cup, CAST(NULL AS VARCHAR) AS regione, "
            "CAST(NULL AS VARCHAR) AS provincia, CAST(NULL AS VARCHAR) AS comune, "
            "CAST(NULL AS VARCHAR) AS codice_comune, CAST(NULL AS VARCHAR) AS stato",
            tmp_path / "localizzazione.parquet",
            con,
        ),
        "fonti": _vuoto(
            "CAST(NULL AS VARCHAR) AS cup, CAST(NULL AS VARCHAR) AS copertura_finanziaria",
            tmp_path / "fonti.parquet",
            con,
        ),
        "pnrr_progetti": _vuoto(
            "CAST(NULL AS VARCHAR) AS cup, CAST(NULL AS VARCHAR) AS missione, "
            "CAST(NULL AS VARCHAR) AS stato_avanzamento, CAST(NULL AS DOUBLE) AS fin_pnrr, "
            "CAST(NULL AS DOUBLE) AS fin_totale",
            tmp_path / "pnrr_progetti.parquet",
            con,
        ),
        "pnrr_gare": _vuoto(
            "CAST(NULL AS VARCHAR) AS cup, CAST(NULL AS DOUBLE) AS importo_aggiudicazione",
            tmp_path / "pnrr_gare.parquet",
            con,
        ),
        "pnrr_pagamenti": _vuoto(
            "CAST(NULL AS VARCHAR) AS cup, CAST(NULL AS DOUBLE) AS pagamento_pnrr, "
            "CAST(NULL AS DOUBLE) AS pagamento_totale",
            tmp_path / "pnrr_pagamenti.parquet",
            con,
        ),
        "opencoesione_progetti": _vuoto(
            "CAST(NULL AS VARCHAR) AS CUP, CAST(NULL AS DOUBLE) AS FINANZ_TOTALE_PUBBLICO",
            tmp_path / "opencoesione.parquet",
            con,
        ),
        "silos": _vuoto(
            "CAST(NULL AS VARCHAR) AS cup, CAST(NULL AS VARCHAR) AS denominazione, "
            "CAST(NULL AS VARCHAR) AS sistema_infrastrutturale, "
            "CAST(NULL AS VARCHAR) AS stato_attuazione, CAST(NULL AS VARCHAR) AS macro_stato, "
            "CAST(NULL AS DOUBLE) AS costi_mln_euro, CAST(NULL AS DOUBLE) AS disponibilita_mln_euro, "
            "CAST(NULL AS DOUBLE) AS gap_finanziario_mln_euro",
            tmp_path / "silos.parquet",
            con,
        ),
    }

    sql = CLEAN_SQL.read_text(encoding="utf-8")
    for name, file in path.items():
        sql = sql.replace(f"{{support.{name}.clean}}", file)
        sql = sql.replace(f"{{support.{name}.path}}", file)
        sql = sql.replace(f"{{support.{name}.mart}}", file)

    cur = con.execute(sql)
    colonne = [c[0] for c in cur.description]
    righe = {r[0]: dict(zip(colonne, r)) for r in cur.fetchall()}

    # 1. il CIG senza aggiudicazione conta: 2 CIG sotto CUP_REAL, 1 gara sola
    real = righe["CUP_REAL"]
    assert real["anac_n_cig"] == 2, "il CIG senza aggiudicazione conta in anac_n_cig"
    assert real["anac_n_gare"] == 1, "ma non genera gare"
    assert real["anac_importo_aggiudicato"] == 100.0
    assert real["anac_n_sal"] == 2, "n_sal conta tutte le righe SAL del CIG"
    assert real["anac_importo_sal"] == 50.0
    assert real["anac_sal_in_ritardo"] == 1, "un solo SAL in ritardo"

    # Costi dal quadro economico: base e consuntivo sommati sui CIG del CUP.
    # CIG_A (100 base, 120 consuntivo) + CIG_NOAGG (50 base, senza consuntivo).
    assert real["anac_importo_base"] == 150.0
    assert real["anac_importo_consuntivo"] == 120.0
    assert float(real["anac_scostamento_pct"]) == pytest.approx(-20.0), (
        "lo scostamento e' calcolato sulla base del CUP, non del singolo CIG"
    )
    assert real["anac_n_varianti_qe"] == 1

    # mart_costi: aggrega solo i CUP con base d'asta (senza base lo scostamento
    # non esiste, contarlo come zero falserebbe la media).
    con.execute("CREATE OR REPLACE VIEW clean_input AS " + sql)
    # la soglia di 10 CUP per gruppo non ha senso su una fixture da 5
    mart_sql = MART_COSTI.read_text(encoding="utf-8").replace("HAVING COUNT(*) >= 10", "HAVING COUNT(*) >= 1")
    mart = con.execute(mart_sql).fetchall()
    assert mart, "il mart deve produrre almeno un gruppo"
    # su una fixture da 150 EUR l'aggregato in mld arrotonda a 0: si verifica
    # il conteggio, l'importo e' gia' asserito sul clean sopra
    assert mart[0][3] == 2, f"CUP con base contati: {mart[0][3]}"

    # 2. il sentinella non ruba il CIG: vale il CUP reale
    sentinel = righe["CUP_SENTINEL_CIG"]
    assert sentinel["anac_n_cig"] == 1
    assert sentinel["anac_n_gare"] == 1
    assert SENTINEL not in righe, "il CUP sentinella non deve comparire in output"

    # 3. un CIG con due CUP reali viene contato una volta, sotto MIN(cup)
    assert righe["CUP_MULTI_AA"]["anac_n_cig"] == 1
    assert righe["CUP_MULTI_ZZ"]["anac_n_cig"] == 0

