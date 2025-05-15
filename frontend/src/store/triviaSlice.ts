import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

interface Question {
  question: string;
  options: string[];
  correct_answer: string;
  explanation: string;
}

interface TriviaState {
  questions: Question[];
  currentQuestionIndex: number;
  score: number;
  loading: boolean;
  error: string | null;
}

const initialState: TriviaState = {
  questions: [],
  currentQuestionIndex: 0,
  score: 0,
  loading: false,
  error: null,
};

// 验证问题数据
const validateQuestions = (questions: any[]): Question[] => {
  if (!Array.isArray(questions)) {
    throw new Error('问题数据格式错误：不是数组');
  }

  return questions.map((q, index) => {
    if (!q || typeof q !== 'object') {
      throw new Error(`问题 ${index + 1} 格式错误：不是对象`);
    }

    if (!q.question || typeof q.question !== 'string') {
      throw new Error(`问题 ${index + 1} 缺少问题文本`);
    }

    if (!Array.isArray(q.options) || q.options.length !== 4) {
      throw new Error(`问题 ${index + 1} 选项格式错误：需要4个选项`);
    }

    if (!q.correct_answer || typeof q.correct_answer !== 'string') {
      throw new Error(`问题 ${index + 1} 缺少正确答案`);
    }

    if (!q.explanation || typeof q.explanation !== 'string') {
      throw new Error(`问题 ${index + 1} 缺少解释`);
    }

    return {
      question: q.question,
      options: q.options,
      correct_answer: q.correct_answer,
      explanation: q.explanation,
    };
  });
};

export const uploadFile = createAsyncThunk(
  'trivia/uploadFile',
  async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('http://localhost:5001/api/upload', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '上传文件失败');
    }

    const data = await response.json();
    if (!data.questions || !Array.isArray(data.questions)) {
      throw new Error('服务器返回的数据格式错误');
    }
    return validateQuestions(data.questions);
  }
);

export const fetchQuestions = createAsyncThunk(
  'trivia/fetchQuestions',
  async ({ documentType, content }: { documentType: string; content: string }) => {
    const response = await fetch('http://localhost:5001/api/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ document_type: documentType, content }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || '获取问题失败');
    }

    const data = await response.json();
    if (!data.questions || !Array.isArray(data.questions)) {
      throw new Error('服务器返回的数据格式错误');
    }
    return validateQuestions(data.questions);
  }
);

const triviaSlice = createSlice({
  name: 'trivia',
  initialState,
  reducers: {
    submitAnswer: (state, action: PayloadAction<string>) => {
      const currentQuestion = state.questions[state.currentQuestionIndex];
      if (currentQuestion && action.payload === currentQuestion.correct_answer) {
        state.score += 1;
      }
    },
    nextQuestion: (state) => {
      if (state.currentQuestionIndex < state.questions.length - 1) {
        state.currentQuestionIndex += 1;
      }
    },
    resetGame: (state) => {
      state.questions = [];
      state.currentQuestionIndex = 0;
      state.score = 0;
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchQuestions.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchQuestions.fulfilled, (state, action) => {
        state.loading = false;
        state.questions = action.payload.map(q => ({
          ...q,
          correct_answer: q.correct_answer.trim()
        }));
        state.currentQuestionIndex = 0;
        state.score = 0;
      })
      .addCase(fetchQuestions.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '获取问题失败';
      })
      .addCase(uploadFile.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(uploadFile.fulfilled, (state, action) => {
        state.loading = false;
        state.questions = action.payload.map(q => ({
          ...q,
          correct_answer: q.correct_answer.trim()
        }));
        state.currentQuestionIndex = 0;
        state.score = 0;
      })
      .addCase(uploadFile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || '上传文件失败';
      });
  },
});

export const { submitAnswer, nextQuestion, resetGame } = triviaSlice.actions;
export default triviaSlice.reducer; 