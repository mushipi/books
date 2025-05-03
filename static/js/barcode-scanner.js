/**
 * バーコードスキャナー機能
 * QuaggaJSを使用してカメラからバーコードを読み取る
 */

class BarcodeScanner {
    constructor(containerId, resultCallback) {
        this.containerId = containerId;
        this.resultCallback = resultCallback;
        this.quaggaInitialized = false;
        this.torchAvailable = false;
        this.torchOn = false;
        this.lastDetectedBarcode = null;
        this.lastDetectedAt = 0;
        this.cooldownPeriod = 3000; // ミリ秒単位のクールダウン期間
    }

    /**
     * カメラデバイスの一覧を取得
     * @returns {Promise} カメラデバイスの配列を解決するPromise
     */
    async getCameraDevices() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
            throw new Error('カメラにアクセスする権限がありません');
        }

        const devices = await navigator.mediaDevices.enumerateDevices();
        return devices.filter(device => device.kind === 'videoinput');
    }

    /**
     * スキャナーを初期化して開始
     * @param {string} deviceId - カメラデバイスID
     */
    async startScanner(deviceId) {
        if (this.quaggaInitialized) {
            this.stopScanner();
        }

        // QuaggaJS初期化設定
        const config = {
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: document.getElementById(this.containerId),
                constraints: {
                    width: 1280,
                    height: 720,
                    deviceId: deviceId,
                    facingMode: "environment"
                },
            },
            locator: {
                patchSize: "medium",
                halfSample: true
            },
            numOfWorkers: 2,
            frequency: 10,
            decoder: {
                readers: [
                    "ean_reader",
                    "ean_8_reader",
                    "isbn_reader"
                ]
            },
            locate: true
        };

        try {
            // QuaggaJSの初期化
            await new Promise((resolve, reject) => {
                Quagga.init(config, error => {
                    if (error) {
                        reject(error);
                    } else {
                        resolve();
                    }
                });
            });

            // 初期化成功
            this.quaggaInitialized = true;
            
            // ライト機能の確認
            const track = Quagga.CameraAccess.getActiveTrack();
            if (track && typeof track.getCapabilities === 'function') {
                const capabilities = track.getCapabilities();
                this.torchAvailable = capabilities.torch || false;
            }

            // バーコード検出時のイベントハンドラ
            Quagga.onDetected(result => this._onBarcodeDetected(result));
            
            // スキャン開始
            Quagga.start();
            
            return {
                success: true,
                torchAvailable: this.torchAvailable
            };
        } catch (error) {
            return {
                success: false,
                error: error.message || 'スキャナーの初期化に失敗しました'
            };
        }
    }

    /**
     * スキャナーを停止
     */
    stopScanner() {
        if (this.quaggaInitialized) {
            Quagga.stop();
            this.quaggaInitialized = false;
            
            // ライトをオフにする
            if (this.torchOn) {
                this.toggleTorch();
            }
        }
    }

    /**
     * ライトの切り替え
     * @returns {Promise<boolean>} 成功した場合はtrue、失敗した場合はfalse
     */
    async toggleTorch() {
        if (!this.torchAvailable || !this.quaggaInitialized) {
            return false;
        }

        const track = Quagga.CameraAccess.getActiveTrack();
        if (track && typeof track.applyConstraints === 'function') {
            try {
                await track.applyConstraints({
                    advanced: [{ torch: !this.torchOn }]
                });
                this.torchOn = !this.torchOn;
                return true;
            } catch (error) {
                console.error('ライト操作エラー:', error);
                return false;
            }
        }
        return false;
    }

    /**
     * バーコード検出時の処理
     * @param {Object} result - 検出結果
     * @private
     */
    _onBarcodeDetected(result) {
        const code = result.codeResult.code;
        const now = new Date().getTime();
        
        // 同じバーコードの連続検出を防止（クールダウン期間内）
        if (this.lastDetectedBarcode === code && now - this.lastDetectedAt < this.cooldownPeriod) {
            return;
        }
        
        // 検出結果の更新
        this.lastDetectedBarcode = code;
        this.lastDetectedAt = now;
        
        // 効果音再生
        this._playBeepSound();
        
        // コールバック関数の呼び出し
        if (typeof this.resultCallback === 'function') {
            this.resultCallback({
                code: code,
                type: result.codeResult.format,
                timestamp: now
            });
        }
    }

    /**
     * 効果音の再生
     * @private
     */
    _playBeepSound() {
        // 短いビープ音のBase64エンコード
        const beepSoundBase64 = 'data:audio/wav;base64,UklGRl9vT19XQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YU...';
        
        try {
            const audio = new Audio(beepSoundBase64);
            audio.play().catch(e => console.log('効果音再生エラー:', e));
        } catch (e) {
            console.log('効果音再生エラー:', e);
        }
    }
}

// グローバルオブジェクトとしてエクスポート
window.BarcodeScanner = BarcodeScanner;
