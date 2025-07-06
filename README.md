# 🏪 Loteria Imperatriz - Sistema Online

Sistema web moderno para controle financeiro de lotéricas, **pronto para deploy online**!

## 🌐 **DEPLOY ONLINE - FÁCIL!**

### 🚀 **Opção 1: Render (Recomendado)**
1. Suba os arquivos no GitHub
2. Crie conta em https://render.com
3. Conecte seu repositório
4. **Deploy automático!**

**Seu link:** `https://loteria-imperatriz.onrender.com`

### 🚀 **Opção 2: Railway**
1. Suba no GitHub
2. Acesse https://railway.app
3. Deploy direto do GitHub
4. **Pronto!**

**Seu link:** `https://loteria-imperatriz.up.railway.app`

📖 **Instruções detalhadas:** [DEPLOY_ONLINE.md](DEPLOY_ONLINE.md)

---

## ✨ **Funcionalidades**

### 📊 **Dashboard Inteligente**
- Visão consolidada de todos os 6 caixas
- Totais automáticos de suprimentos e sangrias
- Alertas visuais para inconsistências
- Interface responsiva (funciona no celular)

### 💰 **Controle Individual**
- **Movimentações detalhadas** lado a lado
- **Seleção de data** com navegação ◄ ►
- **Saldo inicial automático** do dia anterior
- **Cálculos automáticos** de diferenças
- **Observações** para cada fechamento

### 🏢 **Caixa Central**
- **Consolidação automática** de todos os caixas
- **Auditoria rápida** com status coloridos
- **Totais gerais** em tempo real
- **Detalhamento por caixa**

### 📈 **Histórico Completo**
- **Dados preservados** por data
- **Filtros avançados** por período
- **Nunca sobrescreve** informações
- **Busca rápida** por caixa

---

## 🎨 **Design Moderno**

### 🎯 **Interface Intuitiva**
- Layout limpo e profissional
- Cores suaves (azul/verde)
- Botões grandes e fáceis de usar
- Navegação simples

### 📱 **Responsivo**
- Funciona em qualquer dispositivo
- Otimizado para celular e tablet
- Interface adaptável
- Touch-friendly

---

## 🔧 **Tecnologias**

- **Backend**: Flask (Python)
- **Frontend**: HTML5 + CSS3 + JavaScript
- **Banco**: SQLite (local) ou PostgreSQL (online)
- **Deploy**: Render, Railway, Heroku

---

## 📦 **Estrutura do Projeto**

```
loteria-imperatriz/
├── app.py              # Aplicação principal
├── requirements.txt    # Dependências Python
├── Procfile           # Configuração Heroku/Railway
├── runtime.txt        # Versão Python
├── Dockerfile         # Container Docker
├── render.yaml        # Configuração Render
├── static/            # Arquivos frontend
│   ├── index.html     # Interface principal
│   ├── css/style.css  # Estilos
│   └── js/app.js      # JavaScript
└── DEPLOY_ONLINE.md   # Guia de deploy
```

---

## 🚀 **Execução Local** (Opcional)

Se quiser testar localmente antes do deploy:

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar aplicação
python app.py

# Acessar
http://localhost:5000
```

---

## 🌟 **Vantagens do Sistema Online**

### ✅ **Acesso Universal**
- Funciona de qualquer lugar
- Qualquer dispositivo
- Sem instalação

### ✅ **Colaborativo**
- Múltiplos usuários
- Dados sincronizados
- Acesso simultâneo

### ✅ **Seguro**
- Backup automático
- Dados na nuvem
- Sempre disponível

### ✅ **Profissional**
- Link personalizado
- Interface moderna
- Confiável 24/7

---

## 📱 **Como Usar**

### 1. **Dashboard**
- Página inicial com resumo geral
- Clique em qualquer caixa para detalhes

### 2. **Controle de Caixa**
- Selecione a data
- Adicione suprimentos (esquerda)
- Adicione sangrias (direita)
- Informe valor da máquina
- Salve o fechamento

### 3. **Navegação**
- Use ◄ ► para mudar de dia
- Menu superior para outras páginas

### 4. **Caixa Central**
- Visão consolidada
- Auditoria rápida
- Status de todos os caixas

---

## 🔒 **Segurança**

- Validação de dados
- Proteção contra SQL injection
- CORS configurado
- Logs de auditoria

---

## 📞 **Suporte**

- 📖 [Guia de Deploy](DEPLOY_ONLINE.md)
- 🐛 [Issues no GitHub](../../issues)
- 📧 Suporte: suporte@loteriaimperatriz.com

---

## 📝 **Licença**

MIT License - Livre para uso comercial

---

**🎉 Desenvolvido especialmente para a Loteria Imperatriz**

**🌐 Sistema moderno, online e profissional!**

