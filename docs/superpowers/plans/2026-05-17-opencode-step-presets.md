# OpenCode Step Presets Implementation Plan

Datum: 2026-05-17

Spec:
- `C:\Users\AzdahaI9\Documents\local-qwen-control-center-next\docs\superpowers\specs\2026-05-17-opencode-step-presets-design.md`

## Cilj

Premestiti `Step mapping` iz glavnog `Settings` taba u `OpenCode` tab i tamo dodati:

- built-in preset-e
- user preset-e
- ručni editor za `Build / Plan / General / Explore`
- `Save preset`
- `Load preset`
- `Delete preset`
- `Restore default`

## Faza 1: Analiza postojećeg toka

- proveriti kako se trenutno u `SettingsPage` i `OpenCodePage` učitavaju i čuvaju:
  - `buildSteps`
  - `planSteps`
  - `generalSteps`
  - `exploreSteps`
- proveriti postojeći backend tok za:
  - `fetchOpenCodeStatus`
  - `applyOpenCodeSettings`
- proveriti da li već postoji lokalni storage ili backend storage obrazac koji može da se ponovo iskoristi za user preset-e

## Faza 2: Backend preset model

Dodati backend servis ili proširiti postojeći servis tako da podrži:

- built-in OpenCode step preset definicije:
  - `Safe`
  - `Daily`
  - `Deep`
  - `Max`
- user preset storage
- čitanje svih preset-a
- snimanje user preset-a
- brisanje user preset-a
- vraćanje default step vrednosti

Potrebni izlazi:

- payload sa built-in preset-ima
- payload sa user preset-ima
- aktivne step vrednosti

## Faza 3: API sloj

Dodati ili proširiti API rute za OpenCode steps:

- `GET` preset schema / lista preset-a
- `POST` save user preset
- `POST` delete user preset
- eventualno `GET` default step vrednosti ako nisu već obuhvaćene status payload-om

Napomena:
- stvarno upisivanje OpenCode step vrednosti i dalje ostaje kroz postojeći `Save OpenCode settings` tok
- preset API služi za editor/preset UX, ne za paralelni config sistem

## Faza 4: Uklanjanje Step mapping iz Settings taba

U `SettingsPage.tsx`:

- ukloniti prikaz `Step mapping`
- zadržati glavni model/runtime settings fokus:
  - `Settings scope`
  - `Access mode`
  - `Profil`
  - `Thinking mode`
  - `Context`
  - `Output tokens`
  - `Working directory`
  - `Save model settings`
  - `Restore default`

## Faza 5: OpenCode tab UI

U `OpenCodePage.tsx` dodati novi blok `OpenCode steps`.

Blok treba da sadrži:

- summary aktivnih step vrednosti
- listu built-in preset-a
- listu user preset-a
- editor sa 4 brojčana polja:
  - `Build`
  - `Plan`
  - `General`
  - `Explore`
- akcije:
  - `Load preset`
  - `Save preset`
  - `Delete preset`
  - `Restore default`
  - postojeći `Save OpenCode settings`

## Faza 6: UX pravila

- izbor preset-a samo puni editor
- ručni unos samo menja editor
- stvarni upis se dešava tek na:
  - `Save OpenCode settings`
- `Restore default` u OpenCode delu vraća editor na podrazumevane OpenCode step vrednosti
- `Restore default` u glavnom `Settings` delu ostaje odvojen i ne sme da dira OpenCode stepove

## Faza 7: Validacija

Pokriti bar sledeće:

- nema imena pri `Save preset`
- nevalidne ili prazne numeričke vrednosti
- pokušaj brisanja preset-a koji ne postoji
- neuspešan backend save

Akcioni rezultat treba da ide kroz postojeći result panel.

## Faza 8: Testovi

Dodati/izmeniti testove tako da potvrde:

- `SettingsPage` više ne sadrži `Step mapping`
- `OpenCodePage` sadrži:
  - `OpenCode steps`
  - `Safe`
  - `Daily`
  - `Deep`
  - `Max`
  - `Save preset`
  - `Load preset`
  - `Delete preset`
  - `Restore default`
- backend preset tokovi rade za save/load/delete
- frontend build prolazi

## Faza 9: Live verifikacija

Po završetku:

- podići novu verziju po pravilu semver toka korisnika
- rebuild frontend
- restart live instancu na `3210`
- proveriti da:
  - `Step mapping` više nije u `Settings`
  - `OpenCode` tab prikazuje novi preset blok
  - `Save preset` / `Delete preset` rade
  - `Save OpenCode settings` i dalje upisuje aktivne korake

## Završni kriterijum

Rad je gotov kada:

- OpenCode stepovi više nisu prikazani kao sirov model settings podatak
- preset sistem radi i za built-in i za user preset-e
- UI je bliži staroj aplikaciji i funkcionalno jasniji
