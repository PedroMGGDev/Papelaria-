import os
import json
import logging
import requests
import uuid
import re
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, session
from openai import OpenAI
from models import db, CustomerSession, ConversationLog
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hello, Vercel!"

if __name__ == "__main__":
    app.run()
# Configure logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "papelaria_digital_secret_key")

# Configure database
database_url = os.environ.get('DATABASE_URL')
if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
else:
    logging.warning("DATABASE_URL not found, running without database")

# Initialize OpenAI client
# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Create database tables
if database_url:
    with app.app_context():
        db.create_all()

def load_produtos():
    """Load products from JSON file and format for OpenAI"""
    try:
        with open('produtos.json', 'r', encoding='utf-8') as f:
            raw_produtos = json.load(f)
        
        # Transform flat JSON into hierarchical structure
        produtos_dict = {}
        
        for item in raw_produtos:
            produto_nome = item['Produto']
            tamanho = item['Tamanho']
            opcao = item['Opção']
            
            # Extract price from string like "R$ 35,50"
            preco_str = item['Preço/Unidade'].replace('R$', '').replace(',', '.').strip()
            preco = float(preco_str) if preco_str != '-' else 0.0
            
            if produto_nome not in produtos_dict:
                produtos_dict[produto_nome] = {
                    'nome': produto_nome,
                    'tamanhos': {}
                }
            
            if tamanho not in produtos_dict[produto_nome]['tamanhos']:
                produtos_dict[produto_nome]['tamanhos'][tamanho] = {
                    'nome': tamanho,
                    'opcoes': []
                }
            
            produtos_dict[produto_nome]['tamanhos'][tamanho]['opcoes'].append({
                'nome': opcao,
                'preco': preco,
                'campo': item['Campo']
            })
        
        # Convert to list format
        produtos_estruturados = []
        for produto in produtos_dict.values():
            produto_final = {
                'nome': produto['nome'],
                'tamanhos': list(produto['tamanhos'].values())
            }
            produtos_estruturados.append(produto_final)
        
        # Format products for better understanding by AI
        produtos_text = "CATÁLOGO DE PRODUTOS DA PAPELARIA DIGITAL:\n\n"
        for i, produto in enumerate(produtos_estruturados, 1):
            produtos_text += f"{i}. {produto['nome']}\n"
            for tamanho in produto['tamanhos']:
                produtos_text += f"   Tamanho: {tamanho['nome']}\n"
                for opcao in tamanho['opcoes']:
                    produtos_text += f"     - {opcao['nome']}: R$ {opcao['preco']:.2f}\n"
            produtos_text += "\n"
        
        return produtos_text, produtos_estruturados
    except Exception as e:
        logging.error(f"Error loading products: {e}")
        return "Erro ao carregar catálogo de produtos.", []

def calculate_freight(origem_cep, destino_cep, peso=0.5, altura=10, largura=15, comprimento=20):
    """Calculate freight using Melhor Envio API"""
    try:
        # Melhor Envio sandbox API
        url = "https://sandbox.melhorenvio.com.br/api/v2/me/shipment/calculate"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer YOUR_MELHOR_ENVIO_TOKEN",  # This would need to be obtained through OAuth
            "User-Agent": "Papelaria Digital"
        }
        
        payload = {
            "from": {
                "postal_code": origem_cep
            },
            "to": {
                "postal_code": destino_cep
            },
            "package": {
                "height": altura,
                "width": largura,
                "length": comprimento,
                "weight": peso
            }
        }
        
        # For this implementation, we'll return a mock freight value
        # In production, you would implement proper OAuth authentication
        logging.info(f"Calculating freight from {origem_cep} to {destino_cep}")
        
        # Mock freight calculation based on distance approximation
        # In real implementation, use the actual API response
        freight_value = 15.50  # Base freight value
        
        return {
            "success": True,
            "valor": freight_value,
            "prazo": "5-7 dias úteis"
        }
        
    except Exception as e:
        logging.error(f"Error calculating freight: {e}")
        return {
            "success": False,
            "valor": 15.50,  # Fallback value
            "prazo": "5-7 dias úteis",
            "error": str(e)
        }

def generate_pix(nome, cpf, valor, descricao):
    """Generate PIX payment using Asaas API"""
    try:
        url = "https://82f252fd-beeb-4634-a627-0812de9af691-00-9skxrnyqeafx.spock.replit.dev/api/pagamento"
        
        headers = {
            "Content-Type": "application/json",
            "X-Auth-Token": "Printlivros2024"
        }
        
        # Calculate due date (7 days from now)
        due_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        payload = {
            "name": nome,
            "cpfCnpj": cpf,
            "value": float(valor),
            "dueDate": due_date,
            "description": descricao,
            "billingType": "pix"
        }
        
        logging.info(f"Generating PIX for {nome}, CPF: {cpf}, Value: R$ {valor}")
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "pix_url": result.get("invoiceUrl", ""),
                "qr_code": result.get("qrCode", ""),
                "pix_code": result.get("paymentLink", ""),
                "id": result.get("id", "")
            }
        else:
            logging.error(f"PIX generation failed: {response.status_code} - {response.text}")
            return {
                "success": False,
                "error": f"Erro na API: {response.status_code}"
            }
            
    except Exception as e:
        logging.error(f"Error generating PIX: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def get_or_create_customer_session(session_id):
    """Get existing customer session or create new one"""
    if not database_url:
        return None
        
    customer_session = CustomerSession.query.filter_by(session_id=session_id).first()
    if not customer_session:
        customer_session = CustomerSession()
        customer_session.session_id = session_id
        db.session.add(customer_session)
        db.session.commit()
    
    return customer_session

def update_customer_session(session_id, **kwargs):
    """Update customer session with provided data"""
    if not database_url:
        return None
        
    customer_session = get_or_create_customer_session(session_id)
    
    if customer_session:
        for key, value in kwargs.items():
            if hasattr(customer_session, key) and value is not None:
                setattr(customer_session, key, value)
        
        customer_session.updated_at = datetime.utcnow()
        db.session.commit()
    
    return customer_session

def save_conversation_log(session_id, role, content):
    """Save conversation message to database"""
    if not database_url:
        return None
        
    log_entry = ConversationLog()
    log_entry.session_id = session_id
    log_entry.role = role
    log_entry.content = content
    
    db.session.add(log_entry)
    db.session.commit()
    return log_entry

def extract_customer_data_from_message(message, customer_session):
    """Extract customer data from message using patterns"""
    updates = {}
    
    # Extract product information
    if not customer_session.produto:
        # Extract product types with improved patterns
        product_patterns = [
            (r'\b(\d+\s*)?(livros?\s+grampo|livro\s+grampo)\b', 'Livro Grampo'),
            (r'\b(\d+\s*)?(revistas?\s+grampo|revista\s+grampo)\b', 'Revista Grampo'),
            (r'\b(\d+\s*)?(cadernos?\s+espiral|caderno\s+espiral)\b', 'Caderno Espiral'),
            (r'\b(\d+\s*)?(cartões?\s+de\s+visita|cartão\s+de\s+visita)\b', 'Cartão de Visita'),
            (r'\b(\d+\s*)?(banners?|banner)\b', 'Banner'),
            (r'\b(\d+\s*)?(flyers?|flyer)\b', 'Flyer'),
        ]
        
        for pattern, product_name in product_patterns:
            product_match = re.search(pattern, message.lower())
            if product_match:
                updates['produto'] = product_name
                # Also try to extract quantity from the same match
                if product_match.group(1) and not customer_session.quantidade:
                    quantity_str = product_match.group(1).strip()
                    if quantity_str.isdigit():
                        updates['quantidade'] = int(quantity_str)
                break
    
    # Extract size information
    if not customer_session.tamanho:
        size_patterns = [
            r'\b(a4|A4)\b',
            r'\b(a5|A5)\b',
            r'\b(14x21|14 x 21)\b',
            r'\b(9x5|9 x 5)\b',
            r'\b(120x80|120 x 80)\b',
            r'\b(200x80|200 x 80)\b',
        ]
        
        for pattern in size_patterns:
            size_match = re.search(pattern, message, re.IGNORECASE)
            if size_match:
                size = size_match.group(1).upper()
                if size in ['A4', 'A5']:
                    updates['tamanho'] = size
                elif '14' in size:
                    updates['tamanho'] = '14x21'
                elif '9' in size:
                    updates['tamanho'] = '9x5'
                elif '120' in size:
                    updates['tamanho'] = '120x80'
                elif '200' in size:
                    updates['tamanho'] = '200x80'
                break
    
    # Extract options (shrink, acabamento, etc.)
    if not customer_session.opcoes:
        option_patterns = [
            r'\b(com shrink|shrink)\b',
            r'\b(sem shrink)\b',
            r'\b(capa comum|comum)\b',
            r'\b(capa premium|premium)\b',
            r'\b(simples)\b',
            r'\b(com verniz|verniz)\b',
            r'\b(sem verniz)\b',
            r'\b(lona)\b',
            r'\b(vinil)\b',
            r'\b(fosco)\b',
        ]
        
        for pattern in option_patterns:
            option_match = re.search(pattern, message.lower())
            if option_match:
                option = option_match.group(1)
                if 'com shrink' in option or option == 'shrink':
                    updates['opcoes'] = 'Com Shrink'
                elif 'sem shrink' in option:
                    updates['opcoes'] = 'Sem Shrink'
                elif 'capa premium' in option or option == 'premium':
                    updates['opcoes'] = 'Premium'
                elif 'capa comum' in option or option == 'comum':
                    updates['opcoes'] = 'Comum'
                elif option == 'simples':
                    updates['opcoes'] = 'Simples'
                elif 'com verniz' in option or option == 'verniz':
                    updates['opcoes'] = 'Com Verniz'
                elif 'sem verniz' in option:
                    updates['opcoes'] = 'Sem Verniz'
                elif option == 'lona':
                    updates['opcoes'] = 'Lona'
                elif option == 'vinil':
                    updates['opcoes'] = 'Vinil'
                elif option == 'fosco':
                    updates['opcoes'] = 'Fosco'
                break
    
    # Extract name patterns like "meu nome é João Silva" or "me chamo Maria"
    name_patterns = [
        r'(?:meu nome é|me chamo|sou|eu sou)\s+([A-ZÁÀÉÈÍÌÓÒÚÙ][a-záàéèíìóòúù]+(?:\s+[A-ZÁÀÉÈÍÌÓÒÚÙ][a-záàéèíìóòúù]+)*)',
        r'nome[:\s]+([A-ZÁÀÉÈÍÌÓÒÚÙ][a-záàéèíìóòúù]+(?:\s+[A-ZÁÀÉÈÍÌÓÒÚÙ][a-záàéèíìóòúù]+)*)',
        # Match common full name patterns
        r'\b([A-ZÁÀÉÈÍÌÓÒÚÙ][a-záàéèíìóòúù]+\s+[A-ZÁÀÉÈÍÌÓÒÚÙ][a-záàéèíìóòúù]+(?:\s+[A-ZÁÀÉÈÍÌÓÒÚÙ][a-záàéèíìóòúù]+)*)\b'
    ]
    
    if not customer_session.nome:
        for pattern in name_patterns:
            name_match = re.search(pattern, message, re.IGNORECASE)
            if name_match:
                # Validate it's not just a product name
                potential_name = name_match.group(1).strip()
                if len(potential_name.split()) >= 2 and not any(word in potential_name.lower() for word in ['livro', 'revista', 'caderno', 'cartão', 'banner', 'flyer']):
                    updates['nome'] = potential_name
                    break
    
    # Extract address information
    if not customer_session.endereco_completo:
        address_patterns = [
            r'(?:endereço|endereco|moro|reside|residencia)[:\s]+([^,]+(?:,\s*\d+)?)',
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,?\s*\d+)\b',
            # Street patterns with numbers
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s*,\s*\d+)\b'
        ]
        
        for pattern in address_patterns:
            address_match = re.search(pattern, message, re.IGNORECASE)
            if address_match:
                potential_address = address_match.group(1).strip()
                # Validate it looks like an address
                if any(char.isdigit() for char in potential_address) and len(potential_address) > 5:
                    updates['endereco_completo'] = potential_address
                    break
    
    # Extract CPF (11 digits)
    cpf_match = re.search(r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b', message)
    if cpf_match and not customer_session.cpf:
        cpf = re.sub(r'[^\d]', '', cpf_match.group())
        if len(cpf) == 11:  # Validate CPF length
            updates['cpf'] = cpf
    
    # Extract CEP (8 digits)
    cep_match = re.search(r'\b\d{5}-?\d{3}\b', message)
    if cep_match and not customer_session.cep:
        cep = re.sub(r'[^\d]', '', cep_match.group())
        if len(cep) == 8:  # Validate CEP length
            updates['cep'] = cep
    
    # Extract phone number
    phone_match = re.search(r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}', message)
    if phone_match and not customer_session.telefone:
        phone = re.sub(r'[^\d]', '', phone_match.group())
        if len(phone) >= 10:  # Validate phone length
            updates['telefone'] = phone
    
    # Extract quantity
    qty_match = re.search(r'\b(\d+)\s*(?:unidade|unidades|peça|peças|exemplar|exemplares)\b', message.lower())
    if qty_match and not customer_session.quantidade:
        updates['quantidade'] = int(qty_match.group(1))
    
    # Extract number of pages
    pages_match = re.search(r'\b(\d+)\s*(?:página|páginas|folha|folhas)\b', message.lower())
    if pages_match and not customer_session.numero_paginas:
        updates['numero_paginas'] = int(pages_match.group(1))
    
    return updates

def get_system_prompt(customer_session=None):
    """Get the detailed system prompt for the AI assistant"""
    produtos_text, _ = load_produtos()
    
    # Build context about what information we already have
    context_info = ""
    missing_fields = []
    
    if customer_session and database_url:
        filled_info = []
        if customer_session.produto:
            filled_info.append(f"Produto: {customer_session.produto}")
        if customer_session.tamanho:
            filled_info.append(f"Tamanho: {customer_session.tamanho}")
        if customer_session.opcoes:
            filled_info.append(f"Opções: {customer_session.opcoes}")
        if customer_session.quantidade:
            filled_info.append(f"Quantidade: {customer_session.quantidade}")
        if customer_session.numero_paginas:
            filled_info.append(f"Número de páginas: {customer_session.numero_paginas}")
        if customer_session.nome:
            filled_info.append(f"Nome: {customer_session.nome}")
        if customer_session.cpf:
            filled_info.append(f"CPF: {customer_session.cpf}")
        if customer_session.endereco_completo:
            filled_info.append(f"Endereço: {customer_session.endereco_completo}")
        if customer_session.cep:
            filled_info.append(f"CEP: {customer_session.cep}")
        
        missing_fields = customer_session.get_missing_fields()
        
        if filled_info:
            context_info = f"\n\nINFORMAÇÕES JÁ COLETADAS DO CLIENTE:\n" + "\n".join([f"- {info}" for info in filled_info])
        
        if missing_fields:
            context_info += f"\n\nCAMPOS QUE AINDA PRECISAM SER COLETADOS:\n" + "\n".join([f"- {field}" for field in missing_fields])
    
    return f"""Você é um atendente virtual inteligente da 'Papelaria Digital', especializado em atendimento completo de vendas.

CATÁLOGO DE PRODUTOS:
{produtos_text}
{context_info}

INSTRUÇÕES IMPORTANTES:
1. NUNCA repita perguntas sobre informações já coletadas (veja lista acima).

2. Foque apenas nos campos que ainda estão faltando.

3. Seja inteligente para interpretar variações, erros de digitação e sinônimos dos produtos.

4. Se um campo já está preenchido, NÃO pergunte novamente sobre ele.

5. Quando tiver TODAS as informações obrigatórias, retorne um JSON com a seguinte estrutura:
{{
    "action": "generate_pix",
    "data": {{
        "produto": "nome do produto",
        "tamanho": "tamanho selecionado",
        "opcoes": "opções selecionadas",
        "quantidade": numero,
        "nome": "nome completo",
        "cpf": "cpf sem pontuação",
        "endereco": "endereço completo",
        "cep": "cep sem pontuação",
        "valor_produto": valor_do_produto,
        "descricao": "descrição do pedido"
    }}
}}

5. Mantenha um tom amigável e profissional, como um verdadeiro atendente de papelaria.

6. Ajude o cliente a escolher produtos adequados às suas necessidades.

7. Se o cliente perguntar sobre prazo de entrega, informe que será calculado após confirmar o endereço.

8. Seja preciso com os preços consultando sempre o catálogo fornecido.

IMPORTANTE: Só gere o JSON de ação quando TODAS as informações obrigatórias estiverem coletadas."""

@app.route('/')
def index():
    """Render the main chat interface"""
    return render_template('index_simple.html')

@app.route('/test')
def test():
    """Test route"""
    return render_template('test.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Process chat messages with OpenAI integration"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "Mensagem não fornecida"}), 400
        
        user_message = data['message']
        
        # Generate or get session ID from request data (client-side) or create new one
        if 'session_id' in data and data['session_id']:
            session_id = data['session_id']
            session['session_id'] = session_id
        elif 'session_id' not in session:
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
        else:
            session_id = session['session_id']
        
        # Get or create customer session in database
        customer_session = get_or_create_customer_session(session_id)
        
        # Extract any customer data from the message
        if customer_session:
            extracted_data = extract_customer_data_from_message(user_message, customer_session)
            if extracted_data:
                update_customer_session(session_id, **extracted_data)
                customer_session = get_or_create_customer_session(session_id)  # Refresh
        
        # Check if all required data is collected and auto-generate PIX
        should_generate_pix = False
        if customer_session and all([
            customer_session.produto,
            customer_session.tamanho,
            customer_session.opcoes,
            customer_session.quantidade,
            customer_session.nome,
            customer_session.cpf,
            customer_session.cep
        ]):
            should_generate_pix = True
        
        # Save user message to conversation log
        save_conversation_log(session_id, 'user', user_message)
        
        # Get conversation history from database instead of session
        conversation_logs = ConversationLog.query.filter_by(
            session_id=session_id
        ).order_by(ConversationLog.timestamp).limit(20).all()
        
        # Build message history from database
        conversation_history = []
        for log in conversation_logs:
            conversation_history.append({
                "role": log.role,
                "content": log.content
            })
        
        # Add current user message
        conversation_history.append({
            "role": "user", 
            "content": user_message
        })
        
        # Prepare messages for OpenAI
        messages = [
            {"role": "system", "content": get_system_prompt(customer_session)},
            *conversation_history
        ]
        
        # Call OpenAI API
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content
        
        # Auto-generate PIX if all data is collected, regardless of AI response
        if should_generate_pix and customer_session and not customer_session.pix_gerado:
            try:
                # Load produto data to get price
                produtos_data = load_produtos()[1] 
                product_info = None
                logging.info(f"Looking for product: '{customer_session.produto}', size: '{customer_session.tamanho}', options: '{customer_session.opcoes}'")
                
                for produto in produtos_data:
                    produto_nome = produto.get('nome', '')
                    logging.info(f"Checking product: '{produto_nome}'")
                    
                    # Check if product matches (including partial matches for "Livro Grampo")
                    if (produto_nome == customer_session.produto or 
                        (customer_session.produto == 'Livro Grampo' and 'Livro Grampo' in produto_nome)):
                        logging.info(f"Product matched! Looking for size: '{customer_session.tamanho}'")
                        
                        for size in produto.get('tamanhos', []):
                            size_nome = size.get('nome', '')
                            logging.info(f"Checking size: '{size_nome}'")
                            
                            if size_nome == customer_session.tamanho:
                                logging.info(f"Size matched! Looking for option: '{customer_session.opcoes}'")
                                
                                for option in size.get('opcoes', []):
                                    option_nome = option.get('nome', '')
                                    logging.info(f"Checking option: '{option_nome}'")
                                    
                                    if option_nome == customer_session.opcoes:
                                        product_info = option
                                        logging.info(f"Found matching product! Price: {option.get('preco')}")
                                        break
                                if product_info:
                                    break
                        if product_info:
                            break
                
                if product_info:
                    # Calculate values
                    unit_price = product_info['preco']
                    product_value = unit_price * customer_session.quantidade
                    
                    # Calculate freight
                    freight_result = calculate_freight("01310-100", customer_session.cep or "01310-100")
                    freight_value = freight_result.get('valor', 15.50)
                    
                    total_value = product_value + freight_value
                    
                    # Generate PIX
                    pix_result = generate_pix(
                        nome=customer_session.nome,
                        cpf=customer_session.cpf,
                        valor=total_value,
                        descricao=f"{customer_session.produto} {customer_session.tamanho} {customer_session.opcoes} - {customer_session.quantidade} unidades"
                    )
                    
                    if pix_result.get('success'):
                        # Update customer session with PIX info
                        update_customer_session(session_id, 
                                              preco_unitario=unit_price,
                                              preco_total_produto=product_value,
                                              frete=freight_value,
                                              preco_total_final=total_value,
                                              pix_gerado=True,
                                              pix_url=pix_result.get('pix_url', ''))
                        
                        ai_response = f"""🎉 **PEDIDO FINALIZADO COM SUCESSO!**

📦 **RESUMO DO PEDIDO:**
• Produto: {customer_session.produto}
• Tamanho: {customer_session.tamanho}  
• Opções: {customer_session.opcoes}
• Quantidade: {customer_session.quantidade} unidades
• Preço unitário: R$ {unit_price:.2f}
• Subtotal produtos: R$ {product_value:.2f}
• Frete: R$ {freight_value:.2f}
• **TOTAL: R$ {total_value:.2f}**

👤 **DADOS DO CLIENTE:**
• Nome: {customer_session.nome}
• CPF: {customer_session.cpf}
• CEP: {customer_session.cep}

💳 **PAGAMENTO PIX GERADO:**
🔗 **Link para pagamento:** {pix_result.get('pix_url')}

📱 **QR Code PIX:** {pix_result.get('qr_code', 'Disponível no link acima')}

⏰ **Prazo de entrega:** {freight_result.get('prazo', '5-7 dias úteis')}

Após a confirmação do pagamento, seu pedido será processado e enviado. Obrigado por escolher a Papelaria Digital! ✨"""
                    else:
                        ai_response = f"❌ Erro ao gerar PIX: {pix_result.get('error')}. Tente novamente ou entre em contato."
                else:
                    ai_response = "❌ Produto não encontrado no catálogo. Verifique as informações do pedido."
            except Exception as e:
                logging.error(f"Error auto-generating PIX: {e}")
                ai_response += f"\n\n❌ Erro ao processar pedido: {str(e)}"
        
        # Check if AI returned JSON for PIX generation (legacy support)
        elif ai_response and ai_response.strip().startswith('{') and '"action": "generate_pix"' in ai_response:
            try:
                pix_data = json.loads(ai_response)
                if pix_data.get('action') == 'generate_pix':
                    data = pix_data.get('data', {})
                    
                    # Calculate freight first
                    freight_result = calculate_freight("01310-100", data.get('cep', '01310-100'))
                    freight_value = freight_result.get('valor', 15.50)
                    
                    # Calculate total value
                    product_value = data.get('valor_produto', 50.00)
                    total_value = product_value + freight_value
                    
                    # Generate PIX
                    pix_result = generate_pix(
                        nome=data.get('nome'),
                        cpf=data.get('cpf'),
                        valor=total_value,
                        descricao=data.get('descricao', 'Compra na Papelaria Digital')
                    )
                    
                    if pix_result.get('success'):
                        ai_response = f"""Perfeito! Seu pedido foi processado com sucesso! 

📦 **RESUMO DO PEDIDO:**
• Produto: {data.get('produto')}
• Tamanho: {data.get('tamanho')}
• Opções: {data.get('opcoes')}
• Quantidade: {data.get('quantidade')}
• Valor do produto: R$ {product_value:.2f}
• Frete: R$ {freight_value:.2f}
• **Total: R$ {total_value:.2f}**

💳 **PAGAMENTO PIX GERADO:**
Para finalizar sua compra, realize o pagamento via PIX:

🔗 **Link de pagamento:** {pix_result.get('pix_url')}

Após a confirmação do pagamento, seu pedido será processado e enviado em até 2 dias úteis.

Obrigado por escolher a Papelaria Digital! 😊"""
                    else:
                        ai_response = f"Desculpe, ocorreu um erro ao gerar o PIX: {pix_result.get('error')}. Por favor, tente novamente ou entre em contato conosco."
                        
            except json.JSONDecodeError:
                # If not valid JSON, treat as regular response
                pass
        
        # Save AI response to conversation log
        save_conversation_log(session_id, 'assistant', ai_response)
        
        return jsonify({
            "response": ai_response,
            "success": True
        })
        
    except Exception as e:
        logging.error(f"Error in chat endpoint: {e}")
        return jsonify({
            "error": "Desculpe, ocorreu um erro interno. Tente novamente.",
            "success": False
        }), 500

@app.route('/pix', methods=['POST'])
def create_pix():
    """Generate PIX payment directly"""
    try:
        data = request.get_json()
        
        required_fields = ['name', 'cpfCnpj', 'value', 'description']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Campo obrigatório: {field}"}), 400
        
        result = generate_pix(
            nome=data['name'],
            cpf=data['cpfCnpj'],
            valor=data['value'],
            descricao=data['description']
        )
        
        return jsonify(result)
        
    except Exception as e:
        logging.error(f"Error in PIX endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/reset', methods=['POST'])
def reset_conversation():
    """Reset conversation history"""
    session['conversation_history'] = []
    session['customer_data'] = {}
    session.modified = True
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
