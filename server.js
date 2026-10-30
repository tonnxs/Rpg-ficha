#!/usr/bin/env node
'use strict';
const http = require('node:http');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const HOST = process.env.HOST || '0.0.0.0';
const PORT = Number(process.env.PORT || 8080);
const ROOT = __dirname;
const DATA_DIR = path.join(ROOT, 'data');
const DATA_FILE = path.join(DATA_DIR, 'mesa.json');
const MAX_BODY = 1_000_000;
const sessions = new Map();
const MIME = {'.html':'text/html; charset=utf-8','.css':'text/css; charset=utf-8','.js':'text/javascript; charset=utf-8','.json':'application/json; charset=utf-8','.png':'image/png','.svg':'image/svg+xml','.ico':'image/x-icon'};

fs.mkdirSync(DATA_DIR, {recursive:true});
function load() {
  try { return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8')); }
  catch { return {users:{}, sheets:{}}; }
}
let db = load();
function persist() {
  const tmp = DATA_FILE + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(db, null, 2), {mode:0o600});
  fs.renameSync(tmp, DATA_FILE);
}
function send(res, status, obj) {
  res.writeHead(status, {'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'});
  res.end(JSON.stringify(obj));
}
function readBody(req) {
  return new Promise((resolve,reject)=>{
    let body='', size=0;
    req.on('data', chunk=>{size+=chunk.length;if(size>MAX_BODY){reject(new Error('Corpo da requisição muito grande'));req.destroy();return;}body+=chunk;});
    req.on('end',()=>{try{resolve(body?JSON.parse(body):{});}catch{reject(new Error('JSON inválido'));}});
    req.on('error',reject);
  });
}
function hashPassword(password, salt = crypto.randomBytes(16).toString('hex')) {
  const hash = crypto.scryptSync(password, salt, 64).toString('hex');
  return {salt, hash};
}
function verifyPassword(password, record) {
  const actual = crypto.scryptSync(password, record.salt, 64);
  const expected = Buffer.from(record.hash, 'hex');
  return actual.length === expected.length && crypto.timingSafeEqual(actual, expected);
}
function tokenUser(req) {
  const header = req.headers.authorization || '';
  const token = header.startsWith('Bearer ') ? header.slice(7) : '';
  const id = sessions.get(token);
  if (!id || !db.users[id]) return null;
  return {id, ...db.users[id], token};
}
function requireUser(req,res) {
  const user = tokenUser(req);
  if (!user) { send(res,401,{erro:'Sessão expirada. Entre novamente.'}); return null; }
  return user;
}
function isMaster(user) { return user.role === 'master'; }
function safeId(id) { return typeof id === 'string' && /^[a-zA-Z0-9_-]{1,100}$/.test(id); }
async function handle(req,res) {
  const url = new URL(req.url, 'http://localhost');
  const pathname = decodeURIComponent(url.pathname);

  if (req.method === 'GET' && pathname === '/api/ping') return send(res,200,{rpg:true,mode:'lan'});
  if (req.method === 'POST' && pathname === '/api/login') {
    let body;
    try { body=await readBody(req); } catch(e) { return send(res,400,{erro:e.message}); }
    const email = String(body.email||'').trim().toLowerCase();
    const password = String(body.pw||'');
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return send(res,400,{erro:'Informe um e-mail válido.'});
    if (password.length < 6 || password.length > 200) return send(res,400,{erro:'A senha deve ter de 6 a 200 caracteres.'});
    let record = Object.values(db.users).find(u=>u.email===email);
    let id = Object.keys(db.users).find(k=>db.users[k].email===email);
    if (body.create) {
      if (record) return send(res,409,{erro:'E-mail já cadastrado.'});
      const first = Object.keys(db.users).length === 0;
      id = 'u_' + crypto.randomBytes(12).toString('hex');
      const cred = hashPassword(password);
      db.users[id] = {email, salt:cred.salt, hash:cred.hash, role:first?'master':'player', createdAt:new Date().toISOString()};
      persist();
      record=db.users[id];
    } else {
      if (!record || !verifyPassword(password,record)) return send(res,401,{erro:'E-mail ou senha incorretos.'});
    }
    const token = crypto.randomBytes(32).toString('hex');
    sessions.set(token,id);
    return send(res,200,{id,email:record.email,master:isMaster(record),token});
  }
  if (req.method === 'POST' && pathname === '/api/logout') {
    const header=req.headers.authorization||'';
    if(header.startsWith('Bearer ')) sessions.delete(header.slice(7));
    return send(res,200,{ok:true});
  }
  if (req.method === 'GET' && pathname === '/api/me') {
    const u=requireUser(req,res); if(!u)return;
    return send(res,200,{id:u.id,email:u.email,master:isMaster(u)});
  }
  if (pathname.startsWith('/api/')) {
    const user=requireUser(req,res); if(!user)return;
    if (req.method === 'GET' && pathname === '/api/fichas') {
      if(!isMaster(user)) return send(res,403,{erro:'Somente o mestre pode listar todas as fichas.'});
      return send(res,200,{fichas:Object.entries(db.sheets).map(([id,s])=>({id,owner:s.owner,name:s.data?.name||''}))});
    }
    const match=pathname.match(/^\/api\/ficha\/([^/]+)$/);
    if(match && safeId(match[1])) {
      const id=match[1];
      if(req.method==='GET') {
        if(id!==user.id && !isMaster(user)) return send(res,403,{erro:'Você só pode abrir sua própria ficha.'});
        return send(res,200,{data:db.sheets[id]?.data || null});
      }
      if(req.method==='PUT') {
        if(id!==user.id && !isMaster(user)) return send(res,403,{erro:'Você só pode editar sua própria ficha.'});
        let body;
        try { body=await readBody(req); } catch(e) { return send(res,400,{erro:e.message}); }
        if(!body || !body.data || typeof body.data!=='object' || Array.isArray(body.data)) return send(res,400,{erro:'Dados da ficha inválidos.'});
        db.sheets[id]={owner:db.users[id]?.email || user.email,data:body.data,updatedAt:new Date().toISOString()};
        persist();
        return send(res,200,{ok:true});
      }
    }
    return send(res,404,{erro:'Rota da API não encontrada.'});
  }

  let file = pathname === '/' ? 'index.html' : pathname.replace(/^\/+/, '');
  // Nunca exponha o banco local, arquivos de configuração ou o próprio servidor via HTTP.
  if (file.startsWith('data/') || file === 'data' || file.startsWith('.git') ||
      ['server.js','package.json','.gitignore','README-LAN.md'].includes(file)) {
    return send(res,404,{erro:'Arquivo não encontrado.'});
  }
  const full = path.resolve(ROOT,file);
  if (!full.startsWith(ROOT + path.sep) || !fs.existsSync(full) || !fs.statSync(full).isFile()) return send(res,404,{erro:'Arquivo não encontrado.'});
  const ext=path.extname(full);
  res.writeHead(200,{'Content-Type':MIME[ext]||'application/octet-stream','X-Content-Type-Options':'nosniff','Cache-Control':ext==='.html'?'no-cache':'public, max-age=3600'});
  fs.createReadStream(full).pipe(res);
}
http.createServer((req,res)=>{handle(req,res).catch(err=>{console.error(err);if(!res.headersSent)send(res,500,{erro:'Erro interno do servidor.'});else res.end();});}).listen(PORT,HOST,()=>{
  console.log('\nMesa RPG LAN ativa.');
  console.log('Abra no próprio dispositivo: http://localhost:'+PORT);
  console.log('Em outros dispositivos, use o IP local deste dispositivo, por exemplo: http://192.168.1.10:'+PORT);
  console.log('Primeira conta criada será o MESTRE. Demais contas serão JOGADORES.');
  console.log('Dados salvos localmente em ./data/mesa.json. Ctrl+C encerra o servidor.\n');
});
