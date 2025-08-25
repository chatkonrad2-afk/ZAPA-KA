import firebase_admin
from kivy.config import Config
from kivymd.app import MDApp
from datetime import datetime
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivymd.toast import toast
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.screen import MDScreen
from gcip_auth import sign_up_email_password, sign_in_email_password, lookup_user, AuthError
from firebase_rtdb import db_get, db_post, db_put, db_patch, DB_URL
import time, base64, json
from kivy.clock import Clock
from kivy.uix.screenmanager import SlideTransition
from kivymd.uix.toolbar import MDBottomAppBar
from kivymd.uix.bottomnavigation import MDBottomNavigation
from firebase_admin import credentials, db
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.list import OneLineListItem
from kivymd.uix.list import TwoLineAvatarIconListItem, IconRightWidget
from kivymd.uix.list import OneLineAvatarIconListItem
import firebase_rtdb.py
import gcip_auth.py
import main.kv
import serviceAccountKey.json



cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://creditals-469401-default-rtdb.europe-west1.firebasedatabase.app"
})

class LoginScreen(MDScreen):
    pass

class RegisterScreen(MDScreen):
    pass

class MainScreen(MDScreen):
    pass

class ChatScreen(MDScreen):
    pass


class ZapałkaApp(MDApp):
    username = StringProperty("Nieznajomy")
    user_tokens = None
    copyright_text = StringProperty(
        f"© {datetime.now().year} Zapałka. Wszelkie prawa zastrzeżone."
    )


    def build(self):
        self.theme_cls.theme_style = "Dark"
        return Builder.load_file("main.kv")

    def set_language(self, code: str):
        names = {"pl": "polski"}
        toast(f"Język ustawiony: {names.get(code, code)}")

    def open_copyright(self):
        if not hasattr(self, "_cr_dialog"):
            self._cr_dialog = MDDialog(
                title="Prawa autorskie",
                text=(f"{self.copyright_text}\n\n""Regulamin i Polityka prywatności dostępne w aplikacji."),
                buttons=[MDFlatButton(text="Zamknij",on_release=lambda *_: self._cr_dialog.dismiss())],)
        self._cr_dialog.open()

    def login(self, *args):
        try:
            scr = self.root.get_screen("login")
            username = (scr.ids.login_user.text or "").strip().lower()
            password = scr.ids.login_pass.text or ""
        except Exception:
            toast("Błąd interfejsu (login)")
            return

        if not username or not password:
            toast("Podaj nazwę i hasło")
            return

        # 🔎 wyszukaj email po nazwie użytkownika
        user_ref = db.reference(f"usernames/{username}").get()
        if not user_ref:
            toast("Nie znaleziono takiego użytkownika")
            return

        email = user_ref.get("email")
        if not email:
            toast("Brak adresu email dla użytkownika")
            return

        try:
            data = sign_in_email_password(email, password)
            self.user_tokens = {
                "idToken": data["idToken"],
                "refreshToken": data["refreshToken"],
            }

            uid = self._uid_from_idtoken(data["idToken"])
            user_data = db.reference(f"users/{uid}").get() or {}
            self.username = user_data.get("username", username)

            toast(f"Zalogowano: {self.username}")
            self.root.current = "main"
            self.rtdb_smoke_test()
        except AuthError as e:
            code = str(e)
            friendly = {
                "EMAIL_NOT_FOUND": "Nie znaleziono konta.",
                "INVALID_PASSWORD": "Nieprawidłowe hasło.",
                "USER_DISABLED": "Konto zostało wyłączone.",
            }.get(code, "Nieprawidłowe dane logowania.")
            toast(friendly)
            print("LOGIN ERROR:", code)

    def go_register(self, *args): #NOWA ZAPAŁKA AKCJA
        try:
            self.root.current = "register"
        except Exception:
            toast("Nie można przejść do ekranu rejestracji")

    def register_account(self, *args):
        """Utworzenie konta e-mail/hasło i automatyczne zalogowanie."""
        try:
            reg = self.root.get_screen("register")
            username = (reg.ids.reg_user.text or "").strip().lower()
            email = (reg.ids.reg_email.text or "").strip()
            password = reg.ids.reg_pass.text or ""
        except Exception:
            toast("Błąd interfejsu (rejestracja)")
            return

        if not username or not email or not password:
            toast("Podaj nazwę, e-mail i hasło")
            return
        if "@" not in email:
            toast("Nieprawidłowy e-mail")
            return
        if len(password) < 6:
            toast("Hasło min. 6 znaków")
            return

        try:
            data = sign_up_email_password(email, password)
            self.user_tokens = {
                "idToken": data["idToken"],
                "refreshToken": data["refreshToken"],
            }

            # UID użytkownika
            uid = self._uid_from_idtoken(data["idToken"])

            # zapisz użytkownika
            db.reference("users").child(uid).set({
                "username": username,
                "email": email,
            })

            # zapisz mapowanie username → uid + email
            db.reference("usernames").child(username).set({
                "uid": uid,
                "email": email,
            })

            self.username = username
            toast(f"Konto utworzone i zalogowano: {username}")
            self.root.current = "main"
            self.rtdb_smoke_test()
        except AuthError as e:
            toast(f"Błąd rejestracji: {e}")
            print("REGISTER ERROR:", e)

    def go_login(self, *args):
        try:
            self.root.current = "login"
        except Exception:
            from kivymd.toast import toast
            toast("Nie można przejść do ekranu logowania")

    def rtdb_smoke_test(self):
        """Zapisz testową wiadomość i sprawdź odczyt."""
        try:
            idt = self.user_tokens["idToken"]
        except Exception:
            from kivymd.toast import toast
            toast("Najpierw zaloguj się")
            return

        import time
        payload = {"text": "RTDB OK", "ts": int(time.time() * 1000)}
        db_post("messages/test", payload, idt)  # zapis pod /messages/test/<pushId>
        data = db_get("messages/test", idt) or {}

    def _uid_from_idtoken(self, idt: str):
        try:
            payload = idt.split('.')[1] + '=='
            return json.loads(base64.urlsafe_b64decode(payload.encode('ascii'))).get('sub')
        except Exception:
            return None

    def open_public_chat(self):
        """Otwórz prosty pokój 'public' i wczytaj ostatnie wiadomości."""
        self.current_conv_id = "public"
        self.root.current = "chat"
        self.load_messages()

    def _make_bubble(self, text, align="left"):
        from kivy.metrics import dp
        from kivymd.uix.label import MDLabel

        # tymczasowa etykieta do obliczenia szerokości/ wysokości
        tmp = MDLabel(text=text, text_size=(dp(250), None))
        tmp.texture_update()
        width = min(tmp.texture_size[0] + dp(30), dp(250))
        height = tmp.texture_size[1] + dp(20)

        return {
            "text": text,
            "halign": align,
            "height": height,
            "width": width,
        }

    def load_messages(self):
        """Załaduj wiadomości z aktualnego prywatnego czatu."""
        if not self.user_tokens:
            return

        idt = self.user_tokens["idToken"]
        msgs = db.reference(f"private_chats/{self.current_conv_id}/messages").get() or {}

        items = []
        my_uid = self._uid_from_idtoken(idt)

        for k in sorted(msgs.keys()):
            m = msgs[k] or {}
            items.append(self._make_bubble(
                m.get("text", ""),
                "right" if m.get("sender") == my_uid else "left"
            ))

        chat = self.root.get_screen("chat")
        chat.ids.rv.data = items

        # 🔽 po załadowaniu wiadomości przewiń na dół
        self._scroll_chat_to_bottom()

    def send_message(self, text):
        """Wyślij wiadomość do prywatnego czatu."""
        text = (text or "").strip()
        if not text:
            return

        if not self.user_tokens:
            toast("Najpierw zaloguj się")
            return

        uid = self._uid_from_idtoken(self.user_tokens["idToken"])
        payload = {"sender": uid, "text": text, "ts": int(time.time() * 1000)}

        ref = db.reference(f"private_chats/{self.current_conv_id}/messages")
        ref.push(payload)

        chat = self.root.get_screen("chat")
        chat.ids.rv.data.append(self._make_bubble(text, "right"))
        chat.ids.msg_input.text = ""

        # 🔽 przewiń na dół po wysłaniu
        self._scroll_chat_to_bottom()

    def go_main(self, *args):
        self.root.transistion = SlideTransition(direction="right", duration=.25)
        self.root.current = "main"

    _chat_poll_ev = None
    def start_chat_polling(self, *args):
        """Odświeżaj wiadomości co 2 sekundy (prosty polling)."""
        # jeśli już działa – nie uruchamiaj drugi raz
        if self._chat_poll_ev is None:
            self._chat_poll_ev = Clock.schedule_interval(lambda dt: self.load_messages(), 2)

    def stop_chat_polling(self, *args):
        """Zatrzymaj polling, gdy wychodzisz z ekranu czatu."""
        if self._chat_poll_ev:
            self._chat_poll_ev.cancel()
            self._chat_poll_ev = None

    def send_friend_request(self, sender_uid, receiver_uid):
        ts = int(time.time())  # zapisujemy timestamp (sekundy)
        ref = db.reference("friends")

        # zapisz jako dict zamiast gołego stringa
        ref.child(sender_uid).child(receiver_uid).set({
            "status": "pending",
            "ts": ts
        })
        ref.child(receiver_uid).child(sender_uid).set({
            "status": "request",
            "ts": ts
        })

    def accept_friend_request(self, user_uid, friend_uid):
        ref = db.reference("friends")
        ref.child(user_uid).child(friend_uid).update({"status": "accepted"})
        ref.child(friend_uid).child(user_uid).update({"status": "accepted"})

        # --- utwórz prywatny czat ---
        chat_id = f"chat_{user_uid}_{friend_uid}"
        chat_ref = db.reference("private_chats").child(chat_id)
        chat_ref.set({
            "members": [user_uid, friend_uid],
            "messages": {}
        })

        db.reference("user_chats").child(user_uid).child(chat_id).set(True)
        db.reference("user_chats").child(friend_uid).child(chat_id).set(True)

        toast(f"Zaakceptowano zaproszenie. \n Utworzono czat z {user_uid}")

        # 🔄 odśwież listę zaproszeń
        self.load_friend_requests()

    def decline_friend_request(self, user_uid, friend_uid):
        """Odrzuć zaproszenie do znajomych."""
        ref = db.reference("friends")
        ref.child(user_uid).child(friend_uid).delete()
        ref.child(friend_uid).child(user_uid).delete()
        toast("Odrzucono zaproszenie")

        # 🔄 odśwież listę zaproszeń
        self.load_friend_requests()

    def show_invite_friend_dialog(self):
        content = MDBoxLayout(orientation="vertical", spacing="12dp", padding="12dp")
        self.invite_field = MDTextField(
            hint_text="Podaj UID znajomego",
            size_hint_x=1
        )
        content.add_widget(self.invite_field)

        self._invite_dialog = MDDialog(
            title="Zaproś znajomego",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Anuluj", on_release=lambda x: self._invite_dialog.dismiss()),
                MDFlatButton(text="Wyślij", on_release=lambda x: self.send_invite()),
            ],
        )
        self._invite_dialog.open()

    def send_invite(self):
        if not hasattr(self, "user_tokens"):
            toast("Najpierw zaloguj się")
            return

        friend_uid = self.invite_field.text.strip()
        if not friend_uid:
            toast("Podaj UID znajomego")
            return

        my_uid = self._uid_from_idtoken(self.user_tokens["idToken"])
        self.send_friend_request(my_uid, friend_uid)

        toast(f"Wysłano zaproszenie do {friend_uid}")
        self._invite_dialog.dismiss()

    def _scroll_chat_to_bottom(self):
        """Przewiń RecycleView czatu na dół."""
        chat = self.root.get_screen("chat")
        rv = chat.ids.rv
        if rv.data:
            # 🔽 ustawienie scrolla na sam dół po klatce
            Clock.schedule_once(lambda dt: setattr(rv, "scroll_y", 0))

    def remove_chat(self, chat_id):
        """Usuń czat (z bazy i z listy)."""
        if not self.user_tokens:
            toast("Najpierw zaloguj się")
            return

        my_uid = self._uid_from_idtoken(self.user_tokens["idToken"])
        try:
            # usuń z /user_chats
            db.reference(f"user_chats/{my_uid}/{chat_id}").delete()
            # opcjonalnie usuń cały czat (jeśli chcesz usuwać globalnie)
            # db.reference(f"private_chats/{chat_id}").delete()

            toast("Czat usunięty")
            self.load_private_chats()
        except Exception as e:
            toast(f"Błąd przy usuwaniu: {e}")

    def on_enter(self):
        app = MDApp.get_running_app()
        app.load_private_chats()

    def remove_chat(self, chat_id):
        """Usuń czat z listy i bazy."""
        my_uid = self._uid_from_idtoken(self.user_tokens["idToken"])
        db.reference(f"user_chats/{my_uid}/{chat_id}").delete()
        toast("Czat usunięty")
        self.load_private_chats()


    def open_private_chat(self, chat_id, friend_name):
        """Otwórz prywatny czat."""
        self.current_conv_id = chat_id
        self.root.current = "chat"
        self.root.get_screen("chat").ids.topbar.title = friend_name
        self.load_messages()

    def search_user_by_username(self, username):
        ref = db.reference("users")
        users = ref.get() or {}
        for uid, data in users.items():
            if data.get("username", "").lower() == username.lower():
                return uid, data
        return None, None

    def search_friend(self, username):
        """Wywoływane z pola tekstowego w zakładce Szukaj."""
        uid, data = self.search_user_by_username(username)
        results = self.root.get_screen("main").ids.search_results
        results.clear_widgets()

        if not uid:
            results.add_widget(OneLineListItem(text="Nie znaleziono użytkownika"))
            return

        # pokaż znalezionego usera
        results.add_widget(
            OneLineListItem(
                text=f"{data.get('username')}",
                on_release=lambda x: self._invite_by_uid(uid)
            )
        )

    def get_user_chats(self):
        """Pobierz listę prywatnych czatów użytkownika."""
        my_uid = self._uid_from_idtoken(self.user_tokens["idToken"])
        chats = db.reference(f"user_chats/{my_uid}").get() or {}

        result = {}
        for cid in chats.keys():
            chat_data = db.reference(f"private_chats/{cid}").get() or {}
            # znajdź UID znajomego
            members = chat_data.get("members", [])
            friend_uid = [u for u in members if u != my_uid][0]
            friend_data = db.reference(f"users/{friend_uid}").get() or {}
            result[cid] = friend_data.get("username", friend_uid)
        return result

    def load_private_chats(self, *args):
        chat_list = self.root.get_screen("main").ids.private_chats
        chat_list.clear_widgets()

        chats = self.get_user_chats()
        for cid, fname in chats.items():
            item = OneLineAvatarIconListItem(
                text=fname,
                on_release=lambda x, cid=cid, fname=fname: self.open_private_chat(cid, fname)
            )

            remove_btn = IconRightWidget(icon="close")
            remove_btn.bind(on_release=lambda btn, cid=cid: self.remove_chat(cid))

            item.add_widget(remove_btn)
            chat_list.add_widget(item)

    def _invite_by_uid(self, friend_uid):
        if not self.user_tokens:
            toast("Najpierw zaloguj się")
            return

        my_uid = self._uid_from_idtoken(self.user_tokens["idToken"])
        existing = db.reference(f"friends/{my_uid}/{friend_uid}").get()

        # jeżeli już zaakceptowane → blokada
        if isinstance(existing, dict) and existing.get("status") == "accepted":
            toast("Utworzono już czat z tym użytkownikiem!")
            return
        if isinstance(existing, dict) and existing.get("status") in ("pending", "request"):
            toast("Zaproszenie już wysłane!")
            return

        self.send_friend_request(my_uid, friend_uid)

        user_data = db.reference(f"users/{friend_uid}").get() or {}
        uname = user_data.get("username", friend_uid)
        toast(f"Wysłano zaproszenie do {uname}")

    def load_friend_requests(self):
        if not self.user_tokens:
            return
        my_uid = self._uid_from_idtoken(self.user_tokens["idToken"])
        ref = db.reference(f"friends/{my_uid}")
        friends = ref.get() or {}

        results = self.root.get_screen("main").ids.friend_requests
        results.clear_widgets()

        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.label import MDLabel
        from kivymd.uix.button import MDIconButton
        import datetime

        for fid, data in friends.items():
            if not isinstance(data, dict):
                continue
            if data.get("status") == "request":
                user_data = db.reference(f"users/{fid}").get() or {}
                uname = user_data.get("username", fid)

                ts = data.get("ts", 0)
                date_str = datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else ""

                # 🔥 Własny wiersz z tekstem + przyciskami
                row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height="60dp", padding="8dp",
                                  spacing="8dp")

                # Tekst po lewej
                row.add_widget(MDLabel(
                    text=f"Zaproszenie od {uname}\n{date_str}",
                    halign="left",
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1)
                ))

                # ✅ Akceptuj
                row.add_widget(MDIconButton(
                    icon="check",
                    theme_text_color="Custom",
                    text_color=(0, 1, 0, 1),
                    on_release=lambda x, f=fid: self.accept_friend_request(my_uid, f)
                ))

                # ❌ Odrzuć
                row.add_widget(MDIconButton(
                    icon="close",
                    theme_text_color="Custom",
                    text_color=(1, 0, 0, 1),
                    on_release=lambda x, f=fid: self.decline_friend_request(my_uid, f)
                ))

                results.add_widget(row)



if __name__ == "__main__":
    Window.size = (360, 640)
    ZapałkaApp().run()
