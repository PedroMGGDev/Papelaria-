import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class CustomerSession(db.Model):
    """Model to store customer session data and order progress"""
    __tablename__ = 'customer_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), unique=True, nullable=False)
    
    # Customer Information
    nome = db.Column(db.String(255))
    cpf = db.Column(db.String(11))
    telefone = db.Column(db.String(15))
    endereco_completo = db.Column(db.Text)
    cep = db.Column(db.String(8))
    
    # Product Information
    produto = db.Column(db.String(255))
    tamanho = db.Column(db.String(50))
    opcoes = db.Column(db.String(255))
    quantidade = db.Column(db.Integer)
    numero_paginas = db.Column(db.Integer)  # For products with page pricing
    
    # Pricing Information
    preco_unitario = db.Column(db.Numeric(10, 2))
    preco_total_produto = db.Column(db.Numeric(10, 2))
    frete = db.Column(db.Numeric(10, 2))
    preco_total_final = db.Column(db.Numeric(10, 2))
    
    # Order Status
    status = db.Column(db.String(50), default='em_andamento')  # em_andamento, completo, cancelado
    pix_gerado = db.Column(db.Boolean, default=False)
    pix_url = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<CustomerSession {self.session_id}: {self.produto}>'
    
    def to_dict(self):
        """Convert session to dictionary for easy access"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'nome': self.nome,
            'cpf': self.cpf,
            'telefone': self.telefone,
            'endereco_completo': self.endereco_completo,
            'cep': self.cep,
            'produto': self.produto,
            'tamanho': self.tamanho,
            'opcoes': self.opcoes,
            'quantidade': self.quantidade,
            'numero_paginas': self.numero_paginas,
            'preco_unitario': float(self.preco_unitario) if self.preco_unitario else None,
            'preco_total_produto': float(self.preco_total_produto) if self.preco_total_produto else None,
            'frete': float(self.frete) if self.frete else None,
            'preco_total_final': float(self.preco_total_final) if self.preco_total_final else None,
            'status': self.status,
            'pix_gerado': self.pix_gerado,
            'pix_url': self.pix_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_missing_fields(self):
        """Get list of required fields that are still empty"""
        required_fields = {
            'produto': self.produto,
            'tamanho': self.tamanho,
            'opcoes': self.opcoes,
            'quantidade': self.quantidade,
            'nome': self.nome,
            'cpf': self.cpf,
            'endereco_completo': self.endereco_completo,
            'cep': self.cep
        }
        
        missing = []
        for field, value in required_fields.items():
            if not value:
                missing.append(field)
        
        return missing
    
    def is_complete(self):
        """Check if all required fields are filled"""
        return len(self.get_missing_fields()) == 0
    
    def update_field(self, field_name, value):
        """Update a specific field in the session"""
        if hasattr(self, field_name):
            setattr(self, field_name, value)
            self.updated_at = datetime.utcnow()
            return True
        return False

class ConversationLog(db.Model):
    """Model to store conversation history"""
    __tablename__ = 'conversation_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ConversationLog {self.session_id}: {self.role}>'