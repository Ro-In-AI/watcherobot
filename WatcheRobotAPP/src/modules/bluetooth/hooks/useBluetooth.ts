import { useCallback, useRef } from 'react';
import { Platform } from 'react-native';
import { bluetoothService } from '../services/bluetoothService';
import {
    BluetoothStatus,
    BluetoothDeviceInfo,
    BluetoothError,
    BluetoothReceivedData,
    ScanOptions,
    ConnectOptions,
    NotificationOptions,
    DeviceDiscoveredCallback,
    NotificationListener,
    DisconnectListener,
    SendCommandOptions,
    UseBluetoothReturn,
} from '../types';
import bleConfig from '../config/ble_config.json';
import base64 from 'react-native-base64';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useDispatch, useSelector } from 'react-redux';
import {
    setStatus,
    setDeviceInfo,
    setError,
    setReceivedData,
    clearAll,
    selectBluetoothState,
} from '../store';

/**
 * 蓝牙功能自定义 Hook
 *
 * 封装了蓝牙服务的所有功能，并集成了 Redux 状态管理。
 * 提供给 UI 组件使用的统一接口。
 *
 * @category Hooks
 *
 * @example
 * ```typescript
 * function MyComponent() {
 *   const { 
 *     status, 
 *     deviceInfo, 
 *     startScan, 
 *     connectToDevice,
 *     disconnect 
 *   } = useBluetooth();
 *
 *   // 扫描并连接
 *   const handleScan = async () => {
 *     await startScan((device) => {
 *       if (device.name === 'MyDevice') {
 *         connectToDevice(device.id);
 *       }
 *     });
 *   };
 *
 *   return (
 *     <View>
 *       <Text>状态: {status}</Text>
 *       {deviceInfo && <Text>已连接: {deviceInfo.name}</Text>}
 *       <Button title="扫描" onPress={handleScan} />
 *       <Button title="断开" onPress={disconnect} />
 *     </View>
 *   );
 * }
 * ```
 */
export const useBluetooth = (): UseBluetoothReturn => {
    // 使用 Redux 状态管理
    const dispatch = useDispatch();
    const { status, deviceInfo, receivedData, error } = useSelector(selectBluetoothState);

    // 自动重新扫描配置的 ref
    const autoRescanConfigRef = useRef<{
        scanTimeout: number;
        connectTimeout: number;
        autoConnect: boolean;
        enableAutoRescan: boolean;
        maxRescanAttempts: number;
        rescanDelayMs: number;
        currentAttempts: number;
    } | null>(null);

    // 扫描超时定时器 ref
    const scanTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

    /**
     * 初始化蓝牙服务
     */
    const initialize = useCallback(async () => {
        try {
            await bluetoothService.initialize();
        } catch (err: any) {
            dispatch(
                setError({
                    message: err.message || 'Bluetooth initialization failed',
                }),
            );
        }
    }, [dispatch]);

    /**
     * 开始扫描设备
     *
     * @param {DeviceDiscoveredCallback} onDeviceFound - 发现设备时的回调
     * @param {ScanOptions} [options] - 扫描选项
     */
    const startScan = useCallback(
        async (onDeviceFound: DeviceDiscoveredCallback, options?: ScanOptions) => {
            try {
                dispatch(setStatus(BluetoothStatus.Scanning));
                dispatch(setError(null));

                await bluetoothService.startScan(onDeviceFound, options);
            } catch (err: any) {
                dispatch(setStatus(BluetoothStatus.Error));
                dispatch(
                    setError({
                        message: err.message || 'Scan failed',
                    }),
                );
            }
        },
        [dispatch],
    );

    /**
     * 停止扫描
     */
    const stopScan = useCallback(async () => {
        bluetoothService.stopScan();
        if (status === BluetoothStatus.Scanning) {
            dispatch(setStatus(BluetoothStatus.Idle));
        }
    }, [dispatch, status]);

    /**
     * 连接到设备
     *
     * @param {string} deviceId - 设备 ID
     * @param {ConnectOptions} [options] - 连接选项
     */
    const connectToDevice = useCallback(
        async (deviceId: string, options?: ConnectOptions) => {
            try {
                dispatch(setStatus(BluetoothStatus.Connecting));
                dispatch(setError(null));

                const device = await bluetoothService.connectToDevice(deviceId, options);

                dispatch(setStatus(BluetoothStatus.Connected));
                dispatch(
                    setDeviceInfo({
                        id: device.id,
                        name: device.name,
                        mtu: device.mtu,
                    }),
                );

                // 设置断开连接监听
                bluetoothService.setOnDisconnectedListener((disconnectedDevice) => {
                    dispatch(setStatus(BluetoothStatus.Disconnected));
                    dispatch(setDeviceInfo(null));
                    // 可以在这里处理自动重连逻辑
                });
            } catch (err: any) {
                dispatch(setStatus(BluetoothStatus.Error));
                dispatch(
                    setError({
                        message: err.message || 'Connection failed',
                    }),
                );
            }
        },
        [dispatch],
    );

    /**
     * 断开连接
     */
    const disconnect = useCallback(async () => {
        try {
            await bluetoothService.disconnectDevice();
            dispatch(setStatus(BluetoothStatus.Disconnected));
            dispatch(setDeviceInfo(null));
            dispatch(setReceivedData(null));
        } catch (err: any) {
            console.warn('Disconnect error:', err);
        }
    }, [dispatch]);

    /**
     * 发送数据
     *
     * @param {string} serviceUUID - 服务 UUID
     * @param {string} characteristicUUID - 特征值 UUID
     * @param {string | Uint8Array} data - 要发送的数据
     * @param {boolean} [withResponse=false] - 是否需要响应
     */
    const writeData = useCallback(
        async (
            serviceUUID: string,
            characteristicUUID: string,
            data: string | Uint8Array,
            withResponse: boolean = false,
        ) => {
            try {
                const options: NotificationOptions = {
                    serviceUUID,
                    characteristicUUID,
                };

                if (withResponse) {
                    await bluetoothService.sendDataWithResponse(options, data);
                } else {
                    await bluetoothService.sendDataWithoutResponse(options, data);
                }
            } catch (err: any) {
                dispatch(
                    setError({
                        message: err.message || 'Write data failed',
                    }),
                );
                throw err;
            }
        },
        [dispatch],
    );

    /**
     * 读取特征值数据
     *
     * @param {string} serviceUUID - 服务 UUID
     * @param {string} characteristicUUID - 特征值 UUID
     * @returns {Promise<string>} 读取到的数据 (Base64)
     */
    const readData = useCallback(
        async (serviceUUID: string, characteristicUUID: string) => {
            try {
                const options: NotificationOptions = {
                    serviceUUID,
                    characteristicUUID,
                };
                return await bluetoothService.readCharacteristic(options);
            } catch (err: any) {
                dispatch(
                    setError({
                        message: err.message || 'Read data failed',
                    }),
                );
                throw err;
            }
        },
        [dispatch],
    );

    /**
     * 订阅通知
     *
     * @param {NotificationOptions} options - 通知选项
     * @param {NotificationListener} callback - 收到通知时的回调
     * @returns {function} 取消订阅函数
     */
    const subscribeToNotifications = useCallback(
        (options: NotificationOptions, callback: NotificationListener) => {
            try {
                return bluetoothService.startNotifications(options, (data) => {
                    // 查找特征值配置
                    let characteristicName = 'Unknown';
                    let valueFormat = 'string';

                    const service = bleConfig.services.find(s => s.uuid.toLowerCase() === options.serviceUUID.toLowerCase());
                    if (service) {
                        const char = service.characteristics.find(c => c.uuid.toLowerCase() === options.characteristicUUID.toLowerCase());
                        if (char) {
                            characteristicName = char.name;
                            if (char.value_format) {
                                valueFormat = char.value_format;
                            }
                        }
                    }

                    // 尝试解析数据
                    let processedData: any = data;
                    if (typeof data === 'string') {
                        try {
                            // 根据配置的格式进行解析
                            if (valueFormat === 'bytes') {
                                // Base64 转字节数组
                                const binaryString = base64.decode(data);
                                const bytes = new Uint8Array(binaryString.length);
                                for (let i = 0; i < binaryString.length; i++) {
                                    bytes[i] = binaryString.charCodeAt(i);
                                }
                                processedData = Array.from(bytes);
                            } 
                            // 未来可以扩展其他格式支持，如 'int', 'float' 等
                        } catch (e) {
                            console.warn('Data parse error:', e);
                        }
                    }

                    const receivedDataObj: BluetoothReceivedData = {
                        characteristicName,
                        characteristicUUID: options.characteristicUUID,
                        data: processedData,
                        timestamp: new Date().toISOString(),
                    };

                    // 更新 Redux 状态中的接收数据
                    dispatch(setReceivedData(receivedDataObj));
                    // 调用用户回调
                    callback(receivedDataObj);
                });
            } catch (err: any) {
                dispatch(
                    setError({
                        message: err.message || 'Subscribe notifications failed',
                    }),
                );
                return () => { };
            }
        },
        [dispatch],
    );

    /**
     * 连接到配置文件中指定的设备
     *
     * 自动扫描并连接到 ble_config.json 中配置的设备。
     * 支持断开连接后自动重新扫描和连接功能。
     */
    const connectToConfiguredDevice = useCallback(
        async (options?: {
            deviceName?: string;
            scanTimeout?: number;
            connectTimeout?: number;
            autoConnect?: boolean;
            enableAutoRescan?: boolean;
            maxRescanAttempts?: number;
            rescanDelayMs?: number;
        }) => {
            // 确保蓝牙适配器已启用
            const state = await bluetoothService.getAdapterState();

            // iOS 平台需要等待状态变为 PoweredOn
            if (Platform.OS === 'ios') {
                if (state !== 'PoweredOn') {
                    // 等待蓝牙状态变为 PoweredOn
                    await new Promise<void>((resolve, reject) => {
                        const subscription = (bluetoothService as any).manager.onStateChange(
                            (newState: string) => {
                                if (newState === 'PoweredOn') {
                                    subscription.remove();
                                    resolve();
                                } else if (newState === 'PoweredOff' || newState === 'Unauthorized') {
                                    subscription.remove();
                                    reject(new Error('iOS 蓝牙权限被拒绝或未启用'));
                                }
                            },
                            true,
                        );
                    });
                }
            } else {
                // Android 直接检查状态
                if (state !== 'PoweredOn') {
                    throw new Error('手机蓝牙未开启');
                }
            }

            const {
                deviceName = bleConfig.ble_device_name,
                scanTimeout = 10000,
                connectTimeout = 15000,
                autoConnect = true,
                enableAutoRescan = false,
                maxRescanAttempts = 5,
                rescanDelayMs = 3000,
            } = options || {};

            autoRescanConfigRef.current = {
                scanTimeout,
                connectTimeout,
                autoConnect,
                enableAutoRescan,
                maxRescanAttempts,
                rescanDelayMs,
                currentAttempts: 0,
            };

            /**
             * 内部方法：执行一次扫描并连接逻辑
             */
            const performScanAndConnect = async () => {
                try {
                    await bluetoothService.initialize(); // 确保有权限
                    dispatch(setError(null));

                    if (status === BluetoothStatus.Scanning) {
                        return;
                    }

                    dispatch(setStatus(BluetoothStatus.Scanning));

                    let deviceFound = false;

                    // 启动扫描
                    const scanPromise = bluetoothService.startScan(
                        async (device) => {
                            if (device.name === deviceName) {
                                deviceFound = true;
                                await stopScan();

                                try {
                                    await connectToDevice(device.id, { timeout: connectTimeout, autoConnect });

                                    if (autoRescanConfigRef.current) {
                                        autoRescanConfigRef.current.currentAttempts = 0;
                                    }
                                    if (enableAutoRescan) setupAutoRescan();
                                } catch (connectError) {
                                    console.error('❌ 扫描中发现目标设备但连接失败:', connectError);
                                    deviceFound = false;
                                }
                            }
                        },
                        { timeout: scanTimeout },
                    );

                    // 等待扫描完成（包括超时）
                    await scanPromise;

                    // 如果扫描结束但没有发现设备
                    if (!deviceFound) {
                        console.log('设备是 ', deviceName);
                        console.warn('⏰ 扫描结束，未发现目标设备');
                        await stopScan();
                        dispatch(setStatus(BluetoothStatus.Error));
                        dispatch(setError({ message: '未发现目标设备，请确认设备已开机并开启蓝牙广播' }));
                    }
                } catch (error) {
                    console.error('❌ 扫描连接异常:', error);
                    const msg = error instanceof Error ? error.message : '扫描连接设备失败';
                    dispatch(setError({ message: msg }));
                    dispatch(setStatus(BluetoothStatus.Error));
                } finally {
                    // 确保扫描被停止，防止 BLE 未释放导致系统 SIGKILL
                    try {
                        await stopScan();
                    } catch {
                        // 忽略异常
                    }
                }
            };

            /**
             * 内部方法：自动重连逻辑
             */
            const setupAutoRescan = () => {
                bluetoothService.setOnDisconnectedListener((device) => {
                    dispatch(setStatus(BluetoothStatus.Disconnected));
                    dispatch(setDeviceInfo(null));
                    dispatch(setReceivedData(null));

                    if (
                        autoRescanConfigRef.current &&
                        autoRescanConfigRef.current.currentAttempts <
                        autoRescanConfigRef.current.maxRescanAttempts
                    ) {
                        autoRescanConfigRef.current.currentAttempts++;
                        setTimeout(() => {
                            performScanAndConnect().catch((error) => {
                                console.error(
                                    `第 ${autoRescanConfigRef.current?.currentAttempts} 次重新扫描失败:`,
                                    error,
                                );
                                if (
                                    autoRescanConfigRef.current &&
                                    autoRescanConfigRef.current.currentAttempts >=
                                    autoRescanConfigRef.current.maxRescanAttempts
                                ) {
                                    dispatch(setError({ message: '自动重新扫描失败，请手动重新连接' }));
                                }
                            });
                        }, autoRescanConfigRef.current.rescanDelayMs);
                    } else {
                        dispatch(setError({ message: '自动重新扫描失败，请手动重新连接' }));
                    }
                });
            };

            /**
             * 优先尝试从缓存中连接
             */
            try {
                const lastId = await AsyncStorage.getItem('lastConnectedDeviceId');
                if (lastId) {
                    try {
                        await connectToDevice(lastId, { timeout: connectTimeout, autoConnect });
                        if (enableAutoRescan) setupAutoRescan();
                        return; // 直接返回，跳过扫描
                    } catch (err) {
                        console.warn('⚠️ 缓存设备连接失败，清理缓存并按设备名称重新扫描连接', err);
                        await AsyncStorage.removeItem('lastConnectedDeviceId');
                    }
                }

                // 无缓存或连接失败则扫描连接
                await performScanAndConnect();
            } catch (err) {
                console.error('❌ connectToConfiguredDevice 执行异常:', err);
                dispatch(setError({ message: (err as Error).message }));
                dispatch(setStatus(BluetoothStatus.Error));
            }
        },
        [dispatch, status, stopScan, connectToDevice],
    );

    /**
     * 发送命令到设备
     *
     * 向连接的蓝牙设备发送命令数据，支持有响应和无响应两种模式。
     */
    const sendCommand = useCallback(
        async (options: SendCommandOptions) => {
            const {
                data,
                serviceUUID = '00FF',
                characteristicUUID = 'FF01',
                type = 'no_response',
            } = options;

            try {
                // 检查蓝牙连接状态
                if (status !== BluetoothStatus.Connected || !deviceInfo) {
                    throw new Error('蓝牙未连接');
                }

                // 检查设备是否真的连接
                const isConnected = await bluetoothService.isDeviceConnected(deviceInfo.id);
                if (!isConnected) {
                    dispatch(setStatus(BluetoothStatus.Disconnected));
                    dispatch(setDeviceInfo(null));
                    throw new Error('设备已断开连接');
                }

                if (type === 'response') {
                    await bluetoothService.sendDataWithResponse(
                        {
                            serviceUUID,
                            characteristicUUID,
                        },
                        data,
                    );
                } else {
                    await bluetoothService.sendDataWithoutResponse(
                        {
                            serviceUUID,
                            characteristicUUID,
                        },
                        data,
                    );
                }
            } catch (error) {
                console.error('❌ 指令发送失败:', error);
                // 如果是连接问题，更新状态
                if (error instanceof Error && error.message.includes('not connected')) {
                    dispatch(setStatus(BluetoothStatus.Disconnected));
                    dispatch(setDeviceInfo(null));
                }
                const errorMessage = error instanceof Error ? error.message : '发送命令失败';
                dispatch(setError({ message: errorMessage }));
                dispatch(setStatus(BluetoothStatus.Error));
                throw error; // 重新抛出错误，让调用者知道发送失败
            }
        },
        [dispatch, status, deviceInfo],
    );

    /**
     * 清除错误状态
     */
    const clearError = useCallback(() => {
        dispatch(setError(null));
        if (status === BluetoothStatus.Error) {
            dispatch(setStatus(BluetoothStatus.Idle));
        }
    }, [dispatch, status]);

    /**
     * 清除所有蓝牙状态
     */
    const clearAll = useCallback(() => {
        dispatch(setStatus(BluetoothStatus.Idle));
        dispatch(setDeviceInfo(null));
        dispatch(setReceivedData(null));
        dispatch(setError(null));
    }, [dispatch]);

    return {
        // 状态
        status,
        deviceInfo,
        receivedData,
        error,

        // 方法
        initialize,
        startScan,
        stopScan,
        connectToDevice,
        connectToConfiguredDevice,
        disconnect,
        writeData,
        readData,
        subscribeToNotifications,
        sendCommand,
        clearError,
        clearAll,
    };
};