# Tech Stack

| Layer | Technology | Version | Purpose | License |
| --- | --- | --- | --- | --- |
| Operating System | Ubuntu | 24.04 | Core software for managing computer hardware and software resources. | GPL |
||||||
| Database | PostgreSQL | 16 | Relational database system for data storage and retrieval. | PostgreSQL License |
| Database | pgAdmin4 | 9.1 | Web-based administration tool for PostgreSQL. | PostgreSQL License |
||||||
| Server | Python | 3.13 | Primary programming language for backend development. | PSF License |
| Server | UV | 0.6.3 | Python package installer and resolver. | MIT |
| Server | FastAPI | 0.115.11 | High-performance web framework for building APIs. | MIT |
| Server | Resend | 2.8.0 | Modern email API for transactional emails. | MIT |
| Server | SQLAlchemy | 2.0.38 | SQL toolkit and Object Relational Mapper (ORM). | MIT |
| Server | asyncpg | 0.30.0 | Asynchronous PostgreSQL database client library. | Apache 2.0 |
| Server | psycopg2-binary | 2.9.10 | PostgreSQL adapter for Python (binary distribution). | LGPL |
| Server | Alembic | 1.15.1 | Database schema migration tool for SQLAlchemy. | MIT |
| Server | Pydantic | 2.10.6 | Data validation and settings management using Python type hints. | MIT |
| Server | pydantic-settings | 2.8.1 | Pydantic extension for managing application settings. | MIT |
| Server | Authlib | 1.5.1 | Library for OAuth, OpenID Connect, and JWT. | BSD | 
| Server | psutil | 7.0.0 | Cross-platform library for retrieving system and process information. | BSD | 
| Server | structlog | 25.2.0 | Structured logging for Python applications. | Apache 2.0 / MIT | 
| Server | bcrypt | 4.3.0 | Library for hashing passwords securely. | BSD | 
| Server | email-validator | 2.2.0 | Library for validating email addresses. | BSD | 
| Server | slowapi | 0.1.9 | Rate limiting extension for Starlette and FastAPI. | MIT |
| Server | uvicorn | 0.34.0 | ASGI server for running Python web applications. | BSD |
| Server | Svix | 1.81.0 | Webhook delivery and signature verification (used by Resend) | MIT |
| Server | opentelemetry-api | 1.32.0 | API for OpenTelemetry, enabling application observability. | Apache 2.0 |
| Server | opentelemetry-sdk | 1.32.0 | SDK for OpenTelemetry, providing instrumentation capabilities. | Apache 2.0 |
| Server | Pytest | 8.3.5 | Testing framework for Python. | MIT |
| Server | Pytest Asyncio | 0.25.3 | Pytest plugin for testing asyncio code. | Apache 2.0 |
| Server | Pytest Mock | 3.14.0 | Pytest plugin for mocking objects during tests. | MIT |
| Server | Pytest X-Dist | 3.6.1 | Pytest plugin for distributing tests across multiple CPUs. | MIT |
| Server | Pytest-cov | 6.0.0 | Pytest plugin for measuring code coverage. | MIT |
| Server | Coverage | 7.9.1 | Tool for measuring code coverage of Python programs. | Apache 2.0 |
| Server | HTTPX | 0.28.1 | Asynchronous HTTP client for Resend inbound fetches and API testing. | BSD |
| Server | AIOSQLite | 0.21.0 | Asynchronous SQLite driver, for in-memory testing. | MIT |
| Server | Ruff | 0.9.10 | Extremely fast Python linter and code formatter. | MIT |
| Server | MyPy | 1.15.0 | Static type checker for Python. | MIT |
| Server | typing-extensions | 4.12.2 | Backported and experimental type hints for Python. | PSF License |
| Server | types-psutil | 7.0.0.20250218 | Type hints for the psutil library. | MIT |
| Server | types-pyyaml | 6.0.12.20241230 | Type hints for the PyYAML library. | MIT |
| Server | types-python-jose | 3.4.0.20250224 | Type hints for the python-jose library. | MIT |
||||||
| Client | TypeScript | 5.7.2 | Superset of JavaScript adding static typing for frontend development. | Apache 2.0 |
| Client | NPM | 10.9.2 | Package manager for Node.js and JavaScript libraries. | Artistic License 2.0 |
| Client | Node | 22.14.0 | JavaScript runtime environment for frontend build tools and scripts. | MIT |
| Client | @hookform/resolvers | 4.1.3 | Resolvers for React Hook Form to integrate with validation libraries (e.g., Zod). | MIT |
| Client | @radix-ui/react-accordion | 1.2.11 | Unstyled, accessible accordion component for React (Radix UI). | MIT |
| Client | @radix-ui/react-alert-dialog | 1.1.15 | Unstyled, accessible alert dialog component for React (Radix UI). | MIT |
| Client | @radix-ui/react-checkbox | 1.3.3 | Unstyled, accessible checkbox component for React (Radix UI). | MIT |
| Client | @radix-ui/react-dialog | 1.1.6 | Unstyled, accessible dialog component for React (Radix UI). | MIT |
| Client | @radix-ui/react-label | 2.1.2 | Unstyled, accessible label component for React (Radix UI). | MIT |
| Client | @radix-ui/react-popover | 1.1.6 | Unstyled, accessible popover component for React (Radix UI). | MIT |
| Client | @radix-ui/react-progress | 1.1.2 | Unstyled, accessible progress bar component for React (Radix UI). | MIT |
| Client | @radix-ui/react-select | 2.1.6 | Unstyled, accessible select component for React (Radix UI). | MIT |
| Client | @radix-ui/react-slot | 1.2.3 | Utility component for composing React components (Radix UI). | MIT |
| Client | @radix-ui/react-switch | 1.2.6 | Unstyled, accessible switch component for React (Radix UI). | MIT |
| Client | @tanstack/react-query | 5.69.0 | Data-fetching and state management library for React. | MIT |
| Client | axios | 1.8.4 | Promise-based HTTP client for browsers and Node.js. | MIT |
| Client | cmdk | 1.1.1 | Fast, composable command palette for React. | MIT |
| Client | countries-list | 3.1.1 | List of countries, languages, and continents. | MIT |
| Client | idb | 8.0.2 | Lightweight wrapper around IndexedDB with a Promise-based API. | ISC |
| Client | lucide-react | 0.483.0 | Simply beautiful open-source icons for React. | ISC |
| Client | next-themes | 0.4.6 | Theme management for React applications (originally for Next.js). | MIT |
| Client | react | 19.0.0 | JavaScript library for building user interfaces. | MIT |
| Client | react-dom | 19.0.0 | Entry point to the DOM and server renderers for React. | MIT |
| Client | react-hook-form | 7.54.2 | Performant, flexible, and extensible forms library for React. | MIT |
| Client | react-router-dom | 7.4.0 | Client-side routing library for React applications. | MIT |
| Client | react-window | 1.8.11 | React components for efficiently rendering large lists and tabular data. | MIT |
| Client | sonner | 2.0.2 | Opinionated toast component for React. | MIT |
| Client | workbox-expiration | 7.3.0 | Workbox module for managing cache expiration. | MIT |
| Client | workbox-precaching | 7.3.0 | Workbox module for precaching assets. | MIT |
| Client | workbox-routing | 7.3.0 | Workbox module for request routing. | MIT |
| Client | workbox-strategies | 7.3.0 | Workbox module for common caching strategies. | MIT |
| Client | workbox-window | 7.3.0 | Workbox module for service worker registration and communication. | MIT |
| Client | zod | 3.24.2 | TypeScript-first schema declaration and validation library. | MIT |
| Client | @biomejs/biome | 1.9.4 | Fast formatter and linter for web projects. | MIT OR Apache-2.0 |
| Client | @tailwindcss/vite | 4.0.15 | Tailwind CSS integration for Vite projects. | MIT |
| Client | @testing-library/jest-dom | 6.6.3 | Custom Jest matchers for DOM testing. | MIT |
| Client | @testing-library/react | 16.3.0 | Utilities for testing React components. | MIT |
| Client | @testing-library/user-event | 14.6.1 | Utilities for simulating user events in tests. | MIT |
| Client | @types/node | 22.13.11 | TypeScript type definitions for Node.js. | MIT |
| Client | @types/react-dom | 19.0.0 | TypeScript type definitions for React DOM. | MIT |
| Client | @types/react-window | 1.8.8 | TypeScript type definitions for react-window. | MIT |
| Client | @vitejs/plugin-legacy | 6.1.0 | Vite plugin for legacy browser support. | MIT |
| Client | @vitejs/plugin-react-swc | 3.8.0 | Vite plugin for React using SWC for fast compilation. | MIT |
| Client | class-variance-authority | 0.7.1 | Utility for creating type-safe variant classes. | MIT |
| Client | clsx | 2.1.1 | Tiny utility for constructing `className` strings conditionally. | MIT |
| Client | globals | 15.15.0 | Global identifiers for JavaScript environments (used in linting). | MIT |
| Client | jsdom | 26.0.0 | JavaScript implementation of web standards for Node.js, for testing. | MIT |
| Client | msw | 2.7.3 | Mock Service Worker for API mocking in development and testing. | MIT |
| Client | tailwind-merge | 3.0.2 | Utility for merging Tailwind CSS classes without style conflicts. | MIT |
| Client | tailwindcss | 4.0.15 | Utility-first CSS framework for rapid UI development. | MIT |
| Client | tw-animate-css | 1.2.4 | Tailwind CSS plugin for Animate.css animations. | MIT |
| Client | typescript-eslint | 8.24.1 | ESLint tooling for TypeScript. | MIT |
| Client | vite | 6.3.2 | Next-generation frontend tooling for fast development and optimized builds. | MIT |
| Client | vite-imagetools | 7.0.5 | Vite plugin for transforming and optimizing images. | MIT |
| Client | vite-plugin-compression | 0.3.1 | Vite plugin for compressing assets (e.g., gzip, brotli). | MIT |
| Client | vite-plugin-pwa | 0.21.2 | Vite plugin for Progressive Web App generation. | MIT |
| Client | vitest | 3.1.1 | Blazing fast unit test framework powered by Vite. | MIT |
| Client | @vitest/coverage-v8 | 3.1.1 | Coverage provider for Vitest using V8's built-in code coverage. | MIT |
| Client | @vitest/ui | 3.2.4 | UI for Vitest test runner with interactive test exploration. | MIT |
||||||
| Deployment | Docker |  | Platform for developing, shipping, and running applications in containers. | Apache 2.0 |
| Deployment | Render |  | Cloud platform for hosting web applications, databases, and static sites. | Proprietary |
| Deployment | GitHub |  | Platform for version control and collaboration using Git. | Proprietary |
| Deployment | GitHub Actions |  | Automation platform for CI/CD workflows within GitHub. | Proprietary |