# Dual Installer Architecture Design

## Cilj

Napraviti dve jasne instalacione verzije proizvoda koje dele isti runtime/install core:

1. `Classic Full`
2. `Unified Full`

Obe verzije moraju da daju stvarno upotrebljiv sistem posle instalacije, a ne samo UI payload.

## Problem Koji Resavamo

Trenutni `Next` installer ume da podigne `Control Center Next`, ali ne garantuje pun legacy stack u meri u kojoj ga je stari proizvod vec imao:

- `llama.cpp`
- `TurboQuant`
- `OpenCode`
- bootstrap model
- shared launcher i servisni tok

To dovodi do situacije da je `Next` sloj funkcionalan kao UI, ali korisnicki osecaj nije isti kao kod starog kompletnog proizvoda.

Istovremeno, stari proizvod vec ima dobar i provereno upotrebljiv install/runtime tok koji ne treba baciti.

## Osnovna Odluka

Ne pravimo dva nezavisna instalera sa duplom logikom.

Umesto toga uvodimo:

- **jedan shared installer core**
- **dve SKU varijante iznad njega**

To je najzdraviji put jer:

- runtime logika postoji na jednom mestu
- `Classic` i `Unified` dele isti `LocalQwenHome`
- bugfix za runtime/install tok radi za obe linije
- `Next` vise ne ostaje "tanak web sloj", nego postaje pun proizvod nad istim install core-om

## Dve Instalacione Linije

### 1. Classic Full

Ovo je naslednik starog proizvoda i mora da zadrzi njegovu glavnu vrednost:

- kompletna instalacija runtime-a
- kompletna instalacija `OpenCode`
- kompletna instalacija `llama.cpp`
- pokusaj/instalacija `TurboQuant` gde je podrzan
- model bootstrap
- legacy launcheri i legacy control center iskustvo

`Classic Full` je referentna stabilna instalacija.

### 2. Unified Full

`Unified Full` koristi isti shared install core kao `Classic Full`, ali preko njega dodaje:

- ceo `Control Center Next` payload
- `Next` launchere
- `Next` web UI
- `Browser`
- kalkulator kompatibilnosti
- benchmark/web/OpenCode tabove

Drugim recima:

`Unified Full = Classic core + Next shell`

Ovo mora da znaci da korisnik dobija:

- kompletnu instalaciju svega sto je radio stari proizvod
- plus `Next` UI sloj

## Shared Installer Core

Shared installer core mora da bude jedino mesto koje upravlja:

- dependency proverama
- `python` / `venv`
- `node` / `npm`
- `OpenCode`
- `llama.cpp`
- `TurboQuant`
- model bootstrap-om
- `LocalQwenHome` stanjem
- install report-om
- final readiness proverom

To znaci da ni `Classic` ni `Unified` ne smeju da imaju sopstvenu zasebnu "tajnu" install logiku za runtime.

Oni samo biraju koji se UI/launcher sloj instalira preko istog core-a.

## Shared Home i Runtime Stanje

Obe linije moraju da koriste isti shared home:

- `LocalQwenHome` na Windowsu
- odgovarajuci Linux home na Ubuntu

Tu zive:

- modeli
- install-state
- runtime-config
- OpenCode config bridge
- TurboQuant config
- launcher state

To omogucava da korisnik:

- instalira `Classic`
- kasnije doda `Unified`
- ili obrnuto

bez dupliranja modela i runtime-a.

## Verzije i Poravnanje

Verzije moraju da budu poravnate medju:

- `Next` repo verzijom
- legacy repo verzijom
- instaliranim `version.json` kopijama
- Windows zivom instancom
- Ubuntu x86_64 zivom instancom
- Ubuntu arm64 zivom instancom

Pravilo ostaje:

- `a` = kvalitet/veliki reset proizvoda
- `b` = novi feature ili nova produktna sposobnost
- `c` = fix

`Classic Full` i `Unified Full` u istom release-u moraju nositi istu release verziju, iako su razliciti SKU artefakti.

## Platforme

Prva klasa platformi za oba SKU-a:

- Windows x64
- Ubuntu x86_64
- Ubuntu arm64

## Obavezne Komponente Za Uspesnu Instalaciju

Instalacija se smatra uspesnom samo ako su ove komponente spremne:

- `Control Center` odgovarajuce SKU linije
- `llama.cpp`
- `OpenCode`
- barem jedan validan model tok ili jasan model bootstrap status

`TurboQuant` je:

- obavezan za `Classic Full` i `Unified Full` tamo gde je platforma podrzana i build uspeva
- ali mora imati jasan status:
  - `OK`
  - `failed`
  - `unsupported`
  - `not installed`

Na platformama gde realno nije podrzan ili nije potvrden, to ne sme biti cutke ignorisano.

## TurboQuant Politika

`TurboQuant` vise ne sme biti samo "optional ako se desi".

Potrebna su dva nivoa:

1. **Shared core build attempt**
   - kloniranje source-a
   - build prerequisites
   - build
   - detekcija binara

2. **Jasan final status**
   - upisan u install-report
   - prikazan u UI-ju
   - dostupan launch/runtime sloju

Ako build ne uspe:

- instalacija moze ostati upotrebljiva preko upstream `llama.cpp`
- ali readiness report mora jasno reci da `TurboQuant` nije spreman

## Model Bootstrap

Obe instalacione linije moraju imati isti model bootstrap tok:

- izaberi preporuceni model
- ili preskoci download
- ili ostavi model katalog spreman za kasniji izbor

`Unified Full` ne sme imati slabiji model tok od `Classic Full`.

## Launchers

Potrebno je imati dve launcher porodice:

### Classic launcheri

- otvaraju legacy control center
- koriste shared runtime/home

### Unified launcheri

- otvaraju `Control Center Next`
- koriste isti shared runtime/home

Po platformi korisnik mora dobiti jasne precice:

- `Local AI Control Center Classic`
- `Local AI Control Center Unified`

## GitHub i Repo Strategija

Najzdraviji put je novi javni repo za instalere i shared release orkestraciju.

Razlog:

- legacy repo ostaje fokusiran na stabilni proizvod
- `Next` repo ostaje fokusiran na web/backend evoluciju
- installer repo postaje mesto gde se spajaju:
  - shared core
  - classic SKU
  - unified SKU
  - multi-platform release assets

Taj repo moze da referencira:

- legacy payload/source
- next payload/source

ali ne sme da kopa nasumicno po lokalnim putanjama kao danasnji bridge build tok.

## Release Artefakti

Za svaki release treba da postoje dve familije artefakata:

### Classic Full

- Windows `.exe`
- Ubuntu x86_64 `.run`
- Ubuntu arm64 `.run`

### Unified Full

- Windows `.exe`
- Ubuntu x86_64 `.run`
- Ubuntu arm64 `.run`

Uz to:

- `checksums.txt`
- `support-matrix.json`
- release notes

To znaci ukupno sest glavnih instalera po release-u.

## Readiness Report

Svaki installer mora na kraju dati jasan report:

- `Control Center Classic/Unified: OK/failed`
- `llama.cpp: OK/failed`
- `OpenCode: OK/failed`
- `TurboQuant: OK/failed/unsupported`
- `model bootstrap: OK/skipped/failed`
- `install root`
- `launcher paths`
- `local URL`
- `tailscale URL` ako je aktiviran

## Upgrade i Koegzistencija

Sistem mora dozvoliti:

- `Classic` only
- `Unified` only
- oba instalirana nad istim home-om

Ali jedan upgrade ne sme da:

- polomi drugi launcher
- obrise modele
- obrise runtime config
- prebrise OpenCode tok na neocekivan nacin

## Šta Ne Radimo U Ovoj Fazi

- ne uvodimo treci UI SKU
- ne pravimo poseban ARM-only runtime stack
- ne menjamo model format scope van onoga sto vec legacy i next podrzavaju
- ne obecavamo `TurboQuant` na svakoj platformi bez stvarne potvrde

## Fazni Redosled

### Faza 1

Poravnanje verzija i release discipline:

- isti release broj kroz legacy, next i instalirane kopije
- isti release artefakt naming

### Faza 2

Izvlacenje shared installer core-a:

- dependency/install/runtime/model/OpenCode/TurboQuant logika

### Faza 3

`Classic Full` SKU preko shared core-a

### Faza 4

`Unified Full` SKU preko shared core-a

### Faza 5

Realna verifikacija na:

- Windows x64
- Ubuntu x86_64
- Ubuntu arm64

## Kriterijum Gotovosti

Ovo je gotovo tek kada:

1. postoji dve javne instalacione linije
2. obe daju kompletnu instalaciju svega sto je radio stari proizvod
3. `Unified Full` preko toga dodaje ceo `Next` sloj
4. Windows i Ubuntu x86_64 imaju poravnate verzije
5. Ubuntu arm64 ima jasan status za `TurboQuant`
6. korisnik moze da pokrene:
   - `Classic`
   - `Unified`
   nad istim `LocalQwenHome` bez konflikta
