package id.skemanya.localai

import ai.onnxruntime.OnnxTensor
import ai.onnxruntime.OrtEnvironment
import ai.onnxruntime.OrtSession

/**
 * Offline inference adapter for SKEMANYA's own exported Transformer.
 *
 * TokenCodec must be backed by the exact SentencePiece model used during training.
 * This class deliberately does not invent a tokenizer or substitute another model.
 */
interface TokenCodec {
    fun encode(text: String): LongArray
    fun decode(tokenIds: LongArray): String
}

class OnnxLanguageModel(
    modelPath: String,
    private val tokenizer: TokenCodec,
    private val contextLength: Int,
    private val maxNewTokens: Int = 96
) : AutoCloseable {
    private val environment = OrtEnvironment.getEnvironment()
    private val session: OrtSession
    private val inputName: String

    init {
        require(contextLength > 0) { "contextLength harus lebih dari nol" }
        require(maxNewTokens > 0) { "maxNewTokens harus lebih dari nol" }
        val options = OrtSession.SessionOptions().apply {
            setIntraOpNumThreads(2)
            setInterOpNumThreads(1)
            setOptimizationLevel(OrtSession.SessionOptions.OptLevel.BASIC_OPT)
        }
        session = environment.createSession(modelPath, options)
        options.close()
        inputName = session.inputNames.firstOrNull()
            ?: throw IllegalStateException("Model ONNX tidak memiliki input")
        require(session.outputNames.isNotEmpty()) { "Model ONNX tidak memiliki output" }
    }

    /** Run greedy autoregressive generation. Call from a worker thread, never the UI thread. */
    fun generate(prompt: String): String {
        val initial = tokenizer.encode(prompt)
        require(initial.isNotEmpty()) { "Prompt tidak menghasilkan token" }
        val generated = initial.toMutableList()

        repeat(maxNewTokens) {
            val window = generated.takeLast(contextLength).toLongArray()
            val shape = longArrayOf(1L, window.size.toLong())
            // A nested primitive array is copied into a correctly shaped ORT tensor.
            val tensor = OnnxTensor.createTensor(environment, arrayOf(window))
            val nextToken = try {
                val result = session.run(mapOf(inputName to tensor))
                try {
                    val logits = result[0].value as? Array<Array<FloatArray>>
                        ?: throw IllegalStateException("Bentuk output logits tidak sesuai [batch, sequence, vocab]")
                    val last = logits.firstOrNull()?.lastOrNull()
                        ?: throw IllegalStateException("Logits kosong")
                    last.indices.maxByOrNull { last[it] }?.toLong()
                        ?: throw IllegalStateException("Tidak ada token keluaran")
                } finally {
                    result.close()
                }
            } finally {
                tensor.close()
            }
            generated.add(nextToken)
        }
        return tokenizer.decode(generated.drop(initial.size).toLongArray())
    }

    override fun close() {
        session.close()
    }
}
