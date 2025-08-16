# Overview

Papelaria Digital is a complete automated customer service system for a Brazilian stationery store built with Flask and OpenAI GPT-4o. The system provides intelligent customer support from product inquiries to payment processing, featuring a complete sales flow with freight calculation and PIX payment integration. The application uses a responsive chat interface that loads product data from a JSON catalog and guides customers through the entire purchase process without hardcoded keywords or mocked responses.

## Recent Changes (August 16, 2025)

✅ **Complete PIX Automation System**: Implemented fully automated PIX payment generation that triggers when all required customer data is collected (product, size, options, quantity, name, CPF, CEP).

✅ **Enhanced Data Extraction**: Comprehensive automatic extraction of product information, customer details, and address data from natural language messages using intelligent regex patterns.

✅ **Smart Product Catalog Integration**: Transformed flat JSON product data into hierarchical structure with automatic price calculation and product matching for seamless order processing.

✅ **Session Persistence & Context Awareness**: AI maintains complete conversation history through PostgreSQL database, preventing redundant questions and ensuring smooth customer experience.

✅ **End-to-End Sales Flow**: Complete automated sales pipeline from initial inquiry to final PIX payment generation, including freight calculation and order summarization.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
The frontend uses a single-page application (SPA) approach with vanilla JavaScript, Bootstrap 5, and Font Awesome for styling. The interface features a chat-based design with real-time message updates, loading indicators, and responsive layout. The chat system maintains conversation state through session management and provides visual feedback for user interactions.

## Backend Architecture
The application follows a simple Flask-based architecture with a modular design:

- **Main Application**: Flask server handling HTTP requests and responses
- **Chat Processing**: OpenAI GPT-4o integration for natural language processing
- **Product Management**: JSON-based product catalog loading and formatting
- **Session Management**: Flask sessions for maintaining conversation context
- **Logging**: Built-in Python logging for debugging and monitoring

## Data Storage
The system uses a file-based approach for product data storage with JSON format. Product information includes details like sizes, pricing options, and specifications. Session data is managed through Flask's built-in session handling, storing conversation history temporarily.

## Integration Points
The architecture includes integration capabilities for:

- **OpenAI API**: GPT-4o model for intelligent chat responses
- **Melhor Envio API**: Brazilian shipping service for freight calculations (partially implemented)
- **Product Catalog**: JSON file system for maintaining stationery inventory

## Design Patterns
The application follows a request-response pattern with asynchronous frontend interactions. The backend implements a service-oriented approach where product loading and AI processing are separated into distinct functions for maintainability and testing.

# External Dependencies

## AI Services
- **OpenAI API**: Primary dependency for chat functionality using GPT-4o model
- **API Key Management**: Environment variable configuration for secure access

## Frontend Libraries
- **Bootstrap 5.1.3**: UI framework for responsive design and components
- **Font Awesome 6.0.0**: Icon library for visual elements
- **Vanilla JavaScript**: No additional frontend frameworks

## Backend Dependencies
- **Flask**: Web framework for Python
- **OpenAI Python SDK**: Official client library for OpenAI API integration
- **Requests**: HTTP library for external API calls

## Shipping Integration
- **Melhor Envio API**: Brazilian shipping service integration (sandbox environment)
- **CEP-based calculations**: Postal code system for freight estimation

## Development Tools
- **Python Logging**: Built-in debugging and monitoring
- **Environment Variables**: Configuration management for API keys and secrets
- **JSON**: Data format for product catalog management