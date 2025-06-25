import socket
import json

SERVER_ADDRESS = ('localhost', 8889)

def send_command(command):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(3)  
    try:
        s.connect(SERVER_ADDRESS)
        s.sendall((command + '\r\n').encode())

        response = ""
        while True:
            data = s.recv(32)
            if not data:
                break
            response += data.decode()
            if "\r\n\r\n" in response:
                break
        s.close()
        response = response.replace('\r\n\r\n', '')
        return json.loads(response)
    except socket.timeout:
        return {"status": "ERROR", "message": "Timeout saat menghubungi server"}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def main():
    player_id = input("Masukkan nama pemain: ")
    
    # Join game
    print(send_command(f"join {player_id}"))

    while True:
        print("\n=== GILIRAN ===")
        top = send_command("top_card")
        print("Kartu di atas:", top["top_card"])
        print("Giliran:", top["current_turn"])

        hand = send_command(f"hand {player_id}")
        print("Kartu kamu:")
        for i, card in enumerate(hand["hand"]):
            print(f"{i}: {card}")

        if not hand["your_turn"]:
            print("Tunggu giliranmu...")
            input("Tekan ENTER untuk refresh.")
            continue

        print("Aksi: ")
        print("1. Mainkan kartu")
        print("2. Ambil kartu")
        print("3. Keluar")

        choice = input("Pilihanmu: ")

        if choice == "1":
            index = int(input("Index kartu yang ingin dimainkan: "))
            # Dapatkan nama kartu yang dipilih (dari hand)
            selected_card = hand["hand"][index]
            
            # Cek apakah kartu adalah wild
            if "+4" in selected_card or "wild" in selected_card:
                new_color = input("Pilih warna baru (red, green, blue, yellow): ").lower()
                command = f"play {player_id} {index} {new_color}"
            else:
                command = f"play {player_id} {index}"
            
            result = send_command(command)
            print(result)
        elif choice == "2":
            result = send_command(f"draw {player_id}")
            print(result)
        elif choice == "3":
            break
        else:
            print("Pilihan tidak valid.")

if __name__ == "__main__":
    main()