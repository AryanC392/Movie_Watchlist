import json
import os
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WATCHLIST_FILE = os.path.join(BASE_DIR, "watchlist.json")
ENV_FILE = os.path.join(BASE_DIR, ".env")
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MAX_RESULTS = 10


def load_env():
    try:
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, value = line.split("=", 1)
                os.environ.setdefault(name.strip(), value.strip().strip("\"'"))
    except OSError:
        pass


def load_watchlist():
    try:
        with open(WATCHLIST_FILE, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, OSError) as e:
        print(f"Could not read {WATCHLIST_FILE} ({e}). Starting with an empty watchlist.")
        return []


def save_watchlist(watchlist):
    tmp = WATCHLIST_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(watchlist, f, indent=2)
    os.replace(tmp, WATCHLIST_FILE)


def search_tmdb(query):
    key = os.environ.get("TMDB_API_KEY", "").strip()

    params = {"query": query}
    headers = {"Accept": "application/json"}
    if key.count(".") == 2:
        headers["Authorization"] = f"Bearer {key}"
    else:
        params["api_key"] = key

    req = urllib.request.Request(f"{TMDB_SEARCH_URL}?{urllib.parse.urlencode(params)}", headers=headers)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.load(resp)

    return [
        {
            "id": r["id"],
            "title": r.get("title", "Untitled"),
            "year": (r.get("release_date") or "")[:4] or "Unknown",
            "watched": False,
        }
        for r in data.get("results", [])[:MAX_RESULTS]
    ]


def pick_number(prompt, high):
    raw = input(prompt).strip()
    if not raw:
        return None
    if not raw.isdigit() or not 1 <= int(raw) <= high:
        print(f"Please enter a number between 1 and {high}.")
        return None
    return int(raw)


def search_and_add(watchlist):
    query = input("Movie title to search: ").strip()
    if not query:
        print("No title entered.")
        return
    results = search_tmdb(query)
    if not results:
        print(f'No results for "{query}".')
        return

    for i, m in enumerate(results, 1):
        print(f"{i}. {m['title']} ({m['year']})")
    choice = pick_number("Number to add (blank to cancel): ", len(results))
    if choice is None:
        return

    movie = results[choice - 1]
    if any(m["id"] == movie["id"] for m in watchlist):
        print(f"{movie['title']} ({movie['year']}) is already in your watchlist.")
        return
    watchlist.append(movie)
    save_watchlist(watchlist)
    print(f"Added {movie['title']} ({movie['year']}).")


def print_watchlist(watchlist):
    for i, m in enumerate(watchlist, 1):
        mark = "x" if m["watched"] else " "
        print(f"{i}. [{mark}] {m['title']} ({m['year']})")


def view_watchlist(watchlist):
    if not watchlist:
        print("Your watchlist is empty.")
        return
    print_watchlist(watchlist)


def mark_watched(watchlist):
    if not watchlist:
        print("Your watchlist is empty.")
        return
    print_watchlist(watchlist)
    choice = pick_number("Number to mark as watched (blank to cancel): ", len(watchlist))
    if choice is None:
        return
    movie = watchlist[choice - 1]
    if movie["watched"]:
        print(f"{movie['title']} is already marked as watched.")
        return
    movie["watched"] = True
    save_watchlist(watchlist)
    print(f"Marked {movie['title']} as watched.")


def main():
    load_env()
    watchlist = load_watchlist()
    actions = {"1": search_and_add, "2": view_watchlist, "3": mark_watched}
    while True:
        print("\nMOVIE WATCHLIST")
        print("1. Search and add a movie")
        print("2. View watchlist")
        print("3. Mark a movie as watched")
        print("4. Exit")
        try:
            choice = input("> ").strip()
            if choice == "4":
                break
            action = actions.get(choice)
            if action:
                action(watchlist)
            else:
                print("Invalid choice. Enter 1-4.")
        except (EOFError, KeyboardInterrupt):
            print()
            break
    print("Goodbye!")


if __name__ == "__main__":
    main()
