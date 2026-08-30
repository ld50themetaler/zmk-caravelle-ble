# Caravelle BLE用のZMKファームウェア
2019年に発売された左右分割完全無線の傑作キーボード Caravelle BLEをより快適に使い続けるべく、ZMKへ移植しました。  
QMK + nRF52 の純正ファームウェア環境から、そのまま **Bluetooth 経由の OTA アップデート**で本 ZMK ファームウェアを導入・更新できます。  
（※ ST-Link 等の SWD 機器が必要になるのは、何らかの問題が発生して有線でのリカバリが必要になった場合のみです）


## 特徴
* **Bluetooth (OTA) 経由でのファームウェアアップデート対応**
  * Caravelle BLE 純正のブートローダ環境のまま、PC ブラウザやスマホアプリからワイヤレスで書き換え可能
* ZMK Studioによるリアルタイムのキーマップ編集
* GitHub Actionsによるオンラインビルド
  * リポジトリへの push や手動実行で、左右それぞれの `.hex` / `.bin` および署名済み OTA 用パッケージ (`.zip`) が自動生成されます
* 安定＆低遅延な使用感
* 複数デバイス間のBluetooth接続先のスムーズな切り替え

## ファームウェアの更新方法 (OTAアップデート)

GitHub Actions のビルド成果物（Artifacts: `caravelle_ble_firmware`）に含まれる以下のパッケージを使用して、ワイヤレスでアップデートできます。
* **左手用**: `caravelle_left_central_ota.zip`
* **右手用**: `caravelle_right_peripheral_ota.zip`

### 1. PC からの OTA アップデート (Web Bluetooth) 【自己責任】

Web Bluetooth API に対応したブラウザ（Google Chrome、Microsoft Edge など）を使用することで、PC から直接 OTA アップデートが可能です。

> [!WARNING]
> **【重要・自己責任】**  
> PC の Web ブラウザ経由での OTA アップデートは、Bluetooth アダプタや OS 環境・ブラウザの挙動によって通信が途切れるリスクがあります。転送失敗等により万が一文鎮化した場合は、ST-Link 等の SWD ライタを用いた有線復旧が必要となります。必ず**自己責任**であることをご了承の上でご利用ください。

* **アップデートツール**: [Web Bluetooth DFU (thegecko.github.io)](https://thegecko.github.io/web-bluetooth-dfu/examples/web.html)

**手順:**
1. キーボード側で DFU (ブートローダ) モードに入ります（キーマップに割り当てた `&bootloader` を押すか、基板上のリセット操作等）。デバイスが DFU 待機状態 (`DfuTarg` など) になります。
2. 上記サイトを Chrome 等で開き、画面の指示に従って Bluetooth デバイスをスキャン・接続します。
3. ダウンロードした OTA パッケージ（左手なら `caravelle_left_central_ota.zip`、右手なら `caravelle_right_peripheral_ota.zip`）を選択します。
4. アップデートを実行し、100% 完了するまでキーボードの電源を切らずにお待ちください。

### 2. スマートフォンからの OTA アップデート (公式アプリ推奨)

Nordic 公式アプリを使用すると、安定して OTA アップデートが行えます。

* **対応アプリ**:
  * **nRF Connect for Mobile** (iOS / Android)
  * **nRF Device Firmware Update** (iOS / Android)
* **手順**:
  1. スマホに OTA パッケージ (`.zip`) をダウンロード・保存します。
  2. キーボードを DFU モードにします。
  3. アプリを起動してスキャンし、`DfuTarg` に接続します。
  4. DFU 画面から zip ファイル（Distribution packet (ZIP)）を選択して転送します。

---

## 未対応機能 / 課題
* バッテリー残量表示
  * 一次電池＆USB接続がない関係で、既存のバッテリー残量ライブラリがそのままでは正しい残量が表示されず使えませんでした
  * ライブラリをフォークして改造するなどで対応ができそうではあります

## 有線でのトラブル復旧 / リカバリ (ST-Link 使用)
OTA アップデートの失敗等でキーボードが起動しなくなった場合など、有線での緊急復旧が必要になったときの手順です。  
**※ 通常の使用や初回導入時には ST-Link は不要です（OTA で書き換え可能です）。**

* 想定環境 : Windows11 + WSL(Ubuntu) + Devcontainer
* 必要なもの : ST-Link の互換機 (私はこれを使用  
  https://ja.aliexpress.com/item/1005008843849127.html
  * Amazon.co.jp で売ってるこういうのも使えるはず  
    https://www.amazon.co.jp/dp/B09WVQNFNM  
    <img width="215" height="300" alt="image" src="https://github.com/user-attachments/assets/87a66ece-e8ee-479c-a53a-e3ee78e49a1f" />

### 注意
* ブートローダや SoftDevice を全消去（mass_erase）した場合は、OTA 機能が失われます。その場合は本ページ末尾の「ソフトデバイスとブートローダの復旧」手順を行ってください。

### 復旧手順 (ST-Link 使用時)


1. ビルド環境の作成  
   GitHub Actionsでオンラインビルドする場合は不要です
   1. zmk-workspaceの手順で開発コンテナを使用して、zmkのローカルビルドを整える  
     https://t.co/TKqf0q6Pdm  
   1. config/zmk-caravelle-ble として zmk-caravelle-ble リポジトリを git clone
   1. $ just init ./config/zmk-caravelle-ble を実行
   1. $ just clean && just build caravelle でビルド
   1. firmwareディレクトリに以下のファイルが出力される  
      caravelle_left_central.bin  
      caravelle_right_peripheral.bin
1. 以下を参考にして openocd 環境を構築  
   ST-Linkを使用してファームウェアを書き込めれば、OpenOCD以外のツールでもかまいません  
   https://nahitafu.cocolog-nifty.com/nahitafu/2024/01/post-9784e8.html
1. ST-Linkを左手のCaravelle BLEのPCBのシルク印刷に従って接続
1. WSLのUbuntuで以下のコマンドを実行して、PCBと接続できていることを確認(Ctrl+Cで終了できます  
   $ openocd -f interface/stlink.cfg -f target/nordic/nrf52.cfg
1. 以下のコマンドで左手分を書き込み  
   $ openocd -f interface/stlink.cfg -f target/nordic/nrf52.cfg -c "init; halt; nrf5 mass_erase; program ./firmware/caravelle_left_central.bin 0x0 verify reset; exit"
1. 同様に右手のPCBにST-Linkを接続して、以下のコマンドで右手分を書き込み  
   $ openocd -f interface/stlink.cfg -f target/nordic/nrf52.cfg -c "init; halt; nrf5 mass_erase; program ./firmware/caravelle_right_peripheral.bin 0x0 verify reset; exit"
1. ホスト側のBluetooth情報をリセットして、"Caravelle "という名前で検出されるので接続する
1. ZMK Studioを使用する場合は、Web版はUSB接続しか使えないため、Bluetooth接続に対応したデスクトップ版を使用してください

## 補足
* ST-Linkの種類によっては付属ケーブルがメス-メスになっているようです。その時は自キーを作ってるとよく余るピンヘッダを使うとPCBに接続しやすいです
* キーマップは以下になっています。各自でお好みの配列に変更してお使いください  
  https://github.com/ld50themetaler/zmk-caravelle-ble/blob/main/config/caravelle.keymap

## TODO
* ~~純正のソフトデバイス+ブートローダーを使用したOTAによるファームウェア書き込み~~ (対応完了)
* ~~デフォルトレイヤに Qwerty を追加~~ (済)
* バッテリーの残量表示に対応する (現状は常に 100% になってるみたいです)
* 安定性の確認 (1日程度しか動作させていないので、安定性は試せていません)
* 不要な設定の削除や、動作改善に関するチューニング
* Readmeの導入手順の加筆
* OpenOCDではなくもっと簡単な nRF Connect for Desktop での導入 (ST-Linkは必要ですが)
* ~~ZMK の Keymap Editor に対応~~ (済)  
  https://nickcoutsos.github.io/keymap-editor  
  info.jsonを用意すればできるはず

## ソフトデバイスとブートローダの復旧
* openocd -f interface/stlink.cfg -f target/nordic/nrf52.cfg -c init -c "reset init" -c halt -c "nrf5 mass_erase" -c "program ./zmk-workspace/bootloader/s132_nrf52_3.0.0_softdevice.hex verify" -c reset -c exit
* openocd -f interface/stlink.cfg -f target/nordic/nrf52.cfg -c "init; halt; program ./zmk-workspace/caravelle_bootloader/caravelle_ble-bootloader.hex verify reset; exit"
* ソフトデバイスとブートローダーは本家のCaravelle BLEのビルドガイドに入手先が記載されています

