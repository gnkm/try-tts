"""指定した SSML ファイルを受け取り、Azure TTS を使ってオーディオファイルを生成する。

Usage:
    # 出力ファイル名を自動生成する場合
    uv run src/azure_tts.py data/ssmls/input.ssml

    # 出力ファイル名を指定する場合
    uv run src/azure_tts.py data/ssmls/input.ssml --output data/audios/output.mp3

    # 音声を指定する場合
    uv run src/azure_tts.py data/ssmls/input.ssml --voice ja-JP-NanamiNeural
"""

import os
from enum import Enum
from pathlib import Path

import azure.cognitiveservices.speech as speechsdk
import typer
from dotenv import load_dotenv
from rich.console import Console

from utils import generate_output_filename, read_ssml_file


class AzureVoice(str, Enum):
    """Azure Speech Serviceで使用可能な日本語音声モデル"""

    NANAMI = "ja-JP-NanamiNeural"  # 女性、Neural
    KEITA = "ja-JP-KeitaNeural"  # 男性、Neural
    AOI = "ja-JP-AoiNeural"  # 女性、Neural
    DAICHI = "ja-JP-DaichiNeural"  # 男性、Neural
    MAYU = "ja-JP-MayuNeural"  # 女性、Neural
    NAOKI = "ja-JP-NaokiNeural"  # 男性、Neural
    SHIORI = "ja-JP-ShioriNeural"  # 女性、Neural
    MASARU = "ja-JP-MasaruMultilingualNeural"
    MASARU_DRAGON = "ja-JP-Masaru:DragonHDLatestNeural"
    NANAMI_DRAGON = "ja-JP-Nanami:DragonHDLatestNeural"


# 環境変数を読み込み
load_dotenv()
AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")

app = typer.Typer()


def synthesize_ssml(
    ssml_text: str,
    voice_name: str,
    output_path: Path,
) -> None:
    """SSMLをオーディオファイルに変換する。

    Args:
        ssml_text: SSML形式のテキスト（{voice_name}プレースホルダーを含む）
        voice_name: 使用する音声モデル名（例: 'ja-JP-NanamiNeural'）
        output_path: 出力先のオーディオファイルパス
    """
    if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
        raise ValueError(
            "Azure認証情報が設定されていません。AZURE_SPEECH_KEYとAZURE_SPEECH_REGIONを.envファイルに設定してください。"
        )

    # SSMLテキスト内のプレースホルダーにボイス名を設定
    formatted_ssml = ssml_text.format(voice_name=voice_name)

    # Azure Speech設定を初期化
    speech_config = speechsdk.SpeechConfig(
        subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION
    )

    # MP3形式で出力するように設定
    speech_config.set_speech_synthesis_output_format(
        speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3
    )

    # 出力ディレクトリが存在しない場合は作成
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # オーディオ設定（ファイルに出力）
    audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))

    # Speech Synthesizerを作成
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, audio_config=audio_config
    )

    # 音声合成を実行
    console = Console()
    with console.status("[bold green]音声合成を実行中...", spinner="dots"):
        result = speech_synthesizer.speak_ssml_async(formatted_ssml).get()

    # 結果を確認
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        typer.echo(f"✓ オーディオファイルを保存しました: {output_path}")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        typer.echo(f"音声合成がキャンセルされました: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            typer.echo(f"エラー詳細: {cancellation_details.error_details}")
            if cancellation_details.error_details:
                raise Exception(f"音声合成エラー: {cancellation_details.error_details}")


@app.command()
def main(
    input_file: Path = typer.Argument(
        ...,
        help="入力SSMLファイルのパス",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output: Path | None = typer.Option(
        None,
        "--output",
        "-o",
        help="出力オーディオファイルのパス（MP3形式）。指定しない場合は自動生成されます。",
    ),
    voice: AzureVoice = typer.Option(
        AzureVoice.NANAMI,
        "--voice",
        "-v",
        help="使用する音声モデル名（Azure Neural Voice）",
        case_sensitive=False,
    ),
) -> None:
    """SSMLファイルを読み込み、Azure Speech Serviceでオーディオファイルを生成します。"""
    try:
        # SSMLファイルを読み込む（utils.pyの関数を使用）
        typer.echo(f"SSMLファイルを読み込んでいます: {input_file}")
        ssml_text = read_ssml_file(input_file)

        # 出力ファイル名を決定（指定されていない場合は自動生成、utils.pyの関数を使用）
        if output is None:
            output = generate_output_filename(input_file, voice.value)
            typer.echo(f"出力ファイル名: {output}")

        # 音声合成を実行
        synthesize_ssml(ssml_text, voice.value, output)

        typer.echo("✓ 処理が完了しました")

    except FileNotFoundError as e:
        typer.echo(f"エラー: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"エラーが発生しました: {e}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
