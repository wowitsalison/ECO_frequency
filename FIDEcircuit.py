from selenium import webdriver
from bs4 import BeautifulSoup
from collections import Counter
from urllib.parse import urlparse, parse_qs
import time

driver = webdriver.Firefox() 

chessgames = {
    "Praggnanandhaa R": "https://www.chessgames.com/perl/chess.pl?page=72&pid=151629",
    "Giri, Anish": "https://www.chessgames.com/perl/chess.pl?page=125&pid=107252",
    "Caruana, Fabiano": "https://www.chessgames.com/perl/chess.pl?page=155&pid=76172",
    "Bluebaum, Matthias": "https://www.chessgames.com/perl/chess.pl?page=42&pid=117666",
    "Keymer, Vincent": "https://www.chessgames.com/perl/chess.pl?page=41&pid=155740",
    "So, Wesley": "https://www.chessgames.com/perl/chess.pl?page=135&pid=95915",
    "Abdusattorov, Nodirbek": "https://www.chessgames.com/perl/chess.pl?page=62&pid=149949",
    "Carlsen, Magnus": "https://www.chessgames.com/perl/chess.pl?page=211&pid=52948",
    "Tabatabaei, M. Amin": "https://www.chessgames.com/perl/chess.pl?page=42&pid=142947",
    "Aravindh, Chithambaram VR.": "https://www.chessgames.com/perl/chess.pl?page=39&pid=131329",
    "Ding, Liren": "https://www.chessgames.com/perl/chess.pl?page=67&pid=52629",
    "Firouzja, Alireza": "https://www.chessgames.com/perl/chess.pl?page=64&pid=152702",
    "Nihal Sarin": "https://www.chessgames.com/perl/chess.pl?page=43&pid=151598",
    "Sindarov, Javokhir": "https://www.chessgames.com/perl/chess.pl?page=35&pid=155744",
    "Indjic, Aleksandar": "https://www.chessgames.com/perl/chess.pl?page=52&pid=132397",
    "Daneshvar, Bardiya": "https://www.chessgames.com/perl/chess.pl?page=17&pid=156259",
    "Yakubboev, Nodirbek": "https://www.chessgames.com/perl/chess.pl?page=31&pid=154820",
    "Gukesh D": "https://www.chessgames.com/perl/chess.pl?page=60&pid=158070",
    "Vachier-Lagrave, Maxime": "https://www.chessgames.com/perl/chess.pl?page=159&pid=56798",
    "Grebnev, Aleksey": "https://www.chessgames.com/perl/chess.pl?page=10&pid=170990"
}

def get_top_players():
    driver.get("https://data.fide.com/circuit_table_2025.php")
    time.sleep(3)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    players = soup.find_all("a", href=lambda x: x and "ratings.fide.com/profile" in x)
    top_20 = [{"rank": i+1, "name": a.get_text(strip=True)} for i, a in enumerate(players[:20])]
    return top_20

def summarize(white, black):
    return {
        "white": Counter(white).most_common(1)[0][0] if white else None,
        "black": Counter(black).most_common(1)[0][0] if black else None
    }

def normalize_name(name):
    name = name.replace(".", "").strip()

    if "," in name:
        last, first = name.split(",", 1)
        return f"{first.strip().lower()} {last.strip().lower()}"

    parts = name.split()
    return " ".join(parts).lower()

def get_last_name(player_name):
    exceptions = {
        "Praggnanandhaa R": "praggnanandhaa",
        "Aravindh, Chithambaram VR.": "aravindh"
    }
    if player_name in exceptions:
        return exceptions[player_name]

    if "," in player_name:
        last, _ = player_name.split(",", 1)
        return last.strip().lower()

    return player_name.split()[-1].lower()


def get_top_openings(player_name, last_page_url):
    parsed = urlparse(last_page_url)
    qs = parse_qs(parsed.query)

    page = int(qs["page"][0])
    pid = qs["pid"][0]

    white_openings = []
    black_openings = []
    target_last = get_last_name(player_name)

    for p in range(page, 0, -1):
        url = f"https://www.chessgames.com/perl/chess.pl?page={p}&pid={pid}"
        driver.get(url)
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, "html.parser")
        rows = soup.find_all("tr")

        for row in rows:
            game_link = row.find("a", href=lambda h: h and "chessgame" in h)
            if not game_link:
                continue

            text = game_link.get_text(strip=True)
            if " vs " not in text:
                continue

            white_name, black_name = text.split(" vs ")
            white_norm = normalize_name(white_name)
            black_norm = normalize_name(black_name)

            eco_tag = row.find("a", href=lambda h: h and "chessopening?eco=" in h)
            if not eco_tag:
                continue

            eco = eco_tag.get_text(strip=True)
            added_game = False

            if target_last in white_norm:
                white_openings.append(eco)
                added_game = True
            elif target_last in black_norm:
                black_openings.append(eco)
                added_game = True

            if added_game and (len(white_openings) + len(black_openings) >= 50):
                return summarize(white_openings, black_openings)

    return summarize(white_openings, black_openings)

if __name__ == "__main__":
    top_players = get_top_players()

    print("| Rank | Name | Top White Opening | Top Black Opening |")
    print("|------|------|-------------------|-------------------|")

    for i, player in enumerate(top_players, start=1):
        name = player["name"]

        if name not in chessgames:
            print(f"| {player['rank']} | {name} | N/A | N/A |")
        else:
            openings = get_top_openings(name, chessgames[name])
            print(
                f"| {player['rank']} | {name} | "
                f"{openings['white']} | {openings['black']} |"
            )

        # Pause after every 8 players
        if i % 8 == 0 and i != len(top_players):
            time.sleep(300)

    driver.quit()
