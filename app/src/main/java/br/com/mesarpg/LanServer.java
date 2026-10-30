package br.com.mesarpg;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Base64;
import fi.iki.elonen.NanoHTTPD;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.UUID;

public class LanServer extends NanoHTTPD {
    private final Context context;
    private final SharedPreferences prefs;
    private final Map<String,String> sessions = new HashMap<>();
    private JSONObject db;
    private final SecureRandom random = new SecureRandom();

    public LanServer(Context c, int port) throws java.io.IOException {
        super("0.0.0.0", port);
        context = c.getApplicationContext();
        prefs = context.getSharedPreferences("mesa_rpg_db", Context.MODE_PRIVATE);
        try { db = new JSONObject(prefs.getString("db", "{\"users\":{},\"sheets\":{}}")); }
        catch (Exception e) { db = new JSONObject(); }
        if (!db.has("users")) db.put("users", new JSONObject());
        if (!db.has("sheets")) db.put("sheets", new JSONObject());
    }

    private void persist() { prefs.edit().putString("db", db.toString()).apply(); }
    private Response json(int status, JSONObject obj) {
        Response r = newFixedLengthResponse(Response.Status.lookup(status), "application/json; charset=utf-8", obj.toString());
        r.addHeader("Cache-Control","no-store"); r.addHeader("Access-Control-Allow-Headers","Content-Type, Authorization");
        r.addHeader("Access-Control-Allow-Methods","GET, POST, PUT, OPTIONS"); return r;
    }
    private JSONObject obj(Object... pairs) throws Exception {
        JSONObject o = new JSONObject(); for (int i=0;i<pairs.length;i+=2) o.put(String.valueOf(pairs[i]), pairs[i+1]); return o;
    }
    private JSONObject body(IHTTPSession s) throws Exception {
        Map<String,String> files = new HashMap<>(); s.parseBody(files);
        String raw = files.get("postData");
        if (raw == null || raw.isEmpty()) return new JSONObject();
        return new JSONObject(raw);
    }
    private String token(IHTTPSession s) {
        String h=s.getHeaders().get("authorization");
        return h!=null && h.startsWith("Bearer ")?h.substring(7):"";
    }
    private String userId(IHTTPSession s) { return sessions.get(token(s)); }
    private JSONObject users() { return db.optJSONObject("users"); }
    private JSONObject sheets() { return db.optJSONObject("sheets"); }
    private JSONObject user(String id) { return users().optJSONObject(id); }
    private boolean master(String id) { return id!=null && "master".equals(user(id).optString("role")); }
    private Response error(int status,String message) { try{return json(status,obj("erro",message));}catch(Exception e){return newFixedLengthResponse(message);} }
    private String hash(String salt, String password) throws Exception {
        MessageDigest md=MessageDigest.getInstance("SHA-256");
        byte[] b=md.digest((salt+password).getBytes(StandardCharsets.UTF_8));
        return Base64.encodeToString(b,Base64.NO_WRAP);
    }
    private String randomSalt() { byte[] b=new byte[16]; random.nextBytes(b); return Base64.encodeToString(b,Base64.NO_WRAP); }

    @Override public Response serve(IHTTPSession s) {
        String path=s.getUri();
        Method method=s.getMethod();
        try {
            if (method==Method.OPTIONS) return newFixedLengthResponse(Response.Status.NO_CONTENT,"text/plain","");
            if (method==Method.GET && path.equals("/api/ping")) return json(200,obj("rpg",true,"mode","lan"));
            if (method==Method.POST && path.equals("/api/login")) {
                JSONObject b=body(s);
                String email=b.optString("email","").trim().toLowerCase();
                String password=b.optString("pw","");
                boolean create=b.optBoolean("create",false);
                if (!email.matches("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$")) return error(400,"Informe um e-mail válido.");
                if (password.length()<6 || password.length()>200) return error(400,"A senha deve ter de 6 a 200 caracteres.");
                JSONObject us=users(); String id=null; JSONObject record=null;
                Iterator<String> it=us.keys();
                while(it.hasNext()){String k=it.next();JSONObject u=us.optJSONObject(k);if(u!=null && email.equals(u.optString("email"))){id=k;record=u;break;}}
                if(create) {
                    if(record!=null)return error(409,"E-mail já cadastrado.");
                    id="u_"+UUID.randomUUID().toString().replace("-","");
                    String salt=randomSalt();
                    record=obj("email",email,"salt",salt,"hash",hash(salt,password),"role",us.length()==0?"master":"player");
                    us.put(id,record); sheets().put(id,obj("owner",email,"data",new JSONObject())); persist();
                } else {
                    if(record==null || !hash(record.optString("salt"),password).equals(record.optString("hash")))return error(401,"E-mail ou senha incorretos.");
                }
                String tok=UUID.randomUUID().toString()+UUID.randomUUID().toString();
                sessions.put(tok,id);
                return json(200,obj("id",id,"email",email,"master",master(id),"token",tok));
            }
            if (method==Method.POST && path.equals("/api/logout")) { sessions.remove(token(s)); return json(200,obj("ok",true)); }
            if (path.startsWith("/api/")) {
                String id=userId(s);
                if(id==null || user(id)==null)return error(401,"Sessão expirada. Entre novamente.");
                if(method==Method.GET && path.equals("/api/me"))return json(200,obj("id",id,"email",user(id).optString("email"),"master",master(id)));
                if(method==Method.GET && path.equals("/api/fichas")) {
                    if(!master(id))return error(403,"Somente o mestre pode listar todas as fichas.");
                    JSONArray arr=new JSONArray(); Iterator<String> keys=sheets().keys();
                    while(keys.hasNext()){String sid=keys.next();JSONObject sh=sheets().optJSONObject(sid);JSONObject data=sh==null?new JSONObject():sh.optJSONObject("data");arr.put(obj("id",sid,"owner",sh==null?"":sh.optString("owner"),"name",data==null?"":data.optString("name","")));}
                    return json(200,obj("fichas",arr));
                }
                if(path.startsWith("/api/ficha/")) {
                    String sid=path.substring("/api/ficha/".length());
                    if(sid.contains("/") || sid.isEmpty())return error(404,"Ficha não encontrada.");
                    if(method==Method.GET) {
                        if(!sid.equals(id)&&!master(id))return error(403,"Você só pode abrir sua própria ficha.");
                        JSONObject sh=sheets().optJSONObject(sid); return json(200,obj("data",sh==null?JSONObject.NULL:sh.opt("data",JSONObject.NULL)));
                    }
                    if(method==Method.PUT) {
                        if(!sid.equals(id)&&!master(id))return error(403,"Você só pode editar sua própria ficha.");
                        JSONObject b=body(s);JSONObject data=b.optJSONObject("data");
                        if(data==null)return error(400,"Dados da ficha inválidos.");
                        String owner=user(sid)==null?user(id).optString("email"):user(sid).optString("email");
                        sheets().put(sid,obj("owner",owner,"data",data,"updatedAt",System.currentTimeMillis()));persist();
                        return json(200,obj("ok",true));
                    }
                }
                return error(404,"Rota da API não encontrada.");
            }
            if (method==Method.GET && (path.equals("/")||path.equals("/index.html"))) {
                InputStream in=context.getAssets().open("index.html"); ByteArrayOutputStream out=new ByteArrayOutputStream();
                byte[] buf=new byte[8192];int n;while((n=in.read(buf))>0)out.write(buf,0,n);
                return newFixedLengthResponse(Response.Status.OK,"text/html; charset=utf-8",new String(out.toByteArray(),StandardCharsets.UTF_8));
            }
            return newFixedLengthResponse(Response.Status.NOT_FOUND,"text/plain; charset=utf-8","Não encontrado");
        } catch(Exception e) { return error(500,"Erro interno: "+e.getMessage()); }
    }
}
