from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.utils import platform
from threading import Thread
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json, sqlite3, hashlib, secrets, os, socket

APP_DIR = os.path.join(os.path.expanduser("~"), ".mesa_rpg")
os.makedirs(APP_DIR, exist_ok=True)
DB_PATH = os.path.join(APP_DIR, "mesa_rpg.sqlite3")
PORT = 8765

KV = """
ScreenManager:
    HomeScreen:
    JoinScreen:
    TableScreen:

<HomeScreen>:
    name: "home"
    BoxLayout:
        orientation: "vertical"
        padding: "24dp"
        spacing: "16dp"
        canvas.before:
            Color:
                rgba: 0.03, 0.08, 0.06, 1
            Rectangle:
                pos: self.pos
                size: self.size
        Label:
            text: "[b]MESA RPG[/b]"
            markup: True
            font_size: "30sp"
            size_hint_y: .22
        Label:
            text: "D&D 5e • Fichas • Mesa local"
            font_size: "16sp"
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
        padding: "24dp"
        spacing: "12dp"
        Label:
            text: "[b]Entrar na mesa[/b]"
            markup: True
            font_size: "24sp"
        TextInput:
            id: address
            hint_text: "IP do mestre (ex.: 192.168.1.20)"
            multiline: False
            size_hint_y: None
            height: "48dp"
        Button:
            text: "Testar conexão"
            size_hint_y: None
            height: "48dp"
            on_release: app.test_host(root.ids.address.text)
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
        padding: "20dp"
        spacing: "12dp"
        Label:
            text: "[b]Mesa hospedada[/b]"
            markup: True
            font_size: "26sp"
        Label:
            id: host_address
            text: ""
        Label:
            text: "Servidor local ativo. Mantenha este aplicativo aberto."
        Button:
            text: "Atualizar fichas"
            size_hint_y: None
            height: "48dp"
            on_release: app.refresh_sheets()
        Label:
            id: sheets
            text: "Nenhuma ficha carregada."
        Button:
            text: "Parar / voltar"
            size_hint_y: None
            height: "48dp"
            on_release: app.stop_host()
"""

class Store:
    def __init__(self):
        with sqlite3.connect(DB_PATH) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS users(
                id TEXT PRIMARY KEY, email TEXT UNIQUE, salt TEXT, password_hash TEXT, role TEXT)""")
            db.execute("""CREATE TABLE IF NOT EXISTS sheets(
                user_id TEXT PRIMARY KEY, name TEXT NOT NULL DEFAULT 'Nova ficha',
                payload TEXT NOT NULL DEFAULT '{}', updated_at INTEGER DEFAULT (strftime('%s','now')),
                FOREIGN KEY(user_id) REFERENCES users(id))""")

class APIHandler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass
    def send_json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, OPTIONS")
        self.end_headers()
        self.wfile.write(data)
    def do_OPTIONS(self): self.send_json(200, {"ok": True})
    def do_GET(self):
        if self.path == "/api/ping":
            self.send_json(200, {"ok": True, "app": "Mesa RPG", "mode": "lan"})
        elif self.path == "/api/fichas":
            with sqlite3.connect(DB_PATH) as db:
                rows = db.execute("SELECT user_id,name,updated_at FROM sheets ORDER BY name").fetchall()
            self.send_json(200, {"fichas":[{"id":r[0],"name":r[1],"updated_at":r[2]} for r in rows]})
        else: self.send_json(404, {"error":"Rota não encontrada"})
    def do_POST(self):
        if self.path != "/api/ficha":
            self.send_json(404, {"error":"Rota não encontrada"}); return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length) or b"{}")
            uid = str(payload.get("id", ""))
            name = str(payload.get("name", "Nova ficha"))[:100]
            data = json.dumps(payload.get("data", {}), ensure_ascii=False)
            if not uid:
                self.send_json(400, {"error":"ID da ficha obrigatório"}); return
            with sqlite3.connect(DB_PATH) as db:
                db.execute("INSERT INTO sheets(user_id,name,payload) VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET name=excluded.name,payload=excluded.payload,updated_at=strftime('%s','now')",(uid,name,data))
            self.send_json(200, {"ok":True})
        except Exception:
            self.send_json(400, {"error":"Dados inválidos"})
    def do_GET_ficha(self, uid): pass

class MesaRPGApp(App):
    server = None
    server_thread = None
    def build(self):
        Store()
        self.root = Builder.load_string(KV)
        return self.root
    def find_ip(self):
        try:
            s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
            s.connect(("8.8.8.8",80)); ip=s.getsockname()[0]; s.close()
            return ip
        except OSError: return "IP indisponível"
    def host_table(self):
        try:
            if self.server is None:
                self.server = ThreadingHTTPServer(("0.0.0.0", PORT), APIHandler)
                self.server_thread = Thread(target=self.server.serve_forever, daemon=True)
                self.server_thread.start()
            self.root.current = "table"
            self.root.get_screen("table").ids.host_address.text = f"Endereço: {self.find_ip()}:{PORT}"
            self.root.get_screen("home").ids.status.text = "Mesa hospedada na rede local."
        except OSError as e:
            self.root.get_screen("home").ids.status.text = f"Falha ao iniciar servidor: {e}"
    def test_host(self, address):
        import urllib.request
        screen=self.root.get_screen("join")
        host=address.strip().removeprefix("http://").removeprefix("https://").strip("/")
        if not host: screen.ids.result.text="Informe o IP do mestre."; return
        try:
            with urllib.request.urlopen(f"http://{host}:{PORT}/api/ping", timeout=3) as r:
                screen.ids.result.text = "Mesa encontrada! API responde."
        except Exception:
            screen.ids.result.text = "Não foi possível conectar. Confira o IP e a rede Wi-Fi."
    def refresh_sheets(self):
        screen=self.root.get_screen("table")
        import urllib.request
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/api/fichas",timeout=3) as r:
                items=json.load(r).get("fichas",[])
            screen.ids.sheets.text="\\n".join(x["name"]+" ("+x["id"]+")" for x in items) or "Nenhuma ficha salva."
        except Exception as e: screen.ids.sheets.text=f"Erro ao ler fichas: {e}"
    def stop_host(self):
        if self.server:
            self.server.shutdown(); self.server.server_close(); self.server=None
        self.root.current="home"
    def on_stop(self):
        if self.server:
            self.server.shutdown(); self.server.server_close(); self.server=None

if __name__ == "__main__":
    MesaRPGApp().run()
