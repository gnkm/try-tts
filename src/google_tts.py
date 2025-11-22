"""指定した SSML ファイルを受け取り、Google TTS を使ってオーディオファイルを生成する。

Usage:
    # 出力ファイル名を自動生成する場合
    uv run src/google_tts.py data/ssmls/input.ssml

    # 出力ファイル名を指定する場合
    uv run src/google_tts.py data/ssmls/input.ssml --output data/audios/output.mp3

    # モデルを指定する場合
    uv run src/google_tts.py data/ssmls/input.ssml --model 'ja-JP-Chirp3-HD-Sulafat'
"""

from pathlib import Path

import typer
from dotenv import load_dotenv
from google.cloud import texttospeech  # type: ignore
from rich.console import Console

# 環境変数を読み込み
load_dotenv()

app = typer.Typer()


def generate_output_filename(input_file: Path, model_name: str) -> Path:
    """入力ファイル名とモデル名からMP3出力ファイル名を生成する。

    Args:
        input_file: 入力SSMLファイルのパス
        model_name: 使用する音声モデル名

    Returns:
        生成された出力ファイルのパス（data/audios/ディレクトリ）

    Example:
        >>> generate_output_filename(Path("data/ssmls/fish-intro.ssml"), "ja-JP-Chirp3-HD-Zephyr")
        Path("data/audios/fish-intro_ja-JP-Chirp3-HD-Zephyr.mp3")
    """
    # 入力ファイルの拡張子なしのファイル名を取得
    base_name = input_file.stem

    # モデル名をファイル名に使用できる形式に変換（既に問題ないはずだが念のため）
    safe_model_name = model_name.replace("/", "-").replace("\\", "-")

    # 出力ファイル名を生成
    output_filename = f"{base_name}_{safe_model_name}.mp3"

    # data/audios/ディレクトリに配置
    output_dir = Path("data/audios")
    return output_dir / output_filename


def read_ssml_file(file_path: Path) -> str:
    """SSMLファイルを読み込む。

    Args:
        file_path: SSMLファイルのパス

    Returns:
        SSMLコンテンツ

    Raises:
        FileNotFoundError: ファイルが存在しない場合
    """
    if not file_path.exists():
        raise FileNotFoundError(f"SSMLファイルが見つかりません: {file_path}")

    return file_path.read_text(encoding="utf-8")


def synthesize_ssml(
    ssml_text: str,
    voice_name: str,
    output_path: Path,
) -> None:
    """SSMLをオーディオファイルに変換する。

    Args:
        ssml_text: SSML形式のテキスト
        voice_name: 使用する音声モデル名（例: 'ja-JP-Chirp3-HD-Zephyr'）
        output_path: 出力先のオーディオファイルパス
    """
    # Text-to-Speechクライアントを初期化
    client = texttospeech.TextToSpeechClient()

    # 音声リクエストを構築
    synthesis_input = texttospeech.SynthesisInput(ssml=ssml_text)

    # 言語コードを音声名から抽出（例: 'ja-JP-Chirp3-HD-Zephyr' -> 'ja-JP'）
    language_code = "-".join(voice_name.split("-")[:2])

    # 音声パラメータを設定
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name,
    )

    # オーディオ設定（MP3形式で出力）
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    # 音声合成を実行
    console = Console()
    with console.status("[bold green]音声合成を実行中...", spinner="dots"):
        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config,
        )

    # 出力ディレクトリが存在しない場合は作成
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # オーディオコンテンツをファイルに書き込む
    output_path.write_bytes(response.audio_content)
    typer.echo(f"✓ オーディオファイルを保存しました: {output_path}")


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
    model: str = typer.Option(
        "ja-JP-Chirp3-HD-Zephyr",
        "--model",
        "-m",
        help="使用する音声モデル名",
    ),
) -> None:
    """SSMLファイルを読み込み、Google Cloud Text-to-Speechでオーディオファイルを生成します。"""
    try:
        # SSMLファイルを読み込む
        typer.echo(f"SSMLファイルを読み込んでいます: {input_file}")
        ssml_text = read_ssml_file(input_file)

        # 出力ファイル名を決定（指定されていない場合は自動生成）
        if output is None:
            output = generate_output_filename(input_file, model)
            typer.echo(f"出力ファイル名: {output}")

        # 音声合成を実行
        synthesize_ssml(ssml_text, model, output)

        typer.echo("✓ 処理が完了しました")

    except FileNotFoundError as e:
        typer.echo(f"エラー: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"エラーが発生しました: {e}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
