# rest-yolo-detect-py

## YOLOによる物体検出RESTサーバー

物体検出とは、画像データのどこに何があるかを認識する技術である。このRESTサーバーは、YOLOを用いた物体検出エンジンにアクセスすることができるAPIを提供する。標準モデルを用いているので、一般的な対象物（人物、動物、乗り物など）を検出する。

### Pythonをインストールする

[https://www.python.org/downloads/](https://www.python.org/downloads/)からPythonをインストールする。

**注意：** Python 3.12.xを利用すること。バージョン3.13以上では依存するパッケージがインストールできない。

### Redisをインストールする

NoSQLのキーバリュー型の一つで、メモリ上でデータを管理するインメモリデータべースである。ローカルファイルにアクセスするより高速であり、検出した結果画像データを所定の時間内で保持するために用いる。

[https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/)を参考にインストールする。

**補足：** WSL2のLinuxで動作させなくても、Redis for Windows 3.0からでも動作することを確認しています。
**配信サイト：** [https://github.com/MicrosoftArchive/redis/releases](https://github.com/MicrosoftArchive/redis/releases)

### 必要なパッケージのインストール

コマンドプロンプト上で、次のコマンドを実行し、必要なPythonのパッケージをインストールする。

```bash
pip install -r requirements.txt
```

### YOLOモデルファイルを配置する

学習済みのYOLOモデルファイル（YOLO v3）は次のURLからダウンロードし、modelフォルダーに配置する。人物、動物、乗り物などを検出するモデルである。次の2つのバージョンで動作を確認している。

- [yolov8n.pt](
https://huggingface.co/Ultralytics/YOLOv8/blob/main/yolov8n.pt)
- [yolo11n.pt](
https://huggingface.co/Ultralytics/YOLO11/blob/365ed86341e7a7456dbc4cafc09f138814ce9ff1/yolo11n.pt)

### 環境変数を設定する

本アプリを起動するには環境変数の設定が必要である。以下の環境変数が.envファイルに定義されている。YOLOモデルファイル名やRedisサーバーは初期設定されているので、これらに変更があれば修正する。

|  変数名  |  説明  |
| ---- | ---- |
|  LOCAL_FOLDER  | アップロードしたファイルを暫定的に保存するローカルフォルダーの名前 |
|  YOLO_MODEL_FILE  | 利用するYOLOモデルファイルのパス |
|  REDIS_HOST | Redisサーバーのホスト名 |
|  REDIS_PORT | Redisサーバーのポート番号 |
|  REDIS_EXPIRE | Redisキーの有効期限（秒） |

### サーバーを起動する

コマンドプロンプトから次のコマンドを実行し、サーバーを起動する。

開発版（ソースコード編集内容が自動的に反映される）:

```bash
uvicorn main:app --reload
```

本番環境:

```bash
uvicorn main:app
```

※Application startup completeと表示されるまで少し時間がかかります。

コマンドの説明:

| コマンドの要素 |  説明  |
| ---- | ---- |
|  uvicorn  | FastAPIベースの非同期Python Webアプリケーションを実行する |
|  main:app  | Pythonファイルmain.pyの中で、FastAPIが生成する変数がapp |
|  --reload  | 実行中にソースコードが変更されたとき、サーバーが自動的にリロードされる |

デフォルトのポート番号は8000。  
ポート番号を指定するときは --port [ポート番号] を後ろに付与する。

### サーバーへのアクセスを確認する

確認のため、Webブラウザを開き、次のURLへアクセスする（ポート番号が8000の場合）。

[http://127.0.0.1:8000/](http://127.0.0.1:8000/)

トップページが現れる。

### REST APIs

このサーバーが提供するREST APIエンドポイントは、ある定型的なJSON構造を返却する。その構造は、株式会社MetaMoJiの製品 **eYACHO** および **GEMBA Note**の開発者オプションのアグリゲーション検索条件を構成する **RESTコネクタ** の仕様に基づく。

REST用アグリゲーションの出力構造：

```bash
{
   'keys': ['key1', 'key2', ... 'keyN'], # recordsの中で用いるキーの一覧
   'records': [
       {'key1': value-11, 'key2': value-21, ... 'keyN': value-N1}, 
       {'key1': value-12, 'key2': value-22, ... 'keyN': value-N2}, 
       ...,
       {'key1': value-1m, 'key2': value-2m, ... 'keyN': value-Nm}, 
   ],
   'message': エラーメッセージ or null(success)
}
```

#### /rest/detect_objects (POSTメソッド)

eYACHO/GEMBA Noteアプリから送信されてきた画像情報をファイルに一時的に保存し、YOLOの物体検出を実行し、結果をRedisに格納する。

リクエストボディ(JSON)の構造：

| キー | 説明 |
| ---- | ---- |
| _noteLink | eYACHO/GEMBA Noteの対象ノート固有のURL |
| _pageId | eYACHO/GEMBA Noteの対象ページ固有のID番号 |
| inputImage | 物体検出する画像のBase64文字列 |

※_noteLinkと_pageIdは、Redisに情報を格納するときのキーを生成するために利用する。

レスポンスの仕様:

|  キー  | 説明  |
| ---- | ---- |
| objName | 検出された物体名称 |
| probability | 検出精度 |
| topX | 検出された領域の左上のX座標 |
| topY | 検出された領域の左上のY座標 |
| bottomX | 検出された領域の右下のX座標 |
| bottomY | 検出された領域の右下のY座標 |

レスポンス例:

```bash
{
  'keys': ['objName', 'probability', 'topX', 'topY', 'bottomX', 'bottomY'],
  'records': [
    {'objName':<Detected Name>, 
     'probability':<Percentage>, 
      'topX':234, 'topY':140, 'bottmX':249, 'bottomY':156}, 
    ...],
  'message': <コメント>
}
```

#### /rest/detected_boxes (POSTメソッド)

/rest/detect_objectsメソッドで検出された物体の名称と認識領域をRedisから取得する。

リクエストボディ(JSON)の構造：

| キー | 説明 |
| ---- | ---- |
| _NOTE_LINK | eYACHO/GEMBA Noteの対象ノート固有のURL |
| _PAGE_ID | eYACHO/GEMBA Noteの対象ページ固有のID番号 |

※_NOTE_LINKと_PAGE_IDは、Redisから情報を取得するときのキーを生成するために利用する。

レスポンスの仕様:

|  キー  | 説明  |
| ---- | ---- |
| objName | 検出された物体名称 |
| probability | 検出精度 |
| topX | 検出された領域の左上のX座標 |
| topY | 検出された領域の左上のY座標 |
| bottomX | 検出された領域の右下のX座標 |
| bottomY | 検出された領域の右下のY座標 |

レスポンス例:

```bash
{
  'keys': ['objName', 'probability', 'topX', 'topY', 'bottomX', 'bottomY'],
  'records': [
    {'objName':<Detected Name>, 
     'probability':<Percentage>, 
      'topX':234, 'topY':140, 'bottmX':249, 'bottomY':156}, 
    ...],
  'message': <コメント>
}
```

#### /rest/detected_image (POSTメソッド)

/rest/detect_objectsメソッドで生成された検出画像をRedisから取得する。

リクエストボディ(JSON)の構造：

| キー | 説明 |
| ---- | ---- |
| _NOTE_LINK | eYACHO/GEMBA Noteの対象ノート固有のURL |
| _PAGE_ID | eYACHO/GEMBA Noteの対象ページ固有のID番号 |

※_NOTE_LINKと_PAGE_IDは、Redisから情報を取得するときのキーを生成するために利用する。

レスポンスの仕様:

|  キー  | 説明  |
| ---- | ---- |
| outputImage | 生成された画像のBase64文字列 |

レスポンス例:

```bash
{
  'keys': ['outputImage'],
  'records': [{'outputImage':<Base64文字列>}],
  'message': <コメント>
}
```

### eYACHO/GEMBA Noteとのデータ連携テスト

- packageフォルダ以下にある開発パッケージのバックアップファイル（**YOLO_Detect__<バージョン>__backup.gncproj**）をeYACHO/GEMBA Noteに復元する。
  - eYACHO/GEMBA Note **バージョン7** 以降を利用すること。
- サーバーが起動していることを確認する。
  - Windowsアプリからローカルサーバーにアクセスする場合は、管理者モードで利用対象アプリのループバックを有効にする → [Windowsで開発する際の注意点](./NoticesForWindows.md)
- 開発パッケージフォルダ上にある **物体検出ノートテンプレート** をクリックする。
  - 新たなノートが作成される。
- 編集状態のノートの中にある「縦型画像」ページあるいは「横型画像」ページを選択する。
- 対象の画像を「入力画像」に張り付ける。
  - 人物、動物、乗り物などが映っている画像が良い。
- ページ上の **画像送信** ボタンをクリックする [1]
  - 「送信終了」とダイアログが現れると検出成功
- 同ページにある **領域検出** と **結果画像** をクリックすると認識した物体名称とその位置、検出画像が表示される [2]
  - どちらのボタンからクリックしてもよい。
- **一括実行** ボタンは、画像送信、領域検出、結果画像すべてのボタンを一度に実行する。

[1] サーバーのポート番号を変更した場合は、「画像送信」のボタンコマンド「サーバーに送信する」に設定してあるRESTのURL、アグリゲーション検索条件「detectedObjectList」と「detectedImage」のコネクタ定義にある **URL** を変更する。  
[2] 環境変数 REDIS_EXPIREで指定した時間間隔だけ、検出結果は残る。

### 検出例

![物体検出例][detected_sample]

### 更新履歴

- 2025-11-10 - V7に伴う修正・Ultralyticsへのグレードアップ
- 2024-11-14 - 初版

[detected_sample]:./static/image/detected_results_sample.png
