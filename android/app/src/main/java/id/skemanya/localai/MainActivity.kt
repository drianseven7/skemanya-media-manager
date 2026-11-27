package id.skemanya.localai

import android.app.Activity
import android.graphics.Color
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

class MainActivity : Activity() {
    private val bg = Color.rgb(11, 11, 13)
    private val panel = Color.rgb(27, 29, 34)
    private val muted = Color.rgb(167, 174, 184)
    private val white = Color.WHITE

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.statusBarColor = bg
        window.navigationBarColor = bg
        window.decorView.systemUiVisibility = 0
        setContentView(buildScreen())
    }

    private fun buildScreen(): View {
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(28), dp(20), dp(20))
            setBackgroundColor(bg)
        }

        root.addView(TextView(this).apply {
            text = "SKEMANYA AI"
            textSize = 28f
            setTextColor(white)
        })
        root.addView(TextView(this).apply {
            text = "MODEL BAHASA INDONESIA · DIBANGUN SENDIRI"
            textSize = 11f
            setTextColor(muted)
            setPadding(0, dp(5), 0, dp(18))
        })

        val status = TextView(this).apply {
            text = "STATUS PEMBANGUNAN\nMesin bahasa SKEMANYA sedang dikembangkan. Aplikasi ini tidak mengunduh atau menggunakan model AI pihak ketiga."
            textSize = 14f
            setTextColor(white)
            setLineSpacing(dp(5).toFloat(), 1f)
            setPadding(dp(15), dp(15), dp(15), dp(15))
            setBackgroundColor(panel)
        }
        root.addView(status, matchWrap())

        val section = TextView(this).apply {
            text = "RUANG PERCAKAPAN"
            textSize = 12f
            setTextColor(muted)
            setPadding(0, dp(22), 0, dp(10))
        }
        root.addView(section)

        val chatScroll = ScrollView(this).apply {
            setBackgroundColor(Color.rgb(19, 20, 24))
            isFillViewport = true
        }
        val chat = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(15), dp(15), dp(15), dp(15))
        }
        chat.addView(TextView(this).apply {
            text = "Halo. Ini ruang percakapan SKEMANYA AI.\n\nFitur chat akan diaktifkan setelah model bahasa asli SKEMANYA selesai dilatih dan berhasil dijalankan di Android.\n\nTidak ada model pihak ketiga yang dipakai sebagai pengganti."
            textSize = 15f
            setTextColor(white)
            setLineSpacing(dp(5).toFloat(), 1f)
        })
        chatScroll.addView(chat)
        root.addView(chatScroll, LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f).apply {
            topMargin = dp(2)
            bottomMargin = dp(12)
        })

        val input = EditText(this).apply {
            hint = "Chat belum tersedia — model sedang dikembangkan"
            setHintTextColor(Color.GRAY)
            setTextColor(white)
            textSize = 14f
            isEnabled = false
            setPadding(dp(12), dp(12), dp(12), dp(12))
            setBackgroundColor(panel)
        }
        root.addView(input, matchWrap())

        val footer = TextView(this).apply {
            text = "VERSI PROTOTIPE · TANPA MODEL EKSTERNAL"
            textSize = 10f
            setTextColor(muted)
            gravity = Gravity.CENTER
            setPadding(0, dp(14), 0, 0)
        }
        root.addView(footer, matchWrap())
        return root
    }

    private fun matchWrap() = LinearLayout.LayoutParams(
        ViewGroup.LayoutParams.MATCH_PARENT,
        ViewGroup.LayoutParams.WRAP_CONTENT
    )

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
}
