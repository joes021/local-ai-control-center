# Benchmark Real-Time Chart Design

Datum: 2026-05-18

## Problem

Trenutni benchmark grafikon u `Benchmark` tabu ne daje pravi osećaj živog rada:

- ne ponaša se kao stvarni real-time graf
- korisnik nema jasan osećaj vremenskog toka na X osi
- kada nema novih zahteva, nije dovoljno jasno da li je sistem miran ili je graf "stao"
- nema dobar prikaz razlike između stvarnih uzoraka i perioda bez aktivnosti

Korisnik je tražio da grafikon bude stvarno živ i da se to vidi i na X osi.

## Cilj

Benchmark grafikon treba da postane jasan real-time prikaz throughput aktivnosti lokalnog sistema.

To znači:

- osvežava se stalno na svakih `5s`
- X osa prikazuje pravo vreme
- postoje vremenski opsezi za pregled
- periodi bez novih uzoraka prikazuju se kao neaktivnost, ne kao lažni throughput
- korisnik uvek vidi trenutno stanje grafa kroz status u headeru kartice

## Real-time model

Grafikon se osvežava:

- na svakih `5s`
- bez obzira da li je stigao novi zahtev ili ne

To znači da UI mora da prati vremenski tok i kada sistem miruje.

## X osa

X osa koristi:

- stvarne vremenske oznake
- format `HH:MM:SS`

Za duže opsege broj tick oznaka treba smanjiti da se osa ne zaguši.

## Time range

Grafikon dobija segment za izbor opsega:

- `1m`
- `5m`
- `15m`
- `1h`

Podrazumevani opseg:

- `1m`

Promena opsega:

- ne traži poseban backend upit za novi range
- filtrira postojeću lokalnu istoriju u UI-ju

## Header kartice

Status i range kontrola treba da budu u istom headeru kartice `Benchmark grafikon`.

Header treba da sadrži:

- naslov
- stalno vidljiv status
- range segment

## Status u headeru

Status je uvek vidljiv, ali menja sadržaj.

### Kada ima aktivnosti

Prikaz tipa:

- `live | poslednji throughput: 21.3 tok/s | pre 3s`

### Kada nema aktivnosti

Prikaz tipa:

- `nema novih zahteva u poslednjih 15s | poslednji throughput: 21.3 tok/s`

Ovo sprečava da praznina na grafu izgleda kao render bug.

## Stvarni uzorci

Svaki stvarni throughput uzorak treba da ima:

- malu tačku/marker

Linije ostaju glavni signal, a markeri pokazuju gde su stvarna merenja.

## Neaktivni periodi

Kada nema novog uzorka:

- throughput linija treba da ima prekid
- ne sme da se crta lažna ravna linija kao da throughput i dalje traje

Preko tog perioda treba nacrtati:

- diskretnu sivu isprekidanu liniju

To pokazuje da:

- vremenski tok ide dalje
- ali da nema novih merenja

## Vizuelna pravila

- glavne throughput serije ostaju jasno odvojene bojama
- markeri su mali i nenapadni
- siva isprekidana linija za neaktivnost mora biti suptilna
- graf ne sme da treperi ili resetuje postojeći sadržaj pri osvežavanju

## Backend / frontend granica

Za ovu fazu:

- backend nastavlja da puni lokalnu istoriju benchmark uzoraka
- frontend iz te istorije pravi vremenski prozor i graf

Za izbor `1m / 5m / 15m / 1h`:

- nema posebnog backend range API-ja
- UI radi filtraciju nad lokalno učitanom istorijom

## Success criteria

Faza je uspešna kada:

- graf se osvežava na svakih `5s`
- X osa prikazuje pravo vreme
- korisnik može da bira `1m / 5m / 15m / 1h`
- period bez novih zahteva se vidi kao neaktivnost, a ne kao lažna throughput linija
- status u headeru jasno objašnjava da li graf trenutno prima nove uzorke ili miruje
- stvarni uzorci imaju male markere
- graf ostaje stabilan i bez blinkanja
