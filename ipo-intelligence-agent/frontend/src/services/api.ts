import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

const OPTIONAL_RESOURCES_PATTERNS = [
  /\/analysis\/results\//,
  /\/analysis\/history\//,
  /\/analysis\/report\//,
  /\/ipos\/financials\//,
  /\/ipos\/companies\//,
  /\/memory\//,
];

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const url = String(error.config?.url || "");
    const isOptionalNotFound =
      status === 404 &&
      OPTIONAL_RESOURCES_PATTERNS.some((re) => re.test(url));
    const isNetworkError = !error.response;
    if (!isOptionalNotFound && (status >= 500 || isNetworkError)) {
      const message =
        error.response?.data?.detail ||
        error.message ||
        "An unexpected error occurred";
      console.error(`API Error [${url}]:`, message);
    }
    return Promise.reject(error);
  }
);

export default api;
