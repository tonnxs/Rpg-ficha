package br.com.mesarpg;

import android.app.Activity;
import fi.iki.elonen.NanoHTTPD;
import android.os.Bundle;
import android.graphics.Color;
import android.view.View;
import android.view.Gravity;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.net.wifi.WifiManager;
import android.content.Context;
import android.text.InputType;
import android.text.format.Formatter;
import android.widget.Toast;

public class MainActivity extends Activity {
    private LanServer server;
    private LinearLayout root;
    private TextView status;

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        home();
    }

    private int dp(int v) { return (int)(v * getResources().getDisplayMetrics().density); }
    private TextView label(String text, int size) {
        TextView t = new TextView(this); t.setText(text); t.setTextSize(size);
        t.setTextColor(Color.rgb(235,245,238)); t.setGravity(Gravity.CENTER);
        t.setPadding(dp(16),dp(12),dp(16),dp(12)); return t;
    }
    private Button button(String text) {
        Button b = new Button(this); b.setText(text); b.setAllCaps(false); return b;
    }
    private void home() {
        root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL);
        root.setGravity(Gravity.CENTER); root.setPadding(dp(24),dp(24),dp(24),dp(24));
        root.setBackgroundColor(Color.rgb(7,20,15));
        root.addView(label("MESA RPG", 28));
        root.addView(label("D&D 5e • Lanternas • Rede Wi-Fi local", 16));
        Button host = button("Criar / hospedar uma mesa");
        Button join = button("Entrar em uma mesa");
        root.addView(host, new LinearLayout.LayoutParams(-1, -2));
        root.addView(join, new LinearLayout.LayoutParams(-1, -2));
        status = label("Sem conexão ativa. Os celulares precisam estar na mesma rede Wi-Fi.", 14);
        root.addView(status);
        setContentView(root);
        host.setOnClickListener(v -> startHost());
        join.setOnClickListener(v -> joinTable());
    }

    private String localIp() {
        try {
            WifiManager wm = (WifiManager)getApplicationContext().getSystemService(Context.WIFI_SERVICE);
            return Formatter.formatIpAddress(wm.getConnectionInfo().getIpAddress());
        } catch (Exception e) { return "IP indisponível"; }
    }

    private void startHost() {
        try {
            if (server == null) { server = new LanServer(this, 8080); server.start(NanoHTTPD.SOCKET_READ_TIMEOUT, false); }
            String ip = localIp();
            new android.app.AlertDialog.Builder(this)
                .setTitle("Mesa hospedada")
                .setMessage("Endereço para os jogadores:\\n\\n" + ip + ":8080\\n\\nTodos devem estar na mesma rede Wi-Fi. Mantenha este aplicativo aberto enquanto a mesa estiver em uso.")
                .setPositiveButton("Abrir mesa", (dialog, which) -> showWeb("http://127.0.0.1:8080/"))
                .setNegativeButton("Depois", null)
                .show();
            status.setText("Mesa ativa: " + ip + ":8080");
        } catch (Exception e) {
            new android.app.AlertDialog.Builder(this).setTitle("Não foi possível hospedar")
                .setMessage(e.getMessage()).setPositiveButton("OK", null).show();
        }
    }

    private void joinTable() {
        final EditText address = new EditText(this);
        address.setSingleLine(true);
        address.setHint("Ex.: 192.168.1.25:8080");
        address.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        new android.app.AlertDialog.Builder(this).setTitle("Endereço da mesa")
            .setMessage("Digite o IP exibido no celular do mestre.")
            .setView(address).setNegativeButton("Cancelar", null)
            .setPositiveButton("Conectar", (d,w) -> {
                String url = address.getText().toString().trim();
                if (!url.startsWith("http://") && !url.startsWith("https://")) url = "http://" + url;
                if (!url.endsWith("/")) url += "/";
                showWeb(url);
            }).show();
    }

    private void showWeb(String url) {
        WebView web = new WebView(this);
        web.setBackgroundColor(Color.rgb(233,238,233));
        web.getSettings().setJavaScriptEnabled(true);
        web.getSettings().setDomStorageEnabled(true);
        web.getSettings().setDatabaseEnabled(true);
        web.setWebViewClient(new WebViewClient());
        setContentView(web);
        web.loadUrl(url);
    }

    @Override public void onBackPressed() {
        home();
    }

    @Override protected void onDestroy() {
        super.onDestroy();
        // Keep the local server alive while the host activity is open; stop it when the app closes.
        if (server != null) { server.stop(); server = null; }
    }
}
