import api from './api';

export const classifyQuery = async (query) => {
  return api.post('/query/classify', { query });
};

export const processQuery = async (category, query) => {
  return api.post('/query/process', { category, query });
};

export const submitAnswers = async (processId, answers) => {
  return api.post('/query/submit-answers', { processId, answers });
};

export const getConversationalResponse = async (data) => {
  return api.post('/query/conversation', data);
};

export const sendEmail = async (to, subject, content) => {
  return api.post('/email/send', { to, subject, content });
};