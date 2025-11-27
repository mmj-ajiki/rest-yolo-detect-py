#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# [FILE] main.py
#
# [DESCRIPTION]
#  YOLOを利用した物体検出向けのRESTメソッドを定義する
# 
# [NOTES]
#  Ultralytics YOLOを利用している
#
import os, sys, time
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from yolo_detect import yoloDetectObjects
from util.redis_util import redisBoxGet, redisImageGet, redisImagePut
from util.util import getNoteId, pdf2PNG, storeBinaryFile
from dotenv import load_dotenv

# .envファイルの内容を読み込見込む
load_dotenv()

# ローカルフォルダー
local_folder = os.environ.get("LOCAL_FOLDER")
if local_folder == None:
    print("環境変数LOCAL_FOLDERが設定されていません")
    sys.exit()

# YOLOモデルファイル
yolo_model_file = os.environ.get("YOLO_MODEL_FILE")
if yolo_model_file == None:
    print("環境変数YOLO_MODEL_FILEが設定されていません")
    sys.exit()
else:
    print("[MODEL FILE]", yolo_model_file)

app = FastAPI()
app.mount(path="/static", app=StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

#
# [FUNCTION] is_reload_enabled()
#
# [DESCRIPTION]
#  実行するコマンドに--reloadが含まれるか判定する
#
# [INPUTS] None
#
# [OUTPUTS]
#  True: 含まれる False: 含まれない
#
# [NOTES]
#  Trueの場合はデバッグ実行とみなし、JSONデータをコンソール上に表示する
#
def is_reload_enabled():
    return "--reload" in sys.argv
#
# HISTORY
# [1] 2024-11-14 - Initial version
#

#
# GET Method
# End Point: /
#
# [DESCRIPTION]
#  トップページを開く
#
# [INPUTS]
#  request - リクエスト
# 
# [OUTPUTS]
# 
# [NOTES]
#  Web画面上に単に、"YOLO REST Server"と表示するのみ
#
@app.get("/", response_class=HTMLResponse)
async def topPage(request: Request):
    
    return templates.TemplateResponse("top.html", {"request": request, "title": "YOLO REST Server"})
#
# HISTORY
# [1] 2024-11-14 - Initial version
#

#
# POST Method
# End Point: /rest/detect_objects
#
# [DESCRIPTION]
#  eYACHO/GEMBA Noteから送信されてきた画像情報をファイルに保存し、YOLOの物体検出を実行する。
#
# [INPUTS] 
#  json_data - bodyにクライアント（eYACHO/GEMBA Note）からの画像情報が格納されている
#    {..., "_noteLink": <ノートリンク>, "_pageId": <ページID>, 
#     "inputImage":"data:image/jpeg;base64,/9j/4AAQSkZJR...", ...}
# 
# [OUTPUTS]
#   次のJSONを返す
#  {'keys': ['objName', 'probability', 'topX', 'topY', 'bottomX', 'bottomY'],
#   'records': [
#       {'objName':<Detected Name>, 
#        'probability':<Ratio>, 
#        'topX':234, 'topY':140, 'bottmX':249, 'bottomY':156}, 
#       ...],
#   'message': <コメント>}
# 
# [NOTES]
# - eYACHO/GEMBA Noteのボタンコマンド「サーバーへ送信」で物体検索を準備するメソッド
# - Redisへの登録には、_noteLinkと_pageIdから生成したキーを使用する。標準ノートではユニーク性は保証。
#
@app.post("/rest/detect_objects")
def postDetectObjects(json_data: dict):
    results = {}
    results['message'] = "不明なエラーが発生しました"

    if ('inputImage' in json_data) == False:
        results['message'] = "入力画像が設定されていません"
        return results

    # Base64文字列を抽出
    splitString = json_data['inputImage'].split(',')
    b64_text = splitString[1]

    # ファイル拡張子を取得
    splitString = splitString[0].split('/')
    extension   = splitString[1].split(';')

    # 保存する画像ファイル名を準備する
    timestamp = str(time.strftime('%Y%m%d%H%M%S'))
    noteId = getNoteId(json_data['_noteLink'])
    filename = noteId + "-" + timestamp + "." + extension[0]
    file_path = local_folder + "/" + filename

    # Base64文字列を画像ファイルに保存
    error_msg = storeBinaryFile(file_path, b64_text)
    if error_msg != None:
        results['message'] = error_msg
        return results

    if is_reload_enabled():
        print("[SAVED]", file_path)
        
    # 物体を検出する
    annotated_image = local_folder + "/detected-" + filename
    mode = is_reload_enabled()
    detected = yoloDetectObjects(file_path, annotated_image, yolo_model_file, mode)

    # 格納するキーはeYACHO/GEMBA NoteのノートIDとページIDから生成する
    key = noteId + "-" + json_data['_pageId']
    if is_reload_enabled():
        print("[DETECTED]", detected)
        print("[REDIS KEY]", key)
    os.remove(file_path) 

    if len(detected['records']) < 1:
        results['message'] = "何も検出されませんでした"
        return results

    # 生成した画像と認識結果を登録する
    Status = redisImagePut(key, annotated_image, detected)
    os.remove(annotated_image) 

    if Status == False:
        results['message'] = "検出結果がありません"
        return results
    
    return detected
#
# HISTORY
# [3] 2025-11-27 - Minor update using timestamp
# [2] 2025-11-10 - Added mode to yoloDetectObjects()
# [1] 2024-11-14 - Initial version
#

#
# POST Method
# End Point: /rest/detect_pdf
#
# [DESCRIPTION]
#  eYACHO/GEMBA Noteから送信されてきた画面全体(PDF)をファイルに保存し、YOLOの物体検出を実行する。
#
# [INPUTS] 
#  json_data - bodyにクライアント（eYACHO/GEMBA Note）からのページ情報が格納されている
#    {..., 
#     "id": <eYACHO/GEMBAで振られたユニークなID（未使用）>,
#     "label": <PDFラベル名>,
#     "_noteLink": "https://mps.metamoji.com/link/***.mmjloc'",
#     "_notePdf":"JVBERi0xLjQKJeLjz9MKN...", ...}
# 
# [OUTPUTS]
#   次のJSONを返す
#  {'keys': ['objName', 'probability', 'topX', 'topY', 'bottomX', 'bottomY'],
#   'records': [
#       {'objName':<Detected Name>, 
#        'probability':<Ratio>, 
#        'topX':234, 'topY':140, 'bottmX':249, 'bottomY':156}, 
#       ...],
#   'message': <コメント>}
#
# [NOTES]
# - eYACHO/GEMBA Noteのボタンコマンド「サーバーへ送信」で画面全体の物体検出を準備するメソッド
# - Redisへの登録には、labelと_noteLinkから生成したキーを使用する。したがってユニーク性はない。
#
@app.post("/rest/detect_pdf")
def postDetectPDF(json_data: dict):
    results = {}
    results['message'] = "不明なエラーが発生しました"

    if ('label' in json_data) == False:
        results['message'] = "画像ラベルが設定されていません"
        return results

    # 保存するPDFファイル名を準備する
    timestamp = str(time.strftime('%Y%m%d%H%M%S'))
    noteId = getNoteId(json_data['_noteLink'])
    pdf_name = noteId + "-" + timestamp + ".pdf"
    pdf_path = local_folder + "/" + pdf_name

    # Base64文字列をPDFファイルに保存
    error_msg = storeBinaryFile(pdf_path, json_data['_notePdf'])
    if error_msg != None:
        results['message'] = error_msg
        return results

    if is_reload_enabled():
        print("[SAVED]", pdf_path)

    # PDFファイルを画像ファイル(PNG形式)へ変換
    png_name = noteId + "-" + timestamp + ".png"
    png_path = local_folder + "/" + png_name
    error_msg = pdf2PNG(pdf_path, png_path, 0) # 0 - 最初のページが変換対象

    if error_msg != None:
        results['message'] = error_msg
        return results

    if is_reload_enabled():
        print("[SAVED]", png_path)
    os.remove(pdf_path) 

    # 物体を検出する
    annotated_image = local_folder + "/detected-" + png_name
    mode = is_reload_enabled()
    detected = yoloDetectObjects(png_path, annotated_image, yolo_model_file, mode)

    # 格納するキーはeYACHO/GEMBA NoteのノートIDと画像ラベルから生成されたIDから生成する
    key = noteId + "-" + json_data['label']
    if is_reload_enabled():
        print("[DETECTED]", detected)
        print("[REDIS KEY]", key)
    os.remove(png_path) 

    if len(detected['records']) < 1:
        results['message'] = "何も検出されませんでした"
        return results

    # 生成した画像と認識結果を登録する
    Status = redisImagePut(key, annotated_image, detected)
    os.remove(annotated_image) 

    if Status == False:
        results['message'] = "検出結果がありません"
        return results
    
    return detected
#
# HISTORY
# [1] 2025-11-27 - Initial version
#

#
# POST Method
# End Point: /rest/detected_boxes
#
# [DESCRIPTION]
#  /rest/detect_objectsで検出された物体の名称と認識領域を取得する。
#
# [INPUTS] 
#   json_data - bodyにクライアント（eYACHO/GEMBA Note）からの情報が格納されている
#    {..., "_NOTE_LINK": <ノートリンク>, "_PAGE_ID": <ページID>,
#     "label:" <PDFラベル名>, (/rest/detect_pdfを実行した結果を取得するときに利用)
#     ...}
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
#   eYACHO/GEMBA Noteのボタンアクション「アグリゲーションで更新」や「アグリゲーション結果を反映」から実行する
#
@app.post("/rest/detected_boxes")
def postDetectedBoxes(json_data: dict):
    if is_reload_enabled():
        print("[JSON for detected_results]", json_data)
        
    # 格納するキーはeYACHO/GEMBA NoteのノートIDと、ラベルあるいはページIDから生成する
    key = getNoteId(json_data['_NOTE_LINK']) + "-"
    if ('label' in json_data) == True:
        key += json_data['label']
    else:
        key += json_data['_PAGE_ID']

    # Redisからキーの値を取得する
    results = redisBoxGet(key)
   
    return results
#
# HISTORY
# [2] 2025-11-27 - Modified for PDF
# [1] 2024-11-14 - Initial version
#

#
# POST Method
# End Point: /rest/detected_image
#
# [DESCRIPTION]
#  /rest/detect_objectsで生成された検出画像を取得する。
#
# [INPUTS] 
#   json_data - bodyにクライアント（eYACHO/GEMBA Note）からの情報が格納されている
#    {..., "_NOTE_LINK": <ノートリンク>, "_PAGE_ID": <ページID>,
#     "label:" <PDFラベル名>, (/rest/detect_pdfを実行した結果を取得するときに利用)
#     ...}
# 
# [OUTPUTS]
#  認識結果画像（JSON形式）：
#  {'keys': ['outputImage'],
#   'records': [{'outputImage':<String of image>}],
#   'message': <コメント>}
# 
# [NOTES]
#   eYACHO/GEMBA Noteのボタンコマンド「アグリゲーション結果を反映」で実行する
#
@app.post("/rest/detected_image")
def postDetectedImage(json_data: dict):
    if is_reload_enabled():
        print("[JSON for detected_results]", json_data)
        
    # 格納するキーはeYACHO/GEMBA NoteのノートIDと、ラベルあるいはページIDから生成する
    key = getNoteId(json_data['_NOTE_LINK']) + "-"
    if ('label' in json_data) == True:
        key += json_data['label']
    else:
        key += json_data['_PAGE_ID']

    # Redisからキーの値を取得する
    results = redisImageGet(key)
   
    return results
#
# HISTORY
# [2] 2025-11-27 - Modified for PDF
# [1] 2024-11-14 - Initial version
#
