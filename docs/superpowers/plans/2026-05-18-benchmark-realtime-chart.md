# Benchmark Real-Time Chart Implementation Plan

Datum: 2026-05-18

Spec:
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\docs\superpowers\specs\2026-05-18-benchmark-realtime-chart-design.md`

## Cilj

Pretvoriti benchmark grafikon u pravi real-time prikaz sa:

- stalnim osvežavanjem na `5s`
- vremenskom X osom
- izborom opsega
- jasnim statusom aktivnosti
- razlikom između stvarnih uzoraka i neaktivnih perioda

## Faza 1: Analiza postojećeg benchmark toka

Proveriti:

- kako `BenchmarkPage.tsx` trenutno učitava istoriju
- kako backend puni `history`
- kako se danas generišu `chartLabel` i `measuredAt`
- kako se trenutno crta SVG graf

Potvrditi koje informacije već imamo i šta još treba izračunati u frontendu.

## Faza 2: Podaci za real-time prozor

U frontend sloju uvesti:

- lokalni izbor opsega:
  - `1m`
  - `5m`
  - `15m`
  - `1h`
- filtraciju lokalne istorije prema izabranom opsegu
- logiku za određivanje:
  - poslednjeg uzorka
  - trajanja neaktivnosti
  - da li trenutni period ima prazninu bez novog uzorka

## Faza 3: Header kontrolna traka

U `Benchmark grafikon` kartici preurediti header tako da sadrži:

- naslov
- stalni status
- range segment

Status treba da podrži dva glavna stanja:

- aktivan tok
- nema novih zahteva

## Faza 4: Vremenska osa

Promeniti prikaz X ose tako da:

- koristi `HH:MM:SS`
- ne koristi više pomoćne tekstove o osi
- za duže opsege smanjuje gustinu oznaka

## Faza 5: Stvarni uzorci i neaktivni periodi

Dodati razliku između:

- stvarnih throughput uzoraka
- praznih perioda bez novog uzorka

To znači:

- throughput linije imaju prekid kada nema novog uzorka
- crtati malu tačku za svaki stvarni uzorak
- crtati diskretnu sivu isprekidanu liniju kroz neaktivni period

## Faza 6: Real-time status

Uvesti funkciju koja za trenutno stanje računa tekst statusa:

- kada ima novog saobraćaja:
  - `live | poslednji throughput ... | pre ...`
- kada nema novih zahteva:
  - `nema novih zahteva u poslednjih ... | poslednji throughput ...`

## Faza 7: Stabilnost osvežavanja

Zadržati osvežavanje na `5s`, ali:

- ne resetovati graf pri svakom fetch-u
- ne brisati postojeći prikaz dok novi payload stiže
- voditi računa da range promena i osvežavanje ne naprave blinkanje

## Faza 8: Testovi

Dodati ili izmeniti testove tako da potvrde:

- prisustvo range segmenta:
  - `1m`
  - `5m`
  - `15m`
  - `1h`
- prisustvo real-time status linije u graf kartici
- da `BenchmarkPage` i dalje osvežava na `5000`
- da stari tekstovi za ose i dalje ne postoje

Ako bude smisleno, dodati male unit helper testove za:

- filtriranje istorije po opsegu
- detekciju neaktivnog perioda
- format status poruke

## Faza 9: Live verifikacija

Po završetku:

- podići novu verziju
- build frontend
- restart live instancu na `3210`
- proveriti da:
  - graf osvežava prikaz na `5s`
  - menja range između `1m / 5m / 15m / 1h`
  - X osa prikazuje vreme
  - status jasno pokazuje neaktivnost
  - neaktivni periodi imaju diskretnu sivu isprekidanu liniju
  - stvarni uzorci imaju markere

## Završni kriterijum

Rad je gotov kada benchmark graf konačno izgleda kao pravi real-time signal, a ne kao statičan ili polu-zamrznut prikaz istorije.
