# Benchmark Live Tokens Plan

Datum: 2026-05-18

## 1. Backend shape

- pregledati `benchmark_service.py`
- jasno razdvojiti:
  - prosečne throughput vrednosti
  - live poslednji uzorak
- po potrebi dodati eksplicitno polje za live uzorak u benchmark payload

## 2. Frontend types

- ažurirati `frontend/src/lib/types.ts`
- dodati/razjasniti tipove za:
  - `averages`
  - `liveCurrent`

## 3. Benchmark kartice

- u `BenchmarkPage.tsx` preimenovati postojeće kartice u:
  - `Avg input tok/s`
  - `Avg output tok/s`
  - `Avg ukupno tok/s`
- dodati novi `Live tokens` red:
  - `Live input tok/s`
  - `Live output tok/s`
  - `Live total tok/s`

## 4. Graf veza

- osigurati da graf koristi isti live signal kao `Live tokens` kartice
- prosečne `Avg` kartice ne smeju više da deluju kao izvor grafa

## 5. Empty/inactive state

- kada nema live delte:
  - `Live` kartice prikazuju `--` ili poslednju live vrednost po dogovorenom pravilu
  - header/status ostaje informativan
  - graf zadržava neaktivni period

## 6. Styling

- vizuelno odvojiti `Avg` i `Live` kartice
- sačuvati postojeću temu i boje:
  - plavo za input
  - crveno za output
  - žuto za total

## 7. Tests

- dopuniti frontend smoke test da traži:
  - `Avg input tok/s`
  - `Avg output tok/s`
  - `Avg ukupno tok/s`
  - `Live input tok/s`
  - `Live output tok/s`
  - `Live total tok/s`
- po potrebi dopuniti backend test za live payload polje

## 8. Verification

- pokrenuti backend/frontend testove
- uraditi frontend build
- restartovati živu instancu
- potvrditi novi bundle i novu verziju

## 9. Verzija

Pošto je ovo novi funkcionalni dodatak benchmark UX-a, verziju treba podići promenom `c` ili `b` u skladu sa trenutnim release pravilom koje korisnik traži za svaku promenu.
