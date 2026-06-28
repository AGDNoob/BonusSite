#!/usr/bin/env python3
"""
Monatlicher CWL-/Clan-Datensammler fuer die BonusSite.

Holt von der offiziellen Clash-of-Clans-API und schreibt strukturiert nach data/:
  * Clan-Snapshot + Mitgliederliste (aktuelles Rathaus, Liga, Trophaeen,
    Spenden, Rolle, Kriegssterne, beste Trophaeen)        -> data/clan.json
  * aktuelle CWL inkl. detaillierter Angriffsstatistik     -> data/seasons/<key>.json
  * Manifest aller vorhandenen Saisons                      -> data/manifest.json

Der API-Key steht in api_key.txt (oder ENV COC_API_KEY) und ist NICHT Teil des
Repos. Dieses Script selbst enthaelt kein Geheimnis und darf committet werden.

Aufruf:
  python fetch_data.py                       # Saison = aktueller Monat (YYYY-MM)
  python fetch_data.py 2026-06-2             # expliziter Saison-Key
  python fetch_data.py 2026-06-2 "Juni 2.0"  # + eigenes Anzeige-Label
  python fetch_data.py --no-cwl              # nur Clan-Snapshot + Manifest auffrischen
"""
import os, sys, json, time, glob, re
from datetime import datetime, timezone
from collections import defaultdict
import requests

# Windows-Konsole auf UTF-8 (sonst crasht print bei Sonderzeichen)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# ---- Konfiguration ----------------------------------------------------------
CLAN_TAG = "#2GJY8YPUP"
BASE = "https://api.clashofclans.com/v1"
ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
SEASONS_DIR = os.path.join(DATA_DIR, "seasons")

# Punktewertung (identisch zur Anzeige auf der Website):
#   Grundpunkte = Sterne (0/5/10/20) + 0,1 x Zerstoerungs-%
#   gewichtet nach Rathaus-Differenz (hoeher zaehlt mehr, niedriger weniger).
STAR_POINTS = {0: 0, 1: 5, 2: 10, 3: 20}
UP_WEIGHT = 0.25      # Bonus je RH-Stufe hoeher
DOWN_WEIGHT = 0.15    # Malus je RH-Stufe niedriger
MIN_FACTOR = 0.5      # Untergrenze des Faktors bei Angriffen nach unten
FULL_ATTACKS = 7      # volle Angriffszahl in der CWL
FULL_BONUS = 5        # Bonuspunkte bei genau 7/7

MONTHS_DE = ["Januar", "Februar", "Maerz", "April", "Mai", "Juni",
             "Juli", "August", "September", "Oktober", "November", "Dezember"]
ROLE_DE = {"leader": "Anfuehrer", "coLeader": "Vize", "admin": "Aeltester", "member": "Mitglied"}


# ---- API-Key ----------------------------------------------------------------
def load_api_key():
    k = os.environ.get("COC_API_KEY")
    if k:
        return k.strip()
    p = os.path.join(ROOT, "api_key.txt")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read().strip()
    sys.exit("Kein API-Key gefunden. Lege api_key.txt an oder setze ENV COC_API_KEY.")


API_KEY = load_api_key()
HEADERS = {"Authorization": f"Bearer {API_KEY}"}


# ---- HTTP -------------------------------------------------------------------
def get(endpoint, tries=6):
    """Robuster GET mit Rate-Limit-Handling. Gibt dict/list oder None zurueck."""
    for _ in range(tries):
        try:
            r = requests.get(BASE + endpoint, headers=HEADERS, timeout=30)
        except requests.RequestException as e:
            print(f"  Netzwerkfehler ({e}), neuer Versuch in 3s ...")
            time.sleep(3)
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            print("  Rate-Limit erreicht, warte 3s ...")
            time.sleep(3)
            continue
        print(f"  Fehler {r.status_code}: {endpoint}")
        return None
    return None


def enc(tag):
    return tag.replace("#", "%23")


# ---- Punkteberechnung -------------------------------------------------------
def attack_points(stars, destr, atk_th, def_th):
    base = STAR_POINTS.get(stars, 0) + 0.1 * destr
    factor = 1.0
    if atk_th and def_th:
        d = def_th - atk_th
        if d > 0:
            factor = 1 + UP_WEIGHT * d
        elif d < 0:
            factor = max(MIN_FACTOR, 1 + DOWN_WEIGHT * d)
    return base * factor


# ---- Clan-Snapshot ----------------------------------------------------------
def build_clan_snapshot():
    print("Hole Clan + Mitglieder ...")
    clan = get(f"/clans/{enc(CLAN_TAG)}") or {}
    ml = clan.get("memberList", [])
    members = []
    for i, m in enumerate(ml):
        print(f"  Mitglied {i + 1}/{len(ml)}: {m.get('name')}")
        detail = get(f"/players/{enc(m['tag'])}") or {}
        # Neues Ranglisten-Ligasystem (leagueTier), NICHT das alte/Legacy "league".
        tier = m.get("leagueTier") or {}
        ticons = tier.get("iconUrls", {}) or {}
        members.append({
            "tag": m["tag"],
            "name": m["name"],
            "th": m.get("townHallLevel"),
            "role": ROLE_DE.get(m.get("role"), m.get("role")),
            "roleRaw": m.get("role"),
            "league": tier.get("name"),
            "leagueIcon": ticons.get("small") or ticons.get("large"),
            "trophies": m.get("trophies"),
            "donations": m.get("donations"),
            "donationsReceived": m.get("donationsReceived"),
            "expLevel": m.get("expLevel"),
            "clanRank": m.get("clanRank"),
            "warStars": detail.get("warStars"),
            # Best-Trophäen gibt es nur als Legacy-Wert aus dem alten System.
            "legacyBestTrophies": detail.get("bestTrophies"),
            "attackWins": detail.get("attackWins"),
            "warPreference": detail.get("warPreference"),
        })
    badges = clan.get("badgeUrls", {}) or {}
    return {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "clan": {
            "name": clan.get("name"),
            "tag": clan.get("tag"),
            "level": clan.get("clanLevel"),
            "members": clan.get("members"),
            "warLeague": (clan.get("warLeague") or {}).get("name"),
            "warWins": clan.get("warWins"),
            "badge": badges.get("medium") or badges.get("small"),
            "description": clan.get("description"),
        },
        "members": members,
    }


# ---- CWL-Saison -------------------------------------------------------------
def new_stat():
    return {"name": "", "tag": "", "th": None, "points": 0.0, "attacks": 0,
            "stars": 0, "s0": 0, "s1": 0, "s2": 0, "s3": 0, "destr": 0.0,
            "up": 0, "eq": 0, "down": 0, "wars": 0}


def build_season(season_key, label):
    print("Hole CWL-Gruppe ...")
    group = get(f"/clans/{enc(CLAN_TAG)}/currentwar/leaguegroup")
    if not group:
        print("Keine aktive CWL gefunden.")
        return None
    war_tags = [w for r in group.get("rounds", []) for w in r.get("warTags", []) if w and w != "#0"]
    print(f"  {len(war_tags)} Kriege in der Gruppe")

    stats = defaultdict(new_stat)
    for i, wt in enumerate(war_tags):
        print(f"  Krieg {i + 1}/{len(war_tags)} ...")
        war = get(f"/clanwarleagues/wars/{enc(wt)}")
        if not war or war.get("state") != "warEnded":
            continue
        clan_side, opp = war.get("clan", {}), war.get("opponent", {})
        if clan_side.get("tag") != CLAN_TAG:
            if opp.get("tag") == CLAN_TAG:
                clan_side, opp = opp, clan_side
            else:
                continue
        opp_th = {m["tag"]: m.get("townhallLevel") for m in opp.get("members", [])}
        for mem in clan_side.get("members", []):
            s = stats[mem["tag"]]
            s["name"] = mem["name"]
            s["tag"] = mem["tag"]
            s["th"] = mem.get("townhallLevel")
            s["wars"] += 1
            for atk in mem.get("attacks", []):
                dth = opp_th.get(atk["defenderTag"])
                st = atk["stars"]
                de = atk["destructionPercentage"]
                s["points"] += attack_points(st, de, s["th"], dth)
                s["attacks"] += 1
                s["stars"] += st
                s["destr"] += de
                s[f"s{st}"] += 1
                if dth and s["th"] and dth > s["th"]:
                    s["up"] += 1
                elif dth and s["th"] and dth < s["th"]:
                    s["down"] += 1
                else:
                    s["eq"] += 1

    players = []
    for tag, s in stats.items():
        bonus = s["attacks"] == FULL_ATTACKS
        pts = s["points"] + (FULL_BONUS if bonus else 0)
        players.append({
            "name": s["name"], "tag": s["tag"], "th": s["th"],
            "points": round(pts), "attacks": s["attacks"],
            "missed": max(0, s["wars"] - s["attacks"]), "bonus": bonus,
            "stars": s["stars"], "s3": s["s3"], "s2": s["s2"], "s1": s["s1"], "s0": s["s0"],
            "destr": round(s["destr"] / s["attacks"], 1) if s["attacks"] else 0,
            "up": s["up"], "eq": s["eq"], "down": s["down"],
        })
    players.sort(key=lambda x: (-x["points"], x["name"]))
    for i, p in enumerate(players, 1):
        p["rank"] = i

    order = ["rank", "name", "tag", "th", "points", "attacks", "missed", "bonus",
             "stars", "s3", "s2", "s1", "s0", "destr", "up", "eq", "down"]
    ordered = [{k: p[k] for k in order} for p in players]
    return {
        "month": label,
        "key": season_key,
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "players": ordered,
    }


# ---- Manifest ---------------------------------------------------------------
def sort_key(key):
    m = re.match(r"(\d{4})-(\d{2})(?:-(\d+))?$", key)
    if not m:
        return (9999, 99, 99, key)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3) or 1), key)


def rebuild_manifest(snapshot):
    seasons = []
    for fp in glob.glob(os.path.join(SEASONS_DIR, "*.json")):
        try:
            j = json.load(open(fp, encoding="utf-8"))
        except Exception:
            continue
        key = os.path.splitext(os.path.basename(fp))[0]
        seasons.append({
            "key": key,
            "label": j.get("month", key),
            "file": f"seasons/{key}.json",
            "players": len(j.get("players", [])),
        })
    seasons.sort(key=lambda s: sort_key(s["key"]))
    return {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "clan": (snapshot or {}).get("clan", {}).get("name"),
        "seasons": seasons,
    }


# ---- Schreiben --------------------------------------------------------------
def write_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def write_season(path, season):
    """Kompaktes Format: ein Spieler pro Zeile (gut lesbare Diffs)."""
    lines = [json.dumps(p, ensure_ascii=False) for p in season["players"]]
    content = (
        "{\n"
        f'  "month": {json.dumps(season["month"], ensure_ascii=False)},\n'
        f'  "key": {json.dumps(season["key"])},\n'
        f'  "generated": {json.dumps(season["generated"])},\n'
        '  "players": [\n    '
        + ",\n    ".join(lines)
        + "\n  ]\n}\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def label_for(key, explicit):
    if explicit:
        return explicit
    m = re.match(r"(\d{4})-(\d{2})(?:-(\d+))?$", key)
    if not m:
        return key
    base = f"{MONTHS_DE[int(m.group(2)) - 1]} {m.group(1)}"
    return base + (f" ({m.group(3)})" if m.group(3) else "")


# ---- main -------------------------------------------------------------------
def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}

    key = args[0] if args else datetime.now().strftime("%Y-%m")
    label = label_for(key, args[1] if len(args) > 1 else None)

    os.makedirs(SEASONS_DIR, exist_ok=True)

    snapshot = build_clan_snapshot()
    write_json(os.path.join(DATA_DIR, "clan.json"), snapshot)
    print(f"OK Clan-Snapshot: {len(snapshot['members'])} Mitglieder -> data/clan.json")

    if "--no-cwl" not in flags:
        season = build_season(key, label)
        if season:
            write_season(os.path.join(SEASONS_DIR, f"{key}.json"), season)
            print(f"OK Saison {key} ({label}): {len(season['players'])} Spieler -> data/seasons/{key}.json")

    manifest = rebuild_manifest(snapshot)
    write_json(os.path.join(DATA_DIR, "manifest.json"), manifest)
    print(f"OK Manifest: {len(manifest['seasons'])} Saisons -> data/manifest.json")

    if "--no-cwl" not in flags and 'season' in dir() and season and season["players"]:
        print("\nTop 11:")
        for p in season["players"][:11]:
            mark = " *" if p["bonus"] else ""
            print(f"  {p['rank']:>2}. {p['name']} - {p['points']} Pkt ({p['attacks']}/7){mark}")


if __name__ == "__main__":
    main()
