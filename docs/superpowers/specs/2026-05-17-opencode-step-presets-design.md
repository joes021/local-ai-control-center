# OpenCode Step Presets Design

Datum: 2026-05-17

## Problem

U novom `Local AI Control Center` UI-ju trenutno postoji sirov `Step mapping` blok u glavnom `Settings` tabu:

- `Build`
- `Plan`
- `General`
- `Explore`

To je zbunjujuce jer:

- taj blok nije vezan za model runtime settings
- vezan je za `OpenCode`
- trenutno nije organizovan kao u staroj aplikaciji
- nema gotove preset-e ni korisnicke preset-e

Korisnik je eksplicitno trazio da se ovaj deo vrati u smisleniji oblik iz stare aplikacije.

## Cilj

`Step mapping` treba izmestiti iz glavnog `Settings` bloka u `OpenCode` tab i pretvoriti ga u pravi `OpenCode steps` sistem sa:

- gotovim preset-ima
- rucnim unosom brojcanih vrednosti
- snimanjem korisnickih preset-a pod imenom
- ucitavanjem korisnickih preset-a
- brisanjem korisnickih preset-a
- vracanjem na podrazumevane vrednosti

## Scope

Ova faza pokriva samo `OpenCode` stepove:

- `Build`
- `Plan`
- `General`
- `Explore`

Ova faza namerno **ne** ukljucuje u preset:

- `security mode`
- `capability mode`
- `working directory`

Ta podesavanja ostaju odvojena, jer nisu ista vrsta odluke kao step limit-i.

## UX promene

### 1. Glavni Settings tab

Iz glavnog `Settings` taba uklanja se postojeći `Step mapping` prikaz.

Glavni `Settings` ostaje fokusiran na:

- `Settings scope`
- `Access mode`
- `Profil`
- `Thinking mode`
- `Context`
- `Output tokens`
- `Working directory`
- `Save model settings`
- `Restore default`

### 2. OpenCode tab

U `OpenCode` tabu dodaje se novi blok: `OpenCode steps`.

Taj blok sadrzi:

- mali summary aktivnih koraka
- gotove preset-e
- korisnicke preset-e
- editor za rucni unos brojcanih vrednosti
- akcije za cuvanje, ucitavanje, brisanje i restore

## Preset model

Preset sadrzi samo 4 broja:

- `buildSteps`
- `planSteps`
- `generalSteps`
- `exploreSteps`

### Built-in preset-i

Prva verzija ima 4 gotova preset-a:

- `Safe`
- `Daily`
- `Deep`
- `Max`

Svaki preset se prikazuje sa vrednostima u zagradama, na primer:

- `Daily (140 / 100 / 110 / 80)`

Redosled u prikazu je uvek:

- `Build / Plan / General / Explore`

### User preset-i

Korisnik moze:

- da unese rucne vrednosti
- da unese ime preset-a
- da snimi preset
- da ucita prethodno snimljen preset
- da obrise svoj preset

Korisnicki preset-i su odvojeni od built-in preset-a i samo oni mogu da se brisu.

## Restore default

`Restore default` u `OpenCode steps` delu vraca step vrednosti na podrazumevani sistemski preset za trenutno stanje aplikacije.

To nije isto sto i:

- `Restore default` u glavnom `Settings` bloku

Ta dva restore toka ostaju odvojena i jasno oznacena.

## Save ponašanje

OpenCode step editor ne menja stvarno backend stanje samim izborom preset-a ili rucnim unosom.

Pravo upisivanje se desava tek kada korisnik klikne odgovarajuci save tok za OpenCode settings.

To treba da bude jasno iz UI-ja:

- izbor preset-a = puni editor
- ručni unos = menja editor
- save = stvarno upisuje OpenCode step vrednosti

## Integracija sa postojecim OpenCode settings tokovima

Novi `OpenCode steps` blok koristi postojeci OpenCode settings payload i postojeci save tok, ali mu daje jasniji UX sloj.

To znaci:

- nema novog paralelnog backend sistema za stepove
- vec se postojece vrednosti bolje organizuju i prikazuju

## Podaci i cuvanje

Sistem mora da podrzi:

- built-in preset definicije
- user preset storage
- ucitavanje aktivnih vrednosti iz postojeceg OpenCode config/settings izvora

User preset-i treba da budu trajno sacuvani lokalno, kao i ostali korisnicki preset tokovi u aplikaciji.

## Error handling

Treba pokriti bar sledece slucajeve:

- pokusaj snimanja bez imena preset-a
- pokusaj cuvanja sa nevalidnim brojcanim vrednostima
- pokusaj brisanja nepostojeceg preset-a
- neuspeh upisa OpenCode settings-a

UI treba da vrati jasan akcioni rezultat kroz isti rezultat panel koji aplikacija vec koristi.

## Testing

Treba pokriti:

- da `Settings` tab vise ne prikazuje `Step mapping`
- da `OpenCode` tab prikazuje `OpenCode steps`
- da postoje built-in preset-i:
  - `Safe`
  - `Daily`
  - `Deep`
  - `Max`
- da postoje stringovi za:
  - `Save preset`
  - `Load preset`
  - `Delete preset`
  - `Restore default`
- da save tok i dalje ostaje eksplicitan, a ne implicitni auto-save

## Success criteria

Faza je uspesna kada:

- `Step mapping` vise nije u glavnom `Settings` bloku
- `OpenCode` tab postane pravo mesto za OpenCode stepove
- korisnik moze da bira gotove preset-e
- korisnik moze da napravi svoj preset, ucita ga i obrise ga
- UI bude smisleniji i blizi staroj aplikaciji nego trenutni sirovi prikaz
