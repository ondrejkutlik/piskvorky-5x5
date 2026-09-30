import random
import tkinter as tk

N = 15  # Veľkosť plochy N x N
CIEL = 5  # Koľko znakov v rade treba na výhru
SMERY = [(0, 1), (1, 0), (1, 1), (1, -1)]  # Vodorovne, zvislo a 2x šikmo
BUNKA = 34  # Veľkosť políčka v pixeloch

FARBY = {
    "pozadie": "#f2f4f7", "panel": "#ffffff", "text": "#172033", "sive": "#5a6478",
    "ciara": "#c5ccda", "policko": "#fbfcfe", "policko_nad": "#e3e9f8",
    "x": "#1f4bd8", "o": "#d4572a", "vyhra": "#cfeecf", "posledny": "#fff3b8",
    "akcent": "#1f4bd8", "akcent_nad": "#3a63e6", "akcent_text": "#ffffff",
}


def pozicia(r, c):
    return r * N + c


def vnutri(r, c):
    return 0 <= r < N and 0 <= c < N


def rad(plocha, r, c, z, dr, dc):
    bunky = [pozicia(r, c)]
    otvorene = 0
    for smer in (1, -1):
        rr, cc = r + dr * smer, c + dc * smer
        while vnutri(rr, cc) and plocha[pozicia(rr, cc)] == z:
            bunky.append(pozicia(rr, cc))
            rr += dr * smer
            cc += dc * smer
        if vnutri(rr, cc) and plocha[pozicia(rr, cc)] == "":
            otvorene += 1
    return bunky, otvorene


def najdi_vyhru(plocha, r, c, z):
    for dr, dc in SMERY:
        bunky, _ = rad(plocha, r, c, z, dr, dc)
        if len(bunky) >= CIEL:
            return bunky
    return None


# Hodnota radu podľa dĺžky a počtu otvorených koncov (0, 1 alebo 2)
def hodnota_radu(pocet, otvorene):
    if pocet >= CIEL:
        return 100000
    if otvorene == 0:
        return 0
    tabulka = {4: (0, 1000, 10000), 3: (0, 100, 1000), 2: (0, 10, 100), 1: (0, 1, 2)}
    return tabulka[pocet][otvorene]


# Ako dobrý by bol ťah znaku z na políčko (r, c), súčet cez všetky 4 smery
def hodnota_bodu(plocha, r, c, z):
    suma = 0
    for dr, dc in SMERY:
        bunky, otvorene = rad(plocha, r, c, z, dr, dc)
        suma += hodnota_radu(len(bunky), otvorene)
    return suma


def ma_susedov(plocha, r, c, vzdialenost):
    for dr in range(-vzdialenost, vzdialenost + 1):
        for dc in range(-vzdialenost, vzdialenost + 1):
            if vnutri(r + dr, c + dc) and plocha[pozicia(r + dr, c + dc)] != "":
                return True
    return False


def tah_pocitaca(plocha, historia):
    stred = N // 2
    if not historia:
        return pozicia(stred, stred)

    najlepsi, kandidati = float("-inf"), []
    for r in range(N):
        for c in range(N):
            if plocha[pozicia(r, c)] != "" or not ma_susedov(plocha, r, c, 2):
                continue
            # Útok (vlastné rady) a obrana (rady súpera), obrana má mierne nižšiu váhu
            skore = (hodnota_bodu(plocha, r, c, "O") + 0.9 * hodnota_bodu(plocha, r, c, "X")
                     - 0.01 * (abs(r - stred) + abs(c - stred)))  # Mierne uprednostní stred
            if skore > najlepsi + 1e-9:
                najlepsi, kandidati = skore, [pozicia(r, c)]
            elif abs(skore - najlepsi) <= 1e-9:
                kandidati.append(pozicia(r, c))
    return random.choice(kandidati)


class Piskvorky(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Piškvorky - 5 v rade")
        self.resizable(False, False)
        self.configure(bg=FARBY["pozadie"], padx=16, pady=16)

        self.skore = {"X": 0, "O": 0, "remiza": 0}
        self.rezim = "pocitac"
        self.casovac = None
        self.nad = None  # Políčko pod myšou

        ram = tk.Frame(self, bg=FARBY["panel"], padx=18, pady=14)
        ram.pack()

        tk.Label(ram, text="Piškvorky", bg=FARBY["panel"], fg=FARBY["text"],
                 font=("Segoe UI", 18, "bold")).pack()
        tk.Label(ram, text="Ako prvý spoj 5 svojich znakov v rade: vodorovne, zvislo alebo šikmo.",
                 bg=FARBY["panel"], fg=FARBY["sive"], font=("Segoe UI", 10)).pack(pady=(0, 10))

        rezimy = tk.Frame(ram, bg=FARBY["panel"])
        rezimy.pack(pady=(0, 8))
        self.tlacidla_rezimu = {}
        for kluc, popis in (("pocitac", "Proti počítaču"), ("dvaja", "Dvaja hráči")):
            t = tk.Button(rezimy, text=popis, bd=0, padx=12, pady=4, cursor="hand2",
                          font=("Segoe UI", 10), command=lambda k=kluc: self.zmen_rezim(k))
            t.pack(side="left", padx=3)
            self.tlacidla_rezimu[kluc] = t

        self.stav = tk.Label(ram, bg=FARBY["panel"], fg=FARBY["text"],
                             font=("Segoe UI", 12, "bold"))
        self.stav.pack(pady=(0, 8))

        velkost = N * BUNKA + 1
        self.platno = tk.Canvas(ram, width=velkost, height=velkost, bg=FARBY["ciara"],
                                highlightthickness=0, cursor="hand2")
        self.platno.pack()
        self.platno.bind("<Button-1>", self.klik)
        self.platno.bind("<Motion>", self.pohyb)
        self.platno.bind("<Leave>", lambda e: self.nastav_nad(None))

        self.skore_text = tk.Label(ram, bg=FARBY["panel"], fg=FARBY["sive"],
                                   font=("Segoe UI", 11))
        self.skore_text.pack(pady=10)

        akcie = tk.Frame(ram, bg=FARBY["panel"])
        akcie.pack()
        tk.Button(akcie, text="Nová hra", bd=0, padx=16, pady=6, cursor="hand2",
                  bg=FARBY["akcent"], fg=FARBY["akcent_text"],
                  activebackground=FARBY["akcent_nad"], activeforeground=FARBY["akcent_text"],
                  font=("Segoe UI", 11, "bold"), command=self.nova_hra).pack(side="left", padx=4)
        self.tlacidlo_spat = tk.Button(akcie, text="Vrátiť ťah", bd=1, relief="solid", padx=16,
                                       pady=5, cursor="hand2", bg=FARBY["panel"],
                                       fg=FARBY["text"], font=("Segoe UI", 11, "bold"),
                                       command=self.vrat_tah)
        self.tlacidlo_spat.pack(side="left", padx=4)

        self.zmen_rezim("pocitac")

    def na_tahu(self):
        return "X" if len(self.historia) % 2 == 0 else "O"

    def policko_z_bodu(self, x, y):
        r, c = int(y // BUNKA), int(x // BUNKA)
        return pozicia(r, c) if vnutri(r, c) else None

    def nastav_nad(self, i):
        if i != self.nad:
            self.nad = i
            self.vykresli()

    def pohyb(self, e):
        self.nastav_nad(self.policko_z_bodu(e.x, e.y))

    def klik(self, e):
        i = self.policko_z_bodu(e.x, e.y)
        if i is not None:
            self.tah_hraca(i)

    def zmen_rezim(self, rezim):
        self.rezim = rezim
        for kluc, t in self.tlacidla_rezimu.items():
            aktivny = kluc == rezim
            t.config(bg=FARBY["akcent"] if aktivny else FARBY["pozadie"],
                     fg=FARBY["akcent_text"] if aktivny else FARBY["sive"])
        self.skore = {"X": 0, "O": 0, "remiza": 0}
        self.aktualizuj_skore()
        self.nova_hra()

    def nova_hra(self):
        if self.casovac:
            self.after_cancel(self.casovac)
            self.casovac = None
        self.plocha = [""] * (N * N)
        self.historia = []
        self.koniec = False
        self.blokovane = False
        self.vyhra = []
        self.vykresli()
        self.stav.config(text="Na ťahu: X")

    def vykresli(self):
        p = self.platno
        p.delete("all")
        posledny = self.historia[-1] if self.historia else None
        for i in range(N * N):
            r, c = divmod(i, N)
            x, y = c * BUNKA + 1, r * BUNKA + 1
            znak = self.plocha[i]
            if i in self.vyhra:
                farba = FARBY["vyhra"]
            elif i == posledny:
                farba = FARBY["posledny"]
            elif i == self.nad and not znak and not self.koniec:
                farba = FARBY["policko_nad"]
            else:
                farba = FARBY["policko"]
            p.create_rectangle(x, y, x + BUNKA - 1, y + BUNKA - 1, fill=farba, width=0)
            if znak:
                p.create_text(x + BUNKA / 2, y + BUNKA / 2, text=znak,
                              fill=FARBY["x"] if znak == "X" else FARBY["o"],
                              font=("Segoe UI", 15, "bold"))
        vypnute = self.koniec or self.blokovane or not self.historia
        self.tlacidlo_spat.config(state="disabled" if vypnute else "normal")

    def zahraj(self, i):
        znak = self.na_tahu()
        self.plocha[i] = znak
        self.historia.append(i)
        r, c = divmod(i, N)
        vyhra = najdi_vyhru(self.plocha, r, c, znak)

        if vyhra:
            self.koniec = True
            self.vyhra = vyhra
            self.skore[znak] += 1
            self.vykresli()
            self.stav.config(text=f"Vyhráva {znak}!")
            self.aktualizuj_skore()
        elif len(self.historia) == N * N:
            self.koniec = True
            self.skore["remiza"] += 1
            self.vykresli()
            self.stav.config(text="Remíza.")
            self.aktualizuj_skore()
        else:
            self.vykresli()
            self.stav.config(text=f"Na ťahu: {self.na_tahu()}")

    def tah_hraca(self, i):
        if self.koniec or self.blokovane or self.plocha[i] != "":
            return
        self.zahraj(i)

        if self.rezim == "pocitac" and not self.koniec:
            self.blokovane = True
            self.stav.config(text="Počítač premýšľa...")
            self.vykresli()
            self.casovac = self.after(350, self.tah_pocitaca)

    def tah_pocitaca(self):
        self.casovac = None
        self.blokovane = False
        self.zahraj(tah_pocitaca(self.plocha, self.historia))

    def vrat_tah(self):
        if self.koniec or self.blokovane or not self.historia:
            return
        # Proti počítaču vraciame dvojicu ťahov, aby bol opäť na rade hráč X
        kolko = 2 if self.rezim == "pocitac" and len(self.historia) % 2 == 0 else 1
        for _ in range(min(kolko, len(self.historia))):
            self.plocha[self.historia.pop()] = ""
        self.vykresli()
        self.stav.config(text=f"Na ťahu: {self.na_tahu()}")

    def aktualizuj_skore(self):
        s = self.skore
        self.skore_text.config(text=f"X: {s['X']}      Remízy: {s['remiza']}      O: {s['O']}")


if __name__ == "__main__":
    Piskvorky().mainloop()
