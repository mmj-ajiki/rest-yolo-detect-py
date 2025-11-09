# Windowsで開発する際の注意点

eYACHO および GEMBA NoteのようなWindows Storeアプリは、初期設定ではlocalhostに接続できない。localhostへの接続を許可するには、対象製品ごとにループバックを有効化する。

[READMEへ戻る](./README.md)

## ループバックの有効化

管理者モードで起動したコマンドプロンプトを用いて実行する。

### eYACHO for Business の場合

```batch
CheckNetIsolation.exe LoopbackExempt -a -n=MetaMoJiCorporation.eYACHOforBusiness7_dprdgbsyk6pqc
```

### eYACHO Viewer の場合

```batch
CheckNetIsolation.exe LoopbackExempt -a -n=MetaMoJiCorporation.eYACHOViewer7_dprdgbsyk6pqc
```

### GEMBA Note for Business の場合

```batch
CheckNetIsolation.exe LoopbackExempt -a -n=MetaMoJiCorporation.GEMBANoteforBusiness7_dprdgbsyk6pqc
```

### GEMBA Note Viewer の場合

```batch
CheckNetIsolation.exe LoopbackExempt -a -n=MetaMoJiCorporation.GEMBANoteViewer7_dprdgbsyk6pqc
```

※Windowsの設定で開発者用モードをONにしている場合など、環境によってはコマンドの実行が必要ない場合がある。
