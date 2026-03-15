/**
 * @hidden
 */
import { createSlice, PayloadAction } from '@reduxjs/toolkit';
import {
  BluetoothStatus,
  BluetoothDeviceInfo,
  BluetoothError,
  BluetoothState,
  BluetoothReceivedData,
} from '../types';

const initialState: BluetoothState = {
  status: BluetoothStatus.Idle,
  deviceInfo: null,
  error: null,
  receivedData: null,
};

const bluetoothSlice = createSlice({
  name: 'bluetooth',
  initialState,
  reducers: {
    setStatus: (state, action: PayloadAction<BluetoothStatus>) => {
      state.status = action.payload;
    },
    setDeviceInfo: (state, action: PayloadAction<BluetoothDeviceInfo | null>) => {
      state.deviceInfo = action.payload;
    },
    setError: (state, action: PayloadAction<BluetoothError | null>) => {
      state.error = action.payload;
    },
    setReceivedData: (state, action: PayloadAction<BluetoothReceivedData | string | null>) => {
      state.receivedData = action.payload;
    },
    clearAll: () => initialState,
  },
});

/** @hidden */
export const { setStatus, setDeviceInfo, setError, setReceivedData, clearAll } =
  bluetoothSlice.actions;

// Selector to get bluetooth state, decoupling from RootState
/** @hidden */
export const selectBluetoothState = (state: { bluetooth: BluetoothState }) => state.bluetooth;

export default bluetoothSlice.reducer;
