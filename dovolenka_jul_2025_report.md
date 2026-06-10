# Analýza cien last minute dovoleniek z júla 2025

Zdrojom sú archívne zachytenia Dovolenka.SME.sk cez Internet Archive. Ceny sú historické zobrazené ceny `od` a nemusia znamenať dnešnú dostupnosť.

## Metodika

- Snapshoty: `2025-07-10` (`20250710064927`), `2025-07-30` (`20250730145258`).
- Vynechané destinácie: Tunisko, Egypt, Albánsko, Čierna Hora.
- Hotel je plne overený iba vtedy, keď archívny zdroj priamo potvrdil 4*+, AI/UAI, pláž 0 m a bazén.
- Keď karta potvrdila 4*+, AI/UAI a pláž 0 m, ale nie bazén, hotel je uvedený len ako kandidát bez plného overenia.

## Záver

V dostupných júlových archívoch sa nenašiel žiadny hotelový riadok, ktorý by priamo v archívnom zdroji potvrdil všetky štyri kritériá vrátane bazéna.
Našlo sa 0 kandidátov, kde karta potvrdzuje 4*+, AI/UAI a pláž 0 m, ale bazén nie je v archívnej karte potvrdený.

## Doplnený historický AI/UAI prehľad z iných zdrojov

Pretože hotelové karty z Dovolenka.SME.sk neukazovali AI/UAI cenu, bol doplnený samostatný dataset z archívov Invia.sk a Fischer.sk. Zaradené sú iba letecké balíky s odchodom v júli 2025, stravou All inclusive alebo Ultra All inclusive a cenou za osobu zachytenou v archívnej URL alebo stránke. Vynechané zostali Tunisko, Egypt, Albánsko a Čierna Hora.

| destination | count | min | median | max |
| --- | --- | --- | --- | --- |
| arabske-emiraty | 2 | 2016 | 2016 | 2026 |
| bahrajn | 1 | 1293 | 1293 | 1293 |
| bulharsko | 7 | 1002 | 1355 | 1911 |
| cyprus | 1 | 1307 | 1307 | 1307 |
| kanarske-ostrovy | 1 | 2383 | 2383 | 2383 |
| kuba | 1 | 2230 | 2230 | 2230 |
| spanielsko | 1 | 2159 | 2159 | 2159 |
| turecko | 6 | 778 | 1143 | 2408 |

Poznámka ku kvalite: `mealId=11` z Invia bolo overené vzorkou stránky ako Ultra All inclusive. `mealId=5` je označené ako All inclusive s nižšou istotou, pretože vzorová stránka obsahovala opis All Inclusive, ale nie vždy samostatné `mealName`. Fischer riadky majú vyššiu istotu, pretože URL obsahuje `DI=AI`, hviezdičky `MT=5` a cenu v parametri `PC`.

## Kandidáti hotelov
_Žiadne riadky._

## Súhrn kandidátov podľa destinácie
_Žiadne riadky._

## Slabšie ceny `od` podľa destinácie
Tieto riadky sú ceny na úrovni destinácie, nie hotelovo overené ceny.

| destination | count | min | median | max |
| --- | --- | --- | --- | --- |
| Bulharsko | 2 | 304 | 307.0 | 310 |
| Chorvátsko | 2 | 450 | 450.0 | 450 |
| Cyprus | 2 | 447 | 449.5 | 452 |
| Dominikánska republika | 2 | 977 | 982.0 | 987 |
| Grécko | 2 | 335 | 357.0 | 379 |
| Kanárske ostrovy | 2 | 466 | 482.5 | 499 |
| Maldivy / Maledivy | 2 | 1048 | 1058.5 | 1069 |
| Portugalsko | 2 | 468 | 482.5 | 497 |
| Spojené arabské emiráty | 2 | 390 | 465.0 | 540 |
| Taliansko | 2 | 491 | 494.0 | 497 |
| Thajsko | 2 | 742 | 743.5 | 745 |
| Turecko | 2 | 245 | 246.0 | 247 |
| Španielsko | 2 | 341 | 347.0 | 353 |

## Súbory

- `dovolenka_jul_2025_destination_prices.csv`: ceny `od` na úrovni destinácií.
- `dovolenka_jul_2025_hotel_candidates.csv`: všetky extrahované hotelové karty vrátane overovacích flagov.
- `historical_all_inclusive_packages_july_2025.csv`: doplnené historické AI/UAI letecké balíky z Invia.sk a Fischer.sk.

## Chyby pri načítaní

Niektoré archívne URL nebolo možné načítať; tieto riadky neboli použité.

| snapshot | page | error |
| --- | --- | --- |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/bulharsko/zlate-piesky | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/bulharsko/zlate-piesky: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/chorvatsko/2 | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/chorvatsko/2: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/chorvatsko/kvarner | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/chorvatsko/kvarner: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/chorvatsko/pag | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/chorvatsko/pag: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/dominikanska-republika/2 | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/dominikanska-republika/2: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/dominikanska-republika/polostrov-samana | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/dominikanska-republika/polostrov-samana: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/grecko/astypalaia | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/grecko/astypalaia: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/grecko/chalkidiki | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/grecko/chalkidiki: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/grecko/kea | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/grecko/kea: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/grecko/kefalonia | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/grecko/kefalonia: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/grecko/kimolos | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/grecko/kimolos: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/grecko/kreta | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/grecko/kreta: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/grecko/lefkada | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/grecko/lefkada: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/grecko/milos | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/grecko/milos: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/grecko/mykonos | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/grecko/mykonos: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/grecko/pilion | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/grecko/pilion: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/grecko/samos | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/grecko/samos: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/grecko/sifnos | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/grecko/sifnos: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/grecko/skiathos | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/grecko/skiathos: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
| 20250710064927 | https://dovolenka.sme.sk/last-minute/grecko/syros | Failed to fetch https://web.archive.org/web/20250710064927id_/https://dovolenka.sme.sk/last-minute/grecko/syros: <urlopen error [WinError 10061] No connection could be made because the target machine actively refused it> |
