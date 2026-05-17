# Server Control Parity Design

## Goal

Vratiti u `Control Center Next` osnovnu server lifecycle funkcionalnost koja je postojala u staroj Windows aplikaciji, tako da novi zajednicki Web UI ponovo bude stvarni control center i za Windows i za Linux.

Ova faza vraca:

- `Start server`
- `Stop server`
- `Run llama.cpp web`
- puniji `Server` status panel na `Home`

Ovo je prva parity faza zato sto bez upravljanja serverom novi UI i dalje deluje kao parcijalni dashboard, a ne kao glavni control center.

## Scope

U ovoj fazi ulazi:

1. novi `Server` blok na `Home`
2. backend API za server lifecycle
3. Windows i Linux adapteri za iste API rute
4. jasan server status posle svake akcije

Namerno ne ulazi jos:

- benchmark tab
- throughput grafici
- siri diagnostics dashboard
- dodatni quick panel parity delovi koji nisu direktno server lifecycle

## Product Behavior

Na `Home` ekranu treba da postoji poseban `Server` blok, ravnopravan sa runtime i OpenCode informacijama.

Blok prikazuje:

- `Status`
- `Port`
- `Health`
- `PID`
- `Aktivni runtime`
- `Poslednja poruka`
- lokalni URL
- `Tailscale URL` kada postoji

Blok nudi akcije:

- `Start server`
- `Stop server`
- `Run llama.cpp web`

## UX Rules

### Start server

Klik na `Start server` ne sme da deluje mrtvo.

UI mora odmah da prikaze prelazno stanje kao sto su:

- `pokretanje`
- ili `server start je pokrenut`

Posle toga server blok mora da se osvezi i da pokaze realno stanje:

- `aktivan`
- `greska`
- ili `nije potvrden`

### Stop server

Klik na `Stop server` mora da vrati jasan rezultat:

- server je zaustavljen
- server nije bio aktivan
- gasenje nije uspelo i zasto

### Run llama.cpp web

`Run llama.cpp web` treba da ima smisla samo kada postoji upotrebljiv web endpoint ili kada stable launcher ume da otvori ispravnu web stranu.

UI mora da zna da objasni:

- da li je otvoren lokalni web UI
- ili zasto nije mogao da se otvori

## Architecture

Novi Web UI ne treba da izmišlja novi server lifecycle.

Izvor istine ostaje postojeći stable sloj:

- Windows PowerShell launcheri i common helperi
- Linux shell launcheri i common helperi
- postojeći lifecycle/state fajlovi

Novi backend služi kao adapter i izlaže čist API preko toga.

## API Contract

Potrebne su sledeće rute:

- `GET /api/server/status`
- `POST /api/server/start`
- `POST /api/server/stop`
- `POST /api/server/open-web`

### `GET /api/server/status`

Payload treba da sadrži najmanje:

- `status`
- `health`
- `port`
- `pid`
- `activeRuntime`
- `message`
- `localUrl`
- `tailscaleUrl`
- `canOpenWeb`

### `POST /api/server/start`

Treba da vrati:

- da li je start prihvaćen
- kratak rezultat za korisnika
- dovoljno detalja da UI zna da osveži `Server` blok

### `POST /api/server/stop`

Treba da vrati:

- da li je stop uspeo
- ili da li server uopšte nije bio aktivan
- i objašnjenje ako je bilo problema

### `POST /api/server/open-web`

Treba da pokuša da otvori odgovarajući lokalni web endpoint kroz postojeći OS tok.

Odgovor mora da kaže:

- da li je otvaranje pokrenuto
- ili zašto nije moglo

## Shared UI Contract

Frontend mora ostati zajednički za Windows i Linux.

To znači:

- isti `Server` blok
- iste API rute
- ista semantika stanja

OS razlike ostaju samo u backend adapter sloju.

## Windows Adapter Expectations

Windows adapter treba da koristi postojeće stable skripte za:

- start server
- stop server
- otvaranje llama.cpp web toka
- čitanje lifecycle i health stanja

Ne treba uvoditi zasebnu paralelnu logiku ako stable tok već postoji i radi.

## Linux Adapter Expectations

Linux adapter treba da koristi postojeće stable skripte i lifecycle tokove na isti način kao Windows adapter, samo kroz shell/common helper sloj.

Ako neka Linux grana trenutno nema pun parity, backend to treba jasno da prijavi, a ne da UI ostavi u mrtvom stanju.

## Home Layout Change

`Home` treba da dobije novi `Server` blok u gornjoj zoni.

U toj fazi je prihvatljivo da se Home malo reorganizuje kako bi:

- server status bio odmah vidljiv
- glavne akcije bile lako dostupne
- OpenCode i runtime ostali blizu tog bloka

## Error Handling

Server akcije ne smeju da završavaju samo u sirovom donjem result panelu.

Potrebno je:

- result panel kao detaljan trag
- i osvežen `Server` blok kao glavni izvor istine

Ako lifecycle i health nisu saglasni, backend treba da normalizuje stanje i da vrati poruku koja korisniku objašnjava šta se zaista dešava.

## Verification Criteria

Ova faza se smatra gotovom tek kada:

1. `GET /api/server/status` vraća smislen i stabilan payload
2. `Start server` stvarno pokrene server
3. `Stop server` stvarno zaustavi server
4. `Run llama.cpp web` stvarno otvori odgovarajući web tok ili jasno objasni zašto ne može
5. `Home` blok prikazuje pravo stanje posle svake akcije
6. isti API ugovor važi za Windows i Linux

## Recommendation

Ovo treba raditi kao `Phase 1` parity povratak pre benchmark/grafika.

Kada server lifecycle opet bude zdrav i pregledan u novom Web UI-ju, benchmark i live signal mogu da se vrate na isti backend mnogo čistije.
