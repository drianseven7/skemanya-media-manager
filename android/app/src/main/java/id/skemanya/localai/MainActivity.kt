package id.skemanya.localai

import android.app.Activity
import android.app.AlertDialog
import android.content.Intent
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.Uri
import android.os.Bundle
import android.util.Xml
import android.view.Gravity
import android.view.ViewGroup
import android.widget.*
import org.json.JSONArray
import org.json.JSONObject
import org.xmlpull.v1.XmlPullParser
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

class MainActivity : Activity() {
    private val bg = Color.rgb(11, 11, 13)
    private val panel = Color.rgb(25, 27, 32)
    private val silver = Color.rgb(167, 174, 184)
    private val white = Color.WHITE
    private val io = Executors.newSingleThreadExecutor()
    private val prefs by lazy { getSharedPreferences("skemanya_local", MODE_PRIVATE) }
    private val articles = mutableListOf<JSONObject>()
    private val drafts = mutableListOf<String>()
    private lateinit var body: LinearLayout
    private lateinit var status: TextView
    private lateinit var heading: TextView
    private lateinit var navBar: LinearLayout
    private var page = "Beranda"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = bg
        window.navigationBarColor = bg
        loadData()
        setContentView(buildShell())
        showPage("Beranda")
    }

    private fun buildShell(): android.view.View {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(18), dp(20), dp(10))
            setBackgroundColor(bg)
        }
        val top = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER_VERTICAL }
        val mark = TextView(this).apply {
            text = "S"; textSize = 23f; gravity = Gravity.CENTER; setTextColor(bg)
            setTypeface(null, android.graphics.Typeface.BOLD)
            background = rounded(Color.rgb(226, 230, 236), 16)
        }
        top.addView(mark, LinearLayout.LayoutParams(dp(48), dp(48)))
        val brand = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(dp(12), 0, 0, 0) }
        brand.addView(TextView(this).apply {
            text = "SKEMANYA"; textSize = 17f; letterSpacing = .12f
            setTextColor(white); setTypeface(null, android.graphics.Typeface.BOLD)
        })
        brand.addView(TextView(this).apply {
            text = "NEWSROOM"; textSize = 9f; letterSpacing = .18f; setTextColor(silver)
        })
        top.addView(brand, LinearLayout.LayoutParams(0, -2, 1f))
        top.addView(TextView(this).apply {
            text = "●  LIVE"; textSize = 10f; setTextColor(Color.rgb(150, 220, 177))
            setPadding(dp(11), dp(8), dp(11), dp(8)); background = rounded(Color.rgb(27, 48, 39), 30)
        })
        root.addView(top)
        status = TextView(this).apply {
            textSize = 11f; setTextColor(silver); setPadding(dp(12), dp(10), dp(12), dp(10))
            background = rounded(panel, 12)
        }
        root.addView(status, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(18) })
        heading = TextView(this).apply {
            textSize = 23f; setTextColor(white); setTypeface(null, android.graphics.Typeface.BOLD)
            setPadding(0, dp(20), 0, dp(14))
        }
        root.addView(heading)
        val scroll = ScrollView(this).apply { isFillViewport = true; clipToPadding = false }
        body = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(0, 0, 0, dp(14)) }
        scroll.addView(body)
        root.addView(scroll, LinearLayout.LayoutParams(-1, 0, 1f))
        navBar = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL; gravity = Gravity.CENTER
            setPadding(dp(5), dp(7), dp(5), dp(7)); background = rounded(Color.rgb(24, 26, 31), 22)
        }
        root.addView(navBar, LinearLayout.LayoutParams(-1, dp(68)).apply { topMargin = dp(8) })
        return root
    }

    private fun refreshNavigation() {
        navBar.removeAllViews()
        val items = listOf(
            Triple("Beranda", "⌂", "Beranda"), Triple("Berita", "◉", "Berita"),
            Triple("Draft", "✎", "Draft"), Triple("Agenda", "▦", "Agenda"), Triple("Arsip", "▣", "Arsip")
        )
        items.forEach { item ->
            val selected = page == item.first
            val cell = LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL; gravity = Gravity.CENTER
                setPadding(dp(2), dp(5), dp(2), dp(4))
                background = if (selected) rounded(Color.rgb(54, 58, 67), 16) else null
                isClickable = true; isFocusable = true
                setOnClickListener { showPage(item.first) }
            }
            cell.addView(TextView(this).apply {
                text = item.second; textSize = 19f; gravity = Gravity.CENTER
                setTextColor(if (selected) white else Color.rgb(125, 132, 143))
            })
            cell.addView(TextView(this).apply {
                text = item.third; textSize = 9f; gravity = Gravity.CENTER
                setTextColor(if (selected) white else Color.rgb(139, 145, 155))
                if (selected) setTypeface(null, android.graphics.Typeface.BOLD)
            })
            navBar.addView(cell, LinearLayout.LayoutParams(0, -1, 1f))
        }
    }

    private fun showPage(name: String) {
        page = name
        if (::navBar.isInitialized) refreshNavigation()
        body.removeAllViews()
        heading.text = when (name) {
            "Beranda" -> "Pusat kendali newsroom"
            "Berita" -> "Penemuan berita"
            "Draft" -> "Studio konten"
            "Agenda" -> "Agenda editorial"
            else -> "Arsip tersimpan"
        }
        status.text = if (isOnline()) "ONLINE · INTERNET TERSEDIA" else "OFFLINE · MODE LOKAL AKTIF"
        when (name) {
            "Beranda" -> {
                card("RINGKASAN") {
                    textLine("Koleksi berita: " + articles.size, 17f, white, true)
                    textLine("Draft konten: " + drafts.size, 14f, silver)
                    textLine("Data tersimpan di perangkat. Tidak membutuhkan akun atau server.", 12f, silver)
                }
                card("AGEN BERITA") {
                    textLine("Ambil artikel dari sumber RSS saat internet tersedia. Hasilnya disimpan agar tetap bisa dibaca offline.", 13f, white)
                    actionButton("PERIKSA BERITA TERBARU") { fetchFeeds() }
                }
                card("AKSES CEPAT") {
                    actionButton("BUKA BANK BERITA") { showPage("Berita") }
                    actionButton("BUAT DRAFT KONTEN") { showPage("Draft") }
                    actionButton("LIHAT ARSIP") { showPage("Arsip") }
                }
            }
            "Berita" -> {
                body.textLine("Sumber awal: ANTARA dan BBC Indonesia. Pemeriksaan membutuhkan internet.", 12f, silver)
                body.actionButton("↻  PERIKSA BERITA TERBARU") { fetchFeeds() }
                if (articles.isEmpty()) body.textLine("Belum ada berita tersimpan. Hubungkan internet untuk mengambil RSS.", 14f, silver)
                articles.sortedByDescending { it.optLong("published", 0L) }.forEach { articleCard(it) }
            }
            "Arsip" -> {
                val saved = articles.filter { it.optBoolean("saved", false) }
                body.textLine(saved.size.toString() + " artikel disimpan di perangkat.", 12f, silver)
                if (saved.isEmpty()) body.textLine("Arsip masih kosong.", 14f, silver)
                saved.forEach { articleCard(it) }
            }
            "Draft" -> {
                body.textLine("Draft disimpan secara lokal dan tersedia tanpa internet.", 12f, silver)
                body.actionButton("+  BUAT DRAFT") { draftDialog("Draft konten baru") }
                drafts.toList().forEachIndexed { index, draft ->
                    card("DRAFT " + (index + 1)) {
                        textLine(draft, 14f, white)
                        actionButton("HAPUS DRAFT") {
                            drafts.remove(draft); saveDrafts(); showPage("Draft")
                        }
                    }
                }
                if (drafts.isEmpty()) body.textLine("Belum ada draft konten.", 14f, silver)
            }
            "Agenda" -> card("RUANG KERJA") {
                textLine("Catatan agenda editorial dapat disimpan di perangkat. Sinkronisasi tim akan ditambahkan saat backend tersedia.", 13f, silver)
                actionButton("BUAT CATATAN AGENDA") { draftDialog("Catatan agenda") }
            }
        }
    }

    private fun articleCard(item: JSONObject) {
        card(item.optString("source", "SUMBER").uppercase()) {
            textLine(item.optString("title"), 15f, white, true)
            val desc = item.optString("description")
            if (desc.isNotBlank()) textLine(desc.take(240), 12f, silver)
            textLine(item.optString("category", "Berita") + " · " + item.optString("date", "Tanggal tidak tersedia"), 10f, silver)
            actionButton("BUKA SUMBER") {
                val link = item.optString("link")
                if (link.startsWith("https://")) startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(link)))
            }
            actionButton(if (item.optBoolean("saved")) "HAPUS DARI ARSIP" else "SIMPAN KE ARSIP") {
                item.put("saved", !item.optBoolean("saved"))
                saveArticles()
                showPage(page)
            }
        }
    }

    private fun draftDialog(title: String) {
        val input = EditText(this).apply {
            hint = "Tulis ide, hook, atau materi konten…"
            minLines = 4
            gravity = Gravity.TOP
        }
        AlertDialog.Builder(this).setTitle(title).setView(input)
            .setNegativeButton("BATAL", null)
            .setPositiveButton("SIMPAN") { _, _ ->
                val value = input.text.toString().trim()
                if (value.isNotEmpty()) { drafts.add(0, value); saveDrafts(); showPage("Draft") }
            }.show()
    }

    private fun fetchFeeds() {
        if (!isOnline()) {
            Toast.makeText(this, "Tidak ada internet. Data lokal tetap tersedia.", Toast.LENGTH_LONG).show()
            showPage(page)
            return
        }
        status.text = "AGEN BERITA AKTIF · MENGAMBIL RSS…"
        io.execute {
            val feeds = listOf(
                "ANTARA" to "https://www.antaranews.com/rss/terkini.xml",
                "BBC Indonesia" to "https://feeds.bbci.co.uk/indonesia/rss.xml"
            )
            var added = 0
            val failed = mutableListOf<String>()
            feeds.forEach { feed ->
                try {
                    val entries = parseFeed(feed.first, feed.second)
                    synchronized(articles) {
                        entries.forEach { entry ->
                            val link = entry.optString("link")
                            if (link.isNotBlank() && articles.none { it.optString("link") == link }) {
                                articles.add(0, entry); added++
                            }
                        }
                    }
                } catch (_: Exception) { failed.add(feed.first) }
            }
            saveArticles()
            runOnUiThread {
                status.text = "AGEN SELESAI · " + added + " ARTIKEL BARU" +
                    if (failed.isEmpty()) "" else " · GAGAL: " + failed.joinToString()
                showPage(page)
                Toast.makeText(this, "Pemeriksaan selesai: " + added + " berita baru.", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun parseFeed(source: String, address: String): List<JSONObject> {
        val connection = URL(address).openConnection() as HttpURLConnection
        connection.connectTimeout = 10000
        connection.readTimeout = 12000
        connection.setRequestProperty("User-Agent", "SKEMANYA-Newsroom/1.0")
        try {
            connection.inputStream.use { stream ->
                val parser = Xml.newPullParser()
                parser.setInput(stream, null)
                val result = mutableListOf<JSONObject>()
                var event = parser.eventType
                var inside = false
                var title = ""; var link = ""; var desc = ""; var date = ""; var tag = ""
                while (event != XmlPullParser.END_DOCUMENT && result.size < 50) {
                    when (event) {
                        XmlPullParser.START_TAG -> {
                            tag = parser.name.lowercase()
                            if (tag == "item" || tag == "entry") {
                                inside = true; title = ""; link = ""; desc = ""; date = ""
                            } else if (inside && tag == "link") {
                                val href = parser.getAttributeValue(null, "href")
                                if (!href.isNullOrBlank()) link = href
                            }
                        }
                        XmlPullParser.TEXT, XmlPullParser.CDSECT -> if (inside) {
                            when (tag) {
                                "title" -> title += parser.text
                                "link" -> link += parser.text
                                "description", "summary", "content:encoded" -> desc += parser.text
                                "pubdate", "published", "updated", "dc:date" -> date += parser.text
                            }
                        }
                        XmlPullParser.END_TAG -> if (inside && (parser.name.equals("item", true) || parser.name.equals("entry", true))) {
                            if (title.isNotBlank() && link.trim().startsWith("http")) {
                                result.add(JSONObject().apply {
                                    put("source", source); put("title", title.trim()); put("link", link.trim())
                                    put("description", android.text.Html.fromHtml(desc, android.text.Html.FROM_HTML_MODE_COMPACT).toString().trim())
                                    put("date", date.trim()); put("published", System.currentTimeMillis())
                                    put("category", "Berita"); put("saved", false)
                                })
                            }
                            inside = false
                        }
                    }
                    event = parser.next()
                }
                return result
            }
        } finally { connection.disconnect() }
    }

    private fun loadData() {
        val saved = JSONArray(prefs.getString("articles", "[]") ?: "[]")
        for (i in 0 until saved.length()) articles.add(saved.getJSONObject(i))
        val savedDrafts = JSONArray(prefs.getString("drafts", "[]") ?: "[]")
        for (i in 0 until savedDrafts.length()) drafts.add(savedDrafts.getString(i))
    }

    private fun saveArticles() {
        val array = JSONArray()
        synchronized(articles) { articles.forEach { array.put(it) } }
        prefs.edit().putString("articles", array.toString()).apply()
    }

    private fun saveDrafts() {
        val array = JSONArray()
        drafts.forEach { array.put(it) }
        prefs.edit().putString("drafts", array.toString()).apply()
    }

    private fun isOnline(): Boolean {
        val manager = getSystemService(CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = manager.activeNetwork ?: return false
        val caps = manager.getNetworkCapabilities(network) ?: return false
        return caps.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
    }

    private fun card(label: String, content: LinearLayout.() -> Unit) {
        val box = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL; setPadding(dp(17), dp(16), dp(17), dp(15))
            background = rounded(panel, 20)
        }
        box.addView(TextView(this).apply {
            text = label; textSize = 10f; setTextColor(silver); letterSpacing = .12f
            setTypeface(null, android.graphics.Typeface.BOLD); setPadding(0, 0, 0, dp(10))
        })
        box.content()
        body.addView(box, LinearLayout.LayoutParams(-1, -2).apply { bottomMargin = dp(12) })
    }

    private fun LinearLayout.textLine(value: String, size: Float, color: Int, bold: Boolean = false) {
        addView(TextView(this@MainActivity).apply {
            text = value; textSize = size; setTextColor(color)
            setLineSpacing(dp(3).toFloat(), 1f)
            if (bold) setTypeface(null, android.graphics.Typeface.BOLD)
            setPadding(0, dp(2), 0, dp(7))
        })
    }

    private fun LinearLayout.actionButton(label: String, action: () -> Unit) {
        val button = TextView(this@MainActivity).apply {
            text = label; textSize = 12f; gravity = Gravity.CENTER; letterSpacing = .02f
            setTextColor(white); setTypeface(null, android.graphics.Typeface.BOLD)
            setPadding(dp(14), dp(13), dp(14), dp(13))
            background = rounded(Color.rgb(57, 63, 74), 14)
            isClickable = true; isFocusable = true; setOnClickListener { action() }
        }
        addView(button, LinearLayout.LayoutParams(-1, -2).apply { topMargin = dp(7) })
    }

    private fun rounded(color: Int, radius: Int): GradientDrawable =
        GradientDrawable().apply { setColor(color); cornerRadius = dp(radius).toFloat() }

    private fun matchWrap() = LinearLayout.LayoutParams(-1, -2)
    private fun dp(value: Int) = (value * resources.displayMetrics.density).toInt()

    override fun onDestroy() {
        io.shutdown()
        super.onDestroy()
    }
}
