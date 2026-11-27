package id.skemanya.localai

import android.app.Activity
import android.app.DownloadManager
import android.content.Context
import android.database.Cursor
import android.graphics.Color
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import com.google.ai.edge.litertlm.Backend
import com.google.ai.edge.litertlm.Contents
import com.google.ai.edge.litertlm.Conversation
import com.google.ai.edge.litertlm.ConversationConfig
import com.google.ai.edge.litertlm.Engine
import com.google.ai.edge.litertlm.EngineConfig
import java.io.File
import java.util.concurrent.Executors

class MainActivity : Activity() {
    companion object {
        private const val MODEL_FILE = "Qwen2.5-1.5B-Instruct_multi-prefill-seq_q8_ekv4096.litertlm"
        private const val MODEL_BYTES = 1_597_931_520L
        private const val MODEL_URL = "https://huggingface.co/litert-community/Qwen2.5-1.5B-Instruct/resolve/main/Qwen2.5-1.5B-Instruct_multi-prefill-seq_q8_ekv4096.litertlm"
    }

    private val worker = Executors.newSingleThreadExecutor()
    private val mainHandler = Handler(Looper.getMainLooper())
    private var engine: Engine? = null
    private var conversation: Conversation? = null
    private var downloadId: Long? = null
    private lateinit var status: TextView
    private lateinit var chat: TextView
    private lateinit var input: EditText
    private lateinit var loadButton: Button
    private lateinit var sendButton: Button
    private lateinit var scroll: ScrollView
    private lateinit var modelFile: File

    private val downloadPoll = object : Runnable {
        override fun run() {
            val id = downloadId ?: return
            val manager = getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
            var cursor: Cursor? = null
            try {
                cursor = manager.query(DownloadManager.Query().setFilterById(id))
                if (cursor == null || !cursor.moveToFirst()) {
                    setStatus("Status unduhan belum tersedia.")
                    return
                }
                val state = cursor.getInt(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_STATUS))
                when (state) {
                    DownloadManager.STATUS_SUCCESSFUL -> {
                        val actual = modelFile.length()
                        if (modelFile.exists() && actual == MODEL_BYTES) {
                            downloadId = null
                            setStatus("Model selesai diunduh. Menyiapkan mesin AI…")
                            initializeModel()
                        } else {
                            downloadId = null
                            setStatus("Unduhan selesai tetapi ukuran file tidak cocok. Hapus file model lalu coba lagi.")
                            loadButton.isEnabled = true
                        }
                    }
                    DownloadManager.STATUS_FAILED -> {
                        val reason = cursor.getInt(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_REASON))
                        downloadId = null
                        setStatus("Unduhan gagal (kode $reason). Periksa koneksi internet lalu coba lagi.")
                        loadButton.isEnabled = true
                    }
                    else -> {
                        val downloaded = cursor.getLong(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR))
                        val total = cursor.getLong(cursor.getColumnIndexOrThrow(DownloadManager.COLUMN_TOTAL_SIZE_BYTES))
                        val percent = if (total > 0) (downloaded * 100 / total).toInt() else 0
                        setStatus("Mengunduh model Qwen 1.5B: $percent%")
                        mainHandler.postDelayed(this, 1000)
                    }
                }
            } catch (e: Exception) {
                setStatus("Tidak dapat memeriksa unduhan: ${e.message}")
                loadButton.isEnabled = true
            } finally {
                cursor?.close()
            }
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = Color.rgb(11, 11, 13)
        window.navigationBarColor = Color.rgb(11, 11, 13)
        modelFile = File(getExternalFilesDir(null), MODEL_FILE)
        buildScreen()
        setStatus("AI lokal belum aktif. Unduh model satu kali untuk mulai.")
        if (modelFile.exists() && modelFile.length() == MODEL_BYTES) {
            loadButton.text = "Aktifkan model yang sudah diunduh"
        }
    }

    private fun buildScreen() {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(24, 28, 24, 20)
            setBackgroundColor(Color.rgb(11, 11, 13))
        }

        val title = TextView(this).apply {
            text = "SKEMANYA AI"
            textSize = 24f
            setTextColor(Color.WHITE)
        }
        root.addView(title)

        val subtitle = TextView(this).apply {
            text = "MESIN AI LOKAL · ANDROID"
            textSize = 11f
            setTextColor(Color.rgb(167, 174, 184))
            setPadding(0, 4, 0, 18)
        }
        root.addView(subtitle)

        status = TextView(this).apply {
            textSize = 13f
            setTextColor(Color.rgb(220, 225, 232))
            setPadding(14, 14, 14, 14)
            setBackgroundColor(Color.rgb(27, 29, 34))
        }
        root.addView(status, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))

        loadButton = Button(this).apply {
            text = "Unduh & aktifkan AI lokal"
            setOnClickListener { downloadOrLoadModel() }
        }
        root.addView(loadButton, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply { topMargin = 12 })

        scroll = ScrollView(this).apply {
            setBackgroundColor(Color.rgb(19, 20, 24))
            isFillViewport = true
        }
        chat = TextView(this).apply {
            text = "Halo! Aku asisten AI lokal SKEMANYA.\n\nModel berjalan di perangkat setelah berhasil dimuat."
            textSize = 15f
            setTextColor(Color.WHITE)
            setPadding(14, 14, 14, 14)
        }
        scroll.addView(chat)
        root.addView(scroll, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f).apply { topMargin = 14; bottomMargin = 12 })

        input = EditText(this).apply {
            hint = "Tulis pesan…"
            setHintTextColor(Color.GRAY)
            setTextColor(Color.WHITE)
            setSingleLine(false)
            minLines = 1
            maxLines = 4
            setBackgroundColor(Color.rgb(27, 29, 34))
            setPadding(12, 10, 12, 10)
        }
        root.addView(input, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT))

        sendButton = Button(this).apply {
            text = "Kirim"
            isEnabled = false
            setOnClickListener { sendMessage() }
        }
        root.addView(sendButton, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT).apply { topMargin = 8 })

        setContentView(root)
    }

    private fun downloadOrLoadModel() {
        if (downloadId != null) return
        if (modelFile.exists() && modelFile.length() == MODEL_BYTES) {
            setStatus("File model ditemukan. Menyiapkan mesin AI…")
            loadButton.isEnabled = false
            initializeModel()
            return
        }

        loadButton.isEnabled = false
        setStatus("Memulai unduhan model sekitar 1,6 GB. Gunakan Wi-Fi dan jangan tutup aplikasi.")
        try {
            val request = DownloadManager.Request(android.net.Uri.parse(MODEL_URL))
                .setTitle("Model AI SKEMANYA")
                .setDescription("Mengunduh Qwen2.5 1.5B untuk penggunaan lokal")
                .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                .setAllowedOverMetered(true)
                .setAllowedOverRoaming(false)
                .setDestinationInExternalFilesDir(this, null, MODEL_FILE)
            val manager = getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
            downloadId = manager.enqueue(request)
            mainHandler.post(downloadPoll)
        } catch (e: Exception) {
            setStatus("Tidak dapat memulai unduhan: ${e.message}")
            loadButton.isEnabled = true
        }
    }

    private fun initializeModel() {
        worker.execute {
            try {
                val candidate = Engine(
                    EngineConfig(
                        modelPath = modelFile.absolutePath,
                        backend = Backend.CPU(),
                        cacheDir = cacheDir.absolutePath
                    )
                )
                candidate.initialize()
                val newConversation = candidate.createConversation(
                    ConversationConfig(
                        systemInstruction = Contents.of(
                            "Kamu adalah asisten editorial SKEMANYA. Jawab dalam bahasa Indonesia, ringkas, akurat, dan jangan mengarang fakta. Saat membuat konten, susun hook, isi, dan caption."
                        )
                    )
                )
                engine = candidate
                conversation = newConversation
                runOnUiThread {
                    setStatus("AI lokal aktif. Percakapan diproses di perangkat.")
                    loadButton.text = "AI lokal aktif"
                    loadButton.isEnabled = false
                    sendButton.isEnabled = true
                }
            } catch (e: Exception) {
                runOnUiThread {
                    setStatus("Gagal menyiapkan mesin AI: ${e.message}")
                    loadButton.isEnabled = true
                }
            }
        }
    }

    private fun sendMessage() {
        val text = input.text.toString().trim()
        if (text.isEmpty() || conversation == null) return
        input.setText("")
        appendChat("\n\nLO: $text\n\nSKEMANYA AI: ")
        sendButton.isEnabled = false
        worker.execute {
            try {
                val answer = conversation?.sendMessage(text)?.toString() ?: "Tidak ada jawaban."
                runOnUiThread {
                    appendChat(answer)
                    sendButton.isEnabled = true
                }
            } catch (e: Exception) {
                runOnUiThread {
                    appendChat("\n[Kesalahan: ${e.message}]")
                    sendButton.isEnabled = true
                }
            }
        }
    }

    private fun appendChat(text: String) {
        chat.append(text)
        scroll.post { scroll.fullScroll(ScrollView.FOCUS_DOWN) }
    }

    private fun setStatus(message: String) {
        if (::status.isInitialized) status.text = message
    }

    override fun onDestroy() {
        mainHandler.removeCallbacks(downloadPoll)
        worker.execute {
            try { conversation?.close() } catch (_: Exception) {}
            conversation = null
            try { engine?.close() } catch (_: Exception) {}
            engine = null
        }
        worker.shutdown()
        super.onDestroy()
    }
}
