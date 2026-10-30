from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from threading import Thread
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json, sqlite3, os, socket, secrets, urllib.request, urllib.error, time

APP_DIR = os.path.join(os.path.expanduser("~"), ".mesa_rpg")
os.makedirs(APP_DIR, exist_ok=True)
DB_PATH = os.path.join(APP_DIR, "mesa_rpg.sqlite3")
PORT = 8765

KV = """
ScreenManager:
    HomeScreen:
    JoinScreen:
    TableScreen:
    EditorScreen:

<HomeScreen>:
    name: "home"
    BoxLayout:
        orientation: "vertical"
        padding: "24dp"
        spacing: "14dp"
        canvas.before:
            Color:
                rgba: 0.035, 0.07, 0.06, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: "[b]MESA RPG[/b]"
            markup: True
            font_size: "30sp"
            size_hint_y: .2
        Label:
            text: "Fichas de personagem • Mesa local"
            size_hint_y: .12
        Button:
            text: "Criar / hospedar mesa"
            size_hint_y: .16
            on_release: app.host_table()
        Button:
            text: "Entrar em uma mesa"
            size_hint_y: .16
            on_release: app.root.current = "join"
        Label:
            id: status
            text: "Os aparelhos devem estar na mesma rede Wi-Fi."
            size_hint_y: .2

<JoinScreen>:
    name: "join"
    BoxLayout:
        orientation: "vertical"
        padding: "22dp"
        spacing: "12dp"
        Label:
            text: "[b]Entrar na mesa[/b]"
            markup: True
            font_size: "24sp"
            size_hint_y: .18
        TextInput:
            id: address
            hint_text: "IP do mestre (ex.: 192.168.1.20)"
            multiline: False
            size_hint_y: None
            height: "48dp"
        TextInput:
            id: access_code
            hint_text: "Código de acesso da mesa"
            multiline: False
            password: True
            size_hint_y: None
            height: "48dp"
        Button:
            text: "Conectar"
            size_hint_y: None
            height: "48dp"
            on_release: app.join_table(root.ids.address.text, root.ids.access_code.text)
        Label:
            id: result
            text: ""
        Button:
            text: "Voltar"
            size_hint_y: None
            height: "48dp"
            on_release: app.root.current = "home"

<TableScreen>:
    name: "table"
    BoxLayout:
        orientation: "vertical"
        padding: "18dp"
        spacing: "10dp"
        Label:
            text: "[b]Mesa RPG[/b]"
            markup: True
            font_size: "25sp"
            size_hint_y: .12
        Label:
            id: host_address
            text: ""
            size_hint_y: .12
        Button:
            text: "Nova ficha"
            size_hint_y: None
            height: "48dp"
            on_release: app.new_sheet()
        Button:
            text: "Atualizar fichas"
            size_hint_y: None
            height: "44dp"
            on_release: app.refresh_sheets()
        ScrollView:
            do_scroll_x: False
            GridLayout:
                id: sheet_list
                cols: 1
                spacing: "6dp"
                size_hint_y: None
                height: self.minimum_height
        Button:
            text: "Desconectar / parar hospedagem"
            size_hint_y: None
            height: "46dp"
            on_release: app.stop_host()

<EditorScreen>:
    name: "editor"
    BoxLayout:
        orientation: "vertical"
        padding: "16dp"
        spacing: "8dp"
        Label:
            text: "[b]Ficha de personagem[/b]"
            markup: True
            font_size: "23sp"
            size_hint_y: .1
        TextInput:
            id: character_name
            hint_text: "Nome do personagem"
            multiline: False
            size_hint_y: None
            height: "46dp"
        TextInput:
            id: character_class
            hint_text: "Classe / arquétipo"
            multiline: False
            size_hint_y: None
            height: "46dp"
        TextInput:
            id: character_level
            hint_text: "Nível"
            multiline: False
            input_filter: "int"
            size_hint_y: None
            height: "46dp"
        TextInput:
            id: character_race
            hint_text: "Raça / espécie"
            multiline: False
            size_hint_y: None
            height: "46dp"
        TextInput:
            id: character_hp
            hint_text: "Pontos de vida (PV)"
            multiline: False
            input_filter: "int"
            size_hint_y: None
            height: "46dp"
        TextInput:
            id: character_notes
            hint_text: "Atributos, perícias, equipamentos e anotações"
            multiline: True
        Button:
            text: "Salvar ficha"
            size_hint_y: None
            height: "48dp"
            on_release: app.save_sheet()
        Button:
            text: "Excluir ficha"
            size_hint_y: None
            height: "42dp"
            on_release: app.delete_sheet()
        Button:
            text: "Voltar à mesa"
            size_hint_y: None
            height: "42dp"
            on_release: app.root.current = "table"
"""

class Store:
    def __init__(self):
        with sqlite3.connect(DB_PATH) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS sheets(
                id TEXT PRIMARY KEY, name TEXT NOT NULL,
                payload TEXT NOT NULL, updated_at INTEGER NOT NULL)""")

    def list_sheets(self):
        with sqlite3.connect(DB_PATH) as db:
            rows = db.execute("SELECT id,name,updated_at FROM sheets ORDER BY name").fetchall()
        return [{"id": r[0], "name": r[1], "updated_at": r[2]} for r in rows]

    def get_sheet(self, uid):
        with sqlite3.connect(DB_PATH) as db:
            row = db.execute("SELECT id,name,payload,updated_at FROM sheets WHERE id=?", (uid,)).fetchone()
        if not row:
            return None
        return {"id": row[0], "name": row[1], "data": json.loads(row[2]), "updated_at": row[3]}

    def save_sheet(self, uid, name, payload):
        with sqlite3.connect(DB_PATH) as db:
            db.execute("""INSERT INTO sheets(id,name,payload,updated_at) VALUES(?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET name=excluded.name,payload=excluded.payload,updated_at=excluded.updated_at""",
                (uid, name, json.dumps(payload, ensure_ascii=False), int(time.time())))

    def delete_sheet(self, uid):
        with sqlite3.connect(DB_PATH) as db:
            cur = db.execute("DELETE FROM sheets WHERE id=?", (uid,))
            return cur.rowcount > 0

STORE = Store()
ACCESS_CODE = None

class APIHandler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass

    def send_json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Mesa-Code")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.end_headers()
        self.wfile.write(data)

    def authorized(self):
        return ACCESS_CODE is not None and secrets.compare_digest(
            self.headers.get("X-Mesa-Code", ""), ACCESS_CODE)

    def read_body(self):
        size = int(self.headers.get("Content-Length", "0"))
        if size < 1 or size > 1_000_000:
            raise ValueError("Tamanho de requisição inválido")
        return json.loads(self.rfile.read(size).decode("utf-8"))

    def do_OPTIONS(self):
        self.send_json(200, {"ok": True})

    def do_GET(self):
        if self.path == "/api/ping":
            self.send_json(200, {"ok": True, "app": "Mesa RPG", "mode": "lan"})
            return
        if not self.authorized():
            self.send_json(401, {"error": "Código de acesso inválido"}); return
        if self.path == "/api/fichas":
            self.send_json(200, {"fichas": STORE.list_sheets()}); return
        if self.path.startswith("/api/ficha/"):
            uid = self.path.split("/api/ficha/", 1)[1]
            item = STORE.get_sheet(uid)
            if item: self.send_json(200, item)
            else: self.send_json(404, {"error": "Ficha não encontrada"})
            return
        self.send_json(404, {"error": "Rota não encontrada"})

    def do_POST(self):
        if not self.authorized():
            self.send_json(401, {"error": "Código de acesso inválido"}); return
        if self.path != "/api/ficha":
            self.send_json(404, {"error": "Rota não encontrada"}); return
        try:
            obj = self.read_body()
            uid = str(obj.get("id") or secrets.token_hex(8))[:64]
            name = str(obj.get("name") or "Nova ficha").strip()[:80]
            data = obj.get("data", {})
            if not isinstance(data, dict) or not name:
                raise ValueError("Dados inválidos")
            STORE.save_sheet(uid, name, data)
            self.send_json(200, {"ok": True, "id": uid})
        except Exception:
            self.send_json(400, {"error": "Dados inválidos"})

    def do_DELETE(self):
        if not self.authorized():
            self.send_json(401, {"error": "Código de acesso inválido"}); return
        if self.path.startswith("/api/ficha/"):
            uid = self.path.split("/api/ficha/", 1)[1]
            if STORE.delete_sheet(uid): self.send_json(200, {"ok": True})
            else: self.send_json(404, {"error": "Ficha não encontrada"})
        else:
            self.send_json(404, {"error": "Rota não encontrada"})

class MesaRPGApp(App):
    server = None
    server_thread = None
    base_url = None
    access_code = None
    editing_id = None
    is_host = False

    def build(self):
        self.root = Builder.load_string(KV)
        return self.root

    def find_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except OSError:
            return "IP indisponível"

    def host_table(self):
        global ACCESS_CODE
        try:
            if self.server is None:
                ACCESS_CODE = secrets.token_urlsafe(6)
                self.access_code = ACCESS_CODE
                self.server = ThreadingHTTPServer(("0.0.0.0", PORT), APIHandler)
                self.server_thread = Thread(target=self.server.serve_forever, daemon=True)
                self.server_thread.start()
            self.base_url = f"http://127.0.0.1:{PORT}"
            self.is_host = True
            self.root.current = "table"
            self.root.get_screen("table").ids.host_address.text = (
                f"IP: {self.find_ip()}:{PORT}\nCódigo da mesa: {self.access_code}")
            self.refresh_sheets()

        except OSError as exc:
            self.root.get_screen("home").ids.status.text = f"Falha ao iniciar servidor: {exc}"

    def request(self, method, path, body=None):
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.base_url + path, data=data, method=method)
        req.add_header("X-Mesa-Code", self.access_code or "")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def join_table(self, address, code):
        screen = self.root.get_screen("join")
        host = address.strip().replace("http://", "").replace("https://", "").strip("/")
        if not host or not code:
            screen.ids.result.text = "Informe o IP e o código da mesa."
            return
        if ":" not in host:
            host = f"{host}:{PORT}"
        self.base_url = f"http://{host}"
        self.access_code = code.strip()
        self.is_host = False
        try:
            self.request("GET", "/api/fichas")
            self.root.current = "table"
            self.root.get_screen("table").ids.host_address.text = f"Conectado a {host}"
            self.refresh_sheets()
        except Exception:
            screen.ids.result.text = "Conexão recusada. Verifique IP, código e Wi-Fi."

    def refresh_sheets(self):
        screen = self.root.get_screen("table")
        try:
            items = self.request("GET", "/api/fichas").get("fichas", [])
            grid = screen.ids.sheet_list
            from kivy.uix.button import Button
            grid.clear_widgets()
            for item in items:
                b = Button(text=item["name"], size_hint_y=None, height="48dp")
                b.bind(on_release=lambda _btn, uid=item["id"]: self.open_sheet(uid))
                grid.add_widget(b)
            if not items:
                from kivy.uix.label import Label
                grid.add_widget(Label(text="Nenhuma ficha criada ainda.", size_hint_y=None, height="40dp"))
        except Exception:
            screen.ids.sheet_list.clear_widgets()
            from kivy.uix.label import Label
            screen.ids.sheet_list.add_widget(Label(text="Não foi possível carregar as fichas.", size_hint_y=None, height="40dp"))

    def new_sheet(self):
        self.editing_id = None
        self.fill_editor({"name": "", "class": "", "level": "1", "race": "", "hp": "", "notes": ""})
        self.root.current = "editor"

    def open_sheet(self, uid):
        try:
            item = self.request("GET", "/api/ficha/" + uid)
            self.editing_id = uid
            data = item.get("data", {})
            data["name"] = item.get("name", "")
            self.fill_editor(data)
            self.root.current = "editor"
        except Exception:
            self.root.get_screen("table").ids.host_address.text = "Erro ao abrir a ficha."

    def fill_editor(self, data):
        ids = self.root.get_screen("editor").ids
        ids.character_name.text = str(data.get("name", ""))
        ids.character_class.text = str(data.get("class", ""))
        ids.character_level.text = str(data.get("level", "1"))
        ids.character_race.text = str(data.get("race", ""))
        ids.character_hp.text = str(data.get("hp", ""))
        ids.character_notes.text = str(data.get("notes", ""))

    def save_sheet(self):
        ids = self.root.get_screen("editor").ids
        name = ids.character_name.text.strip()
        if not name:
            ids.character_name.hint_text = "O nome é obrigatório"
            return
        data = {
            "class": ids.character_class.text.strip(),
            "level": ids.character_level.text.strip() or "1",
            "race": ids.character_race.text.strip(),
            "hp": ids.character_hp.text.strip(),
            "notes": ids.character_notes.text
        }
        body = {"id": self.editing_id, "name": name, "data": data}
        try:
            result = self.request("POST", "/api/ficha", body)
            self.editing_id = result["id"]
            self.root.current = "table"
            self.refresh_sheets()
        except Exception:
            self.root.get_screen("table").ids.host_address.text = "Falha ao salvar. Verifique a conexão."

    def delete_sheet(self):
        if not self.editing_id:
            self.root.current = "table"
            return
        try:
            self.request("DELETE", "/api/ficha/" + self.editing_id)
            self.editing_id = None
            self.root.current = "table"
            self.refresh_sheets()
        except Exception:
            self.root.get_screen("table").ids.host_address.text = "Falha ao excluir a ficha."

    def stop_host(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        self.is_host = False
        self.base_url = None
        self.access_code = None
        self.root.current = "home"

    def on_stop(self):
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None

if __name__ == "__main__":
    MesaRPGApp().run()
