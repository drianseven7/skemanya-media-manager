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
  const model = 'gemini-3.8-flash';
  const prompt = `Kamu editor SKEMANYA, media fakta, data, dan lifestyle. Buat DRAFT carousel Instagram Bahasa Indonesia berdasarkan bahan sumber berikut. Jangan menambahkan fakta di luar bahan. Tandai hal yang belum diketahui. Gaya: hook menarik tanpa clickbait, 5-7 slide, teks sedang dan ringkas, judul slide bukan pertanyaan, caption menambah konteks. Kembalikan JSON valid tanpa markdown dengan keys title,hook,slides (array string),caption,verification_notes. Sumber: ${article.source} — ${article.url}\nJudul: ${article.title}\nRingkasan: ${article.summary}`;
  const response = await fetch('https://generativelanguage.googleapis.com/v1beta/interactions', { method:'POST', headers:{'Content-Type':'application/json','x-goog-api-key':env.GEMINI_API_KEY}, body:JSON.stringify({model,input:prompt,store:false}) });
  if (!response.ok) throw new Error(`Gemini Interactions API ${response.status}: ${await response.text()}`);
  const data = await response.json();
  const outputStep = (data.steps || []).slice().reverse().find(step => step.type === 'model_output');
  const raw = outputStep?.content?.filter(part => part.type === 'text').map(part => part.text).join('\n') || data.output_text;
  if (!raw) throw new Error('Gemini tidak mengembalikan konten.');
  const cleaned = raw.trim().replace(/^```(?:json)?\s*/i,'').replace(/\s*```$/,'');
  const draft = JSON.parse(cleaned);
  const result = await env.DB.prepare('INSERT INTO content_items (news_id,title,format,category,hook,body,caption,source_url,status,created_at) VALUES (?,?,?,?,?,?,?,?,?,?)').bind(newsId,draft.title||article.title,'Carousel',article.category,draft.hook||'',(draft.slides||[]).map((x,i)=>`Slide ${i+1}: ${x}`).join('\n\n'),draft.caption||'',article.url,'DRAFT',new Date().toISOString()).run();
  return { id: result.meta?.last_row_id, draft, source: article.url, status:'DRAFT — perlu pemeriksaan editorial' };
}
export default {
  async fetch(request, env) {
    if (request.method === 'OPTIONS') return new Response(null,{headers:cors(env)});
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, '') || '/';
    try {
      if (!env.DB) return json({ok:false,error:'D1 binding DB belum dikonfigurasi.'},500,env);
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
