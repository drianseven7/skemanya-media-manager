package id.skemanya.localai

import com.sentencepiece.Model
import com.sentencepiece.Scoring
import com.sentencepiece.SentencePieceAlgorithm
import java.nio.file.Paths

/** SentencePiece BPE codec backed by SKEMANYA's exact tokenizer artifact. */
class SentencePiece4JCodec(modelPath: String) : TokenCodec {
    private val model = Model.parseFrom(Paths.get(modelPath))
    private val algorithm = SentencePieceAlgorithm(true, Scoring.HIGHEST_SCORE)

    override fun encode(text: String): LongArray =
        model.encodeNormalized(text, algorithm).map { it.toLong() }.toLongArray()

    override fun decode(tokenIds: LongArray): String =
        model.decodeSmart(tokenIds.map { it.toInt() })
}
