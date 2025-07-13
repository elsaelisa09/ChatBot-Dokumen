const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface QuestionRequest {
  question: string;
}

export interface QuestionResponse {
  answer: string;
  status: string;
}

export interface HealthResponse {
  status: string;
  message: string;
}

export interface UploadResponse {
  message: string;
  file_id: string;
  filename: string;
  file_path: string;
}

export interface FileInfo {
  filename: string;
  size: number;
  upload_time: number;
}

export interface TaskResponse {
  task_id: string;
  message: string;
  status: string;
}

export interface TaskStatus {
  id: string;
  status: string;
  progress: number;
  result?: any;
  error?: string;
  created_at: string;
  updated_at: string;
}

class DocumentAIAPI {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  // Health check
  async healthCheck(): Promise<HealthResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Health check failed:", error);
      throw error;
    }
  }

  // Upload file
  async uploadFile(file: File): Promise<UploadResponse> {
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${this.baseUrl}/upload`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      return await response.json();
    } catch (error) {
      console.error("File upload failed:", error);
      throw error;
    }
  }

  // Upload file in background
  async uploadFileBackground(file: File): Promise<TaskResponse> {
    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${this.baseUrl}/upload/background`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      return await response.json();
    } catch (error) {
      console.error("Background file upload failed:", error);
      throw error;
    }
  }

  // Ask question
  async askQuestion(question: string): Promise<QuestionResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ question }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      return await response.json();
    } catch (error) {
      console.error("Question failed:", error);
      throw error;
    }
  }

  // Get uploaded files
  async getUploadedFiles(): Promise<{ files: FileInfo[] }> {
    try {
      const response = await fetch(`${this.baseUrl}/files`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Failed to get uploaded files:", error);
      throw error;
    }
  }

  // Delete file
  async deleteFile(filename: string): Promise<{ message: string }> {
    try {
      const response = await fetch(
        `${this.baseUrl}/files/${encodeURIComponent(filename)}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || `HTTP error! status: ${response.status}`
        );
      }

      return await response.json();
    } catch (error) {
      console.error("Failed to delete file:", error);
      throw error;
    }
  }

  // Get task status
  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    try {
      const response = await fetch(`${this.baseUrl}/upload/tasks/${taskId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Failed to get task status:", error);
      throw error;
    }
  }

  // Get all tasks
  async getAllTasks(): Promise<{ tasks: TaskStatus[] }> {
    try {
      const response = await fetch(`${this.baseUrl}/upload/tasks`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Failed to get all tasks:", error);
      throw error;
    }
  }

  // Cleanup old tasks
  async cleanupTasks(): Promise<{ message: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/upload/cleanup`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Failed to cleanup tasks:", error);
      throw error;
    }
  }
}

// Create singleton instance
export const documentAIAPI = new DocumentAIAPI();

export default documentAIAPI;
