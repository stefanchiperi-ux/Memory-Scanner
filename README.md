# GG-Scan

GG-Scan este o aplicatie desktop pentru Windows care analizeaza spatiul ocupat pe un disc sau intr-un folder. Aplicatia identifica cele mai mari foldere, calculeaza dimensiunile fisierelor si folderelor, afiseaza statistici si prezinta structura sub forma de arbore.

## Functionalitati

- scanare selectabila pentru un disc sau folder;
- calcul dimensiuni pentru fisiere si foldere;
- sortarea celor mai mari foldere dupa dimensiune;
- clasificarea folderelor in categorii explicative:
  - Sistem;
  - Aplicatii;
  - Documente;
  - Media;
  - Cache/temporare;
  - Descarcari;
  - Necunoscut;
- statistici pentru spatiu total, spatiu ocupat, spatiu liber si distributie pe categorii;
- reprezentare tip arbore a structurii folderelor;
- tratarea erorilor de permisiuni;
- optiune pentru ignorarea folderelor inaccesibile;
- shortcut si icon personalizat pentru aplicatie.

## Tehnologii folosite

- Python 3;
- Tkinter pentru interfata grafica desktop;
- biblioteca standard Python pentru scanarea fisierelor;
- Pillow a fost folosit local doar pentru generarea iconitei aplicatiei.

Aplicatia principala nu necesita pachete externe pentru rulare.

## Cerinte

- Windows;
- Python 3.10 sau mai nou.

## Pornire rapida

1. Deschide folderul proiectului.
2. Ruleaza `GG-Scan.bat`.
3. Alege folderul sau discul pe care vrei sa il scanezi.
4. Pentru scanari mari, lasa bifata optiunea `Ignora folderele inaccesibile`.
5. Apasa `Scaneaza`.

## Pornire manuala

Din terminal, in folderul proiectului:

```bat
python src\app.py
```

Sau cu Python Launcher:

```bat
py -3 src\app.py
```

## Testare

Din terminal, in folderul proiectului:

```bat
python -m unittest discover -s tests
```

Testele verifica scanarea folderelor, calculul dimensiunilor, sortarea si clasificarea unor cai comune.

## Structura proiectului

```text
GG-Scan/
|-- assets/
|   |-- gg_scan.ico
|   `-- gg_scan_icon.png
|-- src/
|   |-- app.py
|   |-- disk_analyzer.py
|   `-- __init__.py
|-- tests/
|   `-- test_disk_analyzer.py
|-- tools/
|   |-- create_desktop_shortcut.ps1
|   `-- create_icon.py
|-- GG-Scan.bat
|-- GG-Scan.vbs
|-- run_app.bat
`-- README.md
```

## Observatii

- O scanare de disc complet poate dura cateva minute.
- Unele foldere de sistem nu pot fi citite fara drepturi speciale.
- Daca optiunea de ignorare este activa, aplicatia continua scanarea si noteaza elementele inaccesibile.
- Pentru performanta, arborele limiteaza afisarea la primele 250 de elemente din fiecare folder, sortate dupa dimensiune.

## Credit si transparenta

Acest mini proiect a fost realizat cu ajutorul unui asistent AI. Ideea, cerintele si directia proiectului au fost oferite prin prompturi de catre utilizator, iar codul, structura proiectului, interfata, README-ul si fisierele auxiliare au fost generate si ajustate cu ajutorul AI.

Autorul uman al prompturilor: utilizatorul proiectului.

Asistent AI folosit: Codex / ChatGPT.

## Portabilitate

Proiectul nu depinde de calea absoluta de pe calculatorul pe care a fost creat. Aplicatia foloseste cai relative pentru fisierele din proiect, inclusiv iconita din `assets/gg_scan.ico`.

Daca descarci proiectul pe alt laptop, este suficient sa rulezi `GG-Scan.bat` din folderul proiectului, cu Python instalat.

Shortcut-ul de pe desktop creat pe calculatorul initial nu este portabil, deoarece un fisier `.lnk` Windows tine minte calea exacta. Pe alt laptop, ruleaza `GG-Scan.bat` sau creeaza un shortcut nou catre `GG-Scan.vbs`.

Scriptul `tools/create_icon.py` este optional si se foloseste doar daca vrei sa regenerezi iconita dintr-o alta imagine:

```bat
python tools\create_icon.py calea\catre\imagine.avif
```
