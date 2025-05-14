import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import {
  Box,
  Container,
  Typography,
  Button,
  Paper,
  CircularProgress,
  Alert,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from '@mui/material';
import { AppDispatch, RootState } from '../store/store';
import { fetchQuestions, submitAnswer } from '../store/triviaSlice';

const TriviaGame: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { questions, currentQuestionIndex, score, loading, error } = useSelector(
    (state: RootState) => state.trivia
  );
  const [selectedAnswer, setSelectedAnswer] = useState<string>('');
  const [showResult, setShowResult] = useState(false);
  const [documentType, setDocumentType] = useState<string>('pdf');
  const [documentContent, setDocumentContent] = useState<string>('');
  const [isDocumentLoaded, setIsDocumentLoaded] = useState(false);

  const handleDocumentTypeChange = (event: SelectChangeEvent) => {
    if (!isDocumentLoaded) {
      setDocumentType(event.target.value);
    }
  };

  const handleDocumentContentChange = (event: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (!isDocumentLoaded) {
      setDocumentContent(event.target.value);
    }
  };

  const handleStartGame = () => {
    if (!isDocumentLoaded && documentContent) {
      dispatch(fetchQuestions({ documentType, documentContent }));
      setIsDocumentLoaded(true);
    }
  };

  const handleAnswerSubmit = () => {
    if (selectedAnswer) {
      dispatch(submitAnswer(selectedAnswer));
      setSelectedAnswer('');
      setShowResult(true);
    }
  };

  const handleNextQuestion = () => {
    setShowResult(false);
  };

  const handleResetGame = () => {
    setIsDocumentLoaded(false);
    setDocumentContent('');
    setSelectedAnswer('');
    setShowResult(false);
  };

  const currentQuestion = questions[currentQuestionIndex];

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Alert severity="error">{error}</Alert>
        <Button
          variant="contained"
          color="primary"
          onClick={handleResetGame}
          sx={{ mt: 2 }}
        >
          重新开始
        </Button>
      </Container>
    );
  }

  if (questions.length === 0) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography variant="h4" gutterBottom>
            欢迎来到问答游戏
          </Typography>
          <Typography variant="body1" paragraph>
            请选择文档类型并输入内容，然后开始游戏。
          </Typography>
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel>文档类型</InputLabel>
            <Select
              value={documentType}
              label="文档类型"
              onChange={handleDocumentTypeChange}
              disabled={isDocumentLoaded}
            >
              <MenuItem value="pdf">PDF</MenuItem>
              <MenuItem value="markdown">Markdown</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="文档内容"
            value={documentContent}
            onChange={handleDocumentContentChange}
            disabled={isDocumentLoaded}
            sx={{ mb: 2 }}
          />
          <Button
            variant="contained"
            color="primary"
            onClick={handleStartGame}
            disabled={!documentContent || isDocumentLoaded}
          >
            开始游戏
          </Button>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" gutterBottom>
          问答游戏
        </Typography>
        <Typography variant="h6" gutterBottom>
          得分: {score}
        </Typography>
        <Typography variant="h6" gutterBottom>
          问题 {currentQuestionIndex + 1} / {questions.length}
        </Typography>
        <Typography variant="body1" paragraph>
          {currentQuestion.question}
        </Typography>
        {currentQuestion.options.map((option, index) => (
          <Button
            key={index}
            variant={selectedAnswer === option ? 'contained' : 'outlined'}
            color={selectedAnswer === option ? 'primary' : 'inherit'}
            onClick={() => setSelectedAnswer(option)}
            fullWidth
            sx={{ mb: 1 }}
            disabled={showResult}
          >
            {option}
          </Button>
        ))}
        {showResult ? (
          <Box sx={{ mt: 2 }}>
            <Alert
              severity={currentQuestion.correct_answer === selectedAnswer ? 'success' : 'error'}
            >
              {currentQuestion.correct_answer === selectedAnswer
                ? '回答正确！'
                : `回答错误。正确答案是: ${currentQuestion.correct_answer}`}
            </Alert>
            <Button
              variant="contained"
              color="primary"
              onClick={handleNextQuestion}
              sx={{ mt: 2 }}
            >
              {currentQuestionIndex < questions.length - 1 ? '下一题' : '结束游戏'}
            </Button>
            {currentQuestionIndex === questions.length - 1 && (
              <Button
                variant="outlined"
                color="primary"
                onClick={handleResetGame}
                sx={{ mt: 2, ml: 2 }}
              >
                重新开始
              </Button>
            )}
          </Box>
        ) : (
          <Button
            variant="contained"
            color="primary"
            onClick={handleAnswerSubmit}
            disabled={!selectedAnswer}
            sx={{ mt: 2 }}
          >
            提交答案
          </Button>
        )}
      </Paper>
    </Container>
  );
};

export default TriviaGame; 