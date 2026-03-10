from glicko_logic import ClubManager

club = ClubManager()

def main():
    while True:
        print("\n" + "="*30)
        print("UTTR MAIN MENU")
        print("="*30)
        print("[1] Record Match")
        print("[2] View Top 10")
        print("[3] Search Player")
        print("[4] Head-to-Head")
        print("[5] Exit")
        
        choice = input("\nSelect an option: ").strip()

        if choice == '1':
            print("\n--- Enter Match Result (or type 'back' to return) ---")
            w = input("Winner Name: ").strip()
            if w.lower() == 'back': continue
            
            l = input("Loser Name: ").strip()
            if l.lower() == 'back': continue
            
            try:
                wp = int(input(f"{w}'s Score: "))
                lp = int(input(f"{l}'s Score: "))

                club.update_match(w, l, wp, lp)
                club.save_and_show()
                print(f"\n✅ Recorded: {w} def. {l} ({wp}-{lp})")
            except ValueError:
                print("Error: Scores must be numbers.")

        elif choice == '2':
            club.get_top_10()

        elif choice == '3':
            name = input("Enter player name to search: ").strip()
            club.search_player(name)
        elif choice == '4':
            n1 = input("Enter First Player: ").strip()
            n2 = input("Enter Second Player: ").strip()
            club.head_to_head(n1, n2)

        elif choice == '5':
            print("Saving data... Goodbye!")
            break
        else:
            print("Invalid choice. Please pick 1-5.")

if __name__ == "__main__":
    main()