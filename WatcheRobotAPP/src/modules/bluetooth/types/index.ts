import type { Device } from 'react-native-ble-plx';

/**
 * 蓝牙连接状态枚举
 *
 * 定义了蓝牙设备连接过程中的所有可能状态，用于状态管理和 UI 显示。
 * 状态流转通常为：Idle -> Scanning -> Connecting -> Connected
 * 异常情况下可能转为：Error 或 Disconnected
 *
 * @category Types
 */
export enum BluetoothStatus {
    /** 空闲状态 - 初始状态，未进行任何蓝牙操作 */
    Idle = 'idle',

    /** 扫描中 - 正在搜索附近的蓝牙设备 */
    Scanning = 'scanning',

    /** 连接中 - 正在尝试连接到指定设备 */
    Connecting = 'connecting',

    /** 已连接 - 成功连接到设备，可以进行数据通信 */
    Connected = 'connected',

    /** 已断开 - 设备连接已断开，可能是主动断开或意外断开 */
    Disconnected = 'disconnected',

    /** 错误状态 - 连接过程中发生错误，需要用户处理 */
    Error = 'error',
}

/**
 * 蓝牙设备基本信息接口
 *
 * 存储已连接设备的关键信息，用于 UI 显示和状态管理。
 * 这些信息在设备连接成功后获取并缓存。
 */
export interface BluetoothDeviceInfo {
    /** 设备唯一标识符 - 用于设备识别和重连 */
    id: string;

    /** 设备名称 - 可能为空，取决于设备广播信息 */
    name?: string | null;

    /** 最大传输单元 - 影响数据传输效率，可能为空 */
    mtu?: number | null;
}

/**
 * 蓝牙错误信息接口
 *
 * 标准化的错误信息结构，提供详细的错误描述和可选的错误代码。
 * 用于错误处理和用户提示。
 */
export interface BluetoothError {
    /** 错误代码 - 可选的系统级错误代码，用于程序化处理 */
    code?: string;

    /** 错误消息 - 人类可读的错误描述，用于用户提示 */
    message: string;
}

/**
 * 设备发现回调函数类型
 *
 * 在设备扫描过程中，每发现一个设备时调用此回调函数。
 *
 * @param device - 发现的蓝牙设备实例
 */
export type DeviceDiscoveredCallback = (device: Device) => void;

/**
 * 设备扫描选项接口
 *
 * 配置设备扫描行为的参数，提供灵活的扫描控制。
 */
export interface ScanOptions {
    /** 扫描超时时间（毫秒） - 可选，未设置时将持续扫描直到手动停止 */
    timeout?: number;

    /** 设备过滤函数 - 可选，用于筛选符合条件的设备 */
    filter?: (device: Device) => boolean;
}

/**
 * 设备连接选项接口
 *
 * 配置设备连接行为的参数，支持超时控制、自动重连和 MTU 设置。
 */
export interface ConnectOptions {
    /** 连接超时时间（毫秒） - 可选，默认通常为 10 秒 */
    timeout?: number;

    /** 自动重连标志 - 可选，设备断开后是否自动尝试重连 */
    autoConnect?: boolean;

    /** 请求的 MTU 大小 - 可选，仅在 Android 平台有效，影响数据传输效率 */
    requestMTU?: number;
}

/**
 * 特征值通知选项接口
 *
 * 指定要监听或操作的 BLE 特征值，通过服务 UUID 和特征值 UUID 定位。
 * 用于数据读写和通知订阅。
 */
export interface NotificationOptions {
    /** 服务 UUID - 目标特征值所属的服务标识符 */
    serviceUUID: string;

    /** 特征值 UUID - 目标特征值的唯一标识符 */
    characteristicUUID: string;
}

/**
 * 通知监听器函数类型
 *
 * 当订阅的特征值发生变化时，系统会调用此函数传递新的数据。
 * 支持传统的Base64编码字符串格式和新的结构化数据格式。
 *
 * @param value - Base64 编码的特征值数据或结构化的蓝牙接收数据对象
 */
export type NotificationListener = (value: string | BluetoothReceivedData) => void;

/**
 * 断开连接监听器函数类型
 *
 * 当设备意外断开连接时，系统会调用此函数通知应用程序。
 * 可用于实现自动重连、状态更新或用户提示。
 *
 * @param device - 断开连接的设备实例
 */
export type DisconnectListener = (device: Device) => void;

/**
 * 发送命令选项接口
 *
 * 配置发送命令到蓝牙设备的参数，包括数据、服务 UUID、特征值 UUID 和命令类型。
 */
export interface SendCommandOptions {
    data: Uint8Array | string;
    serviceUUID?: string;
    characteristicUUID?: string;
    type?: 'response' | 'no_response';
}

/**
 * 蓝牙接收数据接口
 *
 * 定义了从蓝牙设备接收到的数据结构，包含特征值信息和实际数据。
 */
export interface BluetoothReceivedData {
    /** 特征值名称 - 来源特征值的配置名称 */
    characteristicName: string;

    /** 特征值 UUID - 来源特征值的唯一标识符 */
    characteristicUUID: string;

    /** 实际数据 - 根据value_format解析后的数据，可能是字符串、数组或对象 */
    data: any;

    /** 时间戳 - 数据接收时间的ISO字符串 */
    timestamp: string;
}

/**
 * 蓝牙状态管理接口
 *
 * 定义了蓝牙模块在 Redux 状态树中的状态结构，用于存储和管理蓝牙连接状态、设备信息、错误和接收数据。
 * @hidden
 */
export interface BluetoothState {
    status: BluetoothStatus;
    deviceInfo: BluetoothDeviceInfo | null;
    error: BluetoothError | null;
    receivedData: BluetoothReceivedData | string | null;
}

/**
 * useBluetooth Hook 的返回值类型定义
 *
 * 包含了所有蓝牙功能相关的状态和操作方法
 * 这是使用蓝牙模块的主要接口
 */
export interface UseBluetoothReturn {
    /** 当前蓝牙连接状态 */
    status: BluetoothStatus;

    /** 当前连接的设备信息，未连接时为 null */
    deviceInfo: BluetoothDeviceInfo | null;

    /** 最近接收到的数据，未接收到数据时为 null */
    receivedData: BluetoothReceivedData | string | null;

    /** 当前的错误信息，无错误时为 null */
    error: BluetoothError | null;

    /**
     * 初始化蓝牙服务
     * 检查权限并初始化蓝牙适配器
     */
    initialize: () => Promise<void>;

    /**
     * 开始扫描设备
     * @param onDeviceFound 发现设备时的回调函数
     * @param options 扫描选项
     */
    startScan: (onDeviceFound: DeviceDiscoveredCallback, options?: ScanOptions) => Promise<void>;

    /**
     * 停止扫描
     */
    stopScan: () => Promise<void>;

    /**
     * 连接到指定设备
     * @param deviceId 设备ID
     * @param options 连接选项
     */
    connectToDevice: (deviceId: string, options?: ConnectOptions) => Promise<void>;

    /**
     * 连接到配置文件中指定的设备
     * 自动扫描并连接到 ble_config.json 中配置的设备
     */
    connectToConfiguredDevice: (options?: {
        deviceName?: string;
        scanTimeout?: number;
        connectTimeout?: number;
        autoConnect?: boolean;
        enableAutoRescan?: boolean;
        maxRescanAttempts?: number;
        rescanDelayMs?: number;
    }) => Promise<void>;

    /**
     * 断开当前连接
     */
    disconnect: () => Promise<void>;

    /**
     * 向设备写入数据 (底层方法)
     * @param serviceUUID 服务UUID
     * @param characteristicUUID 特征值UUID
     * @param data 要发送的数据
     * @param withResponse 是否需要响应
     */
    writeData: (
        serviceUUID: string,
        characteristicUUID: string,
        data: string | Uint8Array,
        withResponse?: boolean,
    ) => Promise<void>;

    /**
     * 读取特征值数据
     * @param serviceUUID 服务UUID
     * @param characteristicUUID 特征值UUID
     * @returns 读取到的数据 (Base64 字符串)
     */
    readData: (serviceUUID: string, characteristicUUID: string) => Promise<string>;

    /**
     * 订阅特征值通知
     * @param options 通知选项
     * @param callback 收到通知时的回调
     * @returns 取消订阅的函数
     */
    subscribeToNotifications: (
        options: NotificationOptions,
        callback: NotificationListener,
    ) => () => void;

    /**
     * 发送命令到设备 (高级方法)
     * 封装了常用的发送逻辑
     * @param options 发送命令选项
     */
    sendCommand: (options: SendCommandOptions) => Promise<void>;

    /**
     * 清除错误状态
     */
    clearError: () => void;

    /**
     * 清除所有状态
     * 重置状态、设备信息、接收数据和错误信息
     */
    clearAll: () => void;
}