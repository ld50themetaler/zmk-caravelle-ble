# Caravelle BLE ZMK Firmware (開発版 / Pre-release)

2019年に発売された左右分割完全無線キーボード **Caravelle BLE** 向けの ZMK ファームウェア開発版です。  
純正のブートローダ環境（SoftDevice S132 v3.0.0）をそのまま活かし、**Bluetooth 経由のワイヤレス OTA (Over-The-Air) アップデート** に対応しました。

詳しい導入手順や最新仕様については、[README.md](https://github.com/ld50themetaler/zmk-caravelle-ble/blob/dev-ota/README.md) をご確認ください。

---

## 📦 配布ファイル（Assets）

| ファイル名 | 用途 |
| :--- | :--- |
| **`caravelle_left_central_ota.zip`** | **左手用（Central）BLE OTA アップデートパッケージ**（Nordic Secure DFU 署名済み） |
| **`caravelle_right_peripheral_ota.zip`** | **右手用（Peripheral）BLE OTA アップデートパッケージ**（Nordic Secure DFU 署名済み） |
| `caravelle_left_central.hex` / `.bin` | 左手用 ファームウェア（有線 ST-Link / SWD リカバリ用） |
| `caravelle_right_peripheral.hex` / `.bin` | 右手用 ファームウェア（有線 ST-Link / SWD リカバリ用） |

---

## ⌨️ キーマップ構成

本ファームウェアのデフォルトレイヤーは **Dvorak配列** に設定されています。  
また、ZMK Studio によるリアルタイムなキー配置変更にも対応しています。

### レイヤー構成
* **Layer 0 (Default): Dvorak 配列**
  * 左手: `ESC(GUI)`, `'`, `,`, `.`, `P`, `Y` / `TAB(Ctrl)`, `A`, `O`, `E(Ctrl)`, `U`, `I` / `Shift`, `;`, `Q`, `J`, `K`, `X`
  * 右手: `F`, `G`, `C`, `R`, `L`, `/` / `(`, `)`, `D`, `H`, `T(Ctrl)`, `N`, `S`, `-` / `{`, `}`, `B`, `M`, `W`, `V`, `Z`, `Shift`
  * 親指キー:
    * 左手: `MO(3: ADJUST)`, `BSPC(Alt)`, `MO(1: LOWER)`, `SPACE(Shift)`
    * 右手: `ENTER(Ctrl)`, `MO(2: RAISE)`, `TAB(Alt)`, `MO(3: ADJUST)`
  * ※ Mod-Tap (`&mt`) は `tap-preferred` 設定を採用し、高速ローリング入力時の誤ホールドを防ぎます。
* **Layer 1 (LOWER)**:
  * ファンクションキー (`F1`〜`F12`)、矢印キー (`←` `↓` `↑` `→`)、`Home` / `End` / `PageUp` / `PageDown`、`Alt + ` ` (IME 切替マクロ)
* **Layer 2 (RAISE)**:
  * 数字キー (`1`〜`0`)、記号類 (`[` `]` `/` `=` `-` `` ` `` `\`)
* **Layer 3 (ADJUST)**:
  * 最下段の親指キー両端（`MO 3`）を押すことでアクセスできます。
  * **`bootloader`**: Nordic Secure DFU モードへ移行（OTA アップデート待機状態になります）
  * **`bt BT_SEL 0` 〜 `bt BT_SEL 5`**: Bluetooth 接続プロファイルの切り替え（最大 6 台）
  * **`bt BT_CLR`**: 現在のプロファイルのペアリング情報を削除
  * **`bt BT_CLR_ALL`**: **すべての接続先ペアリング情報を一括全消去**
  * **`sys_reset`**: キーボードのリセット
  * **`studio_unlock`**: ZMK Studio の編集ロック解除

---

## ✨ 主な対応機能

1. **Bluetooth (OTA) 経由のファームウェア更新完全対応**:
   - 純正の QMK + nRF52 ファームウェア環境から、**ハードウェアの分解や ST-Link なしにワイヤレスのまま直接 ZMK へ移行・更新** できます。
2. **PC ブラウザからの Web Bluetooth DFU 対応**:
   - PC の Chrome や Edge から [Web Bluetooth DFU](https://thegecko.github.io/web-bluetooth-dfu/examples/web.html) を使って直接 OTA 書き換えが可能です。
3. **ZMK Studio 対応**:
   - Bluetooth 接続対応の ZMK Studio デスクトップ版から、GUI 上でキーマップを直感的にカスタマイズできます。
4. **マルチペアリング (最大 6 台)**:
   - 複数台の PC やスマートフォンとペアリングし、ADJUST レイヤーからワンタッチで切り替えられます。
5. **一次電池向けバッテリー管理モジュール搭載**:
   - 単4一次電池駆動に配慮したバッテリー管理モジュールを組み込んでいます。

---

## 📲 ファームウェアの更新方法 (OTA)

### 方法 A: PC ブラウザからアップデート (Web Bluetooth) 【自己責任】

> [!WARNING]
> **【重要・自己責任について】**  
> PC の Web ブラウザ経由での OTA アップデートは、Bluetooth アダプタの相性や OS 環境・ブラウザの通信切断等により転送失敗するリスクがあります。万が一起動不能（文鎮化）になった場合は、ST-Link 等の SWD ライタによる有線復旧が必要となります。必ず**自己責任**であることをご理解の上でご使用ください。

1. キーボードを DFU モードにします（ADJUST レイヤーの `bootloader` キーを押すか、基板のリセット操作）。
2. Web Bluetooth 対応ブラウザ（Google Chrome / Microsoft Edge など）で **[Web Bluetooth DFU](https://thegecko.github.io/web-bluetooth-dfu/examples/web.html)** を開きます。
3. 「Connect」を押し、一覧から `DfuTarg` を選択して接続します。
4. 本リリースの Assets からダウンロードした zip（左手なら `caravelle_left_central_ota.zip`、右手なら `caravelle_right_peripheral_ota.zip`）を選択します。
5. 「Send」を押して転送を開始します（100% になるまで電源を切らずにお待ちください）。

### 方法 B: スマートフォンアプリからアップデート (公式アプリ推奨)

より安定した更新を行いたい場合は、Nordic 公式アプリのご利用をおすすめします。

* **対応アプリ**: **nRF Connect for Mobile** または **nRF Device Firmware Update** (iOS / Android)
1. スマートフォンに本リリースの zip パッケージをダウンロードします。
2. キーボードを DFU モードにし、アプリからスキャンして `DfuTarg` に接続します。
3. DFU 画面で zip パッケージを指定して転送を実行します。

---

## 🛠️ 有線リカバリについて
通常の使用や初回導入時には ST-Link は不要ですが、万が一の文鎮化やブートローダ復旧が必要な場合は、[README.md の有線復旧手順](https://github.com/ld50themetaler/zmk-caravelle-ble/blob/dev-ota/README.md#有線でのトラブル復旧--リカバリ-st-link-使用) をご参照ください。
