"""指定した SSML ファイルを受け取り、Amazon Polly を使ってオーディオファイルを生成する。

Usage:
    # 出力ファイル名を自動生成する場合
    uv run src/amazon_tts.py data/ssmls/input.ssml

    # 出力ファイル名を指定する場合
    uv run src/amazon_tts.py data/ssmls/input.ssml --output data/audios/output.mp3

    # モデルを指定する場合
    uv run src/amazon_tts.py data/ssmls/input.ssml --model 'Mizuki'
"""

import os
from enum import Enum
from pathlib import Path

import boto3
import typer
from dotenv import load_dotenv
from rich.console import Console

from utils import generate_output_filename, read_ssml_file


class PollyVoice(str, Enum):
    """Amazon Pollyで使用可能な日本語音声モデル"""

    MIZUKI = "Mizuki"  # 女性、標準
    TAKUMI = "Takumi"  # 男性、標準
    KAZUHA = "Kazuha"  # 女性、Neural
    TOMOKO = "Tomoko"  # 女性、Neural


# 環境変数を読み込み
load_dotenv()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

app = typer.Typer()


def synthesize_ssml(
    ssml_text: str,
    voice_name: str,
    output_path: Path,
) -> None:
    """SSMLをオーディオファイルに変換する。

    Args:
        ssml_text: SSML形式のテキスト
        voice_name: 使用する音声モデル名（例: 'Mizuki', 'Takumi'）
        output_path: 出力先のオーディオファイルパス
    """
    # Amazon Pollyクライアントを初期化
    polly_client = boto3.Session(
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name="us-west-2",
    ).client("polly")

    # 音声合成を実行
    console = Console()
    with console.status("[bold green]音声合成を実行中...", spinner="dots"):
        response = polly_client.synthesize_speech(
            Text=ssml_text,
            TextType="ssml",
            OutputFormat="mp3",
            VoiceId=voice_name,
        )

    # 出力ディレクトリが存在しない場合は作成
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # オーディオコンテンツをファイルに書き込む
    if "AudioStream" in response:
        with output_path.open("wb") as file:
            file.write(response["AudioStream"].read())
        typer.echo(f"✓ オーディオファイルを保存しました: {output_path}")
    else:
        raise Exception("音声データが取得できませんでした")


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
    model: PollyVoice = typer.Option(
        PollyVoice.MIZUKI,
        "--model",
        "-m",
        help="使用する音声モデル名（Amazon Polly VoiceId）",
        case_sensitive=False,
    ),
) -> None:
    """SSMLファイルを読み込み、Amazon Pollyでオーディオファイルを生成します。"""
    try:
        # SSMLファイルを読み込む（utils.pyの関数を使用）
        typer.echo(f"SSMLファイルを読み込んでいます: {input_file}")
        ssml_text = read_ssml_file(input_file)

        # 出力ファイル名を決定（指定されていない場合は自動生成、utils.pyの関数を使用）
        if output is None:
            output = generate_output_filename(input_file, model.value)
            typer.echo(f"出力ファイル名: {output}")

        # 音声合成を実行
        synthesize_ssml(ssml_text, model.value, output)

        typer.echo("✓ 処理が完了しました")

    except FileNotFoundError as e:
        typer.echo(f"エラー: {e}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"エラーが発生しました: {e}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
