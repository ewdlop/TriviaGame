import { configureStore } from '@reduxjs/toolkit';
import triviaReducer from './triviaSlice';
import { triviaApi } from './triviaApi';

export const store = configureStore({
  reducer: {
    trivia: triviaReducer,
    [triviaApi.reducerPath]: triviaApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(triviaApi.middleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch; 