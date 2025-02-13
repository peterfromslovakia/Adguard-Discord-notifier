WATCHLIST_FILE = "/opt/watchlist.txt"

def load_watchlist():
    try:
        with open(WATCHLIST_FILE, "r") as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        return []

def save_watchlist(watchlist):
    with open(WATCHLIST_FILE, "w") as f:
        f.write("\n".join(watchlist))

while True:
    print("\nSpráva sledovaných domén")
    print("1. Zobraziť zoznam")
    print("2. Pridať doménu")
    print("3. Odstrániť doménu")
    print("4. Ukončiť")

    choice = input("Vyber možnosť: ")
    watchlist = load_watchlist()

    if choice == "1":
        print("\nSledované domény:")
        for d in watchlist:
            print(f"- {d}")
    elif choice == "2":
        domain = input("Zadaj doménu na pridanie: ").strip()
        if domain and domain not in watchlist:
            watchlist.append(domain)
            save_watchlist(watchlist)
            print(f"{domain} pridané!")
    elif choice == "3":
        domain = input("Zadaj doménu na odstránenie: ").strip()
        if domain in watchlist:
            watchlist.remove(domain)
            save_watchlist(watchlist)
            print(f"{domain} odstránené!")
    elif choice == "4":
        break
