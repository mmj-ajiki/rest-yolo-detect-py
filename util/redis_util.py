#!/usr/bin/env python
# coding: utf-8
#
# [FILE] redis_util.py
#
# [DESCRIPTION]
#  REDISに関わるメソッドを定義する
#
import os, sys
import base64
import json
import redis
from dotenv import load_dotenv

# .envファイルの内容を読み込見込む
load_dotenv()

# REDISホスト名を取得
redis_host = os.environ.get("REDIS_HOST")
if redis_host == None:
    print("環境変数REDIS_HOSTが設定されていません")
    sys.exit()

# REDISポート番号を取得
redis_port = os.environ.get("REDIS_PORT")
if redis_port == None:
    print("環境変数REDIS_PORTが設定されていません")
    sys.exit()

# REDISキーの有効期限を取得
redis_duration = os.environ.get("REDIS_EXPIRE")
if redis_duration == None:
    print("環境変数REDIS_EXPIREが設定されていません")
    redis_duration = 60
else:
    redis_duration = int(redis_duration)

# REDISに接続する
r_client = redis.Redis(host=redis_host, port=redis_port, db=0)

# 実際に接続を試みる
try:
    r_client.ping()  
    print("REDISと接続成功")
except redis.exceptions.ConnectionError as e:
    print("REDISと接続できません:", e)
    sys.exit()

#
# [FUNCTION] redisBoxGet()
#
# [DESCRIPTION]
#  検出された領域を取得する
#
# [INPUTS]
#  key - REDISに格納されたキー
#
# [OUTPUTS] 
#  物体が検出された領域（JSON形式）：
#  {'keys': ['objName', 'probability', 'topX', 'topY', 'bottomX', 'bottomY'],
#   'records': [
#       {'objName':<Detected Name>, 
#        'probability':<Ratio>, 
#        'topX':234, 'topY':140, 'bottmX':249, 'bottomY':156}, 
#       ...],
#   'message': <コメント>}
#
# [NOTES]
#
def redisBoxGet(key):
    init_val = {}
    init_val['message'] = "検出結果がありません"
    
    # REDISから画像を取得する
    json_string = r_client.hget(key, "boxes")
    if json_string == None:
        return init_val
    
    # 文字列をJSON構造に変換する
    boxes = json.loads(json_string)
    return boxes
#
# HISTORY
# [1] 2024-11-14 - Initial version
#

#
# [FUNCTION] redisImageGet()
#
# [DESCRIPTION]
#  物体を検出した画像データを取得する
#
# [INPUTS]
#  key - REDISに格納されたキー
#
# [OUTPUTS] 
#  認識結果画像（JSON形式）：
#  {'keys': ['outputImage'],
#   'records': [{'outputImage':<String of image>}],
#   'message': <コメント>}
#
# [NOTES]
#
def redisImageGet(key):
    results = {}
    results['message'] = "検出画像はありません"
    
    # REDISから画像を取得する
    image_string = r_client.hget(key, "image")
    if image_string == None:
        return results

    results = {}
    results['keys'] = ['outputImage']
    list = []
    element = {'outputImage': image_string}
    list.append(element)
    results['records'] = list
    results['message'] = None

    return results
#
# HISTORY
# [1] 2024-11-14 - Initial version
#

#
# [FUNCTION] redisImagePut()
#
# [DESCRIPTION]
#  検出された画像データと検出結果をREDISに格納する
#
# [INPUTS]
#  key - REDISに格納するときのキー
#  output_image_file - 出力画像ファイル名
#  detected_boxes - 物体が検出された領域（JSON形式）：
#  {'keys': ['objName', 'probability', 'topX', 'topY', 'bottomX', 'bottomY'],
#   'records': [
#       {'objName':<Detected Name>, 
#        'probability':<Ratio>, 
#        'topX':234, 'topY':140, 'bottmX':249, 'bottomY':156}, 
#       ...],
#   'message': <コメント>}
#
# [OUTPUTS]
#  True - REDISへの格納が成功、False - 失敗
#
# [NOTES]
#  REDISへは、ハッシュとしてimageキーとboxesキーを有効期限付きで格納する。
#
def redisImagePut(key, output_image_file, detected_boxes):
    Status = True
    # Base64文字列に変換する
    with open(output_image_file, "rb") as image_file:
        data = base64.b64encode(image_file.read())

    img_text = "data:image/jpeg;base64," + data.decode('utf-8')

    # REDISにハッシュとして格納
    try:
        r_client.hset(key, "image", img_text)
        r_client.hset(key, "boxes", json.dumps(detected_boxes))
        r_client.expire(key, redis_duration) # 有効期限を設定する
    except Exception as e:
        print(e)
        Status = False
    
    return Status
#
# HISTORY
# [1] 2024-11-14 - Initial version
#