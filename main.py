from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.metrics import dp, sp
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line, Triangle

try:
    from jnius import autoclass
except Exception:
    autoclass = None

Window.clearcolor = (0.02, 0.02, 0.03, 1)

# ---------------------------------------------------------------
# Gestion infrarouge
# ---------------------------------------------------------------
_ir_manager = None


def get_ir_manager():
    """Retourne le ConsumerIrManager (ou None)."""
    global _ir_manager
    if _ir_manager is not None:
        return _ir_manager
    if autoclass is None:
        return None
    try:
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        Context = autoclass("android.content.Context")
        activity = PythonActivity.mActivity
        _ir_manager = activity.getSystemService(Context.CONSUMER_IR_SERVICE)
    except Exception:
        _ir_manager = None
    return _ir_manager


def verifier_infrarouge():
    if autoclass is None:
        return "Bibliothèque Android indisponible"
    try:
        manager = get_ir_manager()
        if manager is None:
            return "Service infrarouge introuvable"
        if manager.hasIrEmitter():
            return "Émetteur IR détecté"
        return "Aucun émetteur IR détecté"
    except Exception as erreur:
        return f"Erreur IR : {erreur}"


# Codes Samsung (protocole 32 bits, porteuse 38 kHz).
# À adapter si votre appareil (TV / clim AC-42) utilise d'autres codes.
CODES = {
    "POWER": 0xE0E040BF, "SOURCE": 0xE0E0807F,
    "1": 0xE0E020DF, "2": 0xE0E0A05F, "3": 0xE0E0609F,
    "4": 0xE0E010EF, "5": 0xE0E0906F, "6": 0xE0E050AF,
    "7": 0xE0E030CF, "8": 0xE0E0B04F, "9": 0xE0E0708F,
    "0": 0xE0E08877, "-": 0xE0E0C43B, "E": 0xE0E0F00F,
    "VOL +": 0xE0E0E01F, "VOL −": 0xE0E0D02F, "MUTE": 0xE0E0F00F,
    "CH +": 0xE0E048B7, "CH −": 0xE0E008F7,
    "LIST": 0xE0E0D629, "INFO": 0xE0E0F807, "GUIDE": 0xE0E0F20D,
    "MENU": 0xE0E058A7, "SMART HUB": 0xE0E09E61, "TOOLS": 0xE0E0D22D,
    "HAUT": 0xE0E006F9, "BAS": 0xE0E08679,
    "GAUCHE": 0xE0E0A659, "DROITE": 0xE0E046B9, "OK": 0xE0E016E9,
    "RETURN": 0xE0E01AE5, "EXIT": 0xE0E0B44B,
    "A": 0xE0E036C9, "B": 0xE0E028D7, "C": 0xE0E0A857, "D": 0xE0E06897,
    "REW": 0xE0E0A25D, "PLAY / PAUSE": 0xE0E0E21D, "FF": 0xE0E012ED,
    "STOP": 0xE0E0629D,
}


def construire_motif(code):
    """Convertit un code 32 bits en motif de durées (µs), LSB first."""
    motif = [4500, 4500]
    for i in range(32):
        bit = (code >> (31 - i)) & 1
        motif.append(560)
        motif.append(1690 if bit else 560)
    motif.append(560)
    return motif


def envoyer_ir(nom, label_statut=None):
    code = CODES.get(nom)
    if code is None:
        message = f"{nom} : code non défini"
    else:
        try:
            manager = get_ir_manager()
            if manager is None or not manager.hasIrEmitter():
                message = "Pas d'émetteur IR"
            else:
                manager.transmit(38000, construire_motif(code))
                message = f"Envoyé : {nom}"
        except Exception as erreur:
            message = f"Erreur : {erreur}"
    if label_statut is not None:
        label_statut.text = message


# ---------------------------------------------------------------
# Widgets : style télécommande réelle
# ---------------------------------------------------------------
DARK = (0.17, 0.18, 0.20, 1)
RING = (0.50, 0.52, 0.57, 1)
WHITE = (1, 1, 1, 1)
RED = (0.80, 0.13, 0.14, 1)
BLUE = (0.12, 0.40, 0.78, 1)
GREEN = (0.14, 0.60, 0.30, 1)
YELLOW = (0.85, 0.62, 0.10, 1)


def eclaircir(c, d=0.18):
    return (min(c[0] + d, 1), min(c[1] + d, 1), min(c[2] + d, 1), c[3])


class RemoteKey(Button):
    """Bouton rond ou en pilule, avec contour (cerclé)."""

    def __init__(self, text="", forme="pill", fill=DARK, ring=RING,
                 fs=11, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.background_normal = ""
        self.background_down = ""
        self.background_color = (0, 0, 0, 0)
        self.color = WHITE
        self.font_size = sp(fs)
        self.bold = True
        self.halign = "center"
        self.forme = forme
        self.fill = fill

        with self.canvas.before:
            self._cfill = Color(*fill)
            self._body = Ellipse() if forme == "circle" else RoundedRectangle()
            Color(*ring)
            self._line = Line(width=dp(1.3))

        self.bind(pos=self._redraw, size=self._redraw, state=self._etat)

    def _redraw(self, *args):
        w, h = self.size
        if self.forme == "circle":
            d = min(w, h) * 0.92
            x, y = self.center_x - d / 2, self.center_y - d / 2
            self._body.pos = (x, y)
            self._body.size = (d, d)
            self._line.ellipse = (x, y, d, d)
        else:
            ww = w * 0.94
            hh = min(h * 0.78, dp(38))
            x, y = self.center_x - ww / 2, self.center_y - hh / 2
            self._body.pos = (x, y)
            self._body.size = (ww, hh)
            self._body.radius = [hh / 2]
            self._line.rounded_rectangle = (x, y, ww, hh, hh / 2)

    def _etat(self, *args):
        self._cfill.rgba = eclaircir(self.fill) if self.state == "down" \
            else self.fill


def bouton_transparent(text="", fs=18, **kwargs):
    return Button(
        text=text,
        background_normal="", background_down="",
        background_color=(0, 0, 0, 0),
        color=WHITE, font_size=sp(fs), bold=True, **kwargs
    )


class Rocker(BoxLayout):
    """Bascule verticale + / - (volume, chaînes)."""

    def __init__(self, titre, nom_plus, nom_moins, envoyer, **kwargs):
        super().__init__(orientation="vertical", **kwargs)
        with self.canvas.before:
            Color(*DARK)
            self._body = RoundedRectangle()
            Color(*RING)
            self._line = Line(width=dp(1.3))
        self.bind(pos=self._redraw, size=self._redraw)

        plus = bouton_transparent("+")
        plus.bind(on_release=lambda b: envoyer(nom_plus))
        moins = bouton_transparent("\u2212")
        moins.bind(on_release=lambda b: envoyer(nom_moins))

        self.add_widget(plus)
        self.add_widget(Label(text=titre, font_size=sp(10), bold=True,
                              color=(0.7, 0.72, 0.78, 1), size_hint_y=0.6))
        self.add_widget(moins)

    def _redraw(self, *args):
        x, y = self.pos
        w, h = self.size
        self._body.pos = (x, y)
        self._body.size = (w, h)
        self._body.radius = [w / 2]
        self._line.rounded_rectangle = (x, y, w, h, w / 2)


class DPad(FloatLayout):
    """Croix directionnelle circulaire avec OK au centre."""

    def __init__(self, envoyer, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*DARK)
            self._disque = Ellipse()
            Color(*RING)
            self._cercle = Line(width=dp(1.3))
        with self.canvas.after:
            Color(*WHITE)
            self._tri = [Triangle() for _ in range(4)]
        self.bind(pos=self._redraw, size=self._redraw)

        zones = [("HAUT", 0.5, 0.83), ("BAS", 0.5, 0.17),
                 ("GAUCHE", 0.17, 0.5), ("DROITE", 0.83, 0.5)]
        for nom, cx, cy in zones:
            b = bouton_transparent(
                size_hint=(0.32, 0.32),
                pos_hint={"center_x": cx, "center_y": cy}
            )
            b.bind(on_release=lambda _b, n=nom: envoyer(n))
            self.add_widget(b)

        ok = RemoteKey("OK", "circle", fill=BLUE, ring=eclaircir(BLUE, 0.3),
                       fs=13, size_hint=(0.36, 0.36),
                       pos_hint={"center_x": 0.5, "center_y": 0.5})
        ok.bind(on_release=lambda _b: envoyer("OK"))
        self.add_widget(ok)

    def _redraw(self, *args):
        d = min(self.size)
        cx, cy = self.center
        r = d / 2
        self._disque.pos = (cx - r, cy - r)
        self._disque.size = (d, d)
        self._cercle.ellipse = (cx - r, cy - r, d, d)
        s, o = d * 0.05, d * 0.33
        pts = [
            [cx - s, cy + o - s, cx + s, cy + o - s, cx, cy + o + s],
            [cx - s, cy - o + s, cx + s, cy - o + s, cx, cy - o - s],
            [cx - o + s, cy - s, cx - o + s, cy + s, cx - o - s, cy],
            [cx + o - s, cy - s, cx + o - s, cy + s, cx + o + s, cy],
        ]
        for tri, p in zip(self._tri, pts):
            tri.points = p


class RemoteBody(BoxLayout):
    """Boîtier de la télécommande."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0.10, 0.10, 0.12, 1)
            self._body = RoundedRectangle(radius=[dp(30)])
            Color(0.32, 0.33, 0.37, 1)
            self._line = Line(width=dp(1.5))
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *args):
        self._body.pos = self.pos
        self._body.size = self.size
        self._line.rounded_rectangle = (*self.pos, *self.size, dp(30))


class YaDeRemote(App):

    def build(self):
        outer = BoxLayout(padding=dp(6))
        corps = RemoteBody(orientation="vertical",
                           padding=[dp(14), dp(14)], spacing=dp(2))
        outer.add_widget(corps)

        def envoyer(nom):
            envoyer_ir(nom, self.statut)

        def touche(nom, forme="pill", fill=DARK, ring=RING,
                   texte=None, fs=11):
            k = RemoteKey(texte or nom, forme, fill, ring, fs)
            k.bind(on_release=lambda _b, n=nom: envoyer(n))
            return k

        def couleur(nom, c):
            return touche(nom, "pill", c, eclaircir(c, 0.25))

        def ligne(widgets, cols, poids):
            g = GridLayout(cols=cols, spacing=dp(2), size_hint_y=poids)
            for w in widgets:
                g.add_widget(w)
            corps.add_widget(g)

        # En-tête
        corps.add_widget(Label(
            text="[b]YA DE REMOTE[/b]  [size=11sp]ACTIVE COOL AC-42[/size]",
            markup=True, color=(0.30, 0.65, 1, 1),
            font_size=sp(18), size_hint_y=0.6
        ))
        self.statut = Label(
            text=verifier_infrarouge(),
            color=(0.30, 0.85, 0.45, 1),
            font_size=sp(11), size_hint_y=0.4
        )
        corps.add_widget(self.statut)

        # Power / Source
        ligne([touche("POWER", "circle", RED, eclaircir(RED, 0.3), fs=10),
               touche("SOURCE")], 2, 1)

        # Pavé numérique
        ligne([touche(n, "circle", fs=14) for n in
               ["1", "2", "3", "4", "5", "6", "7", "8", "9", "-", "0", "E"]],
              3, 4)

        # Volume / chaînes
        vc = BoxLayout(size_hint_y=2.6)
        for titre, p, m in (("VOL", "VOL +", "VOL \u2212"),
                            ("CH", "CH +", "CH \u2212")):
            holder = AnchorLayout()
            holder.add_widget(Rocker(titre, p, m, envoyer,
                                     size_hint=(None, 0.95), width=dp(54)))
            if titre == "VOL":
                vc.add_widget(holder)
                mid = GridLayout(cols=2, spacing=dp(2), size_hint_x=2.6)
                for n in ["MUTE", "INFO", "LIST", "GUIDE"]:
                    mid.add_widget(touche(n, fs=10))
                vc.add_widget(mid)
            else:
                vc.add_widget(holder)
        corps.add_widget(vc)

        # Smart TV
        ligne([touche("MENU", fs=10), touche("SMART HUB", fs=10),
               touche("TOOLS", fs=10)], 3, 0.9)

        # Croix directionnelle
        holder = AnchorLayout(size_hint_y=3.8)
        pad = DPad(envoyer, size_hint=(None, None))
        holder.bind(size=lambda inst, v: setattr(
            pad, "size", (min(v) * 0.98, min(v) * 0.98)))
        holder.add_widget(pad)
        corps.add_widget(holder)

        # Return / Exit
        ligne([touche("RETURN", fs=10), touche("EXIT", fs=10)], 2, 0.9)

        # Touches couleur
        ligne([couleur("A", RED), couleur("B", BLUE),
               couleur("C", GREEN), couleur("D", YELLOW)], 4, 0.8)

        # Multimédia
        ligne([touche("REW", fs=10),
               touche("PLAY / PAUSE", texte="PLAY", fs=10),
               touche("FF", fs=10), touche("STOP", fs=10)], 4, 0.9)

        return outer


if __name__ == "__main__":
    YaDeRemote().run()
