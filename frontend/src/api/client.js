import axios from "axios";

const api = axios.create({
  baseURL: "/api"
});

export const chat = async (userId, message) => {
  const res = await api.post("/chat", { user_id: userId, message });
  return res.data;
};
