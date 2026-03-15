import { PermissionsAndroid, Platform } from 'react-native';
import { BleManager, Device, Subscription } from 'react-native-ble-plx';
import base64 from 'react-native-base64';
import {
    ConnectOptions,
    DeviceDiscoveredCallback,
    DisconnectListener,
    NotificationListener,
    NotificationOptions,
    ScanOptions,
} from '../types';
import { BLUETOOTH_DEFAULT_CONFIG, BLUETOOTH_UUIDS } from '../constants/bluetoothConstants';

// 通知订阅的唯一标识符类型，格式为 "serviceUUID:characteristicUUID"
type NotificationKey = `${string}:${string}`;

/**
 * 蓝牙服务类
 *
 * 该类封装了 React Native BLE PLX 库的核心功能，提供了一套完整的蓝牙设备管理解决方案。
 * 主要功能包括：
 * - 蓝牙权限管理和状态检查
 * - 设备扫描和连接管理
 * - 特征值读写和通知监听
 * - 连接状态监控和自动清理
 * - 设备信息读取
 *
 * 设计原则：
 * - 单例模式：确保全局只有一个蓝牙管理实例
 * - 资源管理：自动清理订阅和连接，防止内存泄漏
 * - 错误处理：提供详细的错误信息和恢复机制
 * - 平台兼容：支持 iOS 和 Android 平台的差异化处理
 *
 * @category Services
 */
class BluetoothService {
    // BLE 管理器实例
    private manager: BleManager;

    // 当前连接的设备实例
    private connectedDevice: Device | null = null;

    // 断开连接监听器集合
    private disconnectListeners = new Set<DisconnectListener>();

    // 设备断开连接的订阅
    private disconnectSubscription: Subscription | null = null;

    // 特征值通知订阅映射表，key 为 "serviceUUID:characteristicUUID"
    private notificationSubscriptions = new Map<NotificationKey, Subscription>();

    // 扫描超时定时器
    private scanTimer: ReturnType<typeof setTimeout> | null = null;

    // 扫描状态标识
    private scanning = false;

    // 断开连接状态标识
    private isDisconnecting = false;

    // #region Initialization & Permissions

    /**
     * 构造函数
     * 初始化 BLE 管理器实例
     */
    constructor() {
        this.manager = new BleManager();
    }

    /**
     * 初始化蓝牙服务
     *
     * 执行必要的初始化步骤：
     * 1. 检查并请求蓝牙相关权限
     * 2. 确保蓝牙功能已启用
     *
     * @throws {Error} 当权限被拒绝或蓝牙未启用时抛出错误
     */
    async initialize(): Promise<void> {
        await this.ensurePermissions();
        await this.ensureBluetoothEnabled();
    }

    /**
     * 获取当前蓝牙适配器状态
     *
     * 可用于判断蓝牙是否已开启。
     * @returns {Promise<string>} 当前蓝牙状态，如 "PoweredOn"、"PoweredOff"、"Unauthorized"
     */
    async getAdapterState(): Promise<string> {
        try {
            return await this.manager.state();
        } catch (error) {
            console.warn('获取蓝牙状态失败:', error);
            return 'Unknown';
        }
    }

    /**
     * 获取当前连接的设备
     *
     * @returns {Device | null} 当前连接的设备实例，未连接时返回 null
     */
    getConnectedDevice(): Device | null {
        return this.connectedDevice;
    }

    /**
     * 检查设备是否已连接
     *
     * @param {string} [deviceId] - 可选的设备 ID，未提供时检查当前连接的设备
     * @returns {Promise<boolean>} 设备连接状态
     */
    async isDeviceConnected(deviceId?: string): Promise<boolean> {
        const targetId = deviceId ?? this.connectedDevice?.id;
        if (!targetId) {
            return false;
        }

        try {
            return await this.manager.isDeviceConnected(targetId);
        } catch (error) {
            console.warn('BLE isDeviceConnected error:', error);
            return false;
        }
    }

    // #endregion

    // #region Scanning

    /**
     * 开始扫描蓝牙设备
     *
     * @param {DeviceDiscoveredCallback} onDeviceFound - 发现设备时的回调函数
     * @param {ScanOptions} [options={}] - 扫描选项
     * @param {number} [options.timeout] - 扫描超时时间（毫秒）
     * @param {function} [options.filter] - 设备过滤函数
     */
    startScan(onDeviceFound: DeviceDiscoveredCallback, options: ScanOptions = {}): Promise<void> {
        return new Promise((resolve, reject) => {
            // 如果正在扫描，先停止当前扫描
            if (this.scanning) {
                this.stopScan();
            }

            const { timeout, filter } = options;
            this.scanning = true;
            let scanError: Error | null = null;

            // 开始设备扫描
            this.manager.startDeviceScan(null, null, (error, device) => {
                if (error) {
                    console.error('BLE scan error:', error);
                    scanError = error;
                    this.stopScan();
                    reject(error);
                    return;
                }

                if (device) {
                    // 应用过滤器（如果提供）
                    if (!filter || filter(device)) {
                        onDeviceFound(device);
                    }
                }
            });

            // 设置扫描超时
            if (timeout) {
                this.scanTimer = setTimeout(() => {
                    // console.log('🕐 扫描超时，停止扫描');
                    this.stopScan();
                    if (!scanError) {
                        resolve(); // 超时正常结束
                    }
                }, timeout);
            }
        });
    }

    /**
     * 停止设备扫描
     *
     * 清理扫描相关的资源：
     * - 清除超时定时器
     * - 停止 BLE 扫描
     * - 重置扫描状态
     */
    stopScan(): void {
        if (this.scanTimer) {
            clearTimeout(this.scanTimer);
            this.scanTimer = null;
        }

        if (this.scanning) {
            try {
                this.manager.stopDeviceScan();
            } catch (error) {
                console.warn('BLE stop scan error:', error);
            }
            this.scanning = false;
        }
    }

    // #endregion

    // #region Connection Management

    /**
     * 连接到指定设备
     *
     * @param {string} deviceId - 要连接的设备 ID
     * @param {ConnectOptions} [options={}] - 连接选项
     * @param {number} [options.timeout=10000] - 连接超时时间
     * @param {boolean} [options.autoConnect=false] - 是否自动重连
     * @param {number} [options.requestMTU] - 请求的 MTU 大小（仅 Android）
     * @returns {Promise<Device>} 连接成功的设备实例
     * @throws {Error} 连接失败时抛出错误
     */
    async connectToDevice(deviceId: string, options: ConnectOptions = {}): Promise<Device> {
        try {
            const {
                timeout = BLUETOOTH_DEFAULT_CONFIG.CONNECT_TIMEOUT,
                autoConnect = false,
                requestMTU = Platform.OS === 'android' ? BLUETOOTH_DEFAULT_CONFIG.MTU_ANDROID : undefined,
            } = options;

            // 🟡 先从缓存查
            const known = await this.manager.devices([deviceId]);

            // 🔵 如果系统还不认识这个设备，快速扫描一次确认
            if (!known || known.length === 0) {
                // console.log('设备未在缓存中，开始快速扫描确认...');
                const found = await new Promise<boolean>((resolve) => {
                    let resolved = false;
                    this.manager.startDeviceScan(null, null, (error, device) => {
                        if (error) {
                            console.warn('快速扫描出错:', error);
                            if (!resolved) resolve(false);
                            resolved = true;
                            this.manager.stopDeviceScan();
                            return;
                        }

                        if (device && device.id === deviceId) {
                            // console.log('快速扫描到目标设备:', deviceId);
                            if (!resolved) resolve(true);
                            resolved = true;
                            this.manager.stopDeviceScan();
                        }
                    });

                    // 最多扫描 3 秒
                    setTimeout(() => {
                        if (!resolved) resolve(false);
                        resolved = true;
                        this.manager.stopDeviceScan();
                    }, 3000);
                });

                if (!found) {
                    throw new Error('未发现目标设备，请确认设备已开机并靠近手机');
                }
            }

            // 执行设备连接
            const device = await this.manager.connectToDevice(deviceId, {
                timeout,
                autoConnect,
                requestMTU,
            });

            // 发现所有服务和特征值
            await device.discoverAllServicesAndCharacteristics();

            // 处理连接成功的设备
            this.handleConnectedDevice(device);
            this.connectedDevice = device;
            return device;
        } catch (error) {
            console.error('BLE connect error:', error);

            // 连接失败时不做额外处理，让上层逻辑处理缓存清理和重连

            throw error;
        }
    }

    /**
     * 断开设备连接
     *
     * @param {string} [deviceId] - 可选的设备 ID，未提供时断开当前连接的设备
     */
    async disconnectDevice(deviceId?: string): Promise<void> {
        const current = this.connectedDevice;
        if (!current) {
            return;
        }

        // 如果指定了设备 ID 且与当前设备不匹配，则不执行断开操作
        if (deviceId && current.id !== deviceId) {
            return;
        }

        // 清理所有通知订阅
        this.stopNotifications();

        // 清理断开连接监听器
        this.disconnectSubscription?.remove();
        this.disconnectSubscription = null;

        try {
            // 取消设备连接
            await current.cancelConnection();
        } catch (error) {
            console.warn('BLE disconnect error:', error);
        } finally {
            // 重置连接状态
            this.connectedDevice = null;
            this.connectedDevice = null;
        }
    }

    /**
     * 设置设备断开连接监听器
     *
     * @param {DisconnectListener} listener - 断开连接时的回调函数
     * @returns {function} 用于移除监听器的清理函数
     */
    setOnDisconnectedListener(listener: DisconnectListener): () => void {
        this.disconnectListeners.add(listener);
        return () => {
            this.disconnectListeners.delete(listener);
        };
    }

    // #endregion

    // #region IO Operations

    /**
     * 开始监听特征值通知
     *
     * @param {NotificationOptions} options - 通知选项（服务和特征值 UUID）
     * @param {NotificationListener} listener - 接收通知数据的回调函数
     * @returns {function} 用于停止通知的清理函数
     * @throws {Error} 设备未连接时抛出错误
     */
    startNotifications(options: NotificationOptions, listener: NotificationListener): () => void {
        const device = this.ensureConnected();
        const key = this.getNotificationKey(options);

        // 监听特征值变化
        const subscription = device.monitorCharacteristicForService(
            options.serviceUUID,
            options.characteristicUUID,
            (error, characteristic) => {
                if (error) {
                    console.error('BLE notification error:', error);
                    return;
                }
                if (characteristic?.value) {
                    listener(characteristic.value);
                }
            },
        );

        // 保存订阅以便后续清理
        this.notificationSubscriptions.set(key, subscription);
        return () => this.stopNotifications(options);
    }

    /**
     * 停止特征值通知监听
     *
     * @param {NotificationOptions} [options] - 要停止的特定通知选项，未提供时停止所有通知
     */
    stopNotifications(options?: NotificationOptions): void {
        try {
            if (!this.connectedDevice) {
                // console.log('🟡 skip stopNotifications: no connected device');
                return;
            }
            if (!options) {
                // 使用 forEach 避免对 Map 进行 for-of 迭代导致的 downlevelIteration 要求
                this.notificationSubscriptions.forEach((subscription) => {
                    try {
                        subscription?.remove?.();
                    } catch (e) {
                        console.warn('BLE stopNotifications: remove failed', e);
                    }
                });
                this.notificationSubscriptions.clear();
                return;
            }

            const key = this.getNotificationKey(options);
            const subscription = this.notificationSubscriptions.get(key);
            if (subscription) {
                try {
                    subscription?.remove?.();
                } catch (e) {
                    console.warn('BLE stopNotifications: single remove failed', e);
                }
                this.notificationSubscriptions.delete(key);
            }
        } catch (error) {
            console.warn('BLE stopNotifications global error:', error);
        }
    }

    /**
     * 向特征值写入数据（需要响应）
     *
     * @param {NotificationOptions} options - 目标特征值选项
     * @param {Uint8Array | string} rawData - 要写入的数据
     * @throws {Error} 设备未连接或写入失败时抛出错误
     */
    async sendDataWithResponse(
        options: NotificationOptions,
        rawData: Uint8Array | string,
    ): Promise<void> {
        const device = this.ensureConnected();
        const data = this.toBase64(rawData);

        // console.log('🔍 发送数据详情:', {
        //   serviceUUID: options.serviceUUID,
        //   characteristicUUID: options.characteristicUUID,
        //   dataLength: data.length,
        //   deviceId: device.id,
        //   deviceName: device.name
        // });

        // console.log('🔍 发送的数据(WithResponse):', data);

        try {
            await device.writeCharacteristicWithResponseForService(
                options.serviceUUID,
                options.characteristicUUID,
                data,
            );
            // console.log('✅ 数据发送成功 (WithResponse)');
        } catch (error: any) {
            console.error('❌ 发送数据失败 (WithResponse):', {
                error: error.message,
                reason: error.reason,
                errorCode: error.errorCode,
                serviceUUID: options.serviceUUID,
                characteristicUUID: options.characteristicUUID,
            });
            throw error;
        }
    }

    /**
     * 向特征值写入数据（无需响应）
     *
     * @param {NotificationOptions} options - 目标特征值选项
     * @param {Uint8Array | string} rawData - 要写入的数据
     * @throws {Error} 设备未连接或写入失败时抛出错误
     */
    async sendDataWithoutResponse(
        options: NotificationOptions,
        rawData: Uint8Array | string,
    ): Promise<void> {
        const device = this.ensureConnected();
        const data = this.toBase64(rawData);

        // console.log('🔍 发送数据详情 (NoResponse):', {
        //   serviceUUID: options.serviceUUID,
        //   characteristicUUID: options.characteristicUUID,
        //   dataLength: data.length,
        //   deviceId: device.id,
        //   deviceName: device.name
        // });

        // console.log('🔍 发送的数据(NoResponse):', data);

        try {
            await device.writeCharacteristicWithoutResponseForService(
                options.serviceUUID,
                options.characteristicUUID,
                data,
            );
            // console.log('✅ 数据发送成功 (WithoutResponse)');
        } catch (error: any) {
            console.error('❌ 发送数据失败 (WithoutResponse):', {
                error: error.message,
                reason: error.reason,
                errorCode: error.errorCode,
                serviceUUID: options.serviceUUID,
                characteristicUUID: options.characteristicUUID,
            });
            throw error;
        }
    }

    /**
     * 读取特征值数据
     *
     * @param {NotificationOptions} options - 目标特征值选项
     * @returns {Promise<string>} 解码后的特征值数据
     * @throws {Error} 设备未连接、读取失败或特征值为空时抛出错误
     */
    async readCharacteristic(options: NotificationOptions): Promise<string> {
        const device = this.ensureConnected();
        const characteristic = await device.readCharacteristicForService(
            options.serviceUUID,
            options.characteristicUUID,
        );

        if (!characteristic.value) {
            throw new Error('Characteristic returned empty value');
        }

        return base64.decode(characteristic.value);
    }

    /**
     * 读取设备信息
     *
     * 从设备信息服务 (0x180A) 读取标准设备信息字段：
     * - manufacturer: 制造商名称
     * - firmwareVersion: 固件版本
     * - hardwareVersion: 硬件版本
     * - serialNumber: 序列号
     *
     * @returns {Promise<Record<string, string>>} 设备信息对象
     */
    async readDeviceInfo(): Promise<Record<string, string>> {
        const fields = new Map([
            ['manufacturer', BLUETOOTH_UUIDS.MANUFACTURER_NAME],
            ['firmwareVersion', BLUETOOTH_UUIDS.FIRMWARE_REVISION],
            ['hardwareVersion', BLUETOOTH_UUIDS.HARDWARE_REVISION],
            ['serialNumber', BLUETOOTH_UUIDS.SERIAL_NUMBER],
        ]);
        const result: Record<string, string> = {};

        // 逐个读取设备信息字段
        // 使用 Array.from(entries) 转为数组后再迭代，避免对 Map 的直接 for-of
        for (const [field, characteristicUUID] of Array.from(fields.entries())) {
            try {
                result[field] = await this.readCharacteristic({
                    serviceUUID: BLUETOOTH_UUIDS.DEVICE_INFO_SERVICE,
                    characteristicUUID,
                });
            } catch (error) {
                console.warn(`Failed to read device info field ${field}:`, error);
            }
        }

        return result;
    }

    // #endregion

    // #region Helpers

    /**
     * 处理设备连接成功后的初始化工作
     *
     * @param {Device} device - 已连接的设备实例
     * @private
     */
    private handleConnectedDevice(device: Device) {
        this.disconnectSubscription?.remove();

        this.disconnectSubscription = device.onDisconnected((error, disconnectedDevice) => {
            // console.log('BLE device disconnected:', error, disconnectedDevice);
            this.isDisconnecting = true;
            this.connectedDevice = null;
            // 使用 forEach 避免对 Set 进行 for-of 迭代导致的 downlevelIteration 要求
            this.disconnectListeners.forEach((listener) => {
                try {
                    listener(disconnectedDevice);
                } catch (e) {
                    console.error(e);
                }
            });
        });
    }

    /**
     * 确保设备已连接
     *
     * @returns {Device} 当前连接的设备实例
     * @throws {Error} 设备未连接时抛出错误
     * @private
     */
    private ensureConnected(): Device {
        // console.log('🔍 检查设备连接状态:', {
        //   hasConnectedDevice: !!this.connectedDevice,
        //   deviceId: this.connectedDevice?.id,
        //   deviceName: this.connectedDevice?.name
        // });

        if (!this.connectedDevice) {
            console.error('❌ ensureConnected: 设备未连接');
            throw new Error('Device not connected');
        }

        return this.connectedDevice;
    }

    /**
     * 生成通知订阅的唯一键
     *
     * @param {NotificationOptions} options - 通知选项
     * @returns {NotificationKey} 格式为 "serviceUUID:characteristicUUID" 的唯一键
     * @private
     */
    private getNotificationKey(options: NotificationOptions): NotificationKey {
        return `${options.serviceUUID.toLowerCase()}:${options.characteristicUUID.toLowerCase()}`;
    }

    /**
     * 将数据转换为 Base64 格式
     *
     * @param {Uint8Array | string} data - 原始数据
     * @returns {string} Base64 编码的数据
     * @private
     */
    private toBase64(data: Uint8Array | string): string {
        // react-native-ble-plx 需要 Base64 编码的字符串
        if (typeof data === 'string') {
            return base64.encode(data);
        }
        return base64.encodeFromByteArray(data);
    }

    /**
     * 确保应用具有必要的蓝牙权限
     *
     * 根据 Android API 级别请求不同的权限：
     * - API 31+: BLUETOOTH_SCAN, BLUETOOTH_CONNECT, ACCESS_FINE_LOCATION
     * - API <31: ACCESS_FINE_LOCATION
     *
     * @throws {Error} 权限被拒绝时抛出错误
     * @private
     */
    private async ensurePermissions(): Promise<void> {
        if (Platform.OS !== 'android') {
            return;
        }

        const apiLevel =
            typeof Platform.Version === 'number'
                ? Platform.Version
                : parseInt(String(Platform.Version), 10);

        if (apiLevel >= 31) {
            // Android 12+ 需要新的蓝牙权限
            const permissions = [
                PermissionsAndroid.PERMISSIONS.BLUETOOTH_SCAN,
                PermissionsAndroid.PERMISSIONS.BLUETOOTH_CONNECT,
                PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
            ];

            const results = await PermissionsAndroid.requestMultiple(permissions);
            const denied = Object.entries(results)
                .filter(([, status]) => status !== PermissionsAndroid.RESULTS.GRANTED)
                .map(([permission]) => permission);

            if (denied.length > 0) {
                throw new Error(`Bluetooth permissions denied: ${denied.join(', ')}`);
            }
        } else {
            // Android 11 及以下版本只需要位置权限
            const result = await PermissionsAndroid.request(
                PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION,
            );

            if (result !== PermissionsAndroid.RESULTS.GRANTED) {
                throw new Error('Location permission denied');
            }
        }
    }

    /**
     * 确保蓝牙功能已启用
     *
     * 检查蓝牙状态并在必要时提示用户启用蓝牙：
     * - iOS: 监听蓝牙状态变化，等待用户启用
     * - Android: 检查当前状态，提示用户手动启用
     *
     * @throws {Error} 蓝牙未启用或被拒绝时抛出错误
     * @private
     */
    private async ensureBluetoothEnabled(): Promise<void> {
        if (Platform.OS === 'ios') {
            const initialState = await this.manager.state();
            if (initialState === 'PoweredOn') {
                return;
            }

            // iOS 需要等待蓝牙状态变化
            await new Promise<void>((resolve, reject) => {
                const subscription = this.manager.onStateChange((state) => {
                    if (state === 'PoweredOn') {
                        subscription.remove();
                        resolve();
                    } else if (state === 'PoweredOff' || state === 'Unauthorized') {
                        subscription.remove();
                        // 移除 Alert，改为抛出错误，由 UI 层处理提示
                        reject(new Error(`Bluetooth state: ${state}`));
                    }
                }, true);
            });
            return;
        }

        // Android 直接检查蓝牙状态
        const state = await this.manager.state();
        if (state !== 'PoweredOn') {
            // 移除 Alert，改为抛出错误
            throw new Error(`Bluetooth state: ${state}`);
        }
    }
    // #endregion
}

/**
 * 蓝牙服务单例实例
 * @internal
 */
export const bluetoothService = new BluetoothService();