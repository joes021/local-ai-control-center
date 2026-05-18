# Benchmark Live Tokens Design

Datum: 2026-05-18

## Cilj

Benchmark tab trenutno meša dve vrste signala:

- prosečne/agregirane throughput vrednosti
- trenutni live throughput signal iz aktivnog `llama.cpp`/OpenCode rada

To pravi konfuziju kada OpenCode stvarno radi, GPU je zauzet, ali graf i kartice ne prikazuju isto značenje.

## Odluka

Benchmark UI se deli na dva jasno odvojena sloja:

1. `Avg` kartice
2. `Live tokens` kartice + live graf

## Avg kartice

Postojeće kartice ostaju, ali se eksplicitno preimenuju u:

- `Avg input tok/s`
- `Avg output tok/s`
- `Avg ukupno tok/s`

Njihovo značenje:

- predstavljaju prosečne/agregirane vrednosti iz benchmark istorije
- nisu pokazatelj trenutne live aktivnosti u realnom vremenu

## Live tokens kartice

Dodaje se novi red kartica:

- `Live input tok/s`
- `Live output tok/s`
- `Live total tok/s`

Njihovo značenje:

- prikazuju najnoviji live throughput uzorak
- uvek su vezane za isti signal koji puni live graf

Ako live signal nema podatak:

- prikazuje se `--`

Ako postoji poslednji poznati live signal, ali trenutno nema nove delte:

- kartice mogu prikazati poslednju live vrednost
- status header i graf i dalje moraju jasno reći da trenutno nema novih zahteva

## Graf

Graf više konceptualno pripada `Live tokens` redu, ne prosečnim karticama.

To znači:

- graf se zasniva na live istoriji/signalu
- prosečne `Avg` kartice ne utiču na ono što graf crta

Graf zadržava postojeća pravila:

- refresh na `5s`
- X osa je pravo vreme `HH:MM:SS`
- range segment:
  - `1m`
  - `5m`
  - `15m`
  - `1h`
- kada nema novih live uzoraka:
  - header pokazuje poruku o neaktivnosti
  - graf prikazuje diskretnu sivu isprekidanu liniju kroz neaktivni period

## Backend model

Payload za benchmark treba jasno da razdvoji:

- agregirane/prosečne throughput vrednosti
- poslednji live uzorak

Preporučeni oblik:

- `averages`
  - prosečne throughput vrednosti
- `liveCurrent`
  - trenutni/poslednji live uzorak za live kartice i graf

Ako se zadrži postojeći `current`, frontend mora da ga tretira kao live signal samo ako je to zaista live benchmark izvor. Poželjno je eksplicitno polje da ne ostane dvosmislenost.

## UX pravilo

Korisnik mora odmah da vidi razliku između:

- `šta je prosek`
- `šta je live`

To znači:

- Avg kartice su jasno označene sa `Avg`
- Live kartice su jasno označene sa `Live`
- graf vizuelno pripada live signalima

## Uspeh

Rešenje je dobro kada:

- korisnik vidi da OpenCode radi i benchmark live kartice to potvrđuju
- graf i `Live` kartice pričaju istu priču
- `Avg` kartice ostaju korisne, ali više ne zbunjuju
