from pathlib import Path


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
