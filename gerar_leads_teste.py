"""
Gera arquivo de teste com leads realistas
"""
import pandas as pd
from datetime import datetime
import random

# Dados realistas para Curitiba
nomes_barbearias = [
    "Barbearia Clássica", "Barber Shop Premium", "Corte & Estilo",
    "Barbearia Tradicional", "The Barber", "Studio do Barbeiro",
    "Barbearia Moderna", "Old School Barber", "Espaço do Homem",
    "Barbearia VIP", "Gentleman's Club", "Barba & Navalha",
    "Cut & Shave", "Barbearia Central", "Rei da Barba",
    "Studio Masculino", "Barbearia Elite", "The Shave Shop",
    "Barbearia Urbana", "Classic Barber", "Estilo Masculino",
    "Barber House", "Barbearia Executiva", "Men's Club",
    "Barbearia Premium", "Old Barber", "Espaço Masculino",
    "Barbearia do Centro", "Gentleman Barber", "Corte Fino",
    "Barbearia Retrô", "Modern Barber", "Estação do Homem",
    "Barbearia São José", "The Cut", "Barba Forte",
    "Studio Premium", "Barbearia Água Verde", "Master Barber",
    "Barbearia Batel", "Classic Cut", "Estilo Único"
]

nomes_saloes = [
    "Salão Beleza Pura", "Studio Hair", "Espaço Feminino",
    "Salão Elegance", "Beauty Center", "Cabelo & Cia",
    "Salão Glamour", "Studio de Beleza", "Art Hair",
    "Salão Charme", "Beauty Studio", "Espaço da Beleza",
    "Salão Premium", "Hair Design", "Beleza Total",
    "Studio Feminino", "Salão VIP", "Estilo Hair",
    "Salão Moderno", "Beauty House", "Cabelo Show",
    "Salão Elite", "Studio Glamour", "Espaço Hair",
    "Salão Fashion", "Beauty Art", "Cabelo Perfeito"
]

nomes_restaurantes = [
    "Restaurante Sabor da Casa", "Cantina Italiana", "Churrascaria Gaúcha",
    "Bistro Francês", "Pizzaria Bella", "Restaurante Executivo",
    "Comida Caseira", "Sushi Bar", "Restaurante Mineiro",
    "Cantinho Gourmet", "Food Station", "Restaurante Regional",
    "Buffet Premium", "Espaço Vegano", "Restaurante Contemporâneo"
]

bairros_curitiba = [
    "Centro", "Batel", "Água Verde", "Cabral", "Bigorrilho",
    "Mercês", "São Francisco", "Rebouças", "Cristo Rei", "Portão",
    "Bacacheri", "Juvevê", "Alto da XV", "Jardim Social", "Hugo Lange"
]

telefones_ddd = ["41"]

def gerar_telefone():
    """Gera telefone realista de Curitiba"""
    ddd = random.choice(telefones_ddd)
    prefixo = random.choice(["9", "8", "7"])
    numero = f"{random.randint(1000,9999)}-{random.randint(1000,9999)}"
    return f"({ddd}) {prefixo}{numero}"

def gerar_whatsapp(telefone):
    """Converte telefone para WhatsApp"""
    numeros = ''.join(filter(str.isdigit, telefone))
    if len(numeros) >= 10:
        if not numeros.startswith('55'):
            numeros = '55' + numeros
        return numeros
    return ""

# Gera leads
leads = []
lead_id = 1000

# 40 Barbearias
for i, nome in enumerate(nomes_barbearias[:40]):
    bairro = random.choice(bairros_curitiba)
    tem_telefone = random.random() > 0.1  # 90% têm telefone
    tem_site = random.random() > 0.7  # 30% têm site
    
    telefone = gerar_telefone() if tem_telefone else ""
    whatsapp = gerar_whatsapp(telefone) if telefone else ""
    
    lead = {
        'id': lead_id,
        'nome': nome,
        'telefone': telefone,
        'whatsapp': whatsapp,
        'whatsapp_link': f"https://wa.me/{whatsapp}" if whatsapp else "",
        'endereco': f"Rua Exemplo, {random.randint(100, 9999)} - {bairro}, Curitiba - PR",
        'avaliacao': round(random.uniform(3.5, 5.0), 1),
        'num_avaliacoes': f"({random.randint(10, 500)} avaliações)",
        'segmento': "Barbearia",
        'nicho': "barbearia",
        'cidade': "Curitiba, PR",
        'tem_site': tem_site,
        'website': f"https://www.{nome.lower().replace(' ', '')}.com.br" if tem_site else "",
        'google_maps_link': f"https://www.google.com/maps/place/{nome.replace(' ', '+')}",
        'contatado': random.choice(['Sim', 'Não', 'Não', 'Não']),  # 25% contactados
        'respondeu': 'Não',
        'observacoes': '',
        'data_coleta': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    leads.append(lead)
    lead_id += 1

# 35 Salões
for i, nome in enumerate(nomes_saloes[:35]):
    bairro = random.choice(bairros_curitiba)
    tem_telefone = random.random() > 0.05  # 95% têm telefone
    tem_site = random.random() > 0.6  # 40% têm site
    
    telefone = gerar_telefone() if tem_telefone else ""
    whatsapp = gerar_whatsapp(telefone) if telefone else ""
    
    lead = {
        'id': lead_id,
        'nome': nome,
        'telefone': telefone,
        'whatsapp': whatsapp,
        'whatsapp_link': f"https://wa.me/{whatsapp}" if whatsapp else "",
        'endereco': f"Av. Exemplo, {random.randint(100, 9999)} - {bairro}, Curitiba - PR",
        'avaliacao': round(random.uniform(4.0, 5.0), 1),
        'num_avaliacoes': f"({random.randint(20, 800)} avaliações)",
        'segmento': "Salão de Beleza",
        'nicho': "salão de beleza",
        'cidade': "Curitiba, PR",
        'tem_site': tem_site,
        'website': f"https://www.{nome.lower().replace(' ', '')}.com.br" if tem_site else "",
        'google_maps_link': f"https://www.google.com/maps/place/{nome.replace(' ', '+')}",
        'contatado': random.choice(['Sim', 'Não', 'Não', 'Não', 'Não']),  # 20% contactados
        'respondeu': 'Não',
        'observacoes': '',
        'data_coleta': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    leads.append(lead)
    lead_id += 1

# 25 Restaurantes
for i, nome in enumerate(nomes_restaurantes[:25]):
    bairro = random.choice(bairros_curitiba)
    tem_telefone = random.random() > 0.02  # 98% têm telefone
    tem_site = random.random() > 0.5  # 50% têm site
    
    telefone = gerar_telefone() if tem_telefone else ""
    whatsapp = gerar_whatsapp(telefone) if telefone else ""
    
    lead = {
        'id': lead_id,
        'nome': nome,
        'telefone': telefone,
        'whatsapp': whatsapp,
        'whatsapp_link': f"https://wa.me/{whatsapp}" if whatsapp else "",
        'endereco': f"Rua Gastronômica, {random.randint(100, 9999)} - {bairro}, Curitiba - PR",
        'avaliacao': round(random.uniform(3.8, 4.9), 1),
        'num_avaliacoes': f"({random.randint(50, 1500)} avaliações)",
        'segmento': "Restaurante",
        'nicho': "restaurante",
        'cidade': "Curitiba, PR",
        'tem_site': tem_site,
        'website': f"https://www.{nome.lower().replace(' ', '')}.com.br" if tem_site else "",
        'google_maps_link': f"https://www.google.com/maps/place/{nome.replace(' ', '+')}",
        'contatado': random.choice(['Sim', 'Não', 'Não']),  # 33% contactados
        'respondeu': 'Não',
        'observacoes': '',
        'data_coleta': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    leads.append(lead)
    lead_id += 1

# Cria DataFrame
df = pd.DataFrame(leads)

# Salva Excel
output_file = "dados_teste/leads_teste_100.xlsx"
import os
os.makedirs("dados_teste", exist_ok=True)

df.to_excel(output_file, index=False, engine='openpyxl')

print(f"✅ Arquivo criado: {output_file}")
print(f"📊 Total de leads: {len(leads)}")
print(f"🎯 Barbearias: {len([l for l in leads if l['nicho'] == 'barbearia'])}")
print(f"💇 Salões: {len([l for l in leads if l['nicho'] == 'salão de beleza'])}")
print(f"🍽️  Restaurantes: {len([l for l in leads if l['nicho'] == 'restaurante'])}")
print(f"✅ Com WhatsApp: {len([l for l in leads if l['whatsapp']])}")
print(f"🚫 Sem Site: {len([l for l in leads if not l['tem_site']])}")
print(f"⭐ Qualificados (sem site + WhatsApp): {len([l for l in leads if not l['tem_site'] and l['whatsapp']])}")
