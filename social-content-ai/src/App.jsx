import { useState } from 'react'
import { AI_PROMPTS } from './prompts'

function App() {
  const [topic, setTopic] = useState('')
  const [slides, setSlides] = useState([])
  const [loading, setLoading] = useState(false)

  const generateCarousel = () => {
    setLoading(true)
    // Simulação de geração de IA (usando os prompts da biblioteca)
    // Em produção, isso chamaria uma API passando AI_PROMPTS.carouselGenerator(topic, 'Público Alvo')
    setTimeout(() => {
      const mockSlides = [
        { slide: 1, title: 'O Segredo de ' + topic, subtitle: 'O que ninguém te conta sobre este mercado.' },
        { slide: 2, title: 'O Problema Atual', subtitle: 'Por que 90% das pessoas falham?' },
        { slide: 3, title: 'A Solução Inesperada', subtitle: 'Como reverter o jogo em 3 passos.' },
        { slide: 10, title: 'Gostou?', subtitle: 'Comente "EU QUERO" para receber o guia completo.' }
      ]
      setSlides(mockSlides)
      setLoading(false)
    }, 2000)
  }

  return (
    <div className="min-h-screen bg-dark-900 text-white p-4 md:p-12">
      <div className="max-w-6xl mx-auto">
        <header className="mb-12">
          <h1 className="text-5xl font-black mb-4 tracking-tighter">
            SOCIAL AI <span className="text-brand-500">CREATOR</span>
          </h1>
          <p className="text-gray-400">Gere carrosséis e conteúdos magnéticos em segundos.</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          {/* Editor/Input Section */}
          <div className="lg:col-span-1 space-y-6">
            <div className="glass p-8 rounded-3xl space-y-4">
              <label className="text-xs font-bold uppercase tracking-widest text-gray-500">O que vamos criar hoje?</label>
              <textarea
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder="Ex: Como vender mais usando CRM"
                className="w-full h-32 bg-dark-800 border border-white/5 rounded-2xl p-4 outline-none focus:border-brand-500 transition-all text-sm font-bold"
              />
              <button
                onClick={generateCarousel}
                disabled={loading}
                className="w-full bg-brand-500 text-white font-black py-4 rounded-2xl uppercase tracking-widest text-[11px] shadow-lg shadow-brand-500/20 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50"
              >
                {loading ? 'Consultando Oráculo...' : 'Gerar Estratégia de Conteúdo'}
              </button>
            </div>

            <div className="bg-brand-500/5 border border-brand-500/10 p-6 rounded-3xl">
              <h4 className="text-xs font-bold text-brand-500 uppercase tracking-widest mb-2">Dica do Especialista</h4>
              <p className="text-[11px] text-gray-400 leading-relaxed italic">
                "Carrosséis funcionam melhor quando você foca em uma única dor e entrega uma vitória rápida até o slide 10."
              </p>
            </div>
          </div>

          {/* Preview Section */}
          <div className="lg:col-span-2">
            <div className="flex justify-between items-end mb-6">
              <h3 className="text-xl font-bold font-display tracking-tight uppercase">Preview do <span className="text-brand-500">Carrossel</span></h3>
              <span className="text-[10px] font-bold text-gray-600">{slides.length > 0 ? slides.length + ' Slides Gerados' : 'Nenhuma geração ativa'}</span>
            </div>

            {slides.length === 0 ? (
              <div className="h-[400px] border-2 border-dashed border-white/5 rounded-[40px] flex flex-col items-center justify-center text-gray-600 gap-4">
                <i className="fas fa-magic text-4xl opacity-20"></i>
                <p className="text-sm font-bold opacity-30 uppercase tracking-[0.2em]">Aguardando seu comando</p>
              </div>
            ) : (
              <div className="flex gap-6 overflow-x-auto pb-8 snap-x">
                {slides.map((s, idx) => (
                  <div key={idx} className="min-w-[300px] aspect-square glass rounded-[40px] p-8 flex flex-col justify-between snap-center group hover:border-brand-500/30 transition-all">
                    <span className="text-[10px] font-black text-brand-500 bg-brand-500/10 px-3 py-1 rounded-full w-fit">SLIDE {s.slide}</span>
                    <div className="space-y-2">
                      <h4 className="text-2xl font-black leading-tight tracking-tight">{s.title}</h4>
                      <p className="text-sm text-gray-500 leading-relaxed font-bold">{s.subtitle}</p>
                    </div>
                    <div className="flex justify-between items-center opacity-30 group-hover:opacity-100 transition-opacity">
                      <i className="fas fa-image text-xs"></i>
                      <span className="text-[9px] font-black uppercase tracking-widest">LeadManager Pro AI</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
