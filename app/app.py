from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import os
import re
import email
from email import policy
from email.parser import BytesParser
import PyPDF2
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import google.generativeai as genai
from dotenv import load_dotenv
import json
from werkzeug.utils import secure_filename
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

# Configurar Flask
app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Configurações
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'eml'}
MAX_FILE_SIZE = 10 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Configurar Gemini AI
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
else:
    print("ATENÇÃO: GEMINI_API_KEY não configurada!")

# Baixar recursos do NLTK
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)

try:
    stop_words = set(stopwords.words('portuguese'))
except:
    stop_words = set()


def allowed_file(filename):
    """Verifica se o arquivo tem uma extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text_from_file(file_path, filename):
    """Extrai texto de diferentes tipos de arquivo"""
    ext = filename.rsplit('.', 1)[1].lower()
    
    try:
        if ext == 'txt':
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        
        elif ext == 'pdf':
            text = []
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page in pdf_reader.pages:
                    text.append(page.extract_text())
            return '\n'.join(text)
        
        elif ext == 'eml':
            with open(file_path, 'rb') as f:
                msg = BytesParser(policy=policy.default).parse(f)
                
            subject = msg.get('subject', '')
            from_addr = msg.get('from', '')
            
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                        except:
                            continue
            else:
                try:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                except:
                    body = str(msg.get_payload())
            
            return f"De: {from_addr}\nAssunto: {subject}\n\n{body}"
        
        else:
            return ""
    
    except Exception as e:
        print(f"Erro ao extrair texto: {str(e)}")
        return ""


def detect_email_type(email_text):
    """
    Detecta o tipo de email: marketing, transacional, corporativo, casual
    """
    text_lower = email_text.lower()
    
    # Indicadores de MARKETING
    marketing_indicators = [
        'desconto', 'promoção', 'oferta', 'compre agora', 'aproveite',
        'última chance', 'por tempo limitado', 'não perca', 'cupom',
        'cashback', 'frete grátis', 'black friday', 'sale', 'economize',
        'unsubscribe', 'cancelar inscrição', 'clique aqui', 'saiba mais',
        'newsletter', 'novidades', 'lançamento', 'anúncio', 'preço especial',
        'garanta já', 'comprar agora', 'acesse agora', 'confira'
    ]
    
    # Indicadores TRANSACIONAIS
    transactional_indicators = [
        'confirmação', 'comprovante', 'recibo', 'nota fiscal',
        'transação', 'pagamento', 'aprovado', 'processado', 'concluído',
        'enviado', 'entregue', 'rastreamento', 'código de rastreio',
        'senha', 'recuperação', 'redefinir senha', 'código de verificação',
        'autenticação', 'notificação automática', 'mensagem automática',
        'não responda', 'do-not-reply', 'noreply', 'cobrança', 'fatura',
        'boleto', 'vencimento', 'extrato', 'saldo'
    ]
    
    # Indicadores de CASUAL/SOCIAL
    casual_indicators = [
        'meme', 'risada', 'engraçado', 'humor', 'piada', 'haha', 'kkk',
        'lol', 'emoji', '😂', '😊', '😍', '🤣',
        'vídeo', 'gif', 'link', 'youtube', 'tiktok',
        'compartilhando', 'só pra descontrair', 'só pra rir',
        'animar o dia', 'pra vocês rirem', 'vcs viram'
    ]
    
    # Indicadores de FILOSOFICE/VAGUE (improdutivo)
    vague_indicators = [
        'sinergia', 'holístico', 'ressignificação', 'ecossistema',
        'resiliente', 'vibração', 'energia', 'filosofar',
        'refletindo sobre', 'pensamentos sobre', 'fluxo',
        'sem pressa', 'jogando ideias', 'talvez devêssemos'
    ]
    
    # Indicadores CORPORATIVOS PRODUTIVOS
    corporate_productive_indicators = [
        'ação necessária', 'urgente', 'prazo', 'entrega', 'deadline',
        'favor confirmar', 'preciso que', 'solicito', 'requisição',
        'status do', 'atualização sobre', 'relatório', 'reunião',
        'projeto', 'cliente', 'contrato', 'aprovação',
        'em anexo', 'segue anexo', 'conforme discutido',
        'até hoje', 'até amanhã', 'imediatamente', 'sem falta',
        'código de acesso', 'senha', 'arquivo está em'
    ]
    
    # Indicadores de AÇÃO/DECISÃO (muito produtivo)
    action_indicators = [
        'está aprovado', 'pode seguir', 'vai fundo', 'faça isso',
        'precisa fazer', 'tem que', 'deve', 'necessário',
        'obrigatório', 'mandatório', 'crítico'
    ]
    
    # Contar indicadores
    marketing_score = sum(1 for ind in marketing_indicators if ind in text_lower)
    transactional_score = sum(1 for ind in transactional_indicators if ind in text_lower)
    casual_score = sum(1 for ind in casual_indicators if ind in text_lower)
    vague_score = sum(1 for ind in vague_indicators if ind in text_lower)
    corporate_score = sum(1 for ind in corporate_productive_indicators if ind in text_lower)
    action_score = sum(1 for ind in action_indicators if ind in text_lower)
    
    # Verificar headers de marketing
    if any(header in text_lower for header in ['list-unsubscribe:', 'x-campaign-id:', 'feedback-id:']):
        marketing_score += 3
    
    # Determinar tipo
    email_type = {
        'is_marketing': marketing_score >= 3,
        'is_transactional': transactional_score >= 3 and marketing_score < 3,
        'is_casual': casual_score >= 2,
        'is_vague': vague_score >= 3,
        'is_corporate': corporate_score >= 2,
        'has_action_items': action_score >= 1,
        'marketing_score': marketing_score,
        'transactional_score': transactional_score,
        'casual_score': casual_score,
        'vague_score': vague_score,
        'corporate_score': corporate_score,
        'action_score': action_score
    }
    
    return email_type


def analyze_email_structure(email_text):
    """
    Análise estrutural detalhada do email
    """
    analysis = {
        'has_greeting': False,
        'has_question': False,
        'has_request': False,
        'has_deadline': False,
        'has_attachment_mention': False,
        'has_urgency_markers': False,
        'has_action_verbs': False,
        'has_numbered_list': False,
        'has_deadline_time': False,
        'tone': 'neutral',
        'length_category': 'medium',
        'formality': 'neutral'
    }
    
    text_lower = email_text.lower()
    
    # Saudações
    corporate_greetings = ['prezado', 'caro', 'olá, equipe', 'prezados']
    casual_greetings = ['oi', 'olá', 'e aí', 'gente']
    
    analysis['has_greeting'] = any(g in text_lower for g in corporate_greetings + casual_greetings)
    analysis['formality'] = 'formal' if any(g in text_lower for g in corporate_greetings) else 'casual'
    
    # Perguntas
    question_markers = ['?', 'como', 'quando', 'onde', 'qual', 'quanto', 'por que', 'porque']
    analysis['has_question'] = any(marker in text_lower for marker in question_markers)
    
    # Solicitações/Pedidos
    request_markers = [
        'favor confirmar', 'preciso que', 'solicito', 'necessito',
        'poderia', 'pode', 'favor', 'pedido', 'requisição',
        'deve', 'tem que', 'precisa', 'obrigatório'
    ]
    analysis['has_request'] = any(marker in text_lower for marker in request_markers)
    
    
    # NOVO: Detecção de reuniões (indicador forte de ação necessária)
    meeting_markers = ['reunião', 'reuniao', 'meeting', 'call', 'encontro', 'alinhamento']
    analysis['has_meeting'] = any(marker in text_lower for marker in meeting_markers)
    # Prazos específicos
    deadline_markers = ['até', 'prazo', 'deadline', 'vencimento', 'antes de']
    time_markers = ['hoje', 'amanhã', 'agora', 'imediatamente', 'urgente', 'h', 'horas', 'segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo', ':', 'às', 'as ']
    
    analysis['has_deadline'] = any(marker in text_lower for marker in deadline_markers)
    analysis['has_deadline_time'] = any(marker in text_lower for marker in time_markers)
    
    
    # Se tem reunião + horário específico, é definitivamente um prazo
    if analysis['has_meeting'] and analysis['has_deadline_time']:
        analysis['has_deadline'] = True
    # Menção a anexos
    attachment_markers = ['anexo', 'anexado', 'em anexo', 'segue anexo', 'arquivo', 'documento', 'pdf']
    analysis['has_attachment_mention'] = any(marker in text_lower for marker in attachment_markers)
    
    # Urgência
    urgency_markers = ['urgente', 'emergência', 'crítico', 'imediato', 'asap', 'sem falta', 'imediatamente']
    analysis['has_urgency_markers'] = any(marker in text_lower for marker in urgency_markers)
    
    # Verbos de ação
    action_verbs = [
        'fazer', 'finalizar', 'validar', 'confirmar', 'seguir',
        'subir', 'enviar', 'revisar', 'aprovar', 'executar',
        'implementar', 'desenvolver', 'testar', 'verificar'
    ]
    analysis['has_action_verbs'] = any(verb in text_lower for verb in action_verbs)
    
    # Lista numerada (forte indicador de tarefas)
    analysis['has_numbered_list'] = bool(re.search(r'\d+[\.\)]\s+\w+', email_text))
    
    # Tom
    celebratory = ['parabéns', 'feliz', 'natal', 'aniversário', 'festa']
    casual_fun = ['meme', 'risada', '😂', 'haha', 'kkk', 'lol']
    vague = ['refletindo', 'filosofar', 'energia', 'vibração']
    
    if any(marker in text_lower for marker in celebratory):
        analysis['tone'] = 'celebratory'
    elif any(marker in text_lower for marker in casual_fun):
        analysis['tone'] = 'casual_fun'
    elif any(marker in text_lower for marker in vague):
        analysis['tone'] = 'vague'
    elif analysis['has_urgency_markers']:
        analysis['tone'] = 'urgent'
    
    # Tamanho
    word_count = len(email_text.split())
    if word_count < 20:
        analysis['length_category'] = 'very_short'
    elif word_count < 50:
        analysis['length_category'] = 'short'
    elif word_count < 150:
        analysis['length_category'] = 'medium'
    else:
        analysis['length_category'] = 'long'
    
    return analysis


def classify_with_contextual_gemini(email_text):
    """
    Classificação final refinada
    """
    if not GEMINI_API_KEY:
        return contextual_fallback_classification(email_text)
    
    try:
        email_type = detect_email_type(email_text)
        structure = analyze_email_structure(email_text)
        
        prompt = f"""Você é um especialista em classificação de emails corporativos no setor financeiro.

════════════════════════════════════════════════════════════════════

⚠️ REGRAS FUNDAMENTAIS ⚠️

**PRODUTIVO** = Email que EXIGE AÇÃO ESPECÍFICA ou RESPOSTA do destinatário

SEMPRE PRODUTIVO quando tem:
✓ Lista de tarefas numeradas com responsáveis e prazos
✓ Solicitação explícita: "favor confirmar", "preciso que"
✓ Pergunta que ESPERA resposta: "qual o status?", "quando?"
✓ Decisão/aprovação já tomada que requer execução: "está aprovado, pode seguir"
✓ Informação crítica com prazo: "arquivo na pasta X, fazer até 14h"
✓ Ação necessária: "deve fazer", "precisa de", "tem que"
✓ Convite para reunião com horário específico: "reunião amanhã às 15h"

SEMPRE IMPRODUTIVO quando é:
✗ Marketing/Promoções externas
✗ Notificações automáticas (pagamento, confirmação)
✗ Memes, piadas, entretenimento casual
✗ Reflexões vagas sem pedido claro ("filosofar sobre")
✗ Mensagens celebratórias (feliz natal, parabéns)
✗ Agradecimentos simples sem perguntas

════════════════════════════════════════════════════════════════════

📚 EXEMPLOS CRÍTICOS:

EXEMPLO 1 - MUITO PRODUTIVO:
Assunto: Ação Necessária: Cronograma Projeto Alpha
Corpo: "Conforme discutido:
1. Marcos: Finalizar relatório até quarta (18h)
2. Sara: Validar dashboard quinta de manhã
Em anexo, PDF com requisitos. Favor confirmar recebimento."
→ PRODUTIVO (95% confiança)
Motivo: Lista de tarefas, responsáveis, prazos específicos, pedido de confirmação

EXEMPLO 2 - IMPRODUTIVO (Casual):
Assunto: Vcs viram isso?? 😂
Corpo: "Acabei de ver aquele meme do gatinho, tive que mandar.
Só pra animar o dia!"
→ IMPRODUTIVO (98% confiança)
Motivo: Entretenimento casual, sem pedido de ação

EXEMPLO 3 - IMPRODUTIVO (Vago):
Assunto: Pensamentos sobre sinergia
Corpo: "Refletindo sobre ressignificação holística dos processos...
Talvez marcar um café para filosofar. Sem pressa, só ideias."
→ IMPRODUTIVO (90% confiança)
Motivo: Vago, filosófico, sem pedido claro, "sem pressa"

EXEMPLO 4 - PRODUTIVO (Curto mas Crítico):
Assunto: Sobre aquilo
Corpo: "Está aprovado. Pode seguir com plano B imediatamente.
Arquivo na pasta oculta. Se não fizer até 14h, contrato cai."
→ PRODUTIVO (95% confiança)
Motivo: Decisão tomada, ação imediata necessária, consequência clara, prazo

EXEMPLO 5 - IMPRODUTIVO (Marketing):
"ÚLTIMO DIA! 50% OFF! Aproveite agora!"
→ IMPRODUTIVO (98% confiança)
Motivo: Marketing externo

EXEMPLO 6 - IMPRODUTIVO (Transacional):
"Seu pagamento de R$75,90 foi aprovado. Não responda este email."
→ IMPRODUTIVO (98% confiança)
Motivo: Notificação automática

EXEMPLO 7 - PRODUTIVO (Reunião):
Corpo: "reunião de alinhamento final no teams amanhã às 15:00"
→ PRODUTIVO (94% confiança)
Motivo: Convite para reunião com horário específico, requer presença/ação

════════════════════════════════════════════════════════════════════

📊 ANÁLISE PRÉVIA:

**Tipo Detectado:**
- Marketing: {email_type['is_marketing']} (score: {email_type['marketing_score']})
- Transacional: {email_type['is_transactional']} (score: {email_type['transactional_score']})
- Casual/Meme: {email_type['is_casual']} (score: {email_type['casual_score']})
- Vago/Filosófico: {email_type['is_vague']} (score: {email_type['vague_score']})
- Corporativo: {email_type['is_corporate']} (score: {email_type['corporate_score']})
- Itens de Ação: {email_type['has_action_items']} (score: {email_type['action_score']})

**Estrutura:**
- Lista numerada: {structure['has_numbered_list']}
- Tem solicitação: {structure['has_request']}
- Tem prazo: {structure['has_deadline']}
- Prazo com horário: {structure['has_deadline_time']}
- Verbos de ação: {structure['has_action_verbs']}
- Menção a anexo: {structure['has_attachment_mention']}
- Urgência: {structure['has_urgency_markers']}
- Tem reunião: {structure.get('has_meeting', False)}
- Tom: {structure['tone']}
- Formalidade: {structure['formality']}

════════════════════════════════════════════════════════════════════

📧 EMAIL PARA CLASSIFICAR:
{email_text[:3000]}

════════════════════════════════════════════════════════════════════

🎯 PROCESSO DE DECISÃO:

1. É marketing/transacional/meme/vago? → IMPRODUTIVO
2. Tem lista de tarefas com prazos? → PRODUTIVO
3. Tem solicitação explícita + prazo? → PRODUTIVO
4. Tem decisão tomada + ação requerida? → PRODUTIVO
5. Tem pergunta que espera resposta? → PRODUTIVO
6. É celebração/agradecimento simples? → IMPRODUTIVO
7. É reflexão sem pedido claro? → IMPRODUTIVO

════════════════════════════════════════════════════════════════════

⚠️ ATENÇÃO ESPECIAL:

- "Vcs viram isso?" + meme/link = IMPRODUTIVO (casual)
- "Sobre aquilo" + ação imediata = PRODUTIVO (contextual)
- "Pensamentos sobre" + vago = IMPRODUTIVO (sem ação clara)
- "Ação Necessária:" + tarefas = PRODUTIVO (muito claro)

════════════════════════════════════════════════════════════════════

Retorne APENAS JSON válido (sem markdown):
{{
    "category": "Produtivo" ou "Improdutivo",
    "confidence": 0.0 a 1.0,
    "email_type": "corporate_productive" | "casual" | "vague" | "marketing" | "transactional",
    "reasoning": "Explicação clara e direta do motivo",
    "communicative_intent": "solicitar_ação" | "entreter" | "refletir" | "promover" | "notificar",
    "requires_action": true ou false,
    "action_clarity": "very_clear" | "clear" | "vague" | "none",
    "priority": "Alta", "Média" ou "Baixa",
    "response_time": "< 24h", "24-48h" ou "> 48h",
    "suggested_response": "resposta apropriada"
}}
"""

        response = model.generate_content(prompt)
        result_text = response.text.strip()
        result_text = result_text.replace('```json', '').replace('```', '').strip()
        result = json.loads(result_text)
        
        # Validações em camadas
        result = validate_against_obvious_types(result, email_type, email_text)
        result = validate_corporate_productivity(result, structure, email_type)
        result = validate_final_consistency(result, structure)
        
        if 'suggested_response' not in result:
            result['suggested_response'] = generate_contextual_response(result)
        
        result['email_type_analysis'] = email_type
        result['structural_analysis'] = structure
        result['classification_method'] = 'gemini_v4_final'
        
        return result
    
    except Exception as e:
        print(f"Erro Gemini: {str(e)}")
        import traceback
        traceback.print_exc()
        return contextual_fallback_classification(email_text)


def validate_against_obvious_types(result, email_type, email_text):
    """
    Validação Layer 1: Tipos óbvios (marketing, transacional, casual, vago)
    """
    text_lower = email_text.lower()
    
    # Marketing
    if email_type['is_marketing'] and email_type['marketing_score'] >= 3:
        print(f"MARKETING detectado - Forçando IMPRODUTIVO")
        result['category'] = 'Improdutivo'
        result['email_type'] = 'marketing'
        result['confidence'] = 0.95
        result['requires_action'] = False
        return result
    
    # Transacional
    if email_type['is_transactional'] and email_type['transactional_score'] >= 3:
        print(f"TRANSACIONAL detectado - Forçando IMPRODUTIVO")
        result['category'] = 'Improdutivo'
        result['email_type'] = 'transactional'
        result['confidence'] = 0.95
        result['requires_action'] = False
        return result
    
    # Casual/Meme
    if email_type['is_casual'] and email_type['casual_score'] >= 2:
        print(f"CASUAL/MEME detectado - Forçando IMPRODUTIVO")
        result['category'] = 'Improdutivo'
        result['email_type'] = 'casual'
        result['confidence'] = 0.92
        result['requires_action'] = False
        result['reasoning'] = "Email casual/entretenimento sem propósito de trabalho"
        return result
    
    # Vago/Filosófico
    if email_type['is_vague'] and email_type['vague_score'] >= 3:
        print(f"VAGO/FILOSÓFICO detectado - Forçando IMPRODUTIVO")
        result['category'] = 'Improdutivo'
        result['email_type'] = 'vague'
        result['confidence'] = 0.88
        result['requires_action'] = False
        result['reasoning'] = "Email vago/filosófico sem pedido claro de ação"
        return result
    
    # "Não responda"
    if 'não responda' in text_lower or 'noreply' in text_lower:
        print(f"'NÃO RESPONDA' - Forçando IMPRODUTIVO")
        result['category'] = 'Improdutivo'
        result['confidence'] = 0.98
        result['requires_action'] = False
        return result
    
    return result


def validate_corporate_productivity(result, structure, email_type):
    """
    Validação Layer 2: Produtividade corporativa
    """
    # Se já foi marcado como improdutivo óbvio, não mexer
    if result.get('email_type') in ['marketing', 'transactional', 'casual', 'vague']:
        return result
    
    # FORTE indicador de produtivo: lista numerada + prazos
    if structure['has_numbered_list'] and structure['has_deadline']:
        print(f"LISTA NUMERADA + PRAZO - Forçando PRODUTIVO")
        result['category'] = 'Produtivo'
        result['confidence'] = max(0.95, result.get('confidence', 0.8))
        result['requires_action'] = True
        result['priority'] = 'Alta'
        return result
    
    
    # NOVO: FORTE indicador - Reunião + Horário específico
    if structure.get('has_meeting') and structure['has_deadline_time']:
        print(f"REUNIÃO + HORÁRIO - Forçando PRODUTIVO")
        result['category'] = 'Produtivo'
        result['confidence'] = max(0.94, result.get('confidence', 0.8))
        result['requires_action'] = True
        result['priority'] = 'Alta'
        return result
    # FORTE indicador: ação aprovada + prazo urgente
    if email_type['has_action_items'] and structure['has_deadline_time']:
        print(f"AÇÃO APROVADA + PRAZO URGENTE - Forçando PRODUTIVO")
        result['category'] = 'Produtivo'
        result['confidence'] = max(0.93, result.get('confidence', 0.8))
        result['requires_action'] = True
        result['priority'] = 'Alta'
        return result
    
    # Solicitação + anexo + prazo
    if structure['has_request'] and structure['has_attachment_mention'] and structure['has_deadline']:
        print(f"SOLICITAÇÃO + ANEXO + PRAZO - Reforçando PRODUTIVO")
        if result['category'].lower() != 'produtivo':
            result['category'] = 'Produtivo'
            result['confidence'] = 0.90
            result['requires_action'] = True
    
    return result


def validate_final_consistency(result, structure):
    """
    Validação Layer 3: Consistência final
    """
    # Se marcou como produtivo mas não tem requires_action
    if result['category'].lower() == 'produtivo' and not result.get('requires_action'):
        print(f"INCONSISTÊNCIA: Produtivo sem requires_action")
        result['requires_action'] = True
    
    # Se marcou como improdutivo mas requires_action = true
    if result['category'].lower() == 'improdutivo' and result.get('requires_action'):
        print(f"INCONSISTÊNCIA: Improdutivo com requires_action")
        result['requires_action'] = False
    
    # Tom celebratório sempre improdutivo
    if structure['tone'] == 'celebratory' and result['category'].lower() == 'produtivo':
        print(f"Tom celebratório - Corrigindo para IMPRODUTIVO")
        result['category'] = 'Improdutivo'
        result['requires_action'] = False
    
    return result


def contextual_fallback_classification(email_text):
    """
    Classificação fallback sem Gemini
    """
    email_type = detect_email_type(email_text)
    structure = analyze_email_structure(email_text)
    
    # Tipos óbvios
    if email_type['is_marketing'] or email_type['is_transactional']:
        return {
            'category': 'Improdutivo',
            'confidence': 0.92,
            'email_type': 'marketing' if email_type['is_marketing'] else 'transactional',
            'reasoning': 'Email de marketing ou transacional',
            'communicative_intent': 'promover' if email_type['is_marketing'] else 'notificar',
            'requires_action': False,
            'action_clarity': 'none',
            'priority': 'Baixa',
            'response_time': '> 48h',
            'suggested_response': 'Este email não requer resposta.',
            'email_type_analysis': email_type,
            'structural_analysis': structure,
            'classification_method': 'fallback_v4'
        }
    
    if email_type['is_casual']:
        return {
            'category': 'Improdutivo',
            'confidence': 0.90,
            'email_type': 'casual',
            'reasoning': 'Email casual/entretenimento',
            'communicative_intent': 'entreter',
            'requires_action': False,
            'action_clarity': 'none',
            'priority': 'Baixa',
            'response_time': '> 48h',
            'suggested_response': 'Email casual, sem necessidade de resposta formal.',
            'email_type_analysis': email_type,
            'structural_analysis': structure,
            'classification_method': 'fallback_v4'
        }
    
    if email_type['is_vague']:
        return {
            'category': 'Improdutivo',
            'confidence': 0.85,
            'email_type': 'vague',
            'reasoning': 'Email vago sem pedido claro',
            'communicative_intent': 'refletir',
            'requires_action': False,
            'action_clarity': 'vague',
            'priority': 'Baixa',
            'response_time': '> 48h',
            'suggested_response': 'Reflexões interessantes, mas sem ação definida necessária.',
            'email_type_analysis': email_type,
            'structural_analysis': structure,
            'classification_method': 'fallback_v4'
        }
    
    # Análise corporativa
    score = 0
    
    if structure['has_numbered_list']:
        score += 5
    if structure['has_request']:
        score += 3
    if structure['has_deadline_time']:
        score += 3
    if email_type['has_action_items']:
        score += 3
    if structure['has_attachment_mention']:
        score += 2
    if structure['has_urgency_markers']:
        score += 2
    
    if score >= 5:
        category = 'Produtivo'
        confidence = min(0.88, 0.65 + (score * 0.04))
        priority = 'Alta' if score >= 8 else 'Média'
    else:
        category = 'Improdutivo'
        confidence = 0.70
        priority = 'Baixa'
    
    return {
        'category': category,
        'confidence': confidence,
        'email_type': 'corporate_productive' if category == 'Produtivo' else 'general',
        'reasoning': f'Análise fallback: Score={score}',
        'communicative_intent': 'solicitar_ação' if category == 'Produtivo' else 'informar',
        'requires_action': category == 'Produtivo',
        'action_clarity': 'clear' if score >= 8 else 'vague',
        'priority': priority,
        'response_time': '< 24h' if priority == 'Alta' else '24-48h',
        'suggested_response': generate_contextual_response({'category': category}),
        'email_type_analysis': email_type,
        'structural_analysis': structure,
        'classification_method': 'fallback_v4'
    }


def generate_contextual_response(result):
    """Gera resposta contextual"""
    category = result.get('category', 'Produtivo').lower()
    email_type = result.get('email_type', 'corporate')
    
    if email_type in ['marketing', 'transactional', 'casual']:
        return "Este email não requer resposta formal."
    
    if category == 'produtivo':
        return """Prezado(a),

Confirmamos o recebimento. Providenciaremos conforme solicitado.

Retornaremos em breve.

Atenciosamente,
Equipe"""
    else:
        return """Prezado(a),

Recebemos sua mensagem.

Atenciosamente,
Equipe"""


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/classify', methods=['POST'])
def classify_email():
    try:
        email_text = ""
        
        if 'text' in request.form:
            email_text = request.form['text']
        elif 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
            if not allowed_file(file.filename):
                return jsonify({'error': 'Tipo de arquivo não permitido'}), 400
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            email_text = extract_text_from_file(filepath, filename)
            
            try:
                os.remove(filepath)
            except:
                pass
        else:
            return jsonify({'error': 'Nenhum texto ou arquivo fornecido'}), 400
        
        if not email_text or len(email_text.strip()) < 10:
            return jsonify({'error': 'Conteúdo muito curto'}), 400
        
        result = classify_with_contextual_gemini(email_text)
        result['original_text_length'] = len(email_text)
        result['analysis_timestamp'] = datetime.now().isoformat()
        
        return jsonify(result), 200
    
    except Exception as e:
        print(f"Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Erro: {str(e)}'}), 500


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'online',
        'gemini_configured': bool(GEMINI_API_KEY),
        'version': '4.0-final'
    }), 200


if __name__ == '__main__':
    print("=" * 80)
    print("Sistema de Classificacao de Emails - VERSAO FINAL 4.0")
    print("=" * 80)
    print(f"(v) Flask iniciado")
    
    if GEMINI_API_KEY:
        print(f"(v) Gemini AI configurado")
    else:
        print(f"(!) Gemini AI NAO configurado")
    
    print("=" * 80)
    print(">> http://localhost:5000")
    print("=" * 80)
    
    app.run(debug=True, host='0.0.0.0', port=5000)