Das ist ein Projekt der Pfarrjugend Mariahilf. In diesem Projekt soll ein Aktiensystem für die Jährliche Mini Au Erarbeitet werden 

# 📈 Mini-Au Aktienmarkt Simulation

Ein webbasiertes Aktiensystem für die Veranstaltung „Mini Au“. Dieses Projekt simuliert einen kleinen Aktienmarkt für Teilnehmer (z. B. Schüler, Gruppen oder fiktive Firmen).

## 🎯 Ziel des Projekts
- Spielerisches Verständnis von Wirtschaft & Börse
- Interaktive Verwaltung von Unternehmen, Aktien, Kursen
- Transparente Benutzerverwaltung mit Depotübersicht

## ⚙️ Geplanter Funktionsumfang
### Benutzerrollen:
- 👤 Normale Benutzer (sehen ihr Depot, können kaufen/verkaufen)
- 🛠️ Admins (erstellen Unternehmen, setzen Kurse)

### Kernfunktionen:
- 📋 Registrierung/Anmeldung
- 🏢 Firmen anlegen & verwalten
- 📈 Aktienkurse einsehen
- 💰 Aktien kaufen & verkaufen
- 🗃️ Depotübersicht + Transaktionshistorie
- 🔧 Admin-Panel für Kursanpassung
- 📊 Live-Kursverlauf (optional dynamisch oder manuell gesetzt)

## 📦 Verwendete Technologien
- PHP 8.x
- MySQL
- HTML/CSS (Bootstrap für UI)
- Composer (Paketverwaltung)
- ggf. JavaScript (nur wo nötig)

## 🗂️ Projektstruktur
- `public/`: öffentliche Einstiegspunkte
- `src/`: Business-Logik (MVC)
- `data/`: Konfiguration und DB-Zugang
- `vendor/`: externe Pakete (per Composer)

## Setup

### Requirements

**Python**:

Python dependencies can be installed from the `requirements.txt` file. We recommend using a venv for installation:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The top level requirements are:

- [Quart], a reimplementation of the popular [Flask] web framework for python
  with ASGI and asyncio support. The webserver is fully sideward-compatible with
  Flask and the code reads the same (safe for the change in names and additional
  features).

- [MariaDB Connector/Python] (may require MariaDB Connector/C, check the
  [MariaDB Connector FAQ] for more information)

**MariaDB / MySQL**:

1. Install MariaDB (e.g. using `apt-get install mariadb-server mariadb-client`).

2. Setup database, user (and role) for DAU-JONES[^1]:

    1. Connect to your MariaDB server as a user with necessary privileges to
       complete the next steps. On a regular debian install of MariaDB this can
       be done by running the following (as root):

       ```
       shell# mariadb
       ```

    2. Create the required MariaDB structure using the provided script. You may
       also edit the script or create the database and a user manually to suit
       your needs. In such cases, take care to also update the appropriate
       config fields.

       ```
       mariadb> source /path/to/dau-jones/create_db.sql;
       ```

    3. Assign a secure password to the `dau_jones` user in MariaDB:

       ```
       mariadb> ALTER USER 'dau_jones' IDENTIFIED BY 'YOUR SECURE PASSWORD HERE';
       ```

       Make sure to pay attention to [MariaDB quoting behavior][MariaDB string
       literals].

    4. Set the `MARIADB_CONNECTION.password` field in the `config.py` file
       accordingly. While not required, we recommend using [raw strings][Python
       literals] in the python file for passwords with special characters. If
       you chose to use a user or database name other than the default in step
       2.2, remember to change the corresponding field of the
       `MARIADB_CONNECTION` dict!

    Note that no convenience function is provided as a shorthand for these steps
    as they should only be run very rarely and generally do not require
    reset. In most cases, it should suffice to (re-)initialize the database as
    described in the next step to fix any misconfiguration or reset the internal
    state. Use the `--overwrite` flag for the `init-db` command to drop and
    rebuild the tables used by DAU-JONES.

3. Initialize the tables in the newly created database (if applicable, remember
   to run this in your venv!):

   ```
   shell(venv)$ python3 -m quart init-db
   ```

4. DB setup complete!

---

[^1]: You may change the user, role and database name to whatever you like if
    you prefer other naming conventions or need to resolve naming conflicts. You
    can do this either by manually executing the required SQL or by editing the
    `create_schema.sql` script accordingly. Make sure to also update these
    values in the config.py file!

[Quart]: https://quart.palletsprojects.com/
[Flask]: https://flask.palletsprojects.com/
[MariaDB Connector/Python]: https://pypi.org/project/mariadb/
[MariaDB Connector FAQ]: https://mariadb-corporation.github.io/mariadb-connector-python/faq.html#installation
[MariaDB string literals]: https://mariadb.com/kb/en/string-literals/
[Python literals]: https://docs.python.org/3/reference/lexical_analysis.html#literals
