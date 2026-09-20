# QSO Logg – Android

En enkel amatörradio-app för att logga QSO lokalt i telefonen.

## Fält

- Datum
- Tid
- Signal
- Sent
- Mottaget
- Frekvens
- Kommentar

Alla QSO sparas automatiskt i en lokal SQLite-databas.

## Funktioner

- Nytt QSO
- Automatisk datum/tid
- Redigera QSO
- Radera QSO
- Sökning
- CSV-export
- Fungerar utan internet

## Bygg APK i WSL/Linux

Installera först Buildozer/Kivy enligt din befintliga Android-miljö.

Gå till projektmappen:

```bash
cd ~/android/QSO_Logg
```

Bygg debug-APK:

```bash
buildozer -v android debug
```

APK hamnar sedan i:

```text
bin/
```

Kopiera till Windows:

```bash
cp bin/*.apk /mnt/c/Users/roger/Downloads/
```

## Installera i Samsung

Kopiera APK:n till telefonen och öppna den. Android kan behöva tillåta installation från den filhanterare/webbläsare som används.

## Databas

Appen använder SQLite. Databasen ligger i Android-appens privata datakatalog och heter:

```text
qso_logg.db
```

CSV-exporten heter:

```text
qso_logg_export.csv
```

