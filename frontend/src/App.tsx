import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import Sidebar from '@/components/SideBar';
import InputArea from '@/components/InputArea';
import { FileText, Gavel, Search, Scale } from 'lucide-react';
import rtlDetect from 'rtl-detect';

interface Message {
  role: 'user' | 'ai';
  content: string;
}

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [darkMode, setDarkMode] = useState(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      return savedTheme === 'dark';
    }
    return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
  });
  const [isLoading, setIsLoading] = useState(false);
  const [currentView, setCurrentView] = useState<'chat' | 'about'>('chat');

  // Ref for auto-scrolling
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // Dark mode effect
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.documentElement.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [darkMode]);

  const handleSendMessage = async (text: string) => {
    setIsLoading(true);
    setMessages(prev => [...prev, { role: 'user', content: text }]);

    try {
      const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });
      const data = await response.json();
      setMessages(prev => [...prev, { role: 'ai', content: data.reply }]);
    } catch (error) {
      console.error("Error connecting to backend:", error);
      setMessages(prev => [...prev, { role: 'ai', content: "Error: Could not connect to the legal AI backend." }]);
    } finally {
      setIsLoading(false);
    }
  };

  const quickStarts = [
    { icon: FileText, title: "Review Family Code", desc: "Analyze marriage and custody laws." },
    { icon: Gavel, title: "Nationality Rights", desc: "Understand citizenship requirements." },
    { icon: Search, title: "Kafala Procedures", desc: "Check guardianship regulations." },
  ];

  return (
    <div className="flex h-screen bg-slate-50 text-slate-800 dark:bg-[#0f172a] dark:text-slate-100 transition-colors duration-200">
      <Sidebar darkMode={darkMode} setDarkMode={setDarkMode} currentView={currentView} setCurrentView={setCurrentView} />

      <main className="flex-1 flex flex-col overflow-hidden">
        {currentView === 'about' ? (
          <div className="flex-1 overflow-y-auto p-12">
            <div className="max-w-3xl mx-auto bg-white dark:bg-[#1e293b] p-8 rounded-2xl shadow-sm border border-slate-200 dark:border-slate-700">
              <h2 className="text-3xl font-bold mb-6 text-blue-600 dark:text-blue-500">À propos de AtlasLegalAI</h2>
              <p className="mb-6 text-lg text-slate-600 dark:text-slate-300">
                AtlasLegalAI est une application alimentée par l'intelligence artificielle conçue pour fournir des réponses et des conseils sur le droit marocain. Elle s'appuie sur une base de données de modèles linguistiques spécialisés pour analyser et interpréter les textes de loi.
              </p>

              <h3 className="text-2xl font-semibold mb-4 mt-8">Les domaines juridiques couverts</h3>
              <p className="mb-4 text-slate-600 dark:text-slate-300">L'application peut actuellement traiter et répondre aux questions concernant :</p>

              <ul className="space-y-4">
                <li className="flex items-start">
                  <div className="bg-blue-100 dark:bg-blue-900/30 p-2 rounded-lg mr-4 mt-1">
                    <FileText className="text-blue-600 dark:text-blue-400" size={20} />
                  </div>
                  <div>
                    <h4 className="font-semibold text-lg">Le Code de la Famille (Moudawana)</h4>
                    <p className="text-slate-500 dark:text-slate-400">Mariage, divorce, garde des enfants, héritage, et pension alimentaire.</p>
                  </div>
                </li>
                <li className="flex items-start">
                  <div className="bg-blue-100 dark:bg-blue-900/30 p-2 rounded-lg mr-4 mt-1">
                    <Gavel className="text-blue-600 dark:text-blue-400" size={20} />
                  </div>
                  <div>
                    <h4 className="font-semibold text-lg">Code de la Nationalité</h4>
                    <p className="text-slate-500 dark:text-slate-400">Conditions d'acquisition, de perte, et de recouvrement de la nationalité marocaine.</p>
                  </div>
                </li>
                <li className="flex items-start">
                  <div className="bg-blue-100 dark:bg-blue-900/30 p-2 rounded-lg mr-4 mt-1">
                    <Search className="text-blue-600 dark:text-blue-400" size={20} />
                  </div>
                  <div>
                    <h4 className="font-semibold text-lg">Procédures de la Kafala</h4>
                    <p className="text-slate-500 dark:text-slate-400">Prise en charge d'enfants abandonnés ou orphelins selon la législation marocaine.</p>
                  </div>
                </li>
                <li className="flex items-start">
                  <div className="bg-blue-100 dark:bg-blue-900/30 p-2 rounded-lg mr-4 mt-1">
                    <Scale className="text-blue-600 dark:text-blue-400" size={20} />
                  </div>
                  <div>
                    <h4 className="font-semibold text-lg">Droit des Obligations et des Contrats</h4>
                    <p className="text-slate-500 dark:text-slate-400">Principes généraux des contrats, obligations civil, et droits réels.</p>
                  </div>
                </li>
              </ul>

              <div className="mt-10 p-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/30 rounded-xl">
                <p className="text-amber-800 dark:text-amber-200 text-sm font-medium text-center">
                  Avertissement : Les informations fournies par AtlasLegalAI ne remplacent pas les conseils d'un avocat ou d'un professionnel du droit agréé.
                </p>
              </div>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center p-8">
            <h1 className="text-4xl font-bold mb-4">AtlasLegalAI</h1>
            <p className="text-slate-500 mb-12">Ask questions about Moroccan Law.</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl">
              {quickStarts.map((item, i) => (
                <div key={i} className="bg-white dark:bg-[#1e293b] border border-slate-200 dark:border-slate-700 p-6 rounded-2xl transition hover:shadow-lg">
                  <item.icon className="text-blue-500 mb-4" size={32} />
                  <h3 className="font-semibold mb-2">{item.title}</h3>
                  <p className="text-sm text-slate-500">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex-1 p-8 overflow-y-auto space-y-6">
            {messages.map((msg, index) => {
              const isRtl = rtlDetect.isRtlLang(rtlDetect.getLangDir(msg.content) || (msg.content.match(/[\u0600-\u06FF]/) ? 'ar' : 'en'));
              return (
                <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`p-4 rounded-xl max-w-[80%] shadow-sm ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-white dark:bg-[#1e293b] border border-slate-200 dark:border-slate-700'}`}
                    dir={isRtl ? 'rtl' : 'ltr'}
                  >
                    {/* Markdown rendering handles bolding and newlines */}
                    <ReactMarkdown>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                </div>
              );
            })}
            {isLoading && (
              <div className="flex justify-start animate-pulse text-slate-400">AI is searching the laws...</div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
        <InputArea onSend={handleSendMessage} isLoading={isLoading} />
      </main>
    </div>
  );
}

export default App;