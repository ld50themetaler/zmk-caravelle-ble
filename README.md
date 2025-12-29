# Caravelle BLE用のZMKファームウェア

## ざっくりとした使い方 (人柱向け
* 想定環境 : Windows11 + WSL(Ubuntu) + Devcontainer
* 必要なもの : ST-Link の互換機 (私はこれを使用  
  https://ja.aliexpress.com/item/1005008843849127.html
  * Amazon.co.jp で売ってるこういうのも使えるはず  
    https://www.amazon.co.jp/dp/B09WVQNFNM  
    <img width="215" height="300" alt="image" src="https://github.com/user-attachments/assets/87a66ece-e8ee-479c-a53a-e3ee78e49a1f" />

## 注意
* ST-Linkを使用してPCBにFWを書き込みます。Bluetoothから書き込むことはできません。
* ブートローダを上書きするので、QMK版のFWが使えなくなります。  
  元に戻すにはブートローダの復旧などが必要です。意味が分からない方は本FWを使用しないでください。

## 手順
1. zmk-workspaceの手順で開発コンテナを使用して、zmkのローカルビルドを整える
   https://t.co/TKqf0q6Pdm
2. config/zmk-caravelle-ble として zmk-caravelle-ble リポジトリを git clone
3. $ just init ./config/zmk-caravelle-ble を実行
4. $ just clean && just build caravelle でビルド
5. firmwareディレクトリに以下のファイルが出力される  
   caravelle_left_central.bin  
   caravelle_right_peripheral.bin
7. 以下を参考にして openocd 環境を構築  
   https://nahitafu.cocolog-nifty.com/nahitafu/2024/01/post-9784e8.html
8. ST-Linkを左手のCaravelle BLEのPCBのシルク印刷に従って接続
9. WSLのUbuntuで以下のコマンドを実行して、PCBと接続できていることを確認(Ctrl+Cで終了できます  
   $ openocd -f interface/stlink.cfg -f target/nordic/nrf52.cfg
10. 以下のコマンドで左手分を書き込み  
   $ openocd -f interface/stlink.cfg -f target/nordic/nrf52.cfg -c "init; halt; nrf5 mass_erase; program ./firmware/caravelle_left_central.bin 0x0 verify reset; exit"
11. 同様に右手のPCBにST-Linkを接続して、以下のコマンドで右手分を書き込み  
   $ openocd -f interface/stlink.cfg -f target/nordic/nrf52.cfg -c "init; halt; nrf5 mass_erase; program ./firmware/caravelle_right_peripheral.bin 0x0 verify reset; exit"
12. ホスト側のBluetooth情報をリセットして、"Caravelle "という名前で検出されるので接続する
13. ZMK Studioを使用する場合は、Web版はUSB接続しか使えないため、Bluetooth接続に対応したデスクトップ版を使用してください

## 補足
* ST-Linkの種類によっては付属ケーブルがメス-メスになっているようです。その時は自キーを作ってるとよく余るピンヘッダを使うとPCBに接続しやすいです
* キーマップは以下になっています。デフォルトレイヤーがDvorakなので各自でお好みの配列に変更してお使いください  
  https://github.com/ld50themetaler/zmk-caravelle-ble/blob/main/config/caravelle.keymap

## TODO
* 純正のソフトデバイス+ブートローダーを使用したOTAによるファームウェア書き込み (現状は ST-Link を使用した有線書き込みのみ対応)
  * nrfutilの現在のインストール手順などの情報の整理が必要
* デフォルトレイヤに Qwerty を追加
* バッテリーの残量表示に対応する (現状は常に 100% になってるみたいです)
* 安定性の確認 (1日程度しか動作させていないので、安定性は試せていません)
* 不要な設定の削除や、動作改善に関するチューニング
* Readmeの導入手順の加筆
* OpenOCDではなくもっと簡単な nRF Connect for Desktop での導入 (ST-Linkは必要ですが)

## ソフトデバイスとブートローダの復旧
* openocd -f interface/stlink.cfg -f target/nordic/nrf52.cfg -c init -c "reset init" -c halt -c "nrf5 mass_erase" -c "program ./zmk-workspace/bootloader/s132_nrf52_3.0.0_softdevice.hex verify" -c reset -c exit
* openocd -f interface/stlink.cfg -f target/nordic/nrf52.cfg -c "init; halt; program ./zmk-workspace/caravelle_bootloader/caravelle_ble-bootloader.hex verify reset; exit"
* ソフトデバイスとブートローダーは本家のCaravelle BLEのビルドガイドに入手先が記載されています

