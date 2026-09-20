from datetime import datetime
import csv
import os
import sqlite3

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput


APP_TITLE = "QSO Logg"


class Database:
    def __init__(self, path):
        self.path = path
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS qso (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datum TEXT NOT NULL,
                tid TEXT NOT NULL,
                signal TEXT,
                sent TEXT,
                mottaget TEXT,
                frekvens TEXT,
                kommentar TEXT
            )
        """)

        self.conn.commit()

    def add(self, datum, tid, signal, sent, mottaget, frekvens, kommentar):
        self.conn.execute("""
            INSERT INTO qso
            (datum, tid, signal, sent, mottaget, frekvens, kommentar)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datum,
            tid,
            signal,
            sent,
            mottaget,
            frekvens,
            kommentar
        ))

        self.conn.commit()

    def all(self, search=""):
        if search.strip():
            q = f"%{search.strip()}%"

            return self.conn.execute("""
                SELECT * FROM qso
                WHERE datum LIKE ? OR tid LIKE ? OR signal LIKE ?
                   OR sent LIKE ? OR mottaget LIKE ?
                   OR frekvens LIKE ? OR kommentar LIKE ?
                ORDER BY id DESC
            """, (
                q,
                q,
                q,
                q,
                q,
                q,
                q
            )).fetchall()

        return self.conn.execute(
            "SELECT * FROM qso ORDER BY id DESC"
        ).fetchall()

    def delete(self, row_id):
        self.conn.execute(
            "DELETE FROM qso WHERE id=?",
            (row_id,)
        )

        self.conn.commit()

    def update(
        self,
        row_id,
        datum,
        tid,
        signal,
        sent,
        mottaget,
        frekvens,
        kommentar
    ):
        self.conn.execute("""
            UPDATE qso
            SET datum=?,
                tid=?,
                signal=?,
                sent=?,
                mottaget=?,
                frekvens=?,
                kommentar=?
            WHERE id=?
        """, (
            datum,
            tid,
            signal,
            sent,
            mottaget,
            frekvens,
            kommentar,
            row_id
        ))

        self.conn.commit()

    def close(self):
        self.conn.close()


class QSOForm(BoxLayout):

    def __init__(self, app, row=None, **kwargs):

        super().__init__(
            orientation="vertical",
            spacing=dp(7),
            padding=dp(10),
            **kwargs
        )

        self.app = app
        self.row = row
        self.fields = {}

        now = datetime.now()

        # ------------------------------------------------
        # Standardvärden
        # ------------------------------------------------

        defaults = {
            "Datum": (
                row["datum"]
                if row
                else now.strftime("%Y-%m-%d")
            ),

            "Tid": (
                row["tid"]
                if row
                else now.strftime("%H:%M")
            ),

            "Signal": (
                row["signal"]
                if row
                else ""
            ),

            "Sent": (
                row["sent"]
                if row
                else ""
            ),

            "Mottaget": (
                row["mottaget"]
                if row
                else ""
            ),

            "Frekvens": (
                row["frekvens"]
                if row
                else ""
            ),

            "Kommentar": (
                row["kommentar"]
                if row
                else ""
            ),
        }

        # ------------------------------------------------
        # Skapa alla fält
        # ------------------------------------------------

        for name in defaults:

            line = BoxLayout(
                size_hint_y=None,
                height=dp(42),
                spacing=dp(6)
            )

            label = Label(
                text=name,
                size_hint_x=0.30
            )

            line.add_widget(label)

            ti = TextInput(
                text=defaults[name],
                multiline=False,
                size_hint_x=0.70,
                write_tab=False
            )

            self.fields[name] = ti

            line.add_widget(ti)

            self.add_widget(line)

        # ------------------------------------------------
        # ENTER = nästa fält
        # ------------------------------------------------

        field_names = list(defaults.keys())

        for index, name in enumerate(field_names):

            field = self.fields[name]

            if index < len(field_names) - 1:

                next_field = self.fields[
                    field_names[index + 1]
                ]

                def go_next(
                    instance,
                    next_field=next_field
                ):
                    next_field.focus = True

                    # Markera eventuell befintlig text
                    next_field.select_all()

                field.bind(
                    on_text_validate=go_next
                )

            else:

                # ----------------------------------------
                # ENTER i Kommentar = Spara
                # ----------------------------------------

                field.bind(
                    on_text_validate=self.save
                )

        # ------------------------------------------------
        # Knappar
        # ------------------------------------------------

        buttons = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(8)
        )

        save = Button(
            text="Spara QSO"
        )

        cancel = Button(
            text="Avbryt"
        )

        save.bind(
            on_release=self.save
        )

        cancel.bind(
            on_release=lambda *_:
            self.app.close_popup()
        )

        buttons.add_widget(save)
        buttons.add_widget(cancel)

        self.add_widget(buttons)

        # ------------------------------------------------
        # Sätt fokus på Signal
        # ------------------------------------------------

        # Vi väntar tills popupen har öppnats innan fokus
        # sätts. Detta fungerar bättre framför allt på Android.

        Clock.schedule_once(
            self.focus_signal,
            0.2
        )

    # ====================================================
    # Fokusera Signal
    # ====================================================

    def focus_signal(self, *_):

        if "Signal" in self.fields:

            self.fields["Signal"].focus = True

            # Om det redan finns text, markera den
            self.fields["Signal"].select_all()

    # ====================================================
    # SPARA QSO
    # ====================================================

    def save(self, *_):

        v = {
            k: field.text.strip()
            for k, field in self.fields.items()
        }

        # ------------------------------------------------
        # Kontrollera datum och tid
        # ------------------------------------------------

        if not v["Datum"]:

            self.app.info(
                "Datum måste fyllas i."
            )

            return

        if not v["Tid"]:

            self.app.info(
                "Tid måste fyllas i."
            )

            return

        # ------------------------------------------------
        # REDIGERA BEFINTLIGT QSO
        # ------------------------------------------------

        if self.row:

            self.app.db.update(
                self.row["id"],
                v["Datum"],
                v["Tid"],
                v["Signal"],
                v["Sent"],
                v["Mottaget"],
                v["Frekvens"],
                v["Kommentar"]
            )

            # Stäng redigeringsfönstret
            self.app.close_popup()

            # Uppdatera listan
            self.app.refresh()

        # ------------------------------------------------
        # NYTT QSO
        # ------------------------------------------------

        else:

            self.app.db.add(
                v["Datum"],
                v["Tid"],
                v["Signal"],
                v["Sent"],
                v["Mottaget"],
                v["Frekvens"],
                v["Kommentar"]
            )

            # Stäng det gamla formuläret
            self.app.close_popup()

            # Uppdatera QSO-listan
            self.app.refresh()

            # --------------------------------------------
            # ÖPPNA AUTOMATISKT ETT NYTT QSO
            # --------------------------------------------

            # Lite fördröjning behövs så att Android/Kivy
            # hinner stänga föregående popup innan den
            # nya öppnas.

            Clock.schedule_once(
                lambda dt: self.new_qso_after_save(),
                0.15
            )

    # ====================================================
    # Öppna nytt QSO efter sparning
    # ====================================================

    def new_qso_after_save(self):

        self.app.new_qso()


class QSOLogApp(App):

    title = APP_TITLE

    # ====================================================
    # STARTA APPEN
    # ====================================================

    def build(self):

        self.db = Database(
            os.path.join(
                self.user_data_dir,
                "qso_logg.db"
            )
        )

        root = BoxLayout(
            orientation="vertical",
            padding=dp(8),
            spacing=dp(7)
        )

        # ------------------------------------------------
        # Huvudknappar
        # ------------------------------------------------

        header = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            spacing=dp(7)
        )

        new_btn = Button(
            text="+ Nytt QSO"
        )

        new_btn.bind(
            on_release=lambda *_:
            self.new_qso()
        )

        export_btn = Button(
            text="Exportera CSV"
        )

        export_btn.bind(
            on_release=lambda *_:
            self.export_csv()
        )

        header.add_widget(new_btn)
        header.add_widget(export_btn)

        root.add_widget(header)

        # ------------------------------------------------
        # Sökfält
        # ------------------------------------------------

        self.search = TextInput(
            hint_text=(
                "Sök på frekvens, datum, "
                "signal, kommentar..."
            ),
            multiline=False,
            size_hint_y=None,
            height=dp(42)
        )

        self.search.bind(
            text=lambda *_:
            self.refresh()
        )

        root.add_widget(self.search)

        # ------------------------------------------------
        # QSO-lista
        # ------------------------------------------------

        self.list_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(5)
        )

        self.list_box.bind(
            minimum_height=self.list_box.setter("height")
        )

        scroll = ScrollView()

        scroll.add_widget(
            self.list_box
        )

        root.add_widget(scroll)

        # ------------------------------------------------
        # Visa befintliga QSO
        # ------------------------------------------------

        self.refresh()

        return root

    # ====================================================
    # UPPDATERA QSO-LISTAN
    # ====================================================

    def refresh(self):

        if not hasattr(self, "list_box"):
            return

        self.list_box.clear_widgets()

        rows = self.db.all(
            self.search.text
            if hasattr(self, "search")
            else ""
        )

        # ------------------------------------------------
        # Inga QSO
        # ------------------------------------------------

        if not rows:

            self.list_box.add_widget(
                Label(
                    text="Inga QSO registrerade.",
                    size_hint_y=None,
                    height=dp(45)
                )
            )

            return

        # ------------------------------------------------
        # Visa QSO
        # ------------------------------------------------

        for r in rows:

            text = (
                f"{r['datum']}  "
                f"{r['tid']}   "
                f"{r['frekvens'] or '-'}   "
                f"Sent {r['sent'] or '-'} / "
                f"Mott {r['mottaget'] or '-'}"
            )

            if r["signal"]:

                text += (
                    f"\nSignal: {r['signal']}"
                )

            if r["kommentar"]:

                text += (
                    f"\n{r['kommentar']}"
                )

            btn = Button(
                text=text,
                size_hint_y=None,
                height=dp(78),
                halign="left",
                valign="middle"
            )

            btn.bind(
                on_release=lambda _, row=r:
                self.edit_qso(row)
            )

            self.list_box.add_widget(btn)

    # ====================================================
    # NYTT QSO
    # ====================================================

    def new_qso(self):

        # Säkerställ att eventuell gammal popup
        # är stängd innan en ny öppnas.

        if hasattr(self, "popup") and self.popup:

            try:
                self.popup.dismiss()
            except Exception:
                pass

            self.popup = None

        content = QSOForm(
            self
        )

        self.popup = Popup(
            title="Nytt QSO",
            content=content,
            size_hint=(0.95, 0.90),
            auto_dismiss=False
        )

        self.popup.open()

    # ====================================================
    # REDIGERA QSO
    # ====================================================

    def edit_qso(self, row):

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(6),
            padding=dp(8)
        )

        form = QSOForm(
            self,
            row=row
        )

        content.add_widget(
            form
        )

        delete_btn = Button(
            text="Radera detta QSO",
            size_hint_y=None,
            height=dp(44)
        )

        delete_btn.bind(
            on_release=lambda *_:
            self.confirm_delete(row["id"])
        )

        content.add_widget(
            delete_btn
        )

        self.popup = Popup(
            title="Redigera QSO",
            content=content,
            size_hint=(0.95, 0.95),
            auto_dismiss=False
        )

        self.popup.open()

    # ====================================================
    # BEKRÄFTA RADERING
    # ====================================================

    def confirm_delete(self, row_id):

        box = BoxLayout(
            orientation="vertical",
            spacing=dp(8),
            padding=dp(10)
        )

        box.add_widget(
            Label(
                text="Vill du verkligen radera QSO:t?"
            )
        )

        buttons = BoxLayout(
            size_hint_y=None,
            height=dp(45),
            spacing=dp(8)
        )

        yes = Button(
            text="Ja, radera"
        )

        no = Button(
            text="Avbryt"
        )

        buttons.add_widget(
            yes
        )

        buttons.add_widget(
            no
        )

        box.add_widget(
            buttons
        )

        p = Popup(
            title="Bekräfta",
            content=box,
            size_hint=(0.8, 0.35)
        )

        def delete_and_close(*_):

            self.db.delete(
                row_id
            )

            p.dismiss()

            self.close_popup()

            self.refresh()

        yes.bind(
            on_release=delete_and_close
        )

        no.bind(
            on_release=p.dismiss
        )

        p.open()

    # ====================================================
    # STÄNG POPUP
    # ====================================================

    def close_popup(self):

        if hasattr(self, "popup") and self.popup:

            try:
                self.popup.dismiss()
            except Exception:
                pass

            self.popup = None

    # ====================================================
    # INFORMATION
    # ====================================================

    def info(self, message):

        Popup(
            title="Information",
            content=Label(
                text=message
            ),
            size_hint=(0.8, 0.3)
        ).open()

    # ====================================================
    # EXPORTERA CSV
    # ====================================================

    def export_csv(self):

        path = os.path.join(
            self.user_data_dir,
            "qso_logg_export.csv"
        )

        rows = self.db.all()

        with open(
            path,
            "w",
            newline="",
            encoding="utf-8-sig"
        ) as f:

            writer = csv.writer(
                f,
                delimiter=";"
            )

            writer.writerow([
                "Datum",
                "Tid",
                "Signal",
                "Sent",
                "Mottaget",
                "Frekvens",
                "Kommentar"
            ])

            for r in rows:

                writer.writerow([
                    r["datum"],
                    r["tid"],
                    r["signal"],
                    r["sent"],
                    r["mottaget"],
                    r["frekvens"],
                    r["kommentar"]
                ])

        self.info(
            f"CSV skapad:\n{path}"
        )

    # ====================================================
    # AVSLUTA APPEN
    # ====================================================

    def on_stop(self):

        self.db.close()


# ========================================================
# START
# ========================================================

if __name__ == "__main__":

    QSOLogApp().run()