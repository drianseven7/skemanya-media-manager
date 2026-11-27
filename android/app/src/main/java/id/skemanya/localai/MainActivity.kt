package id.skemanya.localai

import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import org.json.JSONObject
import java.io.File
import java.util.concurrent.Executors

class MainActivity : Activity() {
    private val bg = Color.rgb(11, 11, 13)
    private val panel = Color.rgb(27, 29, 34)
    private val muted = Color.rgb(167, 174, 184)
    private val white = Color.WHITE
    private val worker = Executors.newSingleThreadExecutor()

    @Volatile private var languageModel: OnnxLanguageModel? = null
    private lateinit var status: TextView
    private lateinit var chat: LinearLayout
    private lateinit var promptInput: EditText
    private lateinit var sendButton: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = bg
        window.navigationBarColor = bg
        window.decorView.systemUiVisibility = 0
        setContentView(buildScreen())
        initializeLocalModel()
    }

    private fun buildScreen(): View {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(28), dp(20), dp(18))
            setBackgroundColor(bg)
        }

        root.addView(TextView(this).apply {
            text = "SKEMANYA AI"
            textSize = 28f
            setTextColor(white)
        })
        root.addView(TextView(this).apply {
            text = "MODEL BAHASA INDONESIA · LOKAL"
            textSize = 11f
            setTextColor(muted)
            setPadding(0, dp(5), 0, dp(16))
        })

        status = TextView(this).apply {
            text = "MEMERIKSA MODEL LOKAL…"
            textSize = 13f
            setTextColor(white)
            setLineSpacing(dp(4).toFloat(), 1f)
            setPadding(dp(14), dp(14), dp(14), dp(14))
            setBackgroundColor(panel)
        }
        root.addView(status, matchWrap())

        root.addView(TextView(this).apply {
            text = "RUANG PERCAKAPAN"
            textSize = 12f
            setTextColor(muted)
            setPadding(0, dp(20), 0, dp(10))
        })

        val chatScroll = ScrollView(this).apply {
            setBackgroundColor(Color.rgb(19, 20, 24))
            isFillViewport = true
        }
        chat = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(14), dp(14), dp(14), dp(14))
        }
        addMessage("SKEMANYA", "Aplikasi siap memuat model bahasa lokal. Jika model belum terpasang, ruang chat akan tetap terkunci.")
        chatScroll.addView(chat)
        root.addView(chatScroll, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f
        ).apply {
            bottomMargin = dp(12)
        })

        val composer = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
        }
        promptInput = EditText(this).apply {
            hint = "Tulis pesan…"
            setHintTextColor(Color.GRAY)
            setTextColor(white)
            textSize = 14f
            isEnabled = false
            setPadding(dp(12), dp(10), dp(12), dp(10))
            setBackgroundColor(panel)
        }
        composer.addView(promptInput, LinearLayout.LayoutParams(0, dp(52), 1f))
        sendButton = Button(this).apply {
            text = "KIRIM"
            isEnabled = false
            setOnClickListener { sendMessage() }
        }
        composer.addView(sendButton, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.WRAP_CONTENT, dp(52)
        ).apply { leftMargin = dp(8) })
        root.addView(composer)

        root.addView(TextView(this).apply {
            text = "OFFLINE · TANPA API EKSTERNAL · PROTOTIPE EKSPERIMENTAL"
            textSize = 9f
            setTextColor(muted)
            gravity = Gravity.CENTER
            setPadding(0, dp(12), 0, 0)
        }, matchWrap())
        return root
    }

    private fun initializeLocalModel() {
        worker.execute {
            try {
                val modelFile = copyAssetToFiles("skemanya.onnx")
                val tokenizerFile = copyAssetToFiles("skemanya_id.model")
                val configFile = copyAssetToFiles("training_config.json")
                val config = JSONObject(configFile.readText()).getJSONObject("config")
                val contextLength = config.optInt("context", 128)
                val codec = SentencePiece4JCodec(tokenizerFile.absolutePath)
                val loaded = OnnxLanguageModel(
                    modelPath = modelFile.absolutePath,
                    tokenizer = codec,
                    contextLength = contextLength,
                    maxNewTokens = 64
                )
                languageModel = loaded
                runOnUiThread {
                    status.text = "MODEL LOKAL AKTIF\nPrototipe dari pelatihan internal. Kualitas jawaban masih eksperimental dan belum layak untuk keputusan penting."
                    promptInput.isEnabled = true
                    sendButton.isEnabled = true
                    addMessage("SKEMANYA", "Model lokal berhasil dimuat. Silakan uji percakapan eksperimental.")
                }
            } catch (error: Exception) {
                runOnUiThread {
                    status.text = "MODEL BELUM TERPASANG\nAPK ini belum memiliki pasangan model ONNX dan tokenizer yang cocok. Chat dikunci agar tidak memberi kesan AI sudah berjalan."
                    promptInput.isEnabled = false
                    sendButton.isEnabled = false
                }
            }
        }
    }

    private fun copyAssetToFiles(name: String): File {
        val target = File(filesDir, name)
        assets.open(name).use { input ->
            target.outputStream().use { output -> input.copyTo(output) }
        }
        if (!target.isFile || target.length() == 0L) {
            throw IllegalStateException("Aset model kosong: $name")
        }
        return target
    }

    private fun sendMessage() {
        val text = promptInput.text.toString().trim()
        if (text.isEmpty()) return
        val activeModel = languageModel ?: return
        promptInput.setText("")
        promptInput.isEnabled = false
        sendButton.isEnabled = false
        addMessage("ANDA", text)
        addMessage("SKEMANYA", "Sedang memproses secara lokal…")

        worker.execute {
            try {
                val answer = activeModel.generate("<|user|>\n$text\n<|assistant|>\n")
                runOnUiThread {
                    if (chat.childCount > 0) chat.removeViewAt(chat.childCount - 1)
                    addMessage("SKEMANYA", answer.ifBlank { "Model belum menghasilkan teks. Coba prompt lain." })
                    promptInput.isEnabled = true
                    sendButton.isEnabled = true
                }
            } catch (error: Exception) {
                runOnUiThread {
                    if (chat.childCount > 0) chat.removeViewAt(chat.childCount - 1)
                    addMessage("SISTEM", "Inferensi gagal: ${error.message ?: "kesalahan tidak diketahui"}")
                    promptInput.isEnabled = true
                    sendButton.isEnabled = true
                }
            }
        }
    }

    private fun addMessage(sender: String, body: String) {
        val message = TextView(this).apply {
            text = "$sender\n$body"
            textSize = 14f
            setTextColor(white)
            setLineSpacing(dp(4).toFloat(), 1f)
            setPadding(dp(11), dp(10), dp(11), dp(10))
            setBackgroundColor(panel)
        }
        chat.addView(message, LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.WRAP_CONTENT
        ).apply { bottomMargin = dp(9) })
    }

    private fun matchWrap() = LinearLayout.LayoutParams(
        ViewGroup.LayoutParams.MATCH_PARENT,
        ViewGroup.LayoutParams.WRAP_CONTENT
    )

    private fun dp(value: Int): Int =
        (value * resources.displayMetrics.density).toInt()

    override fun onDestroy() {
        languageModel?.close()
        worker.shutdown()
        super.onDestroy()
    }
}
