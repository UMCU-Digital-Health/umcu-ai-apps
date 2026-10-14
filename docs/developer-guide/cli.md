# CLI-tools

Deze pagina is bedoeld voor developers en beheerders van de LLM Evaluatie Applicatie.
Hier lees je hoe je de database vult, gebruikers toegang geeft en de app lokaal start.

Na `uv sync` zijn drie commando's beschikbaar (gedefinieerd onder
`[project.scripts]` in `pyproject.toml`):

| Commando | Doel |
|---|---|
| [`prep_llm_eval`](#prep_llm_eval) | Evaluatiedata (context + LLM-resultaat) uit een CSV in de database laden. |
| [`add_eval_user`](#add_eval_user) | Een gebruiker toegang geven tot een project en een of meer afdelingen. |
| [`llm_eval_dash`](#llm_eval_dash) | De Dash-app lokaal starten in debugmodus. |

Draai de commando's met `uv run <commando>` of activeer eerst de virtual environment
(`source .venv/bin/activate`).

---

## Configuratie

Alle commando's lezen de databaseconfiguratie uit een `.env`-bestand in de root van de
repository. Kopieer `.env_example` naar `.env` en vul de waarden in.

```bash
cp .env_example .env
```

De variabele `DB_ENVIRONMENT` bepaalt met welke database je werkt:

| `DB_ENVIRONMENT` | Database | Benodigde variabelen |
|---|---|---|
| `DEBUG` | Lokale SQLite-database `./sql_app.db` | Geen |
| `ACC` | MS SQL Server acceptatie | `DB_USER`, `DB_PASSWD`, `DB_PORT`, `DB_HOST_ACC`, `DB_DATABASE_ACC` |
| `PROD` | MS SQL Server productie | `DB_USER`, `DB_PASSWD`, `DB_PORT`, `DB_HOST_PROD`, `DB_DATABASE_PROD` |

!!! danger "Controleer altijd je omgeving"
    Elk commando logt bij het starten `Using database environment: ...`. Controleer
    dit voordat je data of gebruikers toevoegt, zeker als `DB_ENVIRONMENT` op `PROD`
    staat.

!!! note "SQLite-database"
    In `DEBUG`-modus wordt `sql_app.db` aangemaakt in de map waar je het commando
    draait. Draai de commando's dus altijd vanuit de root van de repository. De
    tabellen worden automatisch aangemaakt als ze nog niet bestaan. `*.db` staat in
    `.gitignore`.

---

## Autorisatiemodel

Toegang werkt op basis van de combinatie **project + afdeling**:

- Elke casus (*reference*) hoort bij één project (opgegeven bij `prep_llm_eval`) en
  één afdeling (kolom `department` in de CSV).
- Een gebruiker krijgt met `add_eval_user` toegang tot een project en een of meer
  afdelingen.
- In de app ziet een gebruiker alleen de casussen waarvan project **én** afdeling
  overeenkomen met een van zijn toegangsregels.

!!! warning "Exacte overeenkomst"
    Project- en afdelingsnamen worden hoofdlettergevoelig vergeleken. `Cardiology` en
    `cardiology` zijn dus verschillende afdelingen. Gebruik in de CSV en bij
    `add_eval_user` exact dezelfde schrijfwijze.

---

## `prep_llm_eval`

Laadt evaluatiedata uit een CSV-bestand in de database. Maakt de tabellen aan als ze
nog niet bestaan.

```bash
prep_llm_eval -p <project> <pad/naar/bestand.csv>
```

| Argument | Verplicht | Uitleg |
|---|---|---|
| `path` | Ja | Pad naar het CSV-bestand. |
| `-p`, `--project` | Ja | Projectnaam die aan alle casussen in dit bestand wordt gekoppeld. |

**Voorbeeld**

```bash
prep_llm_eval -p demo data/processed/llm_evaluation_data_example.csv
```

### CSV-formaat

Het bestand moet UTF-8 gecodeerd zijn, met komma als scheidingsteken en een
header-regel met de volgende kolommen:

| Kolom | Type | Verplicht | Uitleg |
|---|---|---|---|
| `reference_id` | integer | Ja | Unieke ID van de casus. Wordt in de app getoond in de keuzelijst. |
| `reference_description` | tekst | Ja | Korte omschrijving, getoond na de ID in de keuzelijst. |
| `department` | tekst | Ja | Afdeling, gebruikt voor autorisatie. |
| `context_text` | tekst | Ja | De input die naar het LLM is gestuurd (linkervak in de app). |
| `llm_response` | tekst | Ja | Het gegenereerde LLM-resultaat (rechtervak in de app). |
| `model` | tekst | Nee | Naam van het gebruikte model (max. 10 tekens). Leeg wordt `Unknown`. |

Zet teksten met komma's of regeleinden tussen dubbele aanhalingstekens. Zie
`data/processed/llm_evaluation_data_example.csv` voor een voorbeeld.

### Gedrag

- Elke rij wordt gevalideerd met Pydantic. Bij een ontbrekende of ongeldige kolom
  stopt het commando met een foutmelding en wordt **niets** opgeslagen.
- Rijen waarvan het `reference_id` al in de database staat, worden **overgeslagen**
  (er wordt gelogd welke). Dit geldt ook voor dubbele ID's binnen hetzelfde bestand.
- Na afloop wordt gelogd hoeveel rijen zijn toegevoegd en overgeslagen.

!!! warning "Bestaande casussen worden niet bijgewerkt"
    `reference_id` is uniek over de hele database, dus ook over projecten heen. Het
    commando werkt bestaande casussen niet bij. Wil je de tekst van een casus
    aanpassen, doe dat dan direct in de database (let op: bestaande markeringen
    verwijzen naar tekenposities in de oude tekst) of gebruik een nieuw
    `reference_id`.

---

## `add_eval_user`

Maakt een gebruiker aan (als die nog niet bestaat) en geeft toegang tot een project en
een of meer afdelingen. Je kunt het commando ook gebruiken om een bestaande gebruiker
extra toegang te geven.

```bash
add_eval_user -p <project> -d <afdeling> [-d <afdeling> ...] <email>
```

| Argument | Verplicht | Uitleg |
|---|---|---|
| `email` | Ja | E-mailadres van de gebruiker, zoals bekend in Posit Connect. |
| `-p`, `--project` | Ja | Project waartoe de gebruiker toegang krijgt. |
| `-d`, `--department` | Ja | Afdeling. Herhaal de vlag voor meerdere afdelingen. |

**Voorbeelden**

```bash
# Nieuwe gebruiker met toegang tot twee afdelingen
add_eval_user -p demo -d Cardiology -d Neurology j.jansen@umcutrecht.nl

# Bestaande gebruiker extra toegang geven tot een ander project
add_eval_user -p ander_project -d Cardiology j.jansen@umcutrecht.nl
```

!!! warning "Gebruik kleine letters voor het e-mailadres"
    De app haalt het e-mailadres op uit de Posit Connect-header en zet het om naar
    kleine letters. `add_eval_user` doet dat niet. Voer het e-mailadres daarom altijd
    in kleine letters in, anders vindt de app de gebruiker niet en ziet deze geen
    casussen.

!!! info "Toegang bestaat al"
    Bestaat (een van) de combinaties gebruiker + project + afdeling al, dan wordt de
    hele opdracht teruggedraaid en stopt het commando met exitcode `1`. Voer het
    commando in dat geval opnieuw uit met alleen de nieuwe afdelingen.

Toegang intrekken of een gebruiker verwijderen kan (nog) niet via de CLI; doe dit
direct in de tabellen `llm_eval.user_access` en `llm_eval.user`.

---

## `llm_eval_dash`

Start de Dash-app lokaal in debugmodus op poort **8017**.

```bash
llm_eval_dash
```

Open daarna [http://localhost:8017](http://localhost:8017) in je browser.

!!! tip "Lokaal inloggen als `No user`"
    Lokaal is er geen Posit Connect-header met gebruikersgegevens. De app gebruikt
    dan het e-mailadres `No user`. Geef die gebruiker toegang om lokaal casussen te
    zien:

    ```bash
    add_eval_user -p demo -d Cardiology -d Neurology "No user"
    ```

---

## Snel aan de slag (lokaal)

```bash
uv sync
cp .env_example .env            # zet DB_ENVIRONMENT = "DEBUG"
uv run prep_llm_eval -p demo data/processed/llm_evaluation_data_example.csv
uv run add_eval_user -p demo -d Cardiology -d Neurology "No user"
uv run llm_eval_dash            # http://localhost:8017
```

Begin opnieuw met een lege lokale database door `sql_app.db` te verwijderen.

---

## Database

Alle tabellen staan in het schema `llm_eval` (bij SQLite zonder schema):

| Tabel | Inhoud |
|---|---|
| `reference` | Casussen: `reference_id`, omschrijving, project en afdeling. |
| `context` | De meegestuurde context per casus. |
| `evaluation_item` | Het LLM-resultaat en het model per casus. |
| `marking` | Annotaties: type, tekst, start/eind-positie, ernst, opmerking, gebruiker en tijdstip. |
| `assessment_usability` | Bruikbaarheidsscore (1–5) per casus. |
| `user` | Gebruikers (e-mailadres). |
| `user_access` | Toegangsregels: gebruiker + project + afdeling. |

De modellen staan in `src/umcu_ai_apps/llm_evaluation/database/models.py`.
