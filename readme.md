# 📧 Sistema de Classificação Inteligente de Emails

> Sistema automatizado de triagem e classificação de emails corporativos usando Inteligência Artificial Gemini

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![Gemini AI](https://img.shields.io/badge/Gemini-AI-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🎯 Sobre o Projeto

O **Sistema de Classificação Inteligente de Emails** é uma aplicação web que automatiza a triagem de emails corporativos, classificando-os em **Produtivos** (que requerem ação) ou **Improdutivos** (informativos, marketing, etc.).

Utilizando a API do Google Gemini AI combinada com análise estrutural avançada, o sistema identifica:

- 📋 Emails que exigem ação ou resposta
- 🎯 Prioridade e tempo de resposta sugerido
- 💬 Sugestão de resposta contextual
- 🧠 Justificativa detalhada da classificação

### Por que usar este sistema?

- ⚡ **Economia de tempo**: Triagem automática de centenas de emails
- 🎯 **Priorização inteligente**: Identifica emails que realmente precisam de atenção
- 📊 **Alta precisão**: Combina IA generativa com regras estruturais
- 🔒 **Seguro**: Processamento local, sem armazenamento de dados
- 🌐 **Flexível**: Suporta texto direto ou upload de arquivos (.txt, .pdf, .eml)

---

## ✨ Funcionalidades

### 🔍 Classificação Avançada

- **Dual-Layer Analysis**: Análise estrutural + IA Gemini
- **10+ Tipos de Email**: Marketing, transacional, casual, corporativo, etc.
- **Validação em 3 Camadas**: Tipos óbvios → Produtividade corporativa → Consistência final

### 📊 Detecção Inteligente

- ✅ Listas de tarefas numeradas
- ✅ Solicitações explícitas
- ✅ Prazos e deadlines
- ✅ Convites para reuniões
- ✅ Verbos de ação
- ✅ Menções a anexos
- ✅ Marcadores de urgência

### 🎨 Interface Moderna

- Design responsivo com Tailwind CSS
- Upload via drag & drop
- Feedback visual em tempo real
- Indicadores de confiança animados
- Cópia de resposta com um clique

### 📄 Suporte a Múltiplos Formatos

- `.txt` - Arquivos de texto
- `.pdf` - Documentos PDF
- `.eml` - Arquivos de email nativos

---

## 🛠 Tecnologias Utilizadas

### Backend

- **Python 3.8+**
- **Flask** - Framework web
- **Flask-CORS** - Gerenciamento de CORS
- **Google Gemini AI** - Modelo de linguagem generativa
- **NLTK** - Processamento de linguagem natural
- **PyPDF2** - Extração de texto de PDFs
- **python-dotenv** - Gerenciamento de variáveis de ambiente

### Frontend

- **HTML5** / **CSS3**
- **JavaScript (Vanilla)**
- **Tailwind CSS** - Framework de estilização

### IA e Machine Learning

- **Google Gemini Pro** - Classificação inteligente
- **NLTK** - Tokenização e stopwords

---

## 🏗 Arquitetura

```
┌─────────────────┐
│   Usuário       │
│  (Frontend)     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────┐
│        Flask API Server             │
│  ┌─────────────────────────────┐   │
│  │  /classify endpoint         │   │
│  └──────────┬──────────────────┘   │
│             │                       │
│             ▼                       │
│  ┌─────────────────────────────┐   │
│  │  Extração de Texto          │   │
│  │  (.txt, .pdf, .eml)        │   │
│  └──────────┬──────────────────┘   │
│             │                       │
│             ▼                       │
│  ┌─────────────────────────────┐   │
│  │  Análise Estrutural         │   │
│  │  - Tipo de email            │   │
│  │  - Estrutura do conteúdo    │   │
│  └──────────┬──────────────────┘   │
│             │                       │
│             ▼                       │
│  ┌─────────────────────────────┐   │
│  │  Classificação Gemini AI    │   │
│  │  + Prompt Engineering       │   │
│  └──────────┬──────────────────┘   │
│             │                       │
│             ▼                       │
│  ┌─────────────────────────────┐   │
│  │  Validação em 3 Camadas     │   │
│  │  1. Tipos óbvios            │   │
│  │  2. Produtividade corporat. │   │
│  │  3. Consistência final      │   │
│  └──────────┬──────────────────┘   │
│             │                       │
│             ▼                       │
│  ┌─────────────────────────────┐   │
│  │  Resultado JSON             │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
```

---

## 📦 Pré-requisitos

- Python 3.8 ou superior
- Conta Google Cloud com API Gemini ativada
- Navegador moderno (Chrome, Firefox, Safari, Edge)

---

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/email-classification-system.git
cd email-classification-system
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instale as dependências

```bash
cd app
pip install -r requirements.txt
```

### 4. Baixe recursos do NLTK (se necessário)

```python
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

---

## ⚙️ Configuração

### 1. Obtenha sua API Key do Google Gemini

1. Acesse [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Crie um novo projeto (se necessário)
3. Gere uma API Key
4. Copie a chave

### 2. Configure as variáveis de ambiente

Crie um arquivo `.env` na pasta `app/`:

```env
GEMINI_API_KEY=sua_chave_api_aqui
```

### 3. Estrutura de pastas

Certifique-se de que sua estrutura está assim:

```
projeto/
├── app/
│   ├── .env                    # Variáveis de ambiente
│   ├── app.py                  # Aplicação principal
│   ├── requirements.txt        # Dependências
│   ├── templates/
│   │   └── index.html         # Interface web
│   ├── static/
│   │   └── assets/
│   │       └── js/
│   │           └── script.js  # JavaScript frontend
│   └── uploads/               # Pasta temporária (criada automaticamente)
└── README.md
```

---

## 🧠 Lógica de Classificação

### Sistema de 3 Camadas

#### **Layer 1: Tipos Óbvios**

Identifica e classifica automaticamente:

- ❌ **Marketing** (score ≥ 3): Promoções, descontos, ofertas
- ❌ **Transacional** (score ≥ 3): Confirmações, notificações automáticas
- ❌ **Casual** (score ≥ 2): Memes, piadas, entretenimento
- ❌ **Vago** (score ≥ 3): Reflexões filosóficas sem pedido claro

#### **Layer 2: Produtividade Corporativa**

Força classificação como PRODUTIVO quando detecta:

- ✅ Lista numerada + Prazo
- ✅ Reunião + Horário específico
- ✅ Ação aprovada + Prazo urgente
- ✅ Solicitação + Anexo + Prazo

#### **Layer 3: Consistência Final**

Valida e corrige inconsistências:

- Produtivo sem `requires_action` → adiciona flag
- Improdutivo com `requires_action` → remove flag
- Tom celebratório marcado como produtivo → corrige

---

## 🧑‍💻 Autor

- **Nome**: Otavio Inaba
- **Email**: inabaotavio7@gmail.com
- **LinkedIn**: [Otavio](www.linkedin.com/in/otávio-inaba)
