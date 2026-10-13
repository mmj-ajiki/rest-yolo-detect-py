#!/usr/bin/env python
# coding: utf-8
#
# [FILE] util.py
#
# [DESCRIPTION]
#  ユーティリティ関数を定義する
#

import base64
import pymupdf  # PyMuPDF
import os

#
# [FUNCTION] getNoteId()
#
# [DESCRIPTION]
#  eYACHO/GEMBA NoteのノートリンクからノートIDを抽出する
#
# [INPUTS]
#  notelink - ノートリンク（例：https://mps-beta.metamoji.com/link/hsocl-4AynActJIV5e7gMQd5.mmjloc）
#
# [OUTPUTS] 
#  .mmjlocから前の/までの文字列を抽出する（例：hsocl-4AynActJIV5e7gMQd5）
#  スラッシュ(/)とピリオド(.)が含まれなければ、空文字列を返す
#
# [NOTES]
#
def getNoteId(notelink):
    # スラッシュで分割する
    splitString = notelink.split('/')
    if len(splitString) < 1:
        return ""

    # 最後のスラッシュからあとの文字列を取得
    splitString = splitString[len(splitString)-1]
    # ピリオドで分割
    splitString = splitString.split('.')
    if len(splitString) < 1:
        return ""
    
    return splitString[0]
#
# HISTORY
# [1] 2024-11-14 - Initial version
#

#
# [FUNCTION] pdf2PNG()
#
# [DESCRIPTION]
#  PDFファイルをPNGファイルに変換する関数
#
# [INPUTS]
#  pdf_path - PDFファイルのパス
#  output_folder - PNGファイルを出力するフォルダ
#  page_num - 変換するページ番号（0が最初のページ）
#  zoom - 解像度用の係数
#
# [OUTPUTS] 
#  エラーメッセージ。Noneであれば変換成功。
#
# [NOTES]
#
def pdf2PNG(pdf_path, output_path, page_num, zoom=1):
    error = None
    try:
        if not os.path.isfile(pdf_path):
            error = f"PDFファイルが見つからない: {pdf_path}"
            return error

        pdf_document = pymupdf.open(pdf_path)

        if page_num < len(pdf_document):
            page = pdf_document[page_num]
            matrix = pymupdf.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix)
            pix.save(output_path)
        else:
            error = f"ページ数が正しくない: {pdf_path}"

        pdf_document.close()
    except Exception as e:
        error = f"{e}"
    
    return error
#
# HISTORY
# [2] 2026-10-13 - Replaced fitz with pymupdf
# [1] 2025-11-27 - Initial version
#

#
# [FUNCTION] storeBinaryFile()
#
# [DESCRIPTION]
#  Base64文字列からバイナリファイルを保存する。
#
# [INPUTS]
#  filePath - 保存するファイルのパス
#  b64Text  - 画像やPDFのBase64文字列
#
# [OUTPUTS] 
#  成功 - None
#  失敗 - エラーメッセージ
#
# [NOTES]
#
def storeBinaryFile(filePath, b64Text):
    error = None
    
    # Base64をバイナリへ変換
    binContent = base64.b64decode(b64Text)

    # ファイルを保存
    try:
        with open(filePath, 'wb') as file:
            file.write(binContent)
    except Exception as e:
        error = f"{e}"
    
    return error
#
# HISTORY
# [1] 2025-11-27 - Initial version
#
