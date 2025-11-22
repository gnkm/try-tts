# Try TTS

各社、各モデルの TTS を試す。

## 環境構築

```
uv sync
```

## 実行

Google TTS

```
uv run src/google_tts.py data/ssmls/input.ssml --voice ${voice_name}
```

Azure TTS

```
uv run src/azure_tts.py data/ssmls/input.ssml --voice ${voice_name}
```

まとめて実行する。

```
seq 1 3 | xargs -I@ uv run src/google_tts.py data/ssmls/fish-intro-0@.ssml --voice ${voice_name}
```

## 注意

- `<voice>` タグの中で voice name を動的に設定するため、SSML ファイル内にプレースホルダーが存在する
