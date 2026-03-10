/**
 * BIBLIOTECA DE PROMPTS - SOCIAL AI CREATOR
 * 
 * Este arquivo contém os prompts mestres que serão enviados para a API de IA.
 * Eles foram desenhados para gerar conteúdo de alta conversão (High-Stakes Content).
 */

export const AI_PROMPTS = {
    // 1. Prompt para Estrutura de Carrossel (Slides 1-10)
    carouselGenerator: (topic, audience) => `
Você é um estrategista de conteúdo sênior especializado em Instagram e LinkedIn.
Sua missão é criar um carrossel de 10 slides sobre o tema: "${topic}".
O público-alvo é: "${audience}".

Use a estrutura AIDA (Atenção, Interesse, Desejo, Ação):

REGRAS:
- Slide 1: Gancho Irresistível (Hook). Curto, impactante, que resolva uma dor ou gere curiosidade.
- Slides 2-4: Identificação do problema e conscientização.
- Slides 5-8: A solução, passos práticos ou insights valiosos.
- Slide 9: Resumo/Checklist rápido.
- Slide 10: Call to Action (CTA) forte.

FORMATO DE RESPOSTA (JSON):
[
  { "slide": 1, "title": "...", "subtitle": "..." },
  ...
]
`,

    // 2. Prompt para Legendas de Alto Engajamento
    captionGenerator: (topic) => `
Crie uma legenda magnética para um post sobre "${topic}".
Estrutura:
1. Gancho (primeira linha impactante).
2. Desenvolvimento (3 a 4 parágrafos curtos).
3. Espaçamento duplo para facilitar a leitura.
4. Call to Action (pergunta para comentário).
5. 5 Hashtags estratégicas.
`,

    // 3. Prompt para Persona Digital
    personaAnalyzer: (niche) => `
Analise o nicho "${niche}" e defina a Persona Ideal (Avatar).
- Dores latentes.
- Desejos profundos.
- Objeções comuns.
- Estilo de comunicação (formal, descontraído, disruptivo).
`
};
