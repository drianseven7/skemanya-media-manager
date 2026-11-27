/**
 * SKEMANYA AI Media Manager — Cloudflare Worker backend
 * Bindings: DB (D1). Optional secret: GEMINI_API_KEY. Optional vars: GEMINI_MODEL, ALLOWED_ORIGIN.
 */
const DEFAULT_FEEDS = [
  { name: 'ANTARA Terkini', url: 'https://www.antaranews.com/rss/terkini.xml', category: 'Nasional' },
  { name: 'BBC Indonesia', url: 'https://feeds.bbci.co.uk/indonesia/rss.xml', category: 'Internasional' },
  { name: 'NASA News', url: 'https://www.nasa.gov/feed/', category: 'Sains & Teknologi' }
];

function cors(env) {
  return {
    'Access-Control-Allow-Origin': env.ALLOWED_ORIGIN || '*',
    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Content-Type': 'application/json; charset=utf-8'
  };
}
function json(data, status = 200, env = {}) { return new Response(JSON.stringify(data), { status, headers: cors(env) }); }
function clean(s = '') { return String(s).replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1').replace(/<[^>]+>/g, ' ').replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n))).replace(/\s+/g, ' ').trim(); }
function tag(xml, name) { const m = xml.match(new RegExp('<' + name + '(?:\\s[^>]*)?>([\\s\\S]*?)</' + name + '>', 'i')); return m ? clean(m[1]) : ''; }
function itemUrl(block) { const link = tag(block, 'link'); if (link) return link; const m = block.match(/<link[^>]+href=["']([^"']+)["']/i); return m ? m[1] : ''; }
function parseFeed(xml, feed) {
  const blocks = [...xml.matchAll(/<(?:item|entry)\b[^>]*>([\s\S]*?)<\/(?:item|entry)>/gi)].map(m => m[1]);
  return blocks.map(b => ({ title: tag(b, 'title'), url: itemUrl(b), summary: tag(b, 'description') || tag(b, 'summary') || tag(b, 'content:encoded'), published: tag(b, 'pubDate') || tag(b, 'published') || tag(b, 'updated'), category: feed.category, source: feed.name })).filter(x => x.title && x.url);
}
async function ensureFeeds(db) {
  const count = await db.prepare('SELECT COUNT(*) AS n FROM rss_sources').first();
  if (!count || count.n === 0) {
    for (const f of DEFAULT_FEEDS) await db.prepare('INSERT OR IGNORE INTO rss_sources (name,url,category,enabled) VALUES (?,?,?,1)').bind(f.name,f.url,f.category).run();
  }
}
async function scanNews(env) {
  await ensureFeeds(env.DB);
  const { results: feeds } = await env.DB.prepare('SELECT id,name,url,category FROM rss_sources WHERE enabled=1').all();
  let inserted = 0, errors = [];
  for (const feed of feeds || []) {
    try {
      const res = await fetch(feed.url, { headers: { 'User-Agent': 'SKEMANYA-MediaBot/1.0 (+RSS reader)' }, cf: { cacheTtl: 300, cacheEverything: true } });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const xml = await res.text();
      for (const item of parseFeed(xml, feed)) {
        const published = item.published && !Number.isNaN(Date.parse(item.published)) ? new Date(item.published).toISOString() : new Date().toISOString();
        const result = await env.DB.prepare('INSERT OR IGNORE INTO news_items (title,url,summary,category,source,published_at,status,created_at) VALUES (?,?,?,?,?,?,?,?)').bind(item.title,item.url,item.summary,item.category,item.source,published,'NEEDS_REVIEW',new Date().toISOString()).run();
        inserted += result.meta?.changes || 0;
      }
      await env.DB.prepare('UPDATE rss_sources SET last_checked_at=?,last_error=NULL WHERE id=?').bind(new Date().toISOString(),feed.id).run();
    } catch (e) {
      errors.push({ source: feed.name, error: e.message });
      await env.DB.prepare('UPDATE rss_sources SET last_checked_at=?,last_error=? WHERE id=?').bind(new Date().toISOString(),e.message,feed.id).run();
    }
  }
  const trends = await scanTrends(env);
  await env.DB.prepare('INSERT INTO automation_runs (task,status,details,created_at) VALUES (?,?,?,?)').bind('news_and_trends_scan',(errors.length||trends.error)?'PARTIAL':'SUCCESS',JSON.stringify({inserted,errors,trends}),new Date().toISOString()).run();
  return { scanned: feeds?.length || 0, inserted, trend_inserted: trends.inserted, trend_error: trends.error, errors };
}
async function scanTrends(env) {
  let inserted = 0, error = null;
  try {
    const res = await fetch('https://trends.google.com/trending/rss?geo=ID', { headers: { 'User-Agent': 'SKEMANYA-MediaBot/1.0' }, cf: { cacheTtl: 600, cacheEverything: true } });
    if (!res.ok) throw new Error(`Google Trends RSS HTTP ${res.status}`);
    const xml = await res.text();
    const items = parseFeed(xml, { name: 'Google Trends Indonesia', category: 'Tren pencarian' });
    for (const item of items) {
      const published = item.published && !Number.isNaN(Date.parse(item.published)) ? new Date(item.published).toISOString() : new Date().toISOString();
      const result = await env.DB.prepare('INSERT OR IGNORE INTO trend_items (title,url,summary,source,published_at,created_at) VALUES (?,?,?,?,?,?)').bind(item.title,item.url,item.summary,'Google Trends Indonesia',published,new Date().toISOString()).run();
      inserted += result.meta?.changes || 0;
    }
  } catch (e) { error = e.message; }
  return { inserted, error };
}
async function createDailyBrief(env) {
  const { results } = await env.DB.prepare('SELECT title,url,summary,source,category,published_at FROM news_items ORDER BY published_at DESC LIMIT 12').all();
  const payload = { generated_at: new Date().toISOString(), timezone: 'Asia/Jakarta', items: results || [], note: 'Ringkasan otomatis dari feed RSS; setiap item tetap memerlukan pemeriksaan editorial.' };
  await env.DB.prepare('INSERT INTO daily_briefs (brief_date,payload,created_at) VALUES (?,?,?)').bind(new Date().toISOString().slice(0,10),JSON.stringify(payload),new Date().toISOString()).run();
  return payload;
}
async function generateDraft(env, newsId) {
  if (!env.GEMINI_API_KEY) throw new Error('GEMINI_API_KEY belum dipasang sebagai Worker Secret.');
  const article = await env.DB.prepare('SELECT * FROM news_items WHERE id=?').bind(newsId).first();
  if (!article) throw new Error('Berita tidak ditemukan.');
  const prompt = `Kamu editor SKEMANYA, media fakta, data, dan lifestyle. Buat DRAFT carousel Instagram Bahasa Indonesia berdasarkan bahan sumber berikut. Jangan menambahkan fakta di luar bahan. Tandai hal yang belum diketahui. Gaya: hook menarik tanpa clickbait, 5-7 slide, teks sedang dan ringkas, judul slide bukan pertanyaan, caption menambah konteks. Kembalikan JSON valid tanpa markdown dengan keys title,hook,slides (array string),caption,verification_notes. Sumber: ${article.source} — ${article.url}\nJudul: ${article.title}\nRingkasan: ${article.summary}`;
  const primaryModel = env.GEMINI_MODEL || 'gemini-3.5-flash-lite';
  const fallbackModel = primaryModel === 'gemini-3.5-flash-lite' ? 'gemini-3.8-flash' : 'gemini-3.5-flash-lite';
  const models = [...new Set([primaryModel, fallbackModel])];
  let response, result, lastError;
  for (let i = 0; i < models.length; i++) {
    try {
      response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(models[i])}:generateContent`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-goog-api-key': env.GEMINI_API_KEY },
        body: JSON.stringify({
          contents: [{ role: 'user', parts: [{ text: prompt }] }],
          generationConfig: { responseMimeType: 'application/json', temperature: 0.6, maxOutputTokens: 1800 }
        }),
        signal: AbortSignal.timeout(25000)
      });
    } catch (e) {
      lastError = e;
      if (i < models.length - 1 && e.name === 'TimeoutError') continue;
      throw new Error(e.name === 'TimeoutError' ? 'Model utama dan cadangan terlalu lambat. Coba lagi beberapa saat.' : 'Tidak dapat menghubungi server Gemini: ' + e.message);
    }
    result = await response.json().catch(() => ({}));
    if (response.ok) break;
    lastError = new Error(result.error?.message || ('HTTP ' + response.status));
    if (response.status === 503 && i < models.length - 1) continue;
    throw new Error('Gemini API (' + response.status + '): ' + lastError.message);
  }
  if (!response?.ok) throw new Error('Gemini sedang sibuk atau lambat. Coba lagi beberapa saat. ' + (lastError?.message || ''));

  const raw = result.candidates?.[0]?.content?.parts?.map(p => p.text || '').join('').trim();
  if (!raw) throw new Error('Gemini tidak mengembalikan teks. Periksa akses model dan kuota API key.');
  const cleaned = raw.trim().replace(/^\u0060\u0060\u0060(?:json)?\s*/i,'').replace(/\s*\u0060\u0060\u0060$/,'');
  let draft;
  try {
    draft = JSON.parse(cleaned);
  } catch {
    const start = cleaned.indexOf('{');
    const end = cleaned.lastIndexOf('}');
    if (start < 0 || end <= start) throw new Error('Format jawaban Gemini bukan JSON yang valid. Coba buat draft lagi.');
    try { draft = JSON.parse(cleaned.slice(start, end + 1)); }
    catch { throw new Error('Gemini mengirim format draft yang tidak bisa dibaca. Coba buat draft lagi.'); }
  }
  if (!draft || typeof draft !== 'object' || !Array.isArray(draft.slides)) {
    throw new Error('Struktur draft dari Gemini tidak lengkap. Coba buat draft lagi.');
  }
  const insertResult = await env.DB.prepare('INSERT INTO content_items (news_id,title,format,category,hook,body,caption,source_url,status,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)').bind(newsId,draft.title||article.title,'Carousel',article.category,draft.hook||'',(draft.slides||[]).map((x,i)=>`Slide ${i+1}: ${x}`).join('\n\n'),draft.caption||'',article.url,'DRAFT',new Date().toISOString()).run();
  return { id: insertResult.meta?.last_row_id, draft, source: article.url, status:'DRAFT — perlu pemeriksaan editorial' };
}

async function hashText(value) {
  const bytes = new TextEncoder().encode(value);
  const digest = await crypto.subtle.digest('SHA-256', bytes);
  return [...new Uint8Array(digest)].map(x=>x.toString(16).padStart(2,'0')).join('');
}
async function checkAgentLimit(request, env) {
  await env.DB.prepare("CREATE TABLE IF NOT EXISTS agent_usage (ip_hash TEXT NOT NULL, period TEXT NOT NULL, bucket TEXT NOT NULL, count INTEGER NOT NULL DEFAULT 0, PRIMARY KEY(ip_hash,period,bucket))").run();
  const ip = request.headers.get('CF-Connecting-IP') || 'unknown';
  const key = await hashText(ip);
  const hour = String(Math.floor(Date.now()/3600000));
  const day = new Date().toISOString().slice(0,10);
  for (const [period,bucket,limit] of [['hour',hour,12],['day',day,40]]) {
    await env.DB.prepare('INSERT INTO agent_usage (ip_hash,period,bucket,count) VALUES (?,?,?,1) ON CONFLICT(ip_hash,period,bucket) DO UPDATE SET count=count+1').bind(key,period,bucket).run();
    const row = await env.DB.prepare('SELECT count FROM agent_usage WHERE ip_hash=? AND period=? AND bucket=?').bind(key,period,bucket).first();
    if ((row?.count || 0) > limit) return {ok:false,period,limit};
  }
  return {ok:true};
}
async function runAgentTool(name,args,env) {
  if (name === 'search_news') {
    const q = String(args.query || '').trim().slice(0,120);
    const like = '%' + q.replace(/[\\%_]/g,'') + '%';
    const {results} = await env.DB.prepare('SELECT id,title,url,summary,category,source,published_at,status FROM news_items WHERE title LIKE ? OR summary LIKE ? OR source LIKE ? ORDER BY published_at DESC LIMIT 8').bind(like,like,like).all();
    return {items:results||[]};
  }
  if (name === 'get_latest_news') {
    const {results} = await env.DB.prepare('SELECT id,title,url,summary,category,source,published_at,status FROM news_items ORDER BY published_at DESC LIMIT 8').all();
    return {items:results||[]};
  }
  if (name === 'get_trends') {
    const {results} = await env.DB.prepare('SELECT id,title,url,summary,source,published_at FROM trend_items ORDER BY published_at DESC LIMIT 10').all();
    return {items:results||[]};
  }
  if (name === 'scan_news') return await scanNews(env);
  if (name === 'create_content_draft') {
    let id = Number(args.news_id);
    if (!Number.isInteger(id) || id < 1) {
      const title = String(args.news_title || '').trim().slice(0,240);
      if (!title) return {error:'ID berita database atau judul berita diperlukan. Ambil daftar berita terbaru terlebih dahulu.'};
      const found = await env.DB.prepare('SELECT id,title FROM news_items WHERE title=? ORDER BY published_at DESC LIMIT 1').bind(title).first();
      if (!found) return {error:'Berita tidak ditemukan berdasarkan judul. Ambil berita terbaru dari database lalu gunakan ID aslinya.'};
      id = Number(found.id);
    }
    const exists = await env.DB.prepare('SELECT id FROM news_items WHERE id=?').bind(id).first();
    if (!exists) {
      const title = String(args.news_title || '').trim().slice(0,240);
      if (title) {
        const found = await env.DB.prepare('SELECT id FROM news_items WHERE title=? ORDER BY published_at DESC LIMIT 1').bind(title).first();
        if (found) id = Number(found.id);
        else return {error:'Berita tidak ditemukan di database. Ambil daftar berita terbaru dan pilih berita yang benar-benar tersedia.'};
      } else return {error:'ID berita tidak cocok dengan database. Ambil daftar berita terbaru dan gunakan ID database yang sebenarnya, bukan nomor urut.'};
    }
    return await generateDraft(env,id);
  }
  if (name === 'get_latest_brief') {
    const row = await env.DB.prepare('SELECT payload,created_at FROM daily_briefs ORDER BY id DESC LIMIT 1').first();
    return {brief:row ? JSON.parse(row.payload) : null};
  }
  return {error:'Tool tidak tersedia.'};
}
async function agentChat(request,env) {
  if (!env.GEMINI_API_KEY) throw new Error('GEMINI_API_KEY belum dipasang sebagai Worker Secret.');
  const body = await request.json().catch(()=>null);
  if (!body || typeof body.message !== 'string' || !body.message.trim()) return json({error:'Tulis pesan terlebih dahulu.'},400,env);
  if (body.message.length > 3000) return json({error:'Pesan terlalu panjang. Maksimal 3.000 karakter.'},413,env);
  const usage = await checkAgentLimit(request,env);
  if (!usage.ok) return json({error:usage.period==='hour'?'Batas 12 pesan per jam tercapai. Coba lagi nanti.':'Batas 40 pesan per hari tercapai. Coba lagi besok.'},429,env);
  const history = Array.isArray(body.history) ? body.history.slice(-8).filter(x=>x && ['user','model'].includes(x.role) && typeof x.text==='string').map(x=>({role:x.role,parts:[{text:x.text.slice(0,2500)}]})) : [];
  const tools = [{functionDeclarations:[
    {name:'search_news',description:'Cari berita di database SKEMANYA berdasarkan kata kunci.',parameters:{type:'OBJECT',properties:{query:{type:'STRING',description:'Kata kunci pencarian'}},required:['query']}},
    {name:'get_latest_news',description:'Ambil delapan berita terbaru yang tersimpan.',parameters:{type:'OBJECT',properties:{}}},
    {name:'get_trends',description:'Ambil sepuluh tren terbaru yang tersimpan.',parameters:{type:'OBJECT',properties:{}}},
    {name:'scan_news',description:'Jalankan pemindaian RSS untuk mengambil berita dan tren baru. Tidak menerbitkan konten.',parameters:{type:'OBJECT',properties:{}}},
    {name:'create_content_draft',description:'Buat draft carousel dari berita yang benar-benar tersimpan. Selalu panggil get_latest_news atau search_news lebih dahulu, lalu gunakan nilai id database persis dari hasil tool (jangan gunakan nomor urut berita). Bisa gunakan news_id atau judul persis pada news_title. Hanya menyimpan sebagai DRAFT, tidak menerbitkan.',parameters:{type:'OBJECT',properties:{news_id:{type:'INTEGER',description:'ID database asli dari hasil get_latest_news/search_news, bukan nomor urut daftar'},news_title:{type:'STRING',description:'Judul berita persis seperti yang muncul dari hasil database'}}}},
    {name:'get_latest_brief',description:'Ambil Daily Intelligence Brief terbaru.',parameters:{type:'OBJECT',properties:{}}}
  ]}];
  const system = 'Kamu adalah SKEMANYA AI, asisten pribadi sekaligus asisten newsroom media SKEMANYA. Gunakan Bahasa Indonesia yang natural, ramah, ringkas, dan jujur. Bantu urusan pribadi umum, ide, perencanaan, pengambilan keputusan, riset, berita, tren, dan produksi konten. Kamu dapat memakai tools untuk membaca data newsroom, memindai RSS, dan membuat draft. Gunakan tools bila diminta atau relevan. Sebelum membuat draft, panggil get_latest_news atau search_news untuk mengambil berita beserta ID database aslinya. Jangan pernah menganggap nomor urut (misalnya berita nomor 2) sebagai news_id. Cocokkan judul yang diminta dengan hasil database, lalu kirim ID database yang benar ke create_content_draft; bila tidak cocok, tanyakan pilihan kepada pengguna. Jangan pernah mengaku telah menerbitkan konten; tidak ada tool penerbitan. Jangan mengarang data, tanggal, sumber, atau hasil tool. Untuk fakta dari berita, sebut sumber dan tautan bila tersedia. Draft harus mengikuti standar SKEMANYA: hook menarik tanpa clickbait, isi ringkas dengan poin penting, judul slide bukan pertanyaan, caption menambah konteks, dan catat hal yang perlu diverifikasi. Percakapan yang dikirim ke server tidak disimpan sebagai memori server; riwayat percakapan dikirim oleh browser.';
  const contents = [...history,{role:'user',parts:[{text:body.message.trim()}]}];
  const primaryModel = env.GEMINI_MODEL || 'gemini-3.5-flash-lite';
  const fallbackModel = primaryModel === 'gemini-3.5-flash-lite' ? 'gemini-3.8-flash' : 'gemini-3.5-flash-lite';
  let activeModel = primaryModel;
  let reply = '';
  const actions = [];
  for (let turn=0; turn<4; turn++) {
    let response, data, lastError;
    const modelsToTry = primaryModel === fallbackModel ? [primaryModel] : [activeModel, activeModel === primaryModel ? fallbackModel : primaryModel];
    for (const modelName of modelsToTry) {
      try {
        response = await fetch('https://generativelanguage.googleapis.com/v1beta/models/'+encodeURIComponent(modelName)+':generateContent',{
          method:'POST',
          headers:{'Content-Type':'application/json','x-goog-api-key':env.GEMINI_API_KEY},
          body:JSON.stringify({systemInstruction:{parts:[{text:system}]},contents,tools,generationConfig:{temperature:0.65,maxOutputTokens:700}}),
          signal:AbortSignal.timeout(25000)
        });
      } catch(e) {
        if (e.name === 'TimeoutError' && modelName !== modelsToTry[modelsToTry.length-1]) { lastError=e; continue; }
        throw new Error(e.name==='TimeoutError'?'Model utama dan cadangan sama-sama terlalu lambat. Coba lagi sebentar.':'Tidak dapat menghubungi Gemini: '+e.message);
      }
      data = await response.json().catch(()=>({}));
      if (response.ok) { activeModel = modelName; break; }
      if (response.status === 503 && modelName !== modelsToTry[modelsToTry.length-1]) { lastError=new Error(data.error?.message||'Model sedang sibuk'); continue; }
      throw new Error('Gemini API ('+response.status+'): '+(data.error?.message||'Permintaan gagal.'));
    }
    if (!response?.ok) throw new Error('Gemini sedang sibuk atau lambat. Coba lagi beberapa saat. '+(lastError?.message||''));
    const candidate=data.candidates?.[0];
    const parts=candidate?.content?.parts||[];
    const calls=parts.filter(p=>p.functionCall?.name);
    if (!calls.length) { reply=parts.map(p=>p.text||'').join('').trim(); break; }
    contents.push(candidate.content);
    for (const part of calls) {
      const call=part.functionCall;
      const result=await runAgentTool(call.name,call.args||{},env);
      actions.push({tool:call.name,result});
      contents.push({role:'user',parts:[{functionResponse:{name:call.name,response:{result}}}]});
    }
  }
  if (!reply) reply='Tugas selesai diproses. Coba tanyakan hasilnya jika belum terlihat.';
  return json({reply,actions,model:activeModel},200,env);
}

export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return new Response(null,{headers:cors(env)});
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, '') || '/';
    try {
      if (!env.DB) return json({ok:false,error:'D1 binding DB belum dikonfigurasi.'},500,env);
      if (path === '/api/agent/chat' && request.method === 'POST') return await agentChat(request,env);
      if (path === '/api/health') return json({ok:true,database:true,service:'SKEMANYA AI Media Manager Worker',time:new Date().toISOString()},200,env);
      if (path === '/api/news' && request.method === 'GET') {
        const limit = Math.min(Number(url.searchParams.get('limit') || 50),100);
        const {results} = await env.DB.prepare('SELECT id,title,url,summary,category,source,published_at,status FROM news_items ORDER BY published_at DESC LIMIT ?').bind(limit).all();
        return json({items:results||[]},200,env);
      }
      if (path === '/api/trends' && request.method === 'GET') {
        const limit = Math.min(Number(url.searchParams.get('limit') || 50),100);
        const {results} = await env.DB.prepare('SELECT id,title,url,summary,source,published_at FROM trend_items ORDER BY published_at DESC LIMIT ?').bind(limit).all();
        return json({items:results||[]},200,env);
      }
      if (path === '/api/scan' && request.method === 'POST') return json(await scanNews(env),200,env);
      if (path === '/api/automation/run' && request.method === 'POST') {
        const body = await request.json().catch(()=>({}));
        if (!['news_scan','all'].includes(body.task || 'news_scan')) return json({error:'Task tidak dikenal.'},400,env);
        const result = await scanNews(env);
        return json({ok:true,...result},200,env);
      }
      if (path === '/api/content' && request.method === 'GET') {
        const limit = Math.min(Number(url.searchParams.get('limit') || 20),100);
        const {results} = await env.DB.prepare('SELECT id,title,format,category,hook,body,caption,source_url,status,created_at FROM content_items ORDER BY created_at DESC LIMIT ?').bind(limit).all();
        return json({items:results||[]},200,env);
      }
      if (path === '/api/content/generate' && request.method === 'GET') {
        return json({ok:true, endpoint:'/api/content/generate', method:'POST', example_body:{news_id:1}, message:'Endpoint aktif. Kirim POST dengan JSON {"news_id":1} untuk membuat draft.'},200,env);
      }
      if (path === '/api/content/generate' && request.method === 'POST') {
        const body = await request.json().catch(() => null);
        if (!body || typeof body !== 'object') return json({error:'Body harus berupa JSON yang valid.'},400,env);
        const newsId = Number(body.news_id);
        if (!Number.isInteger(newsId) || newsId < 1) return json({error:'news_id wajib berupa angka positif.'},400,env);
        return json(await generateDraft(env,newsId),200,env);
      }
      if (path === '/api/brief/latest' && request.method === 'GET') {
        const row = await env.DB.prepare('SELECT payload,created_at FROM daily_briefs ORDER BY id DESC LIMIT 1').first();
        return json({brief:row ? JSON.parse(row.payload) : null},200,env);
      }
      if (path === '/api/runs' && request.method === 'GET') {
        const {results} = await env.DB.prepare('SELECT * FROM automation_runs ORDER BY id DESC LIMIT 30').all();
        return json({items:results||[]},200,env);
      }
      if (!path.startsWith('/api/') && env.ASSETS) return env.ASSETS.fetch(request);
      return json({error:'Endpoint tidak ditemukan.'},404,env);
    } catch (e) { return json({error:e.message || 'Internal error'},500,env); }
  },
  async scheduled(event, env, ctx) {
    ctx.waitUntil((async()=>{
      try {
        await scanNews(env);
        if (event.cron === '0 17 * * *') await createDailyBrief(env);
      } catch(e) {
        await env.DB.prepare('INSERT INTO automation_runs (task,status,details,created_at) VALUES (?,?,?,?)').bind('scheduled_scan','FAILED',JSON.stringify({error:e.message}),new Date().toISOString()).run();
      }
    })());
  }
};

// Deployment sync marker: confirms GitHub-connected Cloudflare build pipeline.

// Gemini Interactions API migration verified in source; deployment trigger.
