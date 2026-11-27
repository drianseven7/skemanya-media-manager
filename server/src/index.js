import express from "express";
import helmet from "helmet";
import cors from "cors";
import rateLimit from "express-rate-limit";
import pg from "pg";
import bcrypt from "bcryptjs";
import { SignJWT, jwtVerify } from "jose";
import { readFile } from "node:fs/promises";

const { Pool } = pg;
const app = express();
const port = Number(process.env.PORT || 8080);
const publicDir = new URL("../public/", import.meta.url).pathname;
const pool = new Pool({ connectionString: process.env.DATABASE_URL, max: 10, idleTimeoutMillis: 30000 });
const jwtSecret = new TextEncoder().encode(process.env.JWT_SECRET || "");
const bootstrapKey = process.env.BOOTSTRAP_KEY || "";

if (jwtSecret.length < 32) throw new Error("JWT_SECRET wajib diisi minimal 32 karakter.");
if (!bootstrapKey || bootstrapKey.length < 24) throw new Error("BOOTSTRAP_KEY wajib diisi minimal 24 karakter.");

app.disable("x-powered-by");
app.use(helmet());
app.use(cors({ origin: (process.env.CORS_ORIGIN || "").split(",").filter(Boolean), credentials: false }));
app.use(express.json({ limit: "2mb" }));
app.use("/api", rateLimit({ windowMs: 60_000, limit: 120, standardHeaders: "draft-8", legacyHeaders: false }));

const asyncRoute = fn => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);
const clean = value => String(value ?? "").trim();
const issueToken = async user => new SignJWT({ role: user.role, email: user.email })
  .setProtectedHeader({ alg: "HS256" }).setSubject(String(user.id))
  .setIssuedAt().setExpirationTime("12h").sign(jwtSecret);

async function auth(req, res, next) {
  try {
    const token = (req.headers.authorization || "").replace(/^Bearer\s+/i, "");
    if (!token) return res.status(401).json({ error: "Autentikasi diperlukan." });
    const { payload } = await jwtVerify(token, jwtSecret);
    req.user = { id: Number(payload.sub), role: payload.role, email: payload.email };
    next();
  } catch { res.status(401).json({ error: "Token tidak valid atau sudah kedaluwarsa." }); }
}
const adminOnly = (req, res, next) => req.user?.role === "admin" ? next() : res.status(403).json({ error: "Akses admin diperlukan." });

async function migrate() {
  const sql = await readFile(new URL("../migrations/001_initial.sql", import.meta.url), "utf8");
  await pool.query(sql);
}
await migrate();

app.get("/api/health", asyncRoute(async (_req, res) => {
  await pool.query("SELECT 1");
  res.json({ ok: true, service: "SKEMANYA Private Server", database: "connected", time: new Date().toISOString() });
}));

app.post("/api/setup", asyncRoute(async (req, res) => {
  if (req.get("x-bootstrap-key") !== bootstrapKey) return res.status(403).json({ error: "Kunci setup salah." });
  const { rows } = await pool.query("SELECT COUNT(*)::int AS total FROM users");
  if (rows[0].total > 0) return res.status(409).json({ error: "Setup awal sudah selesai." });
  const name = clean(req.body?.name), email = clean(req.body?.email).toLowerCase(), password = String(req.body?.password || "");
  if (!name || !/^\S+@\S+\.\S+$/.test(email) || password.length < 12) return res.status(400).json({ error: "Nama, email valid, dan password minimal 12 karakter wajib diisi." });
  const hash = await bcrypt.hash(password, 12);
  const result = await pool.query("INSERT INTO users(name,email,password_hash,role) VALUES($1,$2,$3,'admin') RETURNING id,name,email,role,created_at", [name,email,hash]);
  const user = result.rows[0];
  res.status(201).json({ user, token: await issueToken(user) });
}));

app.post("/api/auth/login", asyncRoute(async (req, res) => {
  const email = clean(req.body?.email).toLowerCase(), password = String(req.body?.password || "");
  const result = await pool.query("SELECT * FROM users WHERE email=$1 AND is_active=true", [email]);
  const user = result.rows[0];
  if (!user || !(await bcrypt.compare(password, user.password_hash))) return res.status(401).json({ error: "Email atau password salah." });
  await pool.query("UPDATE users SET last_login_at=NOW() WHERE id=$1", [user.id]);
  res.json({ user: { id:user.id,name:user.name,email:user.email,role:user.role }, token: await issueToken(user) });
}));

app.get("/api/me", auth, asyncRoute(async (req, res) => {
  const { rows } = await pool.query("SELECT id,name,email,role,created_at,last_login_at FROM users WHERE id=$1", [req.user.id]);
  if (!rows[0]) return res.status(404).json({ error: "Pengguna tidak ditemukan." });
  res.json({ user: rows[0] });
}));

app.get("/api/dashboard", auth, asyncRoute(async (_req, res) => {
  const [news, content, tasks, recent] = await Promise.all([
    pool.query("SELECT COUNT(*)::int AS total FROM news_items"),
    pool.query("SELECT COUNT(*)::int AS total FROM content_items"),
    pool.query("SELECT COUNT(*)::int AS total FROM tasks WHERE status NOT IN ('DONE','CANCELLED')"),
    pool.query("SELECT id,action,entity_type,created_at FROM activity_logs ORDER BY id DESC LIMIT 8")
  ]);
  res.json({ counts: { news:news.rows[0].total, content:content.rows[0].total, open_tasks:tasks.rows[0].total }, recent_activity:recent.rows });
}));

const resources = {
  news: { table:"news_items", fields:["title","url","summary","category","source","published_at","status"], required:["title"] },
  content: { table:"content_items", fields:["title","format","category","hook","body","caption","source_url","status"], required:["title"] },
  tasks: { table:"tasks", fields:["title","description","assignee","priority","due_at","status"], required:["title"] },
  calendar: { table:"editorial_calendar", fields:["title","content_id","channel","scheduled_at","status"], required:["title"] }
};
for (const [name, cfg] of Object.entries(resources)) {
  app.get("/api/" + name, auth, asyncRoute(async (req,res) => {
    const limit = Math.min(Math.max(Number(req.query.limit)||50,1),100);
    const { rows } = await pool.query(`SELECT * FROM ${cfg.table} ORDER BY updated_at DESC LIMIT $1`,[limit]);
    res.json({ items: rows });
  }));
  app.post("/api/" + name, auth, asyncRoute(async (req,res) => {
    const body=req.body||{};
    for (const key of cfg.required) if (!clean(body[key])) return res.status(400).json({error:key+" wajib diisi."});
    const keys=cfg.fields.filter(k=>body[k]!==undefined);
    if (!keys.length) return res.status(400).json({error:"Tidak ada data untuk disimpan."});
    const cols=keys.join(","), vals=keys.map((_,i)=>"$"+(i+1)).join(",");
    const result=await pool.query(`INSERT INTO ${cfg.table} (${cols},created_by) VALUES (${vals},$${keys.length+1}) RETURNING *`,[...keys.map(k=>body[k]),req.user.id]);
    await pool.query("INSERT INTO activity_logs(user_id,action,entity_type,entity_id) VALUES($1,$2,$3,$4)",[req.user.id,"CREATE",name,result.rows[0].id]);
    res.status(201).json({item:result.rows[0]});
  }));
  app.patch("/api/" + name + "/:id", auth, asyncRoute(async (req,res) => {
    const keys=cfg.fields.filter(k=>req.body?.[k]!==undefined);
    if (!keys.length) return res.status(400).json({error:"Tidak ada perubahan."});
    const set=keys.map((k,i)=>k+"=$"+(i+1)).join(",");
    const values=keys.map(k=>req.body[k]);
    const result=await pool.query(`UPDATE ${cfg.table} SET ${set},updated_at=NOW() WHERE id=$${keys.length+1} RETURNING *`,[...values,Number(req.params.id)]);
    if (!result.rows[0]) return res.status(404).json({error:"Data tidak ditemukan."});
    await pool.query("INSERT INTO activity_logs(user_id,action,entity_type,entity_id) VALUES($1,$2,$3,$4)",[req.user.id,"UPDATE",name,Number(req.params.id)]);
    res.json({item:result.rows[0]});
  }));
}

app.get("/api/users", auth, adminOnly, asyncRoute(async (_req,res) => {
  const { rows }=await pool.query("SELECT id,name,email,role,is_active,created_at,last_login_at FROM users ORDER BY id");
  res.json({items:rows});
}));
app.get("/api/activity", auth, asyncRoute(async (req,res) => {
  const { rows }=await pool.query("SELECT a.*,u.name AS user_name FROM activity_logs a LEFT JOIN users u ON u.id=a.user_id ORDER BY a.id DESC LIMIT 100");
  res.json({items:rows});
}));
app.get("/api/settings", auth, adminOnly, asyncRoute(async (_req,res) => {
  const { rows }=await pool.query("SELECT key,value,updated_at FROM app_settings ORDER BY key");
  res.json({items:rows});
}));
app.put("/api/settings/:key", auth, adminOnly, asyncRoute(async (req,res) => {
  const key=clean(req.params.key);
  if (!/^[a-z0-9_.-]{1,80}$/i.test(key)) return res.status(400).json({error:"Nama pengaturan tidak valid."});
  const value=JSON.stringify(req.body?.value ?? null);
  const { rows }=await pool.query("INSERT INTO app_settings(key,value,updated_at) VALUES($1,$2,NOW()) ON CONFLICT(key) DO UPDATE SET value=EXCLUDED.value,updated_at=NOW() RETURNING key,value,updated_at",[key,value]);
  res.json({item:rows[0]});
}));

app.use(express.static(publicDir));
app.use((req,res)=>res.status(404).json({error:"Endpoint tidak ditemukan."}));
app.use((err,_req,res,_next)=>{ console.error(err); res.status(500).json({error:"Terjadi kesalahan pada server."}); });
app.listen(port,"0.0.0.0",()=>console.log("SKEMANYA Private Server listening on "+port));
