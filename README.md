
# Papelaria Digital - Sistema de Atendimento Automatizado

Sistema completo de atendimento automatizado para papelaria brasileira usando Flask e OpenAI GPT-4o.

## 🚀 Funcionalidades

- **Chat Inteligente**: Atendimento automatizado com IA
- **Catálogo de Produtos**: Sistema completo de produtos JSON
- **Geração PIX**: Integração automática para pagamentos
- **Cálculo de Frete**: Integração com APIs de entrega
- **Sistema de Sessões**: Histórico de conversas persistente

## 📋 Pré-requisitos

- Python 3.11+
- OpenAI API Key
- PostgreSQL (para produção)

## 🔧 Configuração

### Variáveis de Ambiente Necessárias:

```bash
OPENAI_API_KEY=sua_chave_openai
DATABASE_URL=sua_url_postgresql (opcional)
SESSION_SECRET=sua_chave_secreta_sessao
```

## 🚀 Deploy no Vercel

1. **Faça fork/clone do repositório**
2. **Configure as variáveis de ambiente no Vercel:**
   - `OPENAI_API_KEY`
   - `DATABASE_URL` (opcional)
   - `SESSION_SECRET`

3. **Deploy automático:**
   - Conecte seu repositório GitHub ao Vercel
   - O deploy será feito automaticamente

## 📁 Estrutura do Projeto

```
├── app.py              # Aplicação Flask principal
├── main.py             # Ponto de entrada
├── models.py           # Modelos do banco de dados
├── produtos.json       # Catálogo de produtos
├── requirements.txt    # Dependências Python
├── vercel.json        # Configuração Vercel
├── templates/         # Templates HTML
│   └── index.html
└── static/           # Arquivos estáticos
    ├── script.js
    └── style.css
```

## 🛠️ Desenvolvimento Local

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
python app.py
```

## 📱 API Endpoints

- `GET /` - Interface principal do chat
- `POST /chat` - Processamento de mensagens
- `POST /pix` - Geração de PIX
- `POST /reset` - Reset da conversa
- `POST /test-pix` - Teste da API PIX

## 🔒 Segurança

- Todas as chaves de API devem ser configuradas como variáveis de ambiente
- Nunca commitar credenciais no código
- Session keys são criptografadas

## 📄 Licença

Projeto desenvolvido para uso comercial da Papelaria Digital.
