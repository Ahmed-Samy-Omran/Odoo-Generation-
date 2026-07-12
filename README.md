# 🚀 OdooGen: AI-Powered Odoo Module Architect

OdooGen is a cutting-edge, full-stack platform designed to automate the end-to-end development of Odoo modules. By leveraging advanced AI orchestration, RAG (Retrieval-Augmented Generation), and an interactive visual ERD editor, OdooGen transforms natural language requirements into production-ready Odoo modules in seconds.

---

## 🌟 Key Features

### 🧠 AI-Driven Module Generation

- **Natural Language to Code**: Convert complex business requirements into structured Odoo modules.

- **Multi-Provider AI Gateway**: Integrated with NaraRouter, Google Gemini, and OpenRouter with intelligent fallback logic for 99.9% uptime.

- **RAG Integration**: (In Development) Uses a local vector database (`sentence-transformers`) to index official Odoo source code, ensuring the AI follows Odoo 17/18 best practices and reduces hallucinations.

### 🎨 Visual ERD Editor (Low-Code)

- **Interactive Schema Design**: Built with `@xyflow/react`, allowing users to drag-and-drop models and draw relationships (`Many2one`, `One2many`).

- **Two-Way Synchronization**: Real-time sync between the visual diagram and the underlying JSON schema.

- **Contextual Actions**: Smart floating menus for adding fields, relations, and instant deletion with a unified "Smart Delete" logic.

### 🛠️ Developer-First Features

- **GitHub Automation**: Direct integration with GitHub API to create repositories and push generated code automatically.

- **Async Job Processing**: FastAPI-based background tasks with real-time progress tracking via Server-Sent Events (SSE).

- **Comprehensive Module Support**: Generates Python models, XML views (Form, Tree, Kanban, Search), security groups (`ir.model.access.csv`), and QWeb reports.

---

## 🏗️ Tech Stack

### Backend

- **Framework**: FastAPI (Asynchronous Python)

- **AI Orchestration**: LangChain & Custom AI Service

- **Templates**: Jinja2 for precise Odoo code generation

- **Task Management**: Async Job Manager with unique UUID tracking

### Frontend

- **Framework**: React 18 + TypeScript + Vite

- **Diagramming**: React Flow (@xyflow/react)

- **Styling**: Tailwind CSS (Modern Dark Theme)

- **State Management**: Context API with LocalStorage persistence

---

## 🗺️ Roadmap

- [ ] **Advanced RAG**: Full indexing of Odoo 18 community and enterprise addons.

- [ ] **Auto-Testing**: Integrated Docker environment to validate modules before deployment.

- [ ] **Visual OWL Components**: Drag-and-drop builder for Odoo 17+ OWL views.

- [ ] **Undo/Redo History**: Advanced state management for the ERD editor.

---

**Developed with ❤️ by **[**Ahmed Samy**](https://github.com/Ahmed-Samy-Omran)* Transforming how we build Odoo, one prompt at a time.*
