import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import { ErrorBoundary } from "@/components/shell/ErrorBoundary";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    {/* Không có boundary ở gốc thì một lỗi render bất kỳ để lại đúng màn hình
        trắng câm — thứ vừa mất công đi tìm. Fallback dùng style thuần vì lỗi
        có thể đến từ chính lớp theme/CSS. */}
    <ErrorBoundary
      fallback={(error) => (
        <div style={{ padding: "2rem", fontFamily: "system-ui, sans-serif" }}>
          <h1 style={{ fontSize: "1.125rem", fontWeight: 600 }}>
            Dipro AI Boost gặp lỗi khi khởi động
          </h1>
          <p style={{ marginTop: "0.5rem" }}>
            Tải lại cửa sổ để thử lại. Nội dung lỗi:
          </p>
          <pre
            style={{
              marginTop: "0.75rem",
              whiteSpace: "pre-wrap",
              fontSize: "0.75rem",
              opacity: 0.8,
            }}
          >
            {error.message}
          </pre>
        </div>
      )}
    >
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);
