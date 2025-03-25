import axios from "axios";

export interface IApiError {
	detail: string;
	status_code?: number;
}

const api = axios.create({
	baseURL: `${import.meta.env.VITE_API_URL}`,
	headers: {
		"Content-Type": "application/json",
		Accept: "application/json",
	},
	withCredentials: true,
});

api.interceptors.request.use(
	(config) => {
		const token = localStorage.getItem("token");
		if (token) config.headers.Authorization = `Bearer ${token}`;
		return config;
	},
	(error) => {
		return Promise.reject(error);
	},
);

export default api;
