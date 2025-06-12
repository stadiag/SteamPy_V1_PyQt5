import sys
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QFileDialog, QTextEdit, QMessageBox
)
from PyQt5.QtGui import QFont

# Fonction pour récupérer le prix d’un jeu + ses DLC via l’API Steam
def get_steam_price_with_dlc(appid, country='fr', currency='eur'):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}&cc={country}&l=fr"
    try:
        response = requests.get(url)
        data = response.json()
        if not data[str(appid)]["success"]:
            print(f"[DEBUG] AppID {appid} échec d'accès API")
            return None

        info = data[str(appid)]["data"]
        name = info["name"]
        print(f"[DEBUG] Récupération du jeu : {name} (AppID {appid})")

        game_price = {
            "title": name,
            "appid": appid,
            "final": 0,
            "initial": 0,
            "discount_percent": 0,
            "dlcs": []
        }

        # Prix du jeu de base
        if "price_overview" in info:
            p = info["price_overview"]
            game_price["final"] = p["final"] / 100
            game_price["initial"] = p["initial"] / 100
            game_price["discount_percent"] = p["discount_percent"]
        else:
            print(f"[DEBUG] Aucun prix trouvé pour le jeu {name}")

        # Récupération des DLC
        if "dlc" in info:
            dlc_ids = info["dlc"]
            print(f"[DEBUG] {len(dlc_ids)} DLC(s) trouvé(s) pour {name}")
            for dlc_id in dlc_ids:
                dlc_url = f"https://store.steampowered.com/api/appdetails?appids={dlc_id}&cc={country}&l=fr"
                dlc_resp = requests.get(dlc_url).json()
                if dlc_resp.get(str(dlc_id), {}).get("success"):
                    dlc_data = dlc_resp[str(dlc_id)]["data"]
                    if "price_overview" in dlc_data:
                        d = dlc_data["price_overview"]
                        dlc_info = {
                            "title": dlc_data["name"],
                            "appid": dlc_id,
                            "final": d["final"] / 100,
                            "initial": d["initial"] / 100,
                            "discount_percent": d["discount_percent"]
                        }
                        game_price["dlcs"].append(dlc_info)
                        print(f"[DEBUG] DLC ajouté : {dlc_info['title']}")
                    else:
                        print(f"[DEBUG] DLC {dlc_id} sans prix (probablement retiré)")
        else:
            print(f"[DEBUG] Aucun DLC pour {name}")

        return game_price
    except Exception as e:
        print(f"[ERROR] Exception pour AppID {appid} : {e}")
        return {"title": f"Erreur {appid}", "error": str(e)}

# Interface graphique principale
class SteamPriceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Steam Price Checker")
        self.setMinimumSize(10, 10)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.title = QLabel("Vérificateur de Prix Steam")
        self.title.setFont(QFont("Arial", 18))
        self.layout.addWidget(self.title)

        self.load_button = QPushButton("Charger un fichier de jeux (.txt)")
        self.load_button.clicked.connect(self.load_file)
        self.layout.addWidget(self.load_button)

        self.result_area = QTextEdit()
        self.result_area.setReadOnly(True)
        self.layout.addWidget(self.result_area)
        
    # OUVRIR LE TXT (a changer pour mettre des csv ou json par exemple)
    def load_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Ouvrir fichier .txt", "", "Text Files (*.txt)")
        if file_name:
            try:
                with open(file_name, "r") as f:
                    appids = [line.strip() for line in f if line.strip().isdigit()]
                self.process_appids(appids)
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de lire le fichier : {str(e)}")

    def process_appids(self, appids):
        total_with_discount = 0
        total_without_discount = 0
        result_text = ""

        for appid in appids:
            price_info = get_steam_price_with_dlc(appid)
            if price_info:
                if "error" in price_info:
                    result_text += f"{price_info['title']} : Erreur - {price_info['error']}\n"
                    continue

                result_text += (
                    f"\n🎮 {price_info['title']}\n"
                    f"  Prix original : {price_info['initial']} €\n"
                    f"  Prix actuel : {price_info['final']} € (-{price_info['discount_percent']}%)\n"
                )
                total_without_discount += price_info["initial"]
                total_with_discount += price_info["final"]

                # Traitement des DLC
                if price_info["dlcs"]:
                    for dlc in price_info["dlcs"]:
                        result_text += (
                            f"    🧩 DLC - {dlc['title']}\n"
                            f"      Prix original : {dlc['initial']} €\n"
                            f"      Prix actuel : {dlc['final']} € (-{dlc['discount_percent']}%)\n"
                        )
                        total_without_discount += dlc["initial"]
                        total_with_discount += dlc["final"]
            # en cas d'erreur de recuperation de la valeur
            else:
                result_text += f"AppID {appid} : Erreur de récupération\n"

        result_text += "\n" + "=" * 50 + "\n"
        result_text += f"💰 Total sans réduction : {total_without_discount:.2f} €\n"
        result_text += f"💸 Total avec réduction : {total_with_discount:.2f} €\n"
        self.result_area.setPlainText(result_text)

# Lancement de l’application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SteamPriceApp()
    window.show()
    sys.exit(app.exec_())
