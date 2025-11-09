#!/usr/bin/env python
# coding: utf-8
#
# [FILE] yolo_detect.py
#
# [DESCRIPTION]
#   ultralyticsを用いた物体検出に関わるメソッドを定義する
#
from ultralytics import YOLO

#
# [FUNCTION] yoloDetectObjects()
#
# [DESCRIPTION]
#  YOLOモデルを用いて物体を検出する
#
# [INPUTS]
#  inputImageFile - 入力画像ファイル名
#  outputImageFile - 出力画像ファイル名
#  modelFile - YOLOモデルファイル名
#  debug - デバッグモード
#
# [OUTPUTS]
#  {'keys': ['objName', 'probability', 'topX', 'topY', 'bottomX', 'bottomY'],
#   'records': [
#       {'objName':<Detected Name>, 
#        'probability':<Percentage>, 
#        'topX':234, 'topY':140, 'bottmX':249, 'bottomY':156}, 
#       ...],
#   'message': <コメント>}
#
# [NOTES]
#  Confidence Scoreを0.5以上を検出。
#
def yoloDetectObjects(inputImageFile, outputImageFile, modelFile, debug):
    model = YOLO(modelFile) # Load a model
    detected = model.predict(inputImageFile, save=False, conf=0.5)

    # 後のオブジェクト名出力などのため
    names = detected[0].names
    classes = detected[0].boxes.cls
    boxes = detected[0].boxes
    confs = detected[0].boxes.conf

    # 結果用JSONの初期化
    results = {}
    results['keys'] = ['objName', 'probability', 'topX', 'topY', 'bottomX', 'bottomY']
    list = []
    
    # 検出した対象物名、検出精度、検出領域を抽出してJSONを構成する
    for box, cls, conf in zip(boxes, classes, confs):
        name = names[int(cls)]
        x1, y1, x2, y2 = [int(coordinate) for coordinate in box.xyxy[0]]
        elements = {'objName': name, 'probability': '{:.2f}'.format(float(conf)), 'topX': x1, 'topY': y1, 'bottomX': x2, 'bottomY': y2}
        if (debug == True):
            print("Detected:", elements)
        list.append(elements)

    results['records'] = list
    msg = "検出できません"
    if len(list) > 0:
        # ファイルの保存
        detected[0].save(filename=outputImageFile)
        msg = "送信終了"
    results['message'] = msg

    return results

#
# HISTORY
# [2] 2025-11-10 - Upgraded to Ultralytics
# [1] 2024-11-14 - Initial version
#