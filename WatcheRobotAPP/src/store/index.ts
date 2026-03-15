import { configureStore } from '@reduxjs/toolkit';
import bluetoothReducer from '../modules/bluetooth/store';

export const store = configureStore({
  reducer: {
    bluetooth: bluetoothReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
