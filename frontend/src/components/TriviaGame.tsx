import React, { useState, useEffect, useRef } from 'react';
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
  Stack,
  Radio,
  RadioGroup,
  FormControlLabel,
  Card,
  CardContent,
} from '@mui/material';
import { AppDispatch, RootState } from '../store/store';
import { fetchQuestions, submitAnswer, uploadFile, nextQuestion, resetGame } from '../store/triviaSlice';

const TriviaGame: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { questions, currentQuestionIndex, score, loading, error } = useSelector(
    (state: RootState) => state.trivia
  );
  const [topic, setTopic] = useState('');
  const [documentType, setDocumentType] = useState<string>('pdf');
  const [documentContent, setDocumentContent] = useState<string>('');
  const [isDocumentLoaded, setIsDocumentLoaded] = useState(false);
  const [fileName, setFileName] = useState<string>('');
  const [selectedAnswer, setSelectedAnswer] = useState('');
  const [isCorrect, setIsCorrect] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDocumentTypeChange = (event: SelectChangeEvent) => {
    if (!isDocumentLoaded) {
      setDocumentType(event.target.value);
    }
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setFileName(file.name);
      dispatch(uploadFile(file));
      setIsDocumentLoaded(true);
    }
  };

  const handleStartGame = () => {
    if (!isDocumentLoaded && documentContent) {
      dispatch(fetchQuestions({ documentType, content: documentContent }));
      setIsDocumentLoaded(true);
    }
  };

  const handleAnswerSubmit = (answer: string) => {
    setSelectedAnswer(answer);
    const isAnswerCorrect = answer === currentQuestion?.correct_answer;
    setIsCorrect(isAnswerCorrect);
    setShowExplanation(true);
    dispatch(submitAnswer(answer));
  };

  const handleNextQuestion = () => {
    dispatch(nextQuestion());
    setSelectedAnswer('');
    setIsCorrect(false);
    setShowExplanation(false);
  };

  const handleResetGame = () => {
    setIsDocumentLoaded(false);
    setDocumentContent('');
    setFileName('');
    setSelectedAnswer('');
    setShowExplanation(false);
    dispatch(resetGame());
  };

  const handleGenerateDirectly = async () => {
    if (!topic.trim()) {
      alert('请输入主题');
      return;
    }
    try {
      console.log('正在发送生成问题请求...');
      const response = await fetch('http://localhost:5001/generate-directly', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic: topic.trim() }),
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '生成问题失败');
      }
      
      const data = await response.json();
      console.log('收到响应:', data);
      
      if (data.questions && Array.isArray(data.questions)) {
        dispatch({ type: 'trivia/setQuestions', payload: data.questions });
      } else {
        throw new Error('返回的问题格式不正确');
      }
    } catch (error) {
      console.error('生成问题出错:', error);
      alert(error instanceof Error ? error.message : '生成问题失败');
    }
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

  if (questions.length === 0 || !currentQuestion) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Typography variant="h4" gutterBottom>知识问答游戏</Typography>
        <Stack spacing={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>上传文档</Typography>
              <Button
                variant="contained"
                component="label"
                fullWidth
              >
                选择文件
                <input
                  type="file"
                  hidden
                  onChange={handleFileSelect}
                  accept=".pdf,.md"
                />
              </Button>
              {fileName && (
                <Typography variant="body2" sx={{ mt: 1 }}>
                  已选择文件: {fileName}
                </Typography>
              )}
            </CardContent>
          </Card>
          
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>直接生成问题</Typography>
              <TextField
                fullWidth
                label="输入主题"
                placeholder="例如：人工智能、历史、科学等"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                sx={{ mb: 2 }}
              />
              <Button
                variant="contained"
                color="primary"
                onClick={handleGenerateDirectly}
                fullWidth
              >
                生成问题
              </Button>
            </CardContent>
          </Card>
        </Stack>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h4" gutterBottom>知识问答游戏</Typography>
      <Card>
        <CardContent>
          <Stack spacing={3}>
            <Box>
              <Typography variant="subtitle1">
                问题 {currentQuestionIndex + 1} / {questions.length}
              </Typography>
              <Typography variant="h6" sx={{ mt: 1 }}>
                {currentQuestion.question}
              </Typography>
            </Box>

            <FormControl component="fieldset">
              <RadioGroup
                value={selectedAnswer}
                onChange={(e) => handleAnswerSubmit(e.target.value)}
              >
                {currentQuestion.options.map((option) => (
                  <FormControlLabel
                    key={option}
                    value={option}
                    control={<Radio />}
                    label={option}
                    disabled={showExplanation}
                  />
                ))}
              </RadioGroup>
            </FormControl>

            {showExplanation && (
              <Box>
                <Typography
                  color={isCorrect ? 'success.main' : 'error.main'}
                  sx={{ mb: 1 }}
                >
                  {isCorrect ? '回答正确！' : `回答错误。正确答案是: ${currentQuestion.correct_answer}`}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  解释：{currentQuestion.explanation}
                </Typography>
              </Box>
            )}

            <Stack direction="row" spacing={2}>
              {showExplanation && (
                <Button
                  variant="contained"
                  color="primary"
                  onClick={handleNextQuestion}
                >
                  {currentQuestionIndex < questions.length - 1 ? '下一题' : '查看得分'}
                </Button>
              )}
              <Button
                variant="outlined"
                onClick={handleResetGame}
              >
                重新开始
              </Button>
            </Stack>

            {currentQuestionIndex === questions.length - 1 && showExplanation && (
              <Box>
                <Typography variant="h5" gutterBottom>游戏结束！</Typography>
                <Typography>
                  你的得分：{score} / {questions.length}
                </Typography>
              </Box>
            )}
          </Stack>
        </CardContent>
      </Card>
    </Container>
  );
};

export default TriviaGame; 