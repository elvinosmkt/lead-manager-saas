"""
Gerenciamento de Banco de Dados para o SaaS
- Usuários
- Créditos
- Histórico de Uso
"""
import sqlite3
import hashlib
from datetime import datetime
import os

DB_NAME = "lead_manager.db"

def init_db():
    """Inicializa o banco de dados"""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Tabela de Usuários
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT,
            credits INTEGER DEFAULT 0,
            plan_type TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de Histórico de Uso
    c.execute('''
        CREATE TABLE IF NOT EXISTS usage_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT,
            amount INTEGER,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Tabela de Leads Salvos (para o usuário não perder)
    c.execute('''
        CREATE TABLE IF NOT EXISTS saved_leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            whatsapp TEXT,
            website TEXT,
            nicho TEXT,
            cidade TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Cria usuário admin padrão se não existir
    try:
        admin_email = "admin@leadmanager.com"
        # Senha padrão: admin123
        password_hash = hashlib.sha256("admin123".encode()).hexdigest()
        
        c.execute('SELECT * FROM users WHERE email = ?', (admin_email,))
        if not c.fetchone():
            c.execute('''
                INSERT INTO users (email, password_hash, name, credits, plan_type)
                VALUES (?, ?, ?, ?, ?)
            ''', (admin_email, password_hash, "Administrador", 5000, "premium"))
            print("👤 Usuário Admin criado: admin@leadmanager.com / admin123")
    except Exception as e:
        print(f"Erro ao criar admin: {e}")
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado!")

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# Inicializa agora
if __name__ == "__main__":
    init_db()
